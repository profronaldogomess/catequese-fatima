# ==============================================================================
# ARQUIVO: database.py
# VERSÃO: 4.0.0 - BLINDAGEM DE DADOS E PREVENÇÃO DE CORRUPÇÃO
# MISSÃO: Motor de Dados Eclesiástico com Segurança de Sessão Única e Cookies.
# ==============================================================================

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import time
import uuid
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import random

SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def conectar_google_sheets():
    """Conexão com tratamento de erro explícito para diagnóstico."""
    try:
        if "gcp_service_account" in st.secrets:
            info_do_cofre = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(info_do_cofre, scopes=SCOPE)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
        
        client = gspread.authorize(creds)
        return client.open("BD_Catequese")
    except Exception as e:
        st.error(f"Erro de Conexão com Google Sheets: {str(e)}")
        return None

# --- 1. MOTOR DE LEITURA COM CACHE INTELIGENTE E RESILIÊNCIA (DEFESA CONTRA ERRO 429) ---

@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1.5, min=2, max=10))
def _fetch_sheet_data(planilha, nome_aba):
    """Função interna com motor de resiliência (Tenacity) para atuar como Buffer contra o Erro 429."""
    aba = planilha.worksheet(nome_aba)
    return aba.get_all_values()

@st.cache_data(ttl=60) 
def ler_aba(nome_aba):
    """Lê qualquer aba e retorna um DataFrame. Cache de 60s e Retry contra Erro 429."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            todos_os_valores = _fetch_sheet_data(planilha, nome_aba)
            if not todos_os_valores or len(todos_os_valores) < 1:
                return pd.DataFrame()
            headers = [str(h).strip().lower() for h in todos_os_valores[0]]
            headers =[h if h != "" else f"col_{i}" for i, h in enumerate(headers)]
            data = todos_os_valores[1:]
            num_cols = len(headers)
            data_ajustada =[]
            for row in data:
                row_fixed = list(row)
                if len(row_fixed) < num_cols:
                    row_fixed.extend([""] * (num_cols - len(row_fixed)))
                data_ajustada.append(row_fixed[:num_cols])
            df = pd.DataFrame(data_ajustada, columns=headers)
            return df
        except Exception as e:
            # Se falhar mesmo após as 4 tentativas de buffer, retorna vazio para o Gatekeeper atuar
            return pd.DataFrame()
    return pd.DataFrame()

# --- 2. NOVAS FUNÇÕES DE INFRAESTRUTURA E SEGURANÇA ---

@st.cache_data(ttl=60)
def verificar_status_sistema():
    """Consulta a aba 'config' para travar o sistema se necessário."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("config")
            status = aba.acell('B2').value
            return status.upper() if status else "ONLINE"
        except:
            return "ONLINE"
    return "ONLINE"

def atualizar_session_id(email, novo_id):
    """Grava o UUID estritamente na Coluna 13 (M)."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("usuarios")
            celula = aba.find(str(email), in_column=2) # Busca estritamente na coluna de E-mail (B)
            if celula:
                aba.update_cell(celula.row, 13, str(novo_id))
                st.cache_data.clear()
                return True
        except: pass
    return False

@st.cache_data(ttl=30)
def obter_session_id_db(email):
    if not email: return ""
    df_usuarios = ler_aba("usuarios")
    if not df_usuarios.empty and 'email' in df_usuarios.columns:
        usuario = df_usuarios[df_usuarios['email'] == email]
        if not usuario.empty:
            try:
                # Busca na 14ª coluna (índice 13)
                return str(usuario.iloc[0].iloc[13]) 
            except: return ""
    return ""

# --- 3. FUNÇÕES PASTORAIS E DE GESTÃO (INTEGRIDADE TOTAL) ---

def salvar_lote_catequizandos(lista_de_listas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            ids_existentes = aba.col_values(1) # Coluna A
            lista_filtrada = [linha for linha in lista_de_listas if linha[0] not in ids_existentes]
            
            if lista_filtrada:
                aba.append_rows(lista_filtrada)
                st.cache_data.clear()
            return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def salvar_presencas(lista_presencas):
    """Salva presenças e sincroniza em cascata com Diário e Cronograma."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        aba_pres = planilha.worksheet("presencas")
        aba_enc = planilha.worksheet("encontros")
        
        data_alvo = str(lista_presencas[0][0]).strip()
        turma_alvo = str(lista_presencas[0][3]).strip().upper()
        tema_alvo = str(lista_presencas[0][5]).strip().upper()
        catequista = str(lista_presencas[0][6]).strip()

        # 1. Limpa presenças antigas do dia/turma (para reescrever as novas)
        dados = aba_pres.get_all_values()
        linhas_del =[i + 1 for i, linha in enumerate(dados) if len(linha) >= 4 and linha[0] == data_alvo and linha[3].strip().upper() == turma_alvo]
        for row_idx in sorted(linhas_del, reverse=True): 
            aba_pres.delete_rows(row_idx)
        
        # 2. Salva as novas presenças com o tema (novo ou editado)
        aba_pres.append_rows(lista_presencas)
        
        # 3. Sincronia em Cascata com a aba ENCONTROS (Diário)
        dados_enc = aba_enc.get_all_values()
        linha_existente = None
        for i, linha in enumerate(dados_enc):
            if len(linha) >= 2 and str(linha[0]) == data_alvo and str(linha[1]).strip().upper() == turma_alvo:
                linha_existente = i + 1
                break
        
        if linha_existente:
            # Se o encontro já existe, ATUALIZA o tema (modo edição pela chamada)
            aba_enc.update_cell(linha_existente, 3, tema_alvo)
        else:
            # Se não existe, CRIA um novo (modo criação pela chamada)
            aba_enc.append_row([data_alvo, turma_alvo, tema_alvo, catequista, "Registro automático via Chamada"])
            
        # 4. Sincronia em Cascata com a aba CRONOGRAMA
        marcar_tema_realizado_cronograma(turma_alvo, tema_alvo)
        
        st.cache_data.clear()
        return True
    except Exception as e: 
        st.error(f"Erro na sincronia da chamada: {e}")
        return False

def salvar_encontro(dados_encontro):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("encontros")
            aba.append_row(dados_encontro)
            st.cache_data.clear(); return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def atualizar_catequizando(id_catequizando, novos_dados_lista):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            celula = aba.find(str(id_catequizando), in_column=1) # Busca estrita na Coluna A
            if celula:
                # RIGOR 30 COLUNAS: Preenche com N/A se faltar dado, corta se sobrar
                dados_seguros = novos_dados_lista + ["N/A"] * (30 - len(novos_dados_lista)) if len(novos_dados_lista) < 30 else novos_dados_lista[:30]
                aba.update(f"A{celula.row}:AD{celula.row}", [dados_seguros])
                st.cache_data.clear(); return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def mover_catequizandos_em_massa(lista_ids, nova_turma):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            headers = [h.lower() for h in aba.row_values(1)]
            col_id = headers.index("id_catequizando") + 1
            col_etapa = headers.index("etapa") + 1
            for cid in lista_ids:
                celula = aba.find(str(cid), in_column=col_id)
                if celula: aba.update_cell(celula.row, col_etapa, nova_turma)
            st.cache_data.clear(); return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def excluir_turma(id_turma):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("turmas")
            celula = aba.find(str(id_turma), in_column=1) # Busca estrita na Coluna A
            if celula:
                aba.delete_rows(celula.row)
                st.cache_data.clear(); return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def verificar_login(email, senha):
    try:
        df_usuarios = ler_aba("usuarios") 
        if df_usuarios.empty: return None
        usuario = df_usuarios[(df_usuarios['email'].astype(str) == str(email)) & (df_usuarios['senha'].astype(str) == str(senha))]
        if not usuario.empty: return usuario.iloc[0].to_dict()
    except: return None
    return None

def buscar_encontro_por_data(turma, data_procurada):
    try:
        df_enc = ler_aba("encontros")
        if not df_enc.empty:
            filtro = df_enc[(df_enc['turma'] == turma) & (df_enc['data'].astype(str) == str(data_procurada))]
            if not filtro.empty: return filtro.iloc[-1]['tema']
    except: pass
    return None

def salvar_tema_cronograma(dados_tema):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("cronograma"); aba.append_row(dados_tema)
            st.cache_data.clear(); return True
        except: return False
    return False

def atualizar_turma(id_turma, novos_dados_lista):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("turmas")
            celula = aba.find(str(id_turma), in_column=1) # Busca estrita na Coluna A
            if celula:
                # RIGOR 10 COLUNAS: Atualiza de A até J
                dados_seguros = novos_dados_lista + [""] * (10 - len(novos_dados_lista)) if len(novos_dados_lista) < 10 else novos_dados_lista[:10]
                aba.update(f"A{celula.row}:J{celula.row}", [dados_seguros])
                st.cache_data.clear(); return True
        except: return False
    return False

def atualizar_usuario(email_original, novos_dados_lista):
    """Atualiza o perfil completo respeitando as 14 colunas (A até N)."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("usuarios")
            celula = aba.find(str(email_original), in_column=2) # Busca estrita na Coluna B (Email)
            if celula:
                # Garante que a lista tenha exatamente 14 itens antes de gravar
                dados_seguros = novos_dados_lista + [""] * (14 - len(novos_dados_lista)) if len(novos_dados_lista) < 14 else novos_dados_lista[:14]
                aba.update(f"A{celula.row}:N{celula.row}", [dados_seguros], value_input_option='USER_ENTERED')
                st.cache_data.clear()
                return True
        except: pass
    return False

def salvar_formacao(dados_lista):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("formacoes"); aba.append_row(dados_lista)
            st.cache_data.clear(); return True
        except: return False
    return False

def salvar_presenca_formacao(lista_presencas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("presenca_formacao"); aba.append_rows(lista_presencas)
            st.cache_data.clear(); return True
        except: return False
    return False

def registrar_evento_sacramento_completo(dados_evento, lista_participantes, tipo_sacramento):
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        planilha.worksheet("sacramentos_eventos").append_row(dados_evento)
        planilha.worksheet("sacramentos_recebidos").append_rows(lista_participantes)
        aba_cat = planilha.worksheet("catequizandos")
        headers = [h.lower() for h in aba_cat.row_values(1)]
        col_id = headers.index("id_catequizando") + 1
        col_batizado = headers.index("batizado_sn") + 1
        col_sacramentos = headers.index("sacramentos_ja_feitos") + 1
        for p in lista_participantes:
            id_cat = p[1]
            celula = aba_cat.find(str(id_cat), in_column=col_id)
            if celula:
                if tipo_sacramento == "BATISMO":
                    aba_cat.update_cell(celula.row, col_batizado, "SIM")
                else:
                    valor_atual = aba_cat.cell(celula.row, col_sacramentos).value or ""
                    if tipo_sacramento not in valor_atual.upper():
                        novo_valor = f"{valor_atual}, {tipo_sacramento}".strip(", ")
                        aba_cat.update_cell(celula.row, col_sacramentos, novo_valor.upper())
        st.cache_data.clear(); return True
    except Exception as e:
        st.error(f"Erro crítico: {e}"); return False

def excluir_tema_cronograma(turma, titulo_tema):
    """Remove um tema do cronograma após ele ser realizado."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("cronograma")
            celulas = aba.findall(str(titulo_tema))
            for celula in celulas:
                if aba.cell(celula.row, 2).value == turma:
                    aba.delete_rows(celula.row)
                    st.cache_data.clear()
                    return True
        except: pass
    return False

# --- NOVAS FUNÇÕES DE SINCRONIZAÇÃO EM CASCATA ---

def sincronizar_renomeacao_turma_geral(nome_antigo, nome_novo):
    """Varre TODAS as abas e atualiza o nome da turma (Efeito Cascata)."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        # 1. Catequizandos (Coluna B - etapa)
        aba_cat = planilha.worksheet("catequizandos")
        celulas_cat = aba_cat.findall(str(nome_antigo), in_column=2)
        for cel in celulas_cat: aba_cat.update_cell(cel.row, 2, nome_novo)
        
        # 2. Presenças (Coluna D - id_turma)
        aba_pres = planilha.worksheet("presencas")
        celulas_pres = aba_pres.findall(str(nome_antigo), in_column=4)
        for cel in celulas_pres: aba_pres.update_cell(cel.row, 4, nome_novo)
        
        # 3. Encontros (Coluna B - turma)
        aba_enc = planilha.worksheet("encontros")
        celulas_enc = aba_enc.findall(str(nome_antigo), in_column=2)
        for cel in celulas_enc: aba_enc.update_cell(cel.row, 2, nome_novo)
        
        # 4. Cronograma (Coluna B - etapa)
        aba_cron = planilha.worksheet("cronograma")
        celulas_cron = aba_cron.findall(str(nome_antigo), in_column=2)
        for cel in celulas_cron: aba_cron.update_cell(cel.row, 2, nome_novo)
        
        # 5. Reuniões de Pais (Coluna D - turma_alvo)
        aba_reu = planilha.worksheet("reunioes_pais")
        celulas_reu = aba_reu.findall(str(nome_antigo), in_column=4)
        for cel in celulas_reu: aba_reu.update_cell(cel.row, 4, nome_novo)
        
        # 6. Presença Reunião (Coluna D - turma)
        aba_pres_reu = planilha.worksheet("presenca_reuniao")
        celulas_pres_reu = aba_pres_reu.findall(str(nome_antigo), in_column=4)
        for cel in celulas_pres_reu: aba_pres_reu.update_cell(cel.row, 4, nome_novo)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro na sincronia em cascata: {e}")
        return False

def sincronizar_logistica_turma_nos_catequizandos(nome_turma, novo_turno, novo_local):
    """Atualiza Turno e Local de todos os catequizandos vinculados a uma turma."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        aba_cat = planilha.worksheet("catequizandos")
        celulas = aba_cat.findall(str(nome_turma), in_column=2)
        for cel in celulas:
            aba_cat.update_cell(cel.row, 28, novo_turno) # Coluna 28 (AB)
            aba_cat.update_cell(cel.row, 29, novo_local)  # Coluna 29 (AC)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro na logistica: {e}")
        return False

def sincronizar_renomeacao_catequista(nome_antigo, nome_novo):
    """Atualiza o nome do catequista nas turmas e históricos."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        # Turmas
        aba_t = planilha.worksheet("turmas")
        dados_t = aba_t.get_all_values()
        for i, linha in enumerate(dados_t[1:], start=2):
            cats =[c.strip() for c in str(linha[4]).split(',') if c.strip()]
            if nome_antigo in cats:
                cats = [nome_novo if c == nome_antigo else c for c in cats]
                aba_t.update_cell(i, 5, ", ".join(cats))
        # Encontros
        aba_enc = planilha.worksheet("encontros")
        celulas_enc = aba_enc.findall(str(nome_antigo), in_column=4)
        for cel in celulas_enc: aba_enc.update_cell(cel.row, 4, nome_novo)
        # Sacramentos
        aba_sac = planilha.worksheet("sacramentos_eventos")
        celulas_sac = aba_sac.findall(str(nome_antigo), in_column=5)
        for cel in celulas_sac: aba_sac.update_cell(cel.row, 5, nome_novo)
        st.cache_data.clear()
        return True
    except: return False

def limpar_lixo_turma_excluida(nome_turma):
    """Remove registros órfãos de uma turma excluída."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        abas_colunas = [("cronograma", 2), ("encontros", 2), ("presencas", 4), ("reunioes_pais", 4), ("presenca_reuniao", 4)]
        for nome_aba, col in abas_colunas:
            aba = planilha.worksheet(nome_aba)
            celulas = aba.findall(str(nome_turma), in_column=col)
            for cel in sorted(celulas, key=lambda x: x.row, reverse=True):
                aba.delete_rows(cel.row)
        st.cache_data.clear()
        return True
    except: return False

def atualizar_evento_sacramento(id_evento, novos_dados):
    """Atualiza os dados de um evento na aba sacramentos_eventos."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("sacramentos_eventos")
            celula = aba.find(str(id_evento), in_column=1)
            if celula:
                aba.update(f"A{celula.row}:E{celula.row}", [novos_dados])
                st.cache_data.clear()
                return True
        except: pass
    return False

def atualizar_formacao(id_f, novos_dados):
    """Atualiza os dados de uma formação na aba formacoes."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("formacoes")
            celula = aba.find(str(id_f), in_column=1)
            if celula:
                aba.update(f"A{celula.row}:F{celula.row}", [novos_dados])
                st.cache_data.clear()
                return True
        except: pass
    return False

def excluir_formacao_completa(id_f):
    """Exclui a formação e todas as presenças vinculadas a ela."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba_f = planilha.worksheet("formacoes")
            cel_f = aba_f.find(str(id_f), in_column=1)
            if cel_f: aba_f.delete_rows(cel_f.row)
            
            aba_p = planilha.worksheet("presenca_formacao")
            celulas_p = aba_p.findall(str(id_f), in_column=1)
            for cel in sorted(celulas_p, key=lambda x: x.row, reverse=True):
                aba_p.delete_rows(cel.row)
                
            st.cache_data.clear()
            return True
        except: pass
    return False

def salvar_reuniao_pais(dados_lista):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("reunioes_pais")
            aba.append_row(dados_lista)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar reunião: {e}")
            return False
    return False

def salvar_presenca_reuniao_pais(lista_presencas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("presenca_reuniao")
            aba.append_rows(lista_presencas)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar presenças: {e}")
            return False
    return False

def atualizar_reuniao_pais(id_r, novos_dados):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("reunioes_pais")
            celula = aba.find(str(id_r), in_column=1)
            if celula:
                aba.update(f"A{celula.row}:F{celula.row}", [novos_dados])
                st.cache_data.clear()
                return True
        except Exception as e:
            st.error(f"Erro ao atualizar reunião: {e}")
            return False
    return False

def atualizar_encontro_existente(data_e, turma_e, novos_dados):
    """Atualiza um registro de encontro baseado na data e turma."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("encontros")
            celulas_data = aba.findall(str(data_e), in_column=1)
            for celula in celulas_data:
                if aba.cell(celula.row, 2).value == turma_e:
                    aba.update(f"A{celula.row}:E{celula.row}", [novos_dados])
                    st.cache_data.clear()
                    return True
        except Exception as e:
            st.error(f"Erro ao atualizar diário: {e}")
    return False

def marcar_tema_realizado_cronograma(turma, tema):
    """Em vez de excluir, marca como REALIZADO na Coluna E do cronograma."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("cronograma")
            celulas = aba.findall(str(tema))
            for celula in celulas:
                if aba.cell(celula.row, 2).value == turma:
                    aba.update_cell(celula.row, 5, "REALIZADO")
                    st.cache_data.clear()
                    return True
        except: pass
    return False

def adicionar_novo_usuario(dados_usuario):
    """Adiciona novo usuário calculando a próxima linha real (A até N)."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("usuarios")
            proxima_linha = len(aba.col_values(1)) + 1
            dados_seguros = dados_usuario + [""] * (14 - len(dados_usuario)) if len(dados_usuario) < 14 else dados_usuario[:14]
            aba.update(f"A{proxima_linha}:N{proxima_linha}", [dados_seguros], value_input_option='USER_ENTERED')
            st.cache_data.clear()
            return True
        except: return False
    return False

def sincronizar_logistica_turma_nos_catequizandos(nome_turma, novo_turno, novo_local):
    """Atualiza Turno e Local de todos os catequizandos vinculados a uma turma."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        aba_cat = planilha.worksheet("catequizandos")
        # Localiza todos os catequizandos daquela turma (Coluna B - Etapa)
        celulas = aba_cat.findall(str(nome_turma), in_column=2)
        
        for cel in celulas:
            # Coluna 28 (AB) = Turno | Coluna 29 (AC) = Local
            aba_cat.update_cell(cel.row, 28, novo_turno)
            aba_cat.update_cell(cel.row, 29, novo_local)
            
        st.cache_data.clear()
        return True
    except: return False

@st.cache_data(ttl=600) # Cache de 10 minutos para evitar bloqueio
def carregar_dados_globais():
    """Carrega todas as abas essenciais de uma única vez."""
    planilha = conectar_google_sheets()
    if not planilha: return None
    
    # Retorna um dicionário com os DataFrames
    return {
        "catequizandos": ler_aba("catequizandos"),
        "turmas": ler_aba("turmas"),
        "presencas": ler_aba("presencas"),
        "usuarios": ler_aba("usuarios"),
        "sacramentos_eventos": ler_aba("sacramentos_eventos"),
        "presenca_reuniao": ler_aba("presenca_reuniao"),
        "cronograma": ler_aba("cronograma"),
        "encontros": ler_aba("encontros")
    }

def atualizar_encontro_e_cronograma(id_encontro, turma, data, novo_tema, novo_relato, catequista):
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        # 1. Atualiza a aba 'encontros'
        aba_enc = planilha.worksheet("encontros")
        # Busca pela linha que tem a data e turma
        celulas = aba_enc.findall(str(data), in_column=1)
        for cel in celulas:
            if aba_enc.cell(cel.row, 2).value == turma:
                aba_enc.update(f"A{cel.row}:E{cel.row}", [[str(data), turma, novo_tema, catequista, novo_relato]])
        
        # 2. Atualiza o status no 'cronograma' (marca o novo tema como REALIZADO)
        aba_cron = planilha.worksheet("cronograma")
        cel_cron = aba_cron.findall(novo_tema)
        for cel in cel_cron:
            if aba_cron.cell(cel.row, 2).value == turma:
                aba_cron.update_cell(cel.row, 5, "REALIZADO")
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro na sincronia: {e}")
        return False
    
def sincronizar_edicao_catequizando(id_cat, novo_nome, nova_turma):
    """
    Sincroniza alterações de nome e turma em todas as abas dependentes.
    Isso garante que o histórico de presenças não seja perdido.
    """
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        # 1. Atualiza nome na aba 'presencas'
        aba_pres = planilha.worksheet("presencas")
        dados_pres = aba_pres.get_all_values()
        for i, linha in enumerate(dados_pres):
            if len(linha) >= 2 and linha[1] == id_cat:
                # Atualiza nome (coluna 3) e turma (coluna 4)
                aba_pres.update_cell(i + 1, 3, novo_nome)
                aba_pres.update_cell(i + 1, 4, nova_turma)
        
        # 2. Atualiza nome na aba 'sacramentos_recebidos'
        aba_sac = planilha.worksheet("sacramentos_recebidos")
        dados_sac = aba_sac.get_all_values()
        for i, linha in enumerate(dados_sac):
            if len(linha) >= 2 and linha[1] == id_cat:
                aba_sac.update_cell(i + 1, 3, novo_nome)
                
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro na sincronia em cascata: {e}")
        return False
    
def salvar_com_seguranca(funcao_salvar, *args):
    """
    Adiciona um pequeno atraso aleatório para evitar colisões de escrita 
    quando múltiplos catequistas salvam ao mesmo tempo.
    """
    time.sleep(random.uniform(0.5, 2.0)) # Atraso aleatório entre 0.5s e 2s
    return funcao_salvar(*args)

def atualizar_encontro_global(turma, data_alvo, novo_tema, nova_obs):
    """
    Atualiza o tema e relato em cascata: Encontros, Presenças e Cronograma.
    Garante a integridade referencial do banco de dados.
    """
    planilha = conectar_google_sheets()
    if not planilha: return False
    
    try:
        turma_norm = turma.strip().upper()
        tema_norm = novo_tema.strip().upper()
        data_str = str(data_alvo)

        # 1. Atualizar aba ENCONTROS (Coluna 3 = Tema, Coluna 5 = Observações)
        aba_enc = planilha.worksheet("encontros")
        dados_enc = aba_enc.get_all_values()
        for i, linha in enumerate(dados_enc):
            if len(linha) >= 2 and str(linha[0]) == data_str and str(linha[1]).strip().upper() == turma_norm:
                aba_enc.update_cell(i + 1, 3, tema_norm)
                aba_enc.update_cell(i + 1, 5, nova_obs)

        # 2. Atualizar aba PRESENCAS (Coluna 6 = Tema do Dia)
        aba_pres = planilha.worksheet("presencas")
        dados_pres = aba_pres.get_all_values()
        for i, linha in enumerate(dados_pres):
            if len(linha) >= 4 and str(linha[0]) == data_str and str(linha[3]).strip().upper() == turma_norm:
                aba_pres.update_cell(i + 1, 6, tema_norm)

        # 3. Atualizar aba CRONOGRAMA (Se o novo tema existir lá, marca como REALIZADO)
        aba_cron = planilha.worksheet("cronograma")
        dados_cron = aba_cron.get_all_values()
        for i, linha in enumerate(dados_cron):
            if len(linha) >= 3 and str(linha[1]).strip().upper() == turma_norm and str(linha[2]).strip().upper() == tema_norm:
                aba_cron.update_cell(i + 1, 5, "REALIZADO") # Coluna E = Status

        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro na sincronia global: {e}")
        return False

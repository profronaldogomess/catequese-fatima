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

SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def conectar_google_sheets():
    try:
        if "gcp_service_account" in st.secrets:
            info_do_cofre = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(info_do_cofre, scopes=SCOPE)
        else:
            creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
        client = gspread.authorize(creds)
        planilha = client.open("BD_Catequese")
        return planilha
    except Exception as e:
        # Silencioso para não quebrar a UI em caso de instabilidade momentânea
        return None

# --- 1. MOTOR DE LEITURA COM CACHE INTELIGENTE (DEFESA CONTRA ERRO 429) ---

@st.cache_data(ttl=60) 
def ler_aba(nome_aba):
    """Lê qualquer aba e retorna um DataFrame. Cache de 60s para evitar excesso de requisições."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet(nome_aba)
            todos_os_valores = aba.get_all_values()
            if not todos_os_valores or len(todos_os_valores) < 1:
                return pd.DataFrame()
            headers = [str(h).strip().lower() for h in todos_os_valores[0]]
            headers = [h if h != "" else f"col_{i}" for i, h in enumerate(headers)]
            data = todos_os_valores[1:]
            num_cols = len(headers)
            data_ajustada = []
            for row in data:
                row_fixed = list(row)
                if len(row_fixed) < num_cols:
                    row_fixed.extend([""] * (num_cols - len(row_fixed)))
                data_ajustada.append(row_fixed[:num_cols])
            df = pd.DataFrame(data_ajustada, columns=headers)
            return df
        except Exception:
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
            # Garante que todas as linhas tenham exatamente 30 colunas antes de inserir
            lista_blindada = []
            for linha in lista_de_listas:
                linha_segura = linha + ["N/A"] * (30 - len(linha)) if len(linha) < 30 else linha[:30]
                lista_blindada.append(linha_segura)
            
            aba.append_rows(lista_blindada)
            st.cache_data.clear(); return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def salvar_presencas(lista_presencas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("presencas")
            aba.append_rows(lista_presencas)
            st.cache_data.clear(); return True
        except Exception as e: st.error(f"Erro: {e}")
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

def sincronizar_renomeacao_catequista(nome_antigo, nome_novo):
    """Atualiza o nome do catequista nas turmas e históricos."""
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        # 1. Turmas (Coluna E - catequista_responsavel)
        aba_t = planilha.worksheet("turmas")
        dados_t = aba_t.get_all_values()
        for i, linha in enumerate(dados_t[1:], start=2):
            cats =[c.strip() for c in str(linha[4]).split(',') if c.strip()]
            if nome_antigo in cats:
                cats = [nome_novo if c == nome_antigo else c for c in cats]
                aba_t.update_cell(i, 5, ", ".join(cats))
        
        # 2. Encontros (Coluna D - catequista)
        aba_enc = planilha.worksheet("encontros")
        celulas_enc = aba_enc.findall(str(nome_antigo), in_column=4)
        for cel in celulas_enc: aba_enc.update_cell(cel.row, 4, nome_novo)
        
        # 3. Sacramentos Eventos (Coluna E - catequista)
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
        abas_colunas =[
            ("cronograma", 2), ("encontros", 2), 
            ("presencas", 4), ("reunioes_pais", 4), ("presenca_reuniao", 4)
        ]
        for nome_aba, col in abas_colunas:
            aba = planilha.worksheet(nome_aba)
            celulas = aba.findall(str(nome_turma), in_column=col)
            # Deletar de baixo para cima para não bagunçar os índices
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

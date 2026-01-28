# ARQUIVO: database.py
# VERSÃO: 3.0.4 - INTEGRALIDADE TOTAL E DEFESA DE COTA (ANTI-429)
# MISSÃO: Motor de Dados Eclesiástico com Segurança de Sessão Única e Cookies.

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

@st.cache_data(ttl=300) # Cache de 5 minutos para o status de manutenção
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
    """Grava o UUID da sessão na Coluna M (13) da aba usuarios."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("usuarios")
            celula = aba.find(str(email))
            if celula:
                aba.update_cell(celula.row, 13, str(novo_id))
                st.cache_data.clear() # Limpa cache para validar a nova sessão
                return True
        except: pass
    return False

@st.cache_data(ttl=30) # Validação rápida (30s) para evitar erro 429 em navegação
def obter_session_id_db(email):
    """Busca o UUID gravado na planilha. Usa ler_aba para aproveitar o cache."""
    if not email: return ""
    df_usuarios = ler_aba("usuarios")
    if not df_usuarios.empty and 'email' in df_usuarios.columns:
        usuario = df_usuarios[df_usuarios['email'] == email]
        if not usuario.empty:
            # Tenta pegar a coluna 'session_id' ou a 13ª coluna (índice 12)
            try:
                if 'session_id' in usuario.columns:
                    return str(usuario.iloc[0]['session_id'])
                return str(usuario.iloc[0].iloc[12]) # Coluna M
            except: return ""
    return ""

# --- 3. FUNÇÕES PASTORAIS E DE GESTÃO (INTEGRIDADE TOTAL) ---

def salvar_lote_catequizandos(lista_de_listas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            aba.append_rows(lista_de_listas)
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
            celula = aba.find(str(id_catequizando))
            if celula:
                # RIGOR 30 COLUNAS: Atualiza de A até AD
                aba.update(f"A{celula.row}:AD{celula.row}", [novos_dados_lista])
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
            celula = aba.find(str(id_turma))
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
            celula = aba.find(str(id_turma))
            if celula:
                # RIGOR 10 COLUNAS: Atualiza de A até J
                aba.update(f"A{celula.row}:J{celula.row}", [novos_dados_lista])
                st.cache_data.clear(); return True
        except: return False
    return False

def atualizar_usuario(email_original, novos_dados_lista):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("usuarios")
            celula = aba.find(str(email_original))
            if celula:
                # RIGOR 12 COLUNAS: Atualiza de A até L (M é reservada ao UUID)
                aba.update(f"A{celula.row}:L{celula.row}", [novos_dados_lista])
                st.cache_data.clear(); return True
        except: return False
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
            # Busca a linha que contém a turma e o tema
            celulas = aba.findall(str(titulo_tema))
            for celula in celulas:
                # Verifica se na mesma linha a coluna da turma (B=2) coincide
                if aba.cell(celula.row, 2).value == turma:
                    aba.delete_rows(celula.row)
                    st.cache_data.clear()
                    return True
        except: pass
    return False

def sincronizar_renomeacao_turma_catequizandos(nome_antigo, nome_novo):
    """
    Varre a aba catequizandos e atualiza o nome da etapa 
    para todos os vinculados ao nome antigo.
    """
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            dados = aba.get_all_values()
            if len(dados) < 2: return True # Nada para atualizar
            
            headers = [h.lower() for h in dados[0]]
            col_etapa = headers.index("etapa") + 1
            
            # Localiza todas as linhas que precisam de atualização
            celulas_para_atualizar = []
            for i, linha in enumerate(dados[1:], start=2):
                if linha[col_etapa-1] == nome_antigo:
                    aba.update_cell(i, col_etapa, nome_novo)
            
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Erro na sincronia de nomes: {e}")
            return False
    return False

def atualizar_evento_sacramento(id_evento, novos_dados):
    """Atualiza os dados de um evento na aba sacramentos_eventos."""
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("sacramentos_eventos")
            celula = aba.find(str(id_evento))
            if celula:
                # Atualiza as colunas A até E (ID, Tipo, Data, Turmas, Catequista)
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
            celula = aba.find(str(id_f))
            if celula:
                # Atualiza as colunas A até F (ID, Tema, Data, Formador, Local, Status)
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
            # 1. Remove da aba formacoes
            aba_f = planilha.worksheet("formacoes")
            cel_f = aba_f.find(str(id_f))
            if cel_f: aba_f.delete_rows(cel_f.row)
            
            # 2. Remove presenças vinculadas
            aba_p = planilha.worksheet("presenca_formacao")
            celulas_p = aba_p.findall(str(id_f))
            # Deleta de baixo para cima para não perder o índice
            for cel in sorted(celulas_p, key=lambda x: x.row, reverse=True):
                aba_p.delete_rows(cel.row)
                
            st.cache_data.clear()
            return True
        except: pass
    return False

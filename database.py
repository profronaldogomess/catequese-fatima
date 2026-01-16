# ARQUIVO: database.py
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DE ACESSO ---
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
        st.error(f"Erro de conexão: {e}")
        return None

# --- FUNÇÕES DE LEITURA ---

@st.cache_data(ttl=60) 
def ler_aba(nome_aba):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet(nome_aba)
            todos_os_valores = aba.get_all_values()
            
            if len(todos_os_valores) <= 1:
                return pd.DataFrame()
            
            df = pd.DataFrame(todos_os_valores[1:], columns=todos_os_valores[0])
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Erro ao ler a aba {nome_aba}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- FUNÇÕES DE SALVAMENTO E EDIÇÃO ---

def salvar_lote_catequizandos(lista_de_listas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            aba.append_rows(lista_de_listas)
            st.cache_data.clear()
            return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def salvar_presencas(lista_presencas):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("presencas")
            aba.append_rows(lista_presencas)
            st.cache_data.clear()
            return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def salvar_encontro(dados_encontro):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("encontros")
            aba.append_row(dados_encontro)
            st.cache_data.clear()
            return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def atualizar_catequizando(id_catequizando, novos_dados_lista):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            celula = aba.find(str(id_catequizando))
            if celula:
                aba.update(f"A{celula.row}:Q{celula.row}", [novos_dados_lista])
                st.cache_data.clear()
                return True
        except Exception as e: st.error(f"Erro: {e}")
    return False

def mover_catequizandos_em_massa(lista_ids, nova_turma):
    planilha = conectar_google_sheets()
    if planilha:
        try:
            aba = planilha.worksheet("catequizandos")
            headers = aba.row_values(1)
            col_id = headers.index("id_catequizando") + 1
            col_etapa = headers.index("etapa") + 1
            for cid in lista_ids:
                celula = aba.find(str(cid), in_col=col_id)
                if celula:
                    aba.update_cell(celula.row, col_etapa, nova_turma)
            st.cache_data.clear()
            return True
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
                st.cache_data.clear()
                return True
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
                aba.update(f"A{celula.row}:F{celula.row}", [novos_dados_lista])
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

# --- NOVAS FUNÇÕES DE SACRAMENTOS ---

def registrar_evento_sacramento_completo(dados_evento, lista_participantes, tipo_sacramento):
    """
    Salva o evento, os participantes e ATUALIZA a ficha individual de cada um.
    """
    planilha = conectar_google_sheets()
    if not planilha: return False
    
    try:
        # 1. Salva o Evento
        planilha.worksheet("sacramentos_eventos").append_row(dados_evento)
        
        # 2. Salva os Participantes
        planilha.worksheet("sacramentos_recebidos").append_rows(lista_participantes)
        
        # 3. Atualização Cirúrgica na aba 'catequizandos'
        aba_cat = planilha.worksheet("catequizandos")
        headers = aba_cat.row_values(1)
        col_id = headers.index("id_catequizando") + 1
        col_batizado = headers.index("batizado_sn") + 1
        col_sacramentos = headers.index("sacramentos_ja_feitos") + 1
        
        for p in lista_participantes:
            id_cat = p[1]
            celula = aba_cat.find(str(id_cat), in_col=col_id)
            if celula:
                if tipo_sacramento == "BATISMO":
                    aba_cat.update_cell(celula.row, col_batizado, "SIM")
                else:
                    # Para Eucaristia e Crisma, adicionamos ao texto existente
                    valor_atual = aba_cat.cell(celula.row, col_sacramentos).value or ""
                    if tipo_sacramento not in valor_atual:
                        novo_valor = f"{valor_atual}, {tipo_sacramento}".strip(", ")
                        aba_cat.update_cell(celula.row, col_sacramentos, novo_valor)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar sacramento: {e}")
        return False

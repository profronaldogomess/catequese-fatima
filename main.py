# ARQUIVO: main.py
import streamlit as st
import pandas as pd
from datetime import date, datetime
import time
import os 
from fpdf import FPDF
import plotly.express as px

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Catequese Fátima", 
    layout="wide", 
    page_icon="✝️",
    initial_sidebar_state="expanded"
)

# --- VARIÁVEIS GLOBAIS DE PADRONIZAÇÃO ---
MIN_DATA = date(1900, 1, 1)
MAX_DATA = date(2030, 12, 31)

# --- INJEÇÃO DE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    .stTextInput input, .stDateInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #f0f2f6 !important; color: #000000 !important; border: 1px solid #ccc;
    }
    div[data-baseweb="select"] > div { background-color: #f0f2f6 !important; color: #000000 !important; }
    input, textarea, select { color: black !important; -webkit-text-fill-color: black !important; }
    [data-testid="stSidebar"] { background-color: #417b99; }
    [data-testid="stSidebar"] * { color: white !important; }
    h1, h2, h3, h4 { color: #417b99 !important; font-family: 'Helvetica', sans-serif; }
    label, .stMarkdown p { color: #417b99 !important; font-weight: 600; }
    div.stButton > button { background-color: #e03d11; color: white !important; border: none; font-weight: bold; border-radius: 8px; padding: 10px 20px; }
    div.stButton > button:hover { background-color: #c0320d; color: white !important; }
    [data-testid="stMetricValue"] { color: #e03d11 !important; }
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    </style>
""", unsafe_allow_html=True)

# Importações das nossas funções personalizadas
from database import (
    ler_aba, salvar_lote_catequizandos, atualizar_catequizando, 
    conectar_google_sheets, atualizar_turma, salvar_presencas, 
    verificar_login, salvar_encontro, salvar_tema_cronograma, 
    buscar_encontro_por_data, atualizar_usuario, salvar_formacao, 
    salvar_presenca_formacao, mover_catequizandos_em_massa, excluir_turma,
    registrar_evento_sacramento_completo
)
from utils import (
    calcular_idade, sugerir_etapa, eh_aniversariante_da_semana, 
    obter_aniversariantes_mes, converter_para_data, verificar_status_ministerial, 
    obter_aniversariantes_hoje, obter_aniversariantes_mes_unificado, 
    gerar_ficha_cadastral_catequizando, gerar_ficha_catequista_pdf, gerar_pdf_perfil_turma
)
from ai_engine import (
    gerar_analise_pastoral, gerar_mensagem_whatsapp, 
    analisar_turma_local, gerar_relatorio_sacramentos_ia
)

# --- FUNÇÕES AUXILIARES DE LOGO ---
def mostrar_logo_sidebar():
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.sidebar.columns([1, 3, 1])
        with c2: st.image("logo.png", width=130)
    else: st.sidebar.title("Catequese Fátima")

def mostrar_logo_login():
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    else: st.markdown("<h1 style='text-align: center; color: #e03d11;'>✝️</h1>", unsafe_allow_html=True)

# --- CONTROLE DE SESSÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        mostrar_logo_login()
        st.markdown("<h2 style='text-align: center; color: #417b99;'>Acesso Restrito</h2>", unsafe_allow_html=True)
        email_login = st.text_input("E-mail")
        senha_login = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            user = verificar_login(email_login, senha_login)
            if user:
                st.session_state.logado = True
                st.session_state.usuario = user
                st.rerun()
            else: st.error("🚫 Acesso negado.")
    st.stop() 

# --- BARRA LATERAL ---
mostrar_logo_sidebar() 
st.sidebar.markdown(f"📅 **{date.today().strftime('%d/%m/%Y')}**")
st.sidebar.success(f"Bem-vindo(a),\n**{st.session_state.usuario['nome']}**")
st.sidebar.divider()

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear(); st.rerun()
if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False; st.rerun()

papel_usuario = st.session_state.usuario.get('papel', 'CATEQUISTA').upper()
turma_do_catequista = st.session_state.usuario.get('turma_vinculada', 'TODAS')
eh_gestor = papel_usuario in ["COORDENADOR", "ADMIN"]

if eh_gestor:
    menu = st.sidebar.radio("MENU PRINCIPAL", ["🏠 Início / Dashboard", "🏠 Minha Turma", "📖 Diário de Encontros", "📝 Cadastrar Catequizando", "👤 Perfil Individual", "🏫 Gestão de Turmas", "🕊️ Gestão de Sacramentos", "👥 Gestão de Catequistas", "✅ Fazer Chamada"])
else:
    menu = st.sidebar.radio("MENU DO CATEQUISTA", ["🏠 Minha Turma", "📖 Diário de Encontros", "✅ Fazer Chamada", "📝 Cadastrar Catequizando"])

# --- PÁGINA: DASHBOARD ---
if menu == "🏠 Início / Dashboard":
    st.title("📊 Painel de Gestão Pastoral")
    df_cat = ler_aba("catequizandos")
    df_turmas = ler_aba("turmas")
    df_pres = ler_aba("presencas")
    df_usuarios = ler_aba("usuarios") 

    aniversariantes_agora = obter_aniversariantes_hoje(df_cat, df_usuarios)
    if aniversariantes_agora:
        for msg in aniversariantes_agora: st.success(f"🎂 **HOJE É ANIVERSÁRIO!** {msg}")

    if not df_cat.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Catequizandos", len(df_cat))
        m2.metric("Ativos", len(df_cat[df_cat['status'] == 'ATIVO']))
        m3.metric("Total de Turmas", len(df_turmas))
        m4.metric("Equipe", len(df_usuarios))
        
        st.divider()
        if not df_pres.empty:
            df_pres['status_num'] = df_pres['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
            freq_turma = df_pres.groupby('id_turma')['status_num'].mean() * 100
            fig = px.bar(freq_turma.reset_index(), x='id_turma', y='status_num', title="Frequência por Turma")
            st.plotly_chart(fig, use_container_width=True)

        if st.button("✨ Gerar Relatório Inteligente com IA"):
            from ai_engine import gerar_analise_pastoral
            st.markdown(gerar_analise_pastoral(f"Total: {len(df_cat)}"))

# --- PÁGINA: MINHA TURMA ---
elif menu == "🏠 Minha Turma":
    st.title(f"🏠 Painel da Turma: {turma_do_catequista}")
    df_cat = ler_aba("catequizandos")
    meus_alunos = df_cat[df_cat['etapa'] == turma_do_catequista] if not df_cat.empty else pd.DataFrame()
    st.metric("Total de Catequizandos", len(meus_alunos))
    st.dataframe(meus_alunos[['nome_completo', 'contato_principal', 'status']], use_container_width=True)

# --- PÁGINA: DIÁRIO ---
elif menu == "📖 Diário de Encontros":
    st.title("📖 Gestão de Temas e Encontros")
    with st.form("form_encontro"):
        data_e = st.date_input("Data", date.today())
        tema_e = st.text_input("Tema").upper()
        if st.form_submit_button("💾 SALVAR"):
            if tema_e:
                conectar_google_sheets().worksheet("encontros").append_row([str(data_e), turma_do_catequista, tema_e, st.session_state.usuario['nome'], ""])
                st.success("Registrado!"); st.rerun()

# --- PÁGINA: CADASTRAR ---
elif menu == "📝 Cadastrar Catequizando":
    st.title("📝 Cadastro de Catequizandos")
    with st.form("form_cad"):
        nome = st.text_input("Nome Completo").upper()
        data_n = st.date_input("Nascimento", value=date(2015,1,1))
        turma = st.selectbox("Turma", ler_aba("turmas")['nome_turma'].tolist() if not ler_aba("turmas").empty else ["SEM TURMA"])
        contato = st.text_input("WhatsApp")
        if st.form_submit_button("💾 SALVAR"):
            if nome and contato:
                salvar_lote_catequizandos([[f"CAT-{int(time.time())}", turma, nome, str(data_n), "NÃO", contato, "", "", "", "", "", "", "ATIVO", "NÃO", "NÃO", "N/A", "N/A"]])
                st.success("Cadastrado!"); st.rerun()

# --- PÁGINA: PERFIL ---
elif menu == "👤 Perfil Individual":
    st.title("👤 Perfil do Catequizando")
    df_cat = ler_aba("catequizandos")
    escolha = st.selectbox("Selecione:", [""] + df_cat['nome_completo'].tolist() if not df_cat.empty else [""])
    if escolha:
        dados = df_cat[df_cat['nome_completo'] == escolha].iloc[0]
        st.write(dados)

# --- PÁGINA: GESTÃO DE TURMAS ---
elif menu == "🏫 Gestão de Turmas":
    st.title("🏫 Gestão de Turmas")
    t1, t2 = st.tabs(["Lista", "Nova"])
    with t1: st.dataframe(ler_aba("turmas"), use_container_width=True)
    with t2:
        with st.form("nova_t"):
            n = st.text_input("Nome da Turma").upper()
            if st.form_submit_button("CRIAR"):
                conectar_google_sheets().worksheet("turmas").append_row([f"TRM-{int(time.time())}", n, "ETAPA", 2025, "", ""])
                st.success("Criada!"); st.rerun()

# --- PÁGINA: SACRAMENTOS (NOVA) ---
elif menu == "🕊️ Gestão de Sacramentos":
    st.title("🕊️ Gestão de Sacramentos")
    df_cat = ler_aba("catequizandos")
    df_turmas = ler_aba("turmas")
    df_sac_eventos = ler_aba("sacramentos_eventos")

    tab_dash, tab_reg, tab_hist = st.tabs(["📊 Dashboard", "✍️ Registrar", "📜 Histórico"])

    with tab_dash:
        if not df_cat.empty:
            c1, c2, c3 = st.columns(3)
            # Batismo
            bat_counts = df_cat['batizado_sn'].value_counts()
            c1.plotly_chart(px.pie(values=bat_counts.values, names=bat_counts.index, title="Batizados"), use_container_width=True)
            # Eucaristia
            euca_sim = df_cat['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
            c2.plotly_chart(px.pie(values=[euca_sim, len(df_cat)-euca_sim], names=['SIM', 'NÃO'], title="Eucaristia"), use_container_width=True)
            # Crisma
            cris_sim = df_cat['sacramentos_ja_feitos'].str.contains("CRISMA", na=False).sum()
            c3.plotly_chart(px.pie(values=[cris_sim, len(df_cat)-cris_sim], names=['SIM', 'NÃO'], title="Crisma"), use_container_width=True)
            
            if st.button("🤖 Relatório IA"):
                st.info(gerar_relatorio_sacramentos_ia(f"Batismo: {euca_sim}"))

    with tab_reg:
        with st.form("form_sac"):
            tipo = st.selectbox("Sacramento", ["BATISMO", "EUCARISTIA", "CRISMA"])
            data_s = st.date_input("Data", date.today())
            turmas_sel = st.multiselect("Turmas", df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])
            st.divider()
            if turmas_sel:
                alunos = df_cat[df_cat['etapa'].isin(turmas_sel)]
                selecionados = []
                for _, r in alunos.iterrows():
                    if st.checkbox(f"{r['nome_completo']} ({r['etapa']})", key=f"s_{r['id_catequizando']}"):
                        selecionados.append(r)
                if st.form_submit_button("💾 SALVAR E ATUALIZAR"):
                    id_ev = f"SAC-{int(time.time())}"
                    lista_p = [[id_ev, r['id_catequizando'], r['nome_completo'], tipo, str(data_s)] for r in selecionados]
                    if registrar_evento_sacramento_completo([id_ev, tipo, str(data_s), ", ".join(turmas_sel), st.session_state.usuario['nome']], lista_p, tipo):
                        st.success("Atualizado!"); st.rerun()
            else: st.form_submit_button("Selecione as turmas primeiro", disabled=True)

    with tab_hist: st.dataframe(df_sac_eventos, use_container_width=True)

# --- PÁGINA: CATEQUISTAS ---
elif menu == "👥 Gestão de Catequistas":
    st.title("👥 Gestão de Equipe")
    st.dataframe(ler_aba("usuarios"), use_container_width=True)

# --- PÁGINA: CHAMADA ---
elif menu == "✅ Fazer Chamada":
    st.title("✅ Chamada")
    df_cat = ler_aba("catequizandos")
    lista = df_cat[df_cat['etapa'] == turma_do_catequista]
    with st.form("f_chamada"):
        tema = st.text_input("Tema do Dia").upper()
        regs = []
        for _, r in lista.iterrows():
            p = st.checkbox(r['nome_completo'], value=True)
            regs.append([str(date.today()), r['id_catequizando'], r['nome_completo'], turma_do_catequista, "PRESENTE" if p else "AUSENTE", tema, st.session_state.usuario['nome']])
        if st.form_submit_button("🚀 SALVAR"):
            if salvar_presencas(regs): st.success("Salvo!"); st.rerun()

# ARQUIVO: main.py
# VERSÃO: 3.2.0 - INTEGRAL (HOMOLOGAÇÃO + ADMIN BYPASS + SEGURANÇA)
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import time
import os 
import uuid
from fpdf import FPDF
import plotly.express as px
import extra_streamlit_components as stx

# --- CONFIGURAÇÃO DE AMBIENTE (MUDE PARA FALSE NA BRANCH MAIN) ---
IS_HOMOLOGACAO = False 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Catequese Fátima" if not IS_HOMOLOGACAO else "LABORATÓRIO - FÁTIMA", 
    layout="wide", 
    page_icon="✝️",
    initial_sidebar_state="expanded"
)

# --- 2. INICIALIZAÇÃO DE COMPONENTES DE SEGURANÇA ---
def get_cookie_manager():
    return stx.CookieManager(key="catequese_fatima_cookies_v3_2")

cookie_manager = get_cookie_manager()

if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

# --- 3. MOTOR DE MANUTENÇÃO COM BYPASS DE ADMINISTRADOR ---
from database import verificar_status_sistema, verificar_login, atualizar_session_id, obter_session_id_db
status_sistema = verificar_status_sistema()

# Verificação de Identidade para Bypass
is_admin = (st.session_state.logado and st.session_state.usuario.get('papel') == 'ADMIN')

# Banner de Homologação (Aparece apenas na branch de teste)
if IS_HOMOLOGACAO:
    st.warning("🧪 **AMBIENTE DE TESTES (HOMOLOGAÇÃO)** - As alterações feitas aqui podem não ser definitivas.")

# Lógica de Bloqueio de Manutenção
if status_sistema == "MANUTENCAO" and not is_admin:
    from utils import exibir_tela_manutencao
    exibir_tela_manutencao()
    
    # Porta de entrada para o Administrador
    with st.expander("🔐 Acesso Técnico (Administração)"):
        with st.form("login_admin_manutencao"):
            u_adm = st.text_input("E-mail Admin")
            s_adm = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR EM MODO MANUTENÇÃO"):
                user = verificar_login(u_adm, s_adm)
                if user and user.get('papel') == 'ADMIN':
                    st.session_state.logado = True
                    st.session_state.usuario = user
                    st.session_state.session_id = str(uuid.uuid4())
                    atualizar_session_id(u_adm, st.session_state.session_id)
                    st.rerun()
                else:
                    st.error("Apenas Administradores podem acessar durante a manutenção.")
    st.stop()

# --- VARIÁVEIS GLOBAIS DE PADRONIZAÇÃO ---
MIN_DATA = date(1900, 1, 1)
MAX_DATA = date(2030, 12, 31)

# --- 4. INJEÇÃO DE CSS (ESTILIZAÇÃO DIFERENCIADA PARA HOMOLOGAÇÃO) ---
cor_sidebar = "#417b99" if not IS_HOMOLOGACAO else "#5d4037" # Azul para oficial, Marrom para teste

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #333333; }}
    .stTextInput input, .stDateInput input, .stNumberInput input, .stTextArea textarea {{
        background-color: #f0f2f6 !important; color: #000000 !important; border: 1px solid #ccc;
    }}
    div[data-baseweb="select"] > div {{ background-color: #f0f2f6 !important; color: #000000 !important; }}
    input, textarea, select {{ color: black !important; -webkit-text-fill-color: black !important; }}
    [data-testid="stSidebar"] {{ background-color: {cor_sidebar}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    h1, h2, h3, h4 {{ color: {cor_sidebar} !important; font-family: 'Helvetica', sans-serif; }}
    label, .stMarkdown p {{ color: {cor_sidebar} !important; font-weight: 600; }}
    p, li {{ color: #333333; }}
    div.stButton > button {{
        background-color: #e03d11; color: white !important; border: none;
        font-weight: bold; border-radius: 8px; padding: 10px 20px;
    }}
    div.stButton > button:hover {{ background-color: #c0320d; color: white !important; }}
    [data-testid="stMetricValue"] {{ color: #e03d11 !important; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 5rem; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. IMPORTAÇÕES DE MOTORES INTERNOS (INTEGRIDADE TOTAL) ---
from database import (
    ler_aba, salvar_lote_catequizandos, atualizar_catequizando, 
    conectar_google_sheets, atualizar_turma, salvar_presencas, 
    salvar_encontro, salvar_tema_cronograma, 
    buscar_encontro_por_data, atualizar_usuario, salvar_formacao, 
    salvar_presenca_formacao, mover_catequizandos_em_massa, excluir_turma,
    registrar_evento_sacramento_completo
)
from utils import (
    calcular_idade, sugerir_etapa, eh_aniversariante_da_semana, 
    obter_aniversariantes_mes, converter_para_data, verificar_status_ministerial, 
    obter_aniversariantes_hoje, obter_aniversariantes_mes_unificado, 
    gerar_ficha_cadastral_catequizando, gerar_ficha_catequista_pdf, 
    gerar_fichas_turma_completa, gerar_relatorio_diocesano_v4,
    gerar_relatorio_pastoral_v3, gerar_relatorio_sacramentos_tecnico_v2,
    formatar_data_br, gerar_relatorio_familia_pdf,
    gerar_relatorio_local_turma_v2, gerar_fichas_catequistas_lote, 
    gerar_card_aniversario, gerar_termo_saida_pdf, gerar_auditoria_lote_completa,
    gerar_fichas_paroquia_total, gerar_relatorio_diocesano_pdf,
    gerar_relatorio_diocesano_v2, gerar_relatorio_pastoral_v2,
    gerar_relatorio_pastoral_interno_pdf, gerar_pdf_perfil_turma,
    gerar_relatorio_sacramentos_tecnico_pdf, gerar_relatorio_local_turma_pdf
)
from ai_engine import (
    gerar_analise_pastoral, gerar_mensagem_whatsapp, 
    analisar_turma_local, gerar_relatorio_sacramentos_ia, analisar_saude_familiar_ia
)

# --- 6. FUNÇÕES AUXILIARES DE INTERFACE ---
def mostrar_logo_sidebar():
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.sidebar.columns([1, 3, 1])
        with c2: st.image("logo.png", width=130)
    else: st.sidebar.title("Catequese Fátima")

def mostrar_logo_login():
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    else: st.markdown("<h1 style='text-align: center; color: #e03d11;'>✝️</h1>", unsafe_allow_html=True)

# --- 7. LÓGICA DE PERSISTÊNCIA E SESSÃO ÚNICA ---

# A. Auto-Login via Cookies
if not st.session_state.logado:
    auth_cookie = cookie_manager.get("fatima_auth_v2")
    if auth_cookie:
        user = verificar_login(auth_cookie['email'], auth_cookie['senha'])
        if user:
            new_sid = str(uuid.uuid4())
            if atualizar_session_id(user['email'], new_sid):
                st.session_state.logado = True
                st.session_state.usuario = user
                st.session_state.session_id = new_sid
                st.rerun()

# B. Validação de Sessão Única
if st.session_state.logado:
    sid_no_db = obter_session_id_db(st.session_state.usuario['email'])
    if sid_no_db and sid_no_db != st.session_state.session_id:
        st.warning("⚠️ Esta conta foi conectada em outro dispositivo.")
        st.info("Sua sessão atual foi encerrada por segurança.")
        st.session_state.logado = False
        st.session_state.session_id = None
        cookie_manager.delete("fatima_auth_v2")
        if st.button("RECONECTAR"): st.rerun()
        st.stop()

# C. Tela de Login Manual
if not st.session_state.logado:
    st.container()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        col_conteudo = st.columns([0.2, 2, 0.2])[1]
        with col_conteudo:
            st.markdown("<br>", unsafe_allow_html=True)
            mostrar_logo_login()
            st.markdown(f"<h2 style='text-align: center; color: {cor_sidebar};'>Acesso Restrito</h2>", unsafe_allow_html=True)
            
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            lembrar = st.checkbox("Manter conectado por 30 dias")
            
            st.write("") 
            if st.button("ENTRAR NO SISTEMA", use_container_width=True):
                user = verificar_login(email_login, senha_login)
                if user:
                    new_sid = str(uuid.uuid4())
                    if atualizar_session_id(email_login, new_sid):
                        st.session_state.logado = True
                        st.session_state.usuario = user
                        st.session_state.session_id = new_sid
                        if lembrar:
                            cookie_manager.set("fatima_auth_v2", {"email": email_login, "senha": senha_login}, expires_at=datetime.now() + timedelta(days=30))
                        st.success(f"Bem-vindo(a), {user['nome']}!")
                        time.sleep(1)
                        st.rerun()
                    else: st.error("Erro ao validar sessão única.")
                else: st.error("🚫 Acesso negado. Verifique suas credenciais.")
    st.stop() 

# --- 8. CARREGAMENTO GLOBAL DE DADOS (PÓS-LOGIN) ---
df_cat = ler_aba("catequizandos")
df_turmas = ler_aba("turmas")
df_pres = ler_aba("presencas")
df_usuarios = ler_aba("usuarios") 
df_sac_eventos = ler_aba("sacramentos_eventos")

equipe_tecnica = df_usuarios[df_usuarios['papel'] != 'ADMIN'] if not df_usuarios.empty else pd.DataFrame()

# --- 9. BARRA LATERAL E DEFINIÇÃO DE MENU ---
mostrar_logo_sidebar() 
st.sidebar.markdown(f"📅 **{date.today().strftime('%d/%m/%Y')}**")
st.sidebar.success(f"Bem-vindo(a),\n**{st.session_state.usuario['nome']}**")

# Alertas de Ambiente e Manutenção
if IS_HOMOLOGACAO:
    st.sidebar.info("🧪 MODO HOMOLOGAÇÃO")
if status_sistema == "MANUTENCAO":
    st.sidebar.warning("⚠️ MANUTENÇÃO ATIVA")

st.sidebar.divider()

if st.sidebar.button("🔄 Atualizar Dados", key="btn_refresh_99x"):
    st.cache_data.clear(); st.toast("Dados atualizados!", icon="✅"); time.sleep(1); st.rerun()

if st.sidebar.button("🚪 Sair / Logoff", key="btn_logout_99x"):
    cookie_manager.delete("fatima_auth_v2")
    st.session_state.logado = False
    st.session_state.session_id = None
    st.rerun()

papel_usuario = st.session_state.usuario.get('papel', 'CATEQUISTA').upper()
turma_do_catequista = st.session_state.usuario.get('turma_vinculada', 'TODAS')
eh_gestor = papel_usuario in ["COORDENADOR", "ADMIN"]

if eh_gestor:
    menu = st.sidebar.radio("MENU PRINCIPAL", [
        "🏠 Início / Dashboard", "📚 Minha Turma", "👨‍👩‍👧‍👦 Gestão Familiar", 
        "📖 Diário de Encontros", "📝 Cadastrar Catequizando", "👤 Perfil Individual", 
        "🏫 Gestão de Turmas", "🕊️ Gestão de Sacramentos", "👥 Gestão de Catequistas", "✅ Fazer Chamada"
    ])
else:
    menu = st.sidebar.radio("MENU DO CATEQUISTA", [
        "📚 Minha Turma", "👨‍👩‍👧‍👦 Gestão Familiar", "📖 Diário de Encontros", 
        "✅ Fazer Chamada", "📝 Cadastrar Catequizando"
    ])

# --- PÁGINA 1: DASHBOARD (CORREÇÃO DE CARDS DE HOJE) ---
if menu == "🏠 Início / Dashboard":
    st.title("📊 Painel de Gestão Pastoral")
    
    # --- ALERTA DE ANIVERSÁRIO DO DIA ---
    aniversariantes_agora = obter_aniversariantes_hoje(df_cat, df_usuarios)
    
    if aniversariantes_agora:
        for item in aniversariantes_agora:
            # Decompõe a string estruturada: "DIA | PAPEL | NOME"
            partes = item.split(" | ")
            papel = partes[1]
            nome = partes[2]
            
            icone = "🛡️" if papel == "CATEQUISTA" else "😇"
            st.success(f"🎂 **HOJE É ANIVERSÁRIO!** {icone} {papel}: **{nome}**")
            st.balloons()
        
        # --- ÁREA DE CARDS DO DIA ---
        with st.expander("🖼️ GERAR CARDS DE PARABÉNS (HOJE)", expanded=True):
            cols_niver = st.columns(len(aniversariantes_agora) if len(aniversariantes_agora) < 4 else 4)
            for i, item in enumerate(aniversariantes_agora):
                partes = item.split(" | ")
                nome_exibicao = partes[2]
                
                with cols_niver[i % 4]:
                    st.write(f"**{nome_exibicao}**")
                    if st.button(f"🎨 Gerar Card", key=f"btn_dia_v14_{i}"):
                        # Enviamos a string completa para o motor de cards identificar o PAPEL
                        card_img = gerar_card_aniversario(item, tipo="DIA")
                        if card_img:
                            st.image(card_img, use_container_width=True)
                            st.download_button(
                                label="📥 Baixar Card",
                                data=card_img,
                                file_name=f"Parabens_Hoje_{nome_exibicao.replace(' ', '_')}.png",
                                mime="image/png",
                                key=f"dl_dia_v14_{i}"
                            )

    if df_cat.empty:
        st.info("👋 Bem-vindo! Comece cadastrando turmas e catequizandos.")
    else:
        # --- SEÇÃO 1: MÉTRICAS PRINCIPAIS ---
        m1, m2, m3, m4 = st.columns(4)
        total_cat = len(df_cat)
        ativos = len(df_cat[df_cat['status'] == 'ATIVO'])
        total_t = len(df_turmas)
        
        equipe_real = df_usuarios[df_usuarios['papel'] != 'ADMIN'] if not df_usuarios.empty else pd.DataFrame()
        total_equipe = len(equipe_real)
        
        m1.metric("Catequizandos", total_cat)
        m2.metric("Ativos", ativos)
        m3.metric("Total de Turmas", total_t)
        m4.metric("Equipe Catequética", total_equipe)

        st.divider()

        # --- SEÇÃO 2: DESEMPENHO ---
        st.subheader("📈 Desempenho e Frequência")
        freq_global = 0.0
        if df_pres.empty:
            st.info("Ainda não há registros de presença.")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                df_pres['status_num'] = df_pres['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                freq_turma = df_pres.groupby('id_turma')['status_num'].mean() * 100
                freq_turma = freq_turma.reset_index().rename(columns={'status_num': 'Frequência %', 'id_turma': 'Turma'})
                
                fig = px.bar(freq_turma, x='Turma', y='Frequência %', color='Frequência %', color_continuous_scale=['#e03d11', '#ccd628', '#417b99'])
                fig.update_layout(font=dict(color="#000000"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                total_encontros = df_pres['data_encontro'].nunique()
                freq_global = df_pres['status_num'].mean() * 100
                st.metric("Encontros Realizados", total_encontros)
                st.write(f"**Frequência Global:** {freq_global:.1f}%")
                st.progress(freq_global / 100)

        st.divider()

# --- SEÇÃO 3: ALERTAS E ANIVERSARIANTES ---
        col_niver, col_evasao = st.columns(2)
        with col_niver:
            st.subheader("🎂 Aniversariantes do Mês")
            df_niver_unificado = obter_aniversariantes_mes_unificado(df_cat, df_usuarios)
            
            if not df_niver_unificado.empty:
                # --- BOTÃO COLETIVO (TEMPLATE 4) ---
                if st.button("🖼️ GERAR CARD COLETIVO DO MÊS", use_container_width=True, key="btn_coletivo_mes"):
                    # Enviamos no formato "DIA | PAPEL | NOME" para o utils processar
                    lista_para_card = [f"{int(row['dia'])} | {row['tipo']} | {row['nome']}" for _, row in df_niver_unificado.iterrows()]
                    card_coletivo = gerar_card_aniversario(lista_para_card, tipo="MES")
                    if card_coletivo:
                        st.image(card_coletivo, caption="Card Coletivo do Mês")
                        st.download_button("📥 Baixar Card Coletivo", card_coletivo, "Aniversariantes_do_Mes.png", "image/png")
                
                st.divider()

                # --- LISTA INDIVIDUAL ---
                for i, niver in df_niver_unificado.iterrows():
                    icone = "🛡️" if niver['tipo'] == 'CATEQUISTA' else "🎁"
                    c_txt, c_btn = st.columns([3, 1])
                    c_txt.markdown(f"{icone} **Dia {int(niver['dia'])}** - {niver['nome']}")
                    
                    if c_btn.button("🖼️ Card", key=f"btn_indiv_{i}"):
                        # Enviamos no formato "DIA | PAPEL | NOME"
                        dados_envio = f"{int(niver['dia'])} | {niver['tipo']} | {niver['nome']}"
                        card_indiv = gerar_card_aniversario(dados_envio, tipo="DIA")
                        if card_indiv:
                            st.image(card_indiv, caption=f"Card de {niver['nome']}")
                            st.download_button("📥 Baixar", card_indiv, f"Niver_{niver['nome']}.png", "image/png")
            else: 
                st.write("Nenhum aniversariante este mês.")

# --- SEÇÃO 4: DOCUMENTAÇÃO E AUDITORIA (SISTEMA DE QUATRO BOTÕES - VERSÃO INTEGRAL) ---
        st.divider()
        st.subheader("🏛️ Documentação e Auditoria Oficial")
        
        col_paroquial, col_lote = st.columns(2)
        
        with col_paroquial:
            st.markdown("##### 📋 Relatórios de Gestão Paroquial")
            
# --- BOTÃO 1: RELATÓRIO DIOCESANO (FORÇANDO ATUALIZAÇÃO DO NOVO MODELO) ---
            # --- BOTÃO 1: RELATÓRIO DIOCESANO (VERSÃO ANALÍTICA) ---
            if st.button("🏛️ GERAR RELATÓRIO DIOCESANO", use_container_width=True, key="btn_diocesano_v5"):
                st.cache_data.clear()
                if "pdf_diocesano" in st.session_state: 
                    del st.session_state.pdf_diocesano
                
                with st.spinner("Processando Auditoria Diocesana Analítica..."):
                    try:
                        # Envia os 3 DataFrames para o novo motor do utils.py
                        st.session_state.pdf_diocesano = gerar_relatorio_diocesano_v4(df_turmas, df_cat, df_usuarios)
                        st.rerun()
                    except Exception as e: 
                        st.error(f"Erro no Relatório Diocesano: {e}")

            if "pdf_diocesano" in st.session_state:
                st.download_button(
                    label="📥 BAIXAR RELATÓRIO DIOCESANO", 
                    data=st.session_state.pdf_diocesano, 
                    file_name=f"Relatorio_Diocesano_{date.today().year}.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )

            st.write("") # Espaçador visual entre os botões

            # --- BOTÃO 2: RELATÓRIO PASTORAL (VERSÃO NOMINAL COMPLETA) ---
            if st.button("📋 GERAR RELATÓRIO PASTORAL", use_container_width=True, key="btn_pastoral_v5"):
                if "pdf_pastoral" in st.session_state: 
                    del st.session_state.pdf_pastoral
                
                with st.spinner("Gerando Dossiê Pastoral Nominal..."):
                    try:
                        # Envia os DataFrames para listar todos os nomes e estatísticas
                        st.session_state.pdf_pastoral = gerar_relatorio_pastoral_v3(df_turmas, df_cat, df_pres)
                        st.rerun()
                    except Exception as e: 
                        st.error(f"Erro no Relatório Pastoral: {e}")

            if "pdf_pastoral" in st.session_state:
                st.download_button(
                    label="📥 BAIXAR RELATÓRIO PASTORAL", 
                    data=st.session_state.pdf_pastoral, 
                    file_name=f"Relatorio_Pastoral_Nominal_{date.today().year}.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )
            
            # --- BOTÃO 3: TODAS AS FICHAS EM LOTE ---
            if st.button("🗂️ GERAR TODAS AS FICHAS (LOTE GERAL)", use_container_width=True, key="btn_lote_fichas_geral"):
                with st.spinner("Consolidando fichas de todos os catequizandos..."):
                    from utils import gerar_fichas_paroquia_total
                    pdf_lote_f = gerar_fichas_paroquia_total(df_cat)
                    st.session_state.pdf_lote_fichas_geral = pdf_lote_f
                    st.toast("Lote de fichas gerado!", icon="✅")

            if "pdf_lote_fichas_geral" in st.session_state:
                st.download_button("📥 BAIXAR TODAS AS FICHAS (PDF ÚNICO)", st.session_state.pdf_lote_fichas_geral, f"Fichas_Gerais_Fatima_{date.today().year}.pdf", "application/pdf", use_container_width=True)

# --- BOTÃO 4: TODAS AS AUDITORIAS DE TURMA EM LOTE (VERSÃO FLEXÍVEL) ---
            if st.button("📊 GERAR TODAS AS AUDITORIAS DE TURMA", use_container_width=True, key="btn_lote_auditoria_geral_v7"):
                with st.spinner("Analisando cada itinerário de turma..."):
                    # 1. Tenta carregar a aba de sacramentos
                    df_sac_nominais = ler_aba("sacramentos_recebidos")
                    
                    # 2. Se estiver vazia, cria um DataFrame vazio com as colunas necessárias para não dar erro no motor
                    if df_sac_nominais.empty:
                        df_sac_nominais = pd.DataFrame(columns=['id_catequizando', 'nome', 'tipo', 'data'])
                    
                    try:
                        # 3. Chama a função do utils.py (que restauramos na resposta anterior)
                        pdf_lote_a = gerar_auditoria_lote_completa(
                            df_turmas, 
                            df_cat, 
                            df_pres, 
                            df_sac_nominais 
                        )
                        st.session_state.pdf_lote_auditoria_geral = pdf_lote_a
                        st.toast("Dossiê de auditorias concluído!", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar lote de auditorias: {e}")

            if "pdf_lote_auditoria_geral" in st.session_state:
                st.download_button(
                    label="📥 BAIXAR TODAS AS AUDITORIAS (DOSSIÊ)", 
                    data=st.session_state.pdf_lote_auditoria_geral, 
                    file_name=f"Dossie_Auditoria_Turmas_{date.today().year}.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )

# --- PÁGINA: MINHA TURMA (FILTRO DINÂMICO PARA TODOS OS NÍVEIS) ---
elif menu == "📚 Minha Turma":
    # 1. Identificação de Permissões em Tempo Real
    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    
    # Determina quais turmas o usuário pode ver
    if eh_gestor or vinculo_raw == "TODAS":
        turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
    else:
        turmas_permitidas = [t.strip() for t in vinculo_raw.split(',') if t.strip()]

    if not turmas_permitidas:
        st.warning("⚠️ Nenhuma turma vinculada ao seu perfil. Contate a coordenação.")
        st.stop()

    # 2. MECANISMO DE ESCOLHA (Aparece para qualquer usuário com > 1 turma)
    if len(turmas_permitidas) > 1 or eh_gestor or vinculo_raw == "TODAS":
        opcoes_filtro = ["TODAS"] + turmas_permitidas
        turma_ativa = st.selectbox("🔍 Selecione a Turma para Visualizar:", opcoes_filtro, key="filtro_universal_v7")
    else:
        turma_ativa = turmas_permitidas[0]

    st.title(f"🏠 Painel: {turma_ativa}")
    
    # 3. Filtragem de Dados
    df_cron = ler_aba("cronograma")
    if turma_ativa == "TODAS":
        meus_alunos = df_cat[df_cat['etapa'].isin(turmas_permitidas)] if not df_cat.empty else pd.DataFrame()
        minhas_pres = df_pres[df_pres['id_turma'].isin(turmas_permitidas)] if not df_pres.empty else pd.DataFrame()
    else:
        meus_alunos = df_cat[df_cat['etapa'] == turma_ativa] if not df_cat.empty else pd.DataFrame()
        minhas_pres = df_pres[df_pres['id_turma'] == turma_ativa] if not df_pres.empty else pd.DataFrame()

    # 4. Métricas Consolidadas
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Catequizandos", len(meus_alunos))
    
    if not minhas_pres.empty:
        minhas_pres['status_num'] = minhas_pres['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
        freq = minhas_pres['status_num'].mean() * 100
        c2.metric("Frequência Média", f"{freq:.1f}%")
        total_encontros = minhas_pres['data_encontro'].nunique()
        c3.metric("Encontros Realizados", total_encontros)
    else:
        c2.metric("Frequência Média", "0%")
        c3.metric("Encontros Realizados", "0")

    st.divider()

    # 5. Revisão do Último Encontro (Apenas para turmas individuais)
    if turma_ativa != "TODAS":
        st.subheader("🚩 Revisão do Último Encontro")
        if not minhas_pres.empty:
            ultima_data = minhas_pres['data_encontro'].max()
            faltosos = minhas_pres[(minhas_pres['data_encontro'] == ultima_data) & (minhas_pres['status'] == 'AUSENTE')]
            if not faltosos.empty:
                st.warning(f"No último encontro ({ultima_data}), os seguintes catequizandos faltaram:")
                for _, f in faltosos.iterrows(): st.write(f"❌ {f['nome_catequizando']}")
            else:
                st.success(f"Parabéns! No último encontro ({ultima_data}), todos estavam presentes! 🎉")
        st.divider()

    # 6. Aniversariantes do Mês
    st.subheader("🎂 Aniversariantes do Mês")
    df_niver_mes = obter_aniversariantes_mes(meus_alunos)
    if not df_niver_mes.empty:
        if st.button(f"🖼️ GERAR CARD COLETIVO: {turma_ativa}", use_container_width=True, key=f"btn_col_{turma_ativa}"):
            with st.spinner("Renderizando card..."):
                lista_para_card = [f"{int(row['dia'])} | CATEQUIZANDO | {row['nome_completo']}" for _, row in df_niver_mes.iterrows()]
                card_coletivo = gerar_card_aniversario(lista_para_card, tipo="MES")
                if card_coletivo:
                    st.image(card_coletivo)
                    st.download_button("📥 Baixar Card", card_coletivo, f"Niver_{turma_ativa}.png", "image/png")
        
        st.divider()
        cols_n = st.columns(4)
        for i, (_, niver) in enumerate(df_niver_mes.iterrows()):
            with cols_n[i % 4]:
                st.info(f"**Dia {int(niver['dia'])}**\n\n{niver['nome_completo']}")
                if st.button(f"🎨 Card", key=f"btn_ind_{turma_ativa}_{i}"):
                    card_img = gerar_card_aniversario(f"{int(niver['dia'])} | CATEQUIZANDO | {niver['nome_completo']}", tipo="DIA")
                    if card_img:
                        st.image(card_img, use_container_width=True)
                        st.download_button("📥", card_img, f"Niver_{niver['nome_completo']}.png", "image/png", key=f"dl_{turma_ativa}_{i}")
    else:
        st.write("Nenhum aniversariante este mês.")

    # 7. Histórico e Contatos
    col_passado, col_futuro = st.columns(2)
    with col_passado:
        st.subheader("📖 Temas Ministrados")
        if not minhas_pres.empty:
            historico = minhas_pres[['data_encontro', 'tema_do_dia', 'id_turma']].drop_duplicates().sort_values('data_encontro', ascending=False)
            st.dataframe(historico, use_container_width=True, hide_index=True)
    with col_futuro:
        st.subheader("🎯 Próximo Encontro")
        if not df_cron.empty and turma_ativa != "TODAS":
            temas_feitos = minhas_pres['tema_do_dia'].unique().tolist() if not minhas_pres.empty else []
            proximos = df_cron[(df_cron['etapa'] == turma_ativa) & (~df_cron['titulo_tema'].isin(temas_feitos))]
            if not proximos.empty: st.success(f"**Sugestão:** {proximos.iloc[0]['titulo_tema']}")
            else: st.write("✅ Cronograma concluído!")

    st.divider()
    with st.expander("👥 Ver Lista Completa de Contatos"):
        st.dataframe(meus_alunos[['nome_completo', 'contato_principal', 'etapa', 'status']], use_container_width=True, hide_index=True)

# --- PÁGINA: DIÁRIO DE ENCONTROS ---
elif menu == "📖 Diário de Encontros":
    st.title("📖 Gestão de Temas e Encontros")
    tab_registro, tab_planejamento = st.tabs(["✅ Registrar Encontro Realizado", "📅 Planejar Próximos Temas"])

    with tab_registro:
        st.info("Use esta aba para confirmar o que foi trabalhado hoje.")
        with st.form("form_encontro_realizado"):
            data_e = st.date_input("Data", date.today(), min_value=MIN_DATA, max_value=MAX_DATA)
            tema_e = st.text_input("Tema do Encontro Realizado").upper()
            obs_e = st.text_area("Observações / Ocorrências")
            
            if st.form_submit_button("💾 SALVAR NO DIÁRIO"):
                if tema_e:
                    p = conectar_google_sheets()
                    p.worksheet("encontros").append_row([str(data_e), turma_do_catequista, tema_e, st.session_state.usuario['nome'], obs_e])
                    st.success("Encontro registrado!"); st.balloons()
                else:
                    st.warning("Informe o tema.")

    with tab_planejamento:
        st.subheader("📝 Meu Planejamento")
        st.write("Cadastre aqui os temas que você recebeu da coordenação para as próximas semanas.")
        
        with st.form("form_planejar_tema"):
            novo_tema = st.text_input("Título do Próximo Tema (Ex: A EUCARISTIA)").upper()
            detalhes_tema = st.text_area("Breve resumo ou objetivo (Opcional)")
            
            if st.form_submit_button("📌 ADICIONAR AO MEU CRONOGRAMA"):
                if novo_tema:
                    dados_planejamento = [f"PLAN-{int(time.time())}", turma_do_catequista, novo_tema, detalhes_tema]
                    if salvar_tema_cronograma(dados_planejamento):
                        st.success(f"Tema '{novo_tema}' adicionado ao seu planejamento!")
                        st.rerun()
                else:
                    st.warning("Digite o título do tema.")
        
        st.divider()
        st.write("📋 **Meus Temas Planejados:**")
        df_cron = ler_aba("cronograma")
        if not df_cron.empty:
            meu_cron = df_cron[df_cron['etapa'] == turma_do_catequista]
            if not meu_cron.empty:
                st.table(meu_cron[['titulo_tema', 'descricao_base']])
            else:
                st.write("Nenhum tema planejado ainda.")

# ==================================================================================
# BLOCO ATUALIZADO: CADASTRO COM FOCO EM RESPONSÁVEL LEGAL E DIVERSIDADE FAMILIAR
# ==================================================================================
elif menu == "📝 Cadastrar Catequizando":
    st.title("📝 Cadastro de Catequizandos")
    tab_manual, tab_csv = st.tabs(["📄 Cadastro Individual", "📂 Importar via CSV"])

    with tab_manual:
        tipo_ficha = st.radio("Tipo de Inscrição:", ["Infantil/Juvenil", "Adulto"], horizontal=True)
        lista_turmas = ["CATEQUIZANDOS SEM TURMA"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])

        with st.form("form_cadastro_30_colunas_v5", clear_on_submit=True):
            st.subheader("📍 1. Identificação")
            c1, c2, c3 = st.columns([2, 1, 1])
            nome = c1.text_input("Nome Completo").upper()
            data_nasc = c2.date_input("Data de Nascimento", value=date(1990, 1, 1), min_value=MIN_DATA, max_value=MAX_DATA)
            etapa_inscricao = c3.selectbox("Turma/Etapa", lista_turmas)

            c4, c5, c6 = st.columns(3)
            contato = c4.text_input("Telefone/WhatsApp Principal (Catequese)")
            batizado = c5.selectbox("Já é Batizado?", ["SIM", "NÃO"])
            docs_faltando = c6.text_input("Documentos em Falta").upper()
            endereco = st.text_input("Endereço Completo (Morada)").upper()

            st.divider()
            st.subheader("👪 2. Filiação e Responsáveis")
            
            # Sub-bloco para Pais Biológicos
            col_mae, col_pai = st.columns(2)
            with col_mae:
                st.markdown("##### 👩‍🦱 Dados da Mãe")
                nome_mae = st.text_input("Nome da Mãe").upper()
                prof_mae = st.text_input("Profissão da Mãe").upper()
                tel_mae = st.text_input("Telemóvel da Mãe")
            with col_pai:
                st.markdown("##### 👨‍🦱 Dados do Pai")
                nome_pai = st.text_input("Nome do Pai").upper()
                prof_pai = st.text_input("Profissão do Pai").upper()
                tel_pai = st.text_input("Telemóvel do Pai")

            # NOVO ESPAÇO EXTRA: RESPONSÁVEL LEGAL / CUIDADOR (Acolhimento de novas realidades familiares)
            st.markdown("---")
            st.info("🛡️ **Responsável Legal / Cuidador (Caso não more com os pais)**")
            st.caption("Preencha caso a criança seja cuidada por Avós, Tios, Primos ou Tutores. Isso NÃO apaga os nomes dos pais acima.")
            
            cr1, cr2, cr3 = st.columns([2, 1, 1])
            responsavel_nome = cr1.text_input("Nome do Cuidador/Responsável").upper()
            vinculo_resp = cr2.selectbox("Vínculo", ["NENHUM", "AVÓS", "TIOS", "IRMÃOS", "PADRINHOS", "OUTRO"])
            tel_responsavel = cr3.text_input("Telefone do Cuidador")

            st.divider()
            if tipo_ficha == "Adulto":
                st.subheader("💍 3. Vida Eclesial e Estado Civil (Adulto)")
                a1, a2 = st.columns(2)
                estado_civil = a1.selectbox("Seu Estado Civil", ["SOLTEIRO(A)", "CONVIVEM", "CASADO(A) IGREJA", "CASADO(A) CIVIL", "DIVORCIADO(A)", "VIÚVO(A)"])
                sacramentos_list = a2.multiselect("Sacramentos que VOCÊ já possui:", ["BATISMO", "EUCARISTIA", "MATRIMÔNIO"])
                sacramentos = ", ".join(sacramentos_list)
                
                part_grupo = a1.radio("Participa de algum Grupo/Pastoral?", ["NÃO", "SIM"], horizontal=True)
                qual_grupo = a1.text_input("Se sim, qual?") if part_grupo == "SIM" else "N/A"
                est_civil_pais, sac_pais, tem_irmaos, qtd_irmaos = "N/A", "N/A", "NÃO", 0
            else:
                st.subheader("⛪ 3. Vida Eclesial da Família (Infantil)")
                fe1, fe2 = st.columns(2)
                est_civil_pais = fe1.selectbox("Estado Civil dos Pais/Responsáveis", ["CASADOS", "UNIÃO DE FACTO", "SEPARADOS/DIVORCIADOS", "SOLTEIROS", "VIÚVO(A)"])
                sac_pais_list = fe2.multiselect("Sacramentos que os PAIS/RESPONSÁVEIS já fizeram:", ["BATISMO", "CRISMA", "EUCARISTIA", "MATRIMÔNIO"])
                sac_pais = ", ".join(sac_pais_list)
                
                part_grupo = fe1.radio("Os pais ou a criança participam de Grupo/Pastoral?", ["NÃO", "SIM"], horizontal=True)
                qual_grupo = fe1.text_input("Se sim, qual?") if part_grupo == "SIM" else "N/A"
                
                tem_irmaos = fe2.radio("Tem irmãos na catequese?", ["NÃO", "SIM"], horizontal=True)
                qtd_irmaos = fe2.number_input("Se sim, quantos?", min_value=0, step=1) if tem_irmaos == "SIM" else 0
                estado_civil, sacramentos = "N/A", "N/A"

            st.divider()
            st.subheader("🏥 4. Saúde e Preferências")
            s1, s2 = st.columns(2)
            medicamento = s1.text_input("Toma algum medicamento? (Se sim, por quê?)").upper()
            tgo = s2.selectbox("Possui TGO (Transtorno Global do Desenvolvimento)?", ["NÃO", "SIM"])
            turno = s1.selectbox("Turno de preferência", ["MANHÃ (M)", "TARDE (T)", "NOITE (N)"])
            local_enc = s2.text_input("Local do Encontro").upper()

            if st.form_submit_button("💾 SALVAR INSCRIÇÃO"):
                if nome and contato and etapa_inscricao != "SEM TURMAS":
                    novo_id = f"CAT-{int(time.time())}"
                    
                    # Lógica de definição do Responsável Principal (Coluna J)
                    # Se houver um cuidador específico, ele vai para a ficha, senão usa os pais.
                    resp_final = responsavel_nome if responsavel_nome else f"{nome_mae} / {nome_pai}"
                    
                    # Lógica da 30ª Coluna (AD): Observação Pastoral da Família
                    obs_familia = f"CUIDADOR: {responsavel_nome} ({vinculo_resp}). TEL: {tel_responsavel}" if responsavel_nome else "Mora com os pais."

                    # MONTAGEM RIGOROSA DAS 30 COLUNAS (A até AD)
                    registro = [[
                        novo_id,          # A: id_catequizando
                        etapa_inscricao,  # B: etapa
                        nome,             # C: nome_completo
                        str(data_nasc),   # D: data_nascimento
                        batizado,         # E: batizado_sn
                        contato,          # F: contato_principal
                        endereco,         # G: endereco_completo
                        nome_mae,         # H: nome_mae
                        nome_pai,         # I: nome_pai
                        resp_final,       # J: nome_responsavel (Cuidador ou Pais)
                        docs_faltando,    # K: doc_em_falta
                        qual_grupo,       # L: engajado_grupo
                        "ATIVO",          # M: status
                        medicamento,      # N: toma_medicamento_sn
                        tgo,              # O: tgo_sn
                        estado_civil,     # P: estado_civil_pais_ou_proprio
                        sacramentos,      # Q: sacramentos_ja_feitos
                        prof_mae,         # R: profissao_mae
                        tel_mae,          # S: tel_mae
                        prof_pai,         # T: profissao_pai
                        tel_pai,          # U: tel_pai
                        est_civil_pais,   # V: est_civil_pais
                        sac_pais,         # W: sac_pais
                        part_grupo,       # X: participa_grupo
                        qual_grupo,       # Y: qual_grupo
                        tem_irmaos,       # Z: tem_irmaos
                        qtd_irmaos,       # AA: qtd_irmaos
                        turno,            # AB: turno
                        local_enc,        # AC: local_encontro
                        obs_familia       # AD: obs_pastoral_familia (30ª Coluna)
                    ]]
                    
                    if salvar_lote_catequizandos(registro):
                        st.success(f"✅ {nome} CADASTRADO COM SUCESSO!"); st.balloons(); time.sleep(1); st.rerun()
      
# --- SUBSTITUIÇÃO: ABA tab_csv (CORREÇÃO TERMINOLÓGICA) ---
    with tab_csv:
        st.subheader("📂 Importação em Massa (29 Colunas)")
        st.write("O sistema reconhecerá automaticamente os dados do seu Excel/CSV.")
        
        arquivo_csv = st.file_uploader("Selecione o arquivo .csv", type="csv", key="uploader_csv_v5_final")
        
        if arquivo_csv:
            try:
                # Lendo o CSV com tratamento de separador
                df_import = pd.read_csv(arquivo_csv, encoding='utf-8').fillna("N/A")
                df_import.columns = [c.strip().lower() for c in df_import.columns]
                
                st.markdown("### 🔍 1. Revisão dos Dados Importados")
                
                # Mapeamento Inteligente de Colunas para o Preview
                col_nome = 'nome_completo' if 'nome_completo' in df_import.columns else ('nome' if 'nome' in df_import.columns else None)
                col_etapa = 'etapa' if 'etapa' in df_import.columns else None
                col_contato = 'contato_principal' if 'contato_principal' in df_import.columns else ('contato' if 'contato' in df_import.columns else None)

                if not col_nome or not col_etapa:
                    st.error("❌ Erro: O CSV precisa ter ao menos as colunas 'nome_completo' e 'etapa'.")
                else:
                    df_preview = pd.DataFrame()
                    df_preview['Nome do Catequizando'] = df_import[col_nome].astype(str).str.upper()
                    df_preview['Turma no CSV'] = df_import[col_etapa].astype(str).str.upper()
                    df_preview['Contato'] = df_import[col_contato].astype(str) if col_contato else "N/A"
                    
                    # Validação de Turmas Existentes
                    turmas_cadastradas = [str(t).upper() for t in df_turmas['nome_turma'].tolist()] if not df_turmas.empty else []
                    df_preview['Status da Turma'] = df_preview['Turma no CSV'].apply(
                        lambda x: "✅ Turma Encontrada" if x in turmas_cadastradas else "⏳ Irá para Fila de Espera"
                    )

                    st.dataframe(df_preview, use_container_width=True, hide_index=True)

                    st.markdown(f"### 📊 2. Resumo da Carga: {len(df_import)} catequizandos")
                    
                    st.divider()
                    
                    if st.button("🚀 CONFIRMAR E GRAVAR NO BANCO DE DADOS", key="btn_confirmar_import_v5"):
                        with st.spinner("Processando 29 colunas..."):
                            lista_final = []
                            for i, linha in df_import.iterrows():
                                t_csv = str(linha.get('etapa', 'CATEQUIZANDOS SEM TURMA')).upper()
                                t_final = t_csv if t_csv in turmas_cadastradas else "CATEQUIZANDOS SEM TURMA"
                                
                                # MONTAGEM RIGOROSA DAS 29 COLUNAS (A-AC)
                                # Se a coluna não existir no CSV, ele preenche com "N/A" ou 0
                                registro = [
                                    f"CSV-{int(time.time()) + i}", # A: ID
                                    t_final,                       # B: Etapa
                                    str(linha.get(col_nome, 'SEM NOME')).upper(), # C: Nome
                                    str(linha.get('data_nascimento', '01/01/2000')), # D: Nasc
                                    str(linha.get('batizado_sn', 'NÃO')).upper(), # E: Batizado
                                    str(linha.get(col_contato, 'N/A')), # F: Contato
                                    str(linha.get('endereco_completo', 'N/A')).upper(), # G: Endereço
                                    str(linha.get('nome_mae', 'N/A')).upper(), # H: Mãe
                                    str(linha.get('nome_pai', 'N/A')).upper(), # I: Pai
                                    str(linha.get('nome_responsavel', 'N/A')).upper(), # J: Resp
                                    str(linha.get('doc_em_falta', 'NADA')).upper(), # K: Docs
                                    str(linha.get('engajado_grupo', 'N/A')).upper(), # L: Engajado
                                    "ATIVO", # M: Status
                                    str(linha.get('toma_medicamento_sn', 'NÃO')).upper(), # N: Med
                                    str(linha.get('tgo_sn', 'NÃO')).upper(), # O: TGO
                                    str(linha.get('estado_civil_pais_ou_proprio', 'N/A')).upper(), # P: Est Civil
                                    str(linha.get('sacramentos_ja_feitos', 'N/A')).upper(), # Q: Sacr
                                    str(linha.get('profissao_mae', 'N/A')).upper(), # R: Prof M
                                    str(linha.get('tel_mae', 'N/A')), # S: Tel M
                                    str(linha.get('profissao_pai', 'N/A')).upper(), # T: Prof P
                                    str(linha.get('tel_pai', 'N/A')), # U: Tel P
                                    str(linha.get('est_civil_pais', 'N/A')).upper(), # V: Est Civil P
                                    str(linha.get('sac_pais', 'N/A')).upper(), # W: Sac P
                                    str(linha.get('participa_grupo', 'NÃO')).upper(), # X: Part Grupo
                                    str(linha.get('qual_grupo', 'N/A')).upper(), # Y: Qual Grupo
                                    str(linha.get('tem_irmaos', 'NÃO')).upper(), # Z: Irmãos
                                    linha.get('qtd_irmaos', 0), # AA: Qtd Irmãos
                                    str(linha.get('turno', 'N/A')).upper(), # AB: Turno
                                    str(linha.get('local_encontro', 'N/A')).upper() # AC: Local
                                ]
                                lista_final.append(registro)
                            
                            if salvar_lote_catequizandos(lista_final):
                                st.success(f"✅ Sucesso! {len(lista_final)} catequizandos importados.")
                                st.balloons()
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {e}")

# ==============================================================================
# PÁGINA: 👤 PERFIL INDIVIDUAL (VERSÃO COM STATUS EM DESTAQUE - 30 COLUNAS)
# ==============================================================================
elif menu == "👤 Perfil Individual":
    st.title("👤 Perfil e Ficha do Catequizando")
    
    if df_cat.empty:
        st.warning("⚠️ Base de dados vazia.")
    else:
        # 1. ÁREA DE BUSCA E FILTRAGEM
        c1, c2 = st.columns([2, 1])
        busca = c1.text_input("🔍 Pesquisar por nome:", key="busca_perfil_v5").upper()
        lista_t = ["TODAS"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])
        filtro_t = c2.selectbox("Filtrar por Turma:", lista_t, key="filtro_turma_perfil_v5")

        df_f = df_cat.copy()
        if busca: 
            df_f = df_f[df_f['nome_completo'].str.contains(busca, na=False)]
        if filtro_t != "TODAS": 
            df_f = df_f[df_f['etapa'] == filtro_t]
        
        st.dataframe(df_f[['nome_completo', 'etapa', 'status']], use_container_width=True, hide_index=True)
        
        # 2. SELEÇÃO DO CATEQUIZANDO
        df_f['display_select'] = df_f['nome_completo'] + " (" + df_f['etapa'] + ")"
        escolha_display = st.selectbox("Selecione para VER PRÉVIA ou EDITAR:", [""] + df_f['display_select'].tolist(), key="sel_catequizando_perfil_v5")

        if escolha_display:
            nome_sel = escolha_display.split(" (")[0]
            turma_sel = escolha_display.split(" (")[1].replace(")", "")
            dados = df_cat[(df_cat['nome_completo'] == nome_sel) & (df_cat['etapa'] == turma_sel)].iloc[0]
            
            # --- PRÉVIA VISUAL ---
            st.markdown("---")
            status_atual = str(dados['status']).upper()
            if status_atual == "ATIVO": icone, cor_txt = "🟢", "green"
            elif status_atual == "TRANSFERIDO": icone, cor_txt = "🔵", "blue"
            elif status_atual == "DESISTENTE": icone, cor_txt = "🔴", "red"
            else: icone, cor_txt = "⚪", "gray"
            
            st.markdown(f"### {icone} {dados['nome_completo']} ({status_atual})")

            # 3. ABAS DE AÇÃO
            tab_edit, tab_doc = st.tabs(["✏️ Editar Cadastro e Status", "📄 Documentação PDF"])
            
            with tab_edit:
                with st.form("form_edicao_30_colunas_v5"):
                    st.subheader("📍 1. Identificação e Status Pastoral")
                    c1, c2 = st.columns([2, 1])
                    ed_nome = c1.text_input("Nome Completo", value=dados['nome_completo']).upper()
                    
                    # CAMPO DE STATUS EM DESTAQUE
                    opcoes_status = ["ATIVO", "TRANSFERIDO", "DESISTENTE", "INATIVO"]
                    idx_status = opcoes_status.index(status_atual) if status_atual in opcoes_status else 0
                    ed_status = c2.selectbox("Alterar Status para:", opcoes_status, index=idx_status)

                    c3, c4, c5 = st.columns([1, 1, 2])
                    ed_nasc = c3.date_input("Nascimento", value=converter_para_data(dados['data_nascimento']))
                    ed_batizado = c4.selectbox("Batizado?", ["SIM", "NÃO"], index=0 if dados['batizado_sn'] == "SIM" else 1)
                    ed_etapa = c5.selectbox("Turma Atual", df_turmas['nome_turma'].tolist() if not df_turmas.empty else [dados['etapa']])

                    st.divider()
                    st.subheader("👪 2. Contatos e Filiação")
                    f1, f2 = st.columns(2)
                    ed_contato = f1.text_input("WhatsApp Principal", value=dados['contato_principal'])
                    ed_end = f2.text_input("Endereço Completo", value=dados['endereco_completo']).upper()

                    m1, m2, m3 = st.columns(3)
                    ed_mae = m1.text_input("Nome da Mãe", value=dados['nome_mae']).upper()
                    ed_prof_m = m2.text_input("Profissão Mãe", value=dados.get('profissao_mae', 'N/A')).upper()
                    ed_tel_m = m3.text_input("Tel. Mãe", value=dados.get('tel_mae', 'N/A'))

                    p1, p2, p3 = st.columns(3)
                    ed_pai = p1.text_input("Nome do Pai", value=dados['nome_pai']).upper()
                    ed_prof_p = p2.text_input("Profissão Pai", value=dados.get('profissao_pai', 'N/A')).upper()
                    ed_tel_p = p3.text_input("Tel. Pai", value=dados.get('tel_pai', 'N/A'))
                    
                    ed_resp = st.text_input("Responsável Legal / Cuidador", value=dados['nome_responsavel']).upper()

                    st.divider()
                    st.subheader("🏥 3. Saúde e Observações")
                    o1, o2, o3 = st.columns(3)
                    ed_med = o1.text_input("Medicamentos/Alergias", value=dados['toma_medicamento_sn']).upper()
                    ed_tgo = o2.selectbox("Possui TGO?", ["NÃO", "SIM"], index=0 if dados['tgo_sn'] == "NÃO" else 1)
                    ed_doc = o3.text_input("Docs em Falta", value=dados['doc_em_falta']).upper()

                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES NO BANCO DE DADOS", use_container_width=True):
                        # MONTAGEM RIGOROSA DAS 30 COLUNAS (A até AD)
                        lista_up = [
                            dados['id_catequizando'],           # A: id_catequizando
                            ed_etapa,                           # B: etapa
                            ed_nome,                            # C: nome_completo
                            str(ed_nasc),                       # D: data_nascimento
                            ed_batizado,                        # E: batizado_sn
                            ed_contato,                         # F: contato_principal
                            ed_end,                             # G: endereco_completo
                            ed_mae,                             # H: nome_mae
                            ed_pai,                             # I: nome_pai
                            ed_resp,                            # J: nome_responsavel
                            ed_doc,                             # K: doc_em_falta
                            dados.get('engajado_grupo', 'N/A'), # L: engajado_grupo
                            ed_status,                          # M: status (COLUNA M)
                            ed_med,                             # N: toma_medicamento_sn
                            ed_tgo,                             # O: tgo_sn
                            dados.get('estado_civil_pais_ou_proprio', 'N/A'), # P
                            dados.get('sacramentos_ja_feitos', 'N/A'),        # Q
                            ed_prof_m,                          # R: profissao_mae
                            ed_tel_m,                           # S: tel_mae
                            ed_prof_p,                          # T: profissao_pai
                            ed_tel_p,                           # U: tel_pai
                            dados.get('est_civil_pais', 'N/A'), # V
                            dados.get('sac_pais', 'N/A'),       # W
                            dados.get('participa_grupo', 'NÃO'),# X
                            dados.get('qual_grupo', 'N/A'),     # Y
                            dados.get('tem_irmaos', 'NÃO'),     # Z
                            dados.get('qtd_irmaos', 0),         # AA
                            dados.get('turno', 'N/A'),          # AB
                            dados.get('local_encontro', 'N/A'), # AC
                            dados.get('obs_pastoral_familia', '') # AD: 30ª Coluna
                        ]
                        if atualizar_catequizando(dados['id_catequizando'], lista_up):
                            st.success(f"✅ Cadastro de {ed_nome} atualizado para {ed_status}!"); time.sleep(1); st.rerun()

            with tab_doc:
                st.subheader("📄 Documentação PDF")
                if st.button("📑 Gerar Ficha de Inscrição", key="btn_pdf_v5", use_container_width=True):
                    st.session_state.pdf_catequizando = gerar_ficha_cadastral_catequizando(dados.to_dict())
                
                if "pdf_catequizando" in st.session_state:
                    st.download_button("📥 BAIXAR FICHA PDF", st.session_state.pdf_catequizando, f"Ficha_{nome_sel}.pdf", "application/pdf", use_container_width=True)

# --- PÁGINA: GESTÃO DE TURMAS (VERSÃO BLINDADA CONTRA KEYERROR) ---
elif menu == "🏫 Gestão de Turmas":
    st.title("🏫 Gestão de Turmas e Fila de Espera")
    
    t0, t1, t2, t3, t4, t5 = st.tabs([
        "⏳ Fila de Espera", "📋 Visualizar Turmas", "➕ Criar Nova Turma", 
        "✏️ Detalhes e Edição", "📊 Dashboard Local", "🚀 Movimentação em Massa"
    ])
    
    dias_opcoes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    etapas_lista = [
        "PRÉ", "PRIMEIRA ETAPA", "SEGUNDA ETAPA", "TERCEIRA ETAPA", 
        "PERSEVERANÇA", "ADULTOS TURMA EUCARISTIA/BATISMO", "ADULTOS CRISMA"
    ]

    with t0:
        st.subheader("⏳ Fila de Espera")
        if df_cat.empty:
            st.info("Nenhum catequizando cadastrado no sistema.")
        else:
            # Identifica turmas que realmente existem no banco para achar os 'órfãos'
            turmas_reais = df_turmas['nome_turma'].unique().tolist() if not df_turmas.empty else []
            
            # Filtra quem está sem turma ou em turma que não existe mais
            fila_espera = df_cat[(df_cat['etapa'] == "CATEQUIZANDOS SEM TURMA") | (~df_cat['etapa'].isin(turmas_reais))]
            
            if not fila_espera.empty:
                # Blindagem: Só tenta filtrar colunas se o DataFrame não estiver vazio
                colunas_para_exibir = ['nome_completo', 'etapa', 'contato_principal']
                # Garante que só usaremos colunas que realmente existem no DF
                cols_existentes = [c for c in colunas_para_exibir if c in fila_espera.columns]
                
                st.dataframe(fila_espera[cols_existentes], use_container_width=True, hide_index=True)
            else:
                st.success("Todos os catequizandos estão alocados em turmas válidas! 🎉")

    with t1:
        st.subheader("📋 Turmas Cadastradas")
        st.dataframe(df_turmas, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("➕ Cadastrar Nova Turma")
        with st.form("form_criar_t_v15"):
            c1, c2 = st.columns(2)
            n_t = c1.text_input("Nome da Turma (Ex: PRÉ ETAPA 2026)").upper()
            e_t = c1.selectbox("Etapa Base", etapas_lista)
            ano = c2.number_input("Ano Letivo", value=2026)
            n_dias = st.multiselect("Dias de Encontro", dias_opcoes)
            
            st.markdown("---")
            c3, c4 = st.columns(2)
            turno_t = c3.selectbox("Turno do Encontro", ["MANHÃ", "TARDE", "NOITE"])
            local_t = c4.text_input("Local/Sala do Encontro", value="SALA").upper()
            
            # Catequistas agora são opcionais na criação
            cats_selecionados = st.multiselect("Catequistas Responsáveis (Opcional)", equipe_tecnica['nome'].tolist() if not equipe_tecnica.empty else [])
            
            if st.form_submit_button("🚀 SALVAR NOVA TURMA"):
                # Validação: Apenas Nome e Dias são obrigatórios para a turma existir
                if n_t and n_dias:
                    try:
                        planilha = conectar_google_sheets()
                        if planilha:
                            # 1. Grava na aba 'turmas' (A turma nasce aqui, independente de catequista)
                            nova_t = [f"TRM-{int(time.time())}", n_t, e_t, int(ano), ", ".join(cats_selecionados), ", ".join(n_dias), "", "", turno_t, local_t]
                            planilha.worksheet("turmas").append_row(nova_t)
                            
                            # 2. Sincroniza Perfis (Apenas se houver catequistas selecionados)
                            if cats_selecionados:
                                aba_u = planilha.worksheet("usuarios")
                                for c_nome in cats_selecionados:
                                    celula = aba_u.find(c_nome, in_column=1)
                                    if celula:
                                        v_atual = aba_u.cell(celula.row, 5).value or ""
                                        v_list = [x.strip() for x in v_atual.split(',') if x.strip()]
                                        if n_t not in v_list:
                                            v_list.append(n_t)
                                            aba_u.update_cell(celula.row, 5, ", ".join(v_list))
                            
                            st.success(f"✅ Turma '{n_t}' criada com sucesso!")
                            st.cache_data.clear()
                            time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Erro ao salvar: {e}")
                else: st.warning("⚠️ O Nome da Turma e os Dias de Encontro são obrigatórios.")

    with t3:
        st.subheader("✏️ Detalhes e Edição da Turma")
        if not df_turmas.empty:
            sel_t = st.selectbox("Selecione a turma para editar:", [""] + df_turmas['nome_turma'].tolist(), key="sel_edit_final_v15")
            
            if sel_t:
                d = df_turmas[df_turmas['nome_turma'] == sel_t].iloc[0]
                nome_turma_original = str(d['nome_turma'])
                
                c1, c2 = st.columns(2)
                en = c1.text_input("Nome da Turma", value=d['nome_turma'], key="edit_nome_v15").upper()
                ee = c1.selectbox("Etapa Base", etapas_lista, index=etapas_lista.index(d['etapa']) if d['etapa'] in etapas_lista else 0, key="edit_etapa_v15")
                ea = c2.number_input("Ano Letivo", value=int(d['ano']), key="edit_ano_v15")
                
                dias_atuais = [x.strip() for x in str(d.get('dias_semana', '')).split(',') if x.strip()]
                ed_dias = st.multiselect("Dias de Encontro", dias_opcoes, default=[d for d in dias_atuais if d in dias_opcoes], key="edit_dias_v15")
                
                st.markdown("---")
                c3, c4 = st.columns(2)
                opcoes_turno = ["MANHÃ", "TARDE", "NOITE"]
                turno_atual = str(d.get('turno', 'MANHÃ')).upper()
                et = c3.selectbox("Turno", opcoes_turno, index=opcoes_turno.index(turno_atual) if turno_atual in opcoes_turno else 0, key="edit_turno_v15")
                el = c4.text_input("Local / Sala", value=d.get('local', 'SALA'), key="edit_local_v15").upper()
                
                pe = c1.text_input("Previsão Eucaristia", value=d.get('previsao_eucaristia', ''), key="edit_pe_v15")
                pc = c2.text_input("Previsão Crisma", value=d.get('previsao_crisma', ''), key="edit_pc_v15")
                
                lista_todos_cats = equipe_tecnica['nome'].tolist() if not equipe_tecnica.empty else []
                cats_atuais_lista = [c.strip() for c in str(d.get('catequista_responsavel', '')).split(',') if c.strip()]
                ed_cats = st.multiselect("Catequistas Responsáveis", options=lista_todos_cats, default=[c for c in cats_atuais_lista if c in lista_todos_cats], key="edit_cats_v15")
                
                col_btn_save, col_btn_del = st.columns([3, 1])
                
                with col_btn_save:
                    if st.button("💾 SALVAR ALTERAÇÕES E SINCRONIZAR", key="btn_save_edit_v15", use_container_width=True):
                        with st.spinner("Processando atualizações..."):
                            lista_up = [str(d['id_turma']), en, ee, int(ea), ", ".join(ed_cats), ", ".join(ed_dias), pe, pc, et, el]
                            if atualizar_turma(d['id_turma'], lista_up):
                                planilha = conectar_google_sheets()
                                aba_u = planilha.worksheet("usuarios")
                                for _, cat_row in equipe_tecnica.iterrows():
                                    c_nome = cat_row['nome']
                                    celula = aba_u.find(c_nome, in_column=1)
                                    if celula:
                                        v_atual = aba_u.cell(celula.row, 5).value or ""
                                        v_list = [x.strip() for x in v_atual.split(',') if x.strip()]
                                        mudou = False
                                        if c_nome in ed_cats:
                                            if en not in v_list: v_list.append(en); mudou = True
                                            if nome_turma_original in v_list and en != nome_turma_original:
                                                v_list.remove(nome_turma_original); mudou = True
                                        else:
                                            if en in v_list: v_list.remove(en); mudou = True
                                            if nome_turma_original in v_list: v_list.remove(nome_turma_original); mudou = True
                                        if mudou: aba_u.update_cell(celula.row, 5, ", ".join(v_list))
                                st.success("✅ Sincronizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

                # --- NOVO MECANISMO: EXCLUIR TURMA ---
                st.markdown("<br><br>", unsafe_allow_html=True)
                with st.expander("🗑️ ZONA DE PERIGO: Excluir Turma"):
                    st.error(f"Atenção: Ao excluir a turma '{sel_t}', todos os catequizandos nela matriculados serão movidos para a Fila de Espera.")
                    confirmar_exclusao = st.checkbox(f"Confirmo a exclusão definitiva da turma {sel_t}", key="chk_del_t")
                    
                    if st.button("🗑️ EXCLUIR TURMA AGORA", type="primary", disabled=not confirmar_exclusao, use_container_width=True):
                        with st.spinner("Movendo catequizandos e excluindo itinerário..."):
                            # 1. Localiza e move catequizandos para a Fila de Espera
                            alunos_da_turma = df_cat[df_cat['etapa'] == sel_t]
                            if not alunos_da_turma.empty:
                                ids_para_mover = alunos_da_turma['id_catequizando'].tolist()
                                mover_catequizandos_em_massa(ids_para_mover, "CATEQUIZANDOS SEM TURMA")
                            
                            # 2. Remove vínculo dos catequistas na aba usuarios
                            planilha = conectar_google_sheets()
                            aba_u = planilha.worksheet("usuarios")
                            for _, cat_row in equipe_tecnica.iterrows():
                                v_atual = str(cat_row.get('turma_vinculada', ''))
                                if sel_t in v_atual:
                                    v_list = [x.strip() for x in v_atual.split(',') if x.strip()]
                                    if sel_t in v_list:
                                        v_list.remove(sel_t)
                                        celula_u = aba_u.find(cat_row['nome'], in_column=1)
                                        if celula_u:
                                            aba_u.update_cell(celula_u.row, 5, ", ".join(v_list))
                            
                            # 3. Exclui a turma da aba turmas
                            if excluir_turma(d['id_turma']):
                                st.success(f"Turma excluída! {len(alunos_da_turma)} catequizandos movidos para a Fila de Espera.")
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()

    with t4:
        st.subheader("📊 Inteligência Pastoral da Turma")
        if not df_turmas.empty:
            # Usamos uma chave v6 para garantir um estado limpo no navegador
            t_alvo = st.selectbox("Selecione a turma para auditoria:", df_turmas['nome_turma'].tolist(), key="sel_dash_t_v6_final")
            
            alunos_t = df_cat[df_cat['etapa'] == t_alvo] if not df_cat.empty else pd.DataFrame()
            info_t = df_turmas[df_turmas['nome_turma'] == t_alvo].iloc[0]
            pres_t = df_pres[df_pres['id_turma'] == t_alvo] if not df_pres.empty else pd.DataFrame()
            df_recebidos = ler_aba("sacramentos_recebidos")
            
            if not alunos_t.empty:
                # --- MÉTRICAS ---
                m1, m2, m3, m4 = st.columns(4)
                
                # Cálculo real de catequistas para a tela e para o PDF
                qtd_cats_real = len(str(info_t['catequista_responsavel']).split(','))
                m1.metric("Catequistas", qtd_cats_real)
                m2.metric("Catequizandos", len(alunos_t))
                
                freq_global = 0.0
                lista_freq_mensal = []
                
                # BLINDAGEM: Verifica se a coluna de ID existe na tabela de presenças
                tem_coluna_id = not pres_t.empty and 'id_catequizando' in pres_t.columns
                
                if not pres_t.empty:
                    pres_t['status_num'] = pres_t['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                    freq_global = round(pres_t['status_num'].mean() * 100, 1)
                    try:
                        pres_t['data_dt'] = pd.to_datetime(pres_t['data_encontro'], dayfirst=True, errors='coerce')
                        pres_t['mes_ano'] = pres_t['data_dt'].dt.strftime('%m/%Y')
                        mensal = pres_t.groupby('mes_ano')['status_num'].mean() * 100
                        for mes, taxa in mensal.items():
                            lista_freq_mensal.append({'mes': mes, 'taxa': round(taxa, 1)})
                    except: pass
                
                m3.metric("Frequência Global", f"{freq_global}%")
                
                # Cálculo real da idade média para a tela e para o PDF
                idades = [calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
                idade_media_val = round(sum(idades)/len(idades), 1) if idades else 0
                m4.metric("Idade Média", f"{idade_media_val} anos")

                st.divider()
                
                # --- BLOCO DE DOCUMENTAÇÃO ---
                st.markdown("#### 📄 Documentação e Auditoria")
                col_doc1, col_doc2 = st.columns(2)
                
                with col_doc1:
                    if st.button(f"✨ GERAR AUDITORIA PASTORAL: {t_alvo}", use_container_width=True, key="btn_auditoria_v6"):
                        with st.spinner("Analisando itinerário..."):
                            resumo_ia = f"Turma {t_alvo}: {len(alunos_t)} catequizandos. Freq: {freq_global}%."
                            parecer_ia = analisar_turma_local(t_alvo, resumo_ia)
                            
                            # Coleta de dados nominais BLINDADA contra KeyError
                            lista_geral = []
                            for _, r in alunos_t.iterrows():
                                f = 0
                                if tem_coluna_id:
                                    # Só tenta filtrar se a coluna existir
                                    f = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')])
                                lista_geral.append({'nome': r['nome_completo'], 'faltas': f})
                            
                            lista_sac = []
                            if not df_recebidos.empty and 'id_catequizando' in df_recebidos.columns:
                                sac_t = df_recebidos[df_recebidos['id_catequizando'].isin(alunos_t['id_catequizando'].tolist())]
                                for _, s in sac_t.iterrows():
                                    lista_sac.append({'nome': s.get('nome',''), 'tipo': s.get('tipo',''), 'data': s.get('data','')})

                            # CORREÇÃO APLICADA AQUI: Passando qtd_cats_real e idade_media_val
                            st.session_state[f"pdf_auditoria_{t_alvo}"] = gerar_relatorio_local_turma_v2(
                                t_alvo, 
                                {
                                    'qtd_catequistas': qtd_cats_real, 
                                    'qtd_cat': len(alunos_t), 
                                    'freq_global': freq_global, 
                                    'idade_media': idade_media_val, 
                                    'freq_mensal': lista_freq_mensal
                                }, 
                                {'geral': lista_geral, 'sac_recebidos': lista_sac}, 
                                parecer_ia
                            )
                    
                    if f"pdf_auditoria_{t_alvo}" in st.session_state:
                        st.download_button("📥 BAIXAR AUDITORIA", st.session_state[f"pdf_auditoria_{t_alvo}"], f"Auditoria_{t_alvo}.pdf", use_container_width=True)

                with col_doc2:
                    if st.button(f"📄 GERAR FICHAS DA TURMA (LOTE)", use_container_width=True, key="btn_fichas_v6"):
                        with st.spinner("Gerando fichas individuais..."):
                            pdf_fichas = gerar_fichas_turma_completa(t_alvo, alunos_t)
                            st.session_state[f"pdf_fichas_{t_alvo}"] = pdf_fichas
                    
                    if f"pdf_fichas_{t_alvo}" in st.session_state:
                        st.download_button("📥 BAIXAR FICHAS (LOTE)", st.session_state[f"pdf_fichas_{t_alvo}"], f"Fichas_{t_alvo}.pdf", use_container_width=True)

                st.divider()
                
                # --- PREVIEW NOMINAL ---
                st.markdown("### 📋 Lista Nominal de Caminhada")
                lista_preview = []
                for _, r in alunos_t.iterrows():
                    f = 0
                    if tem_coluna_id:
                        f = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')])
                    lista_preview.append({'Catequizando': r['nome_completo'], 'Faltas': f, 'Status': r['status']})
                st.dataframe(pd.DataFrame(lista_preview), use_container_width=True, hide_index=True)
            else:
                st.info("Selecione uma turma com catequizandos ativos.")

    with t5:
        st.subheader("🚀 Movimentação em Massa")
        if not df_turmas.empty and not df_cat.empty:
            c1, c2 = st.columns(2)
            opcoes_origem = ["CATEQUIZANDOS SEM TURMA"] + sorted(df_cat['etapa'].unique().tolist())
            t_origem = c1.selectbox("1. Turma de ORIGEM (Sair de):", opcoes_origem, key="mov_orig_v6")
            t_destino = c2.selectbox("2. Turma de DESTINO (Ir para):", df_turmas['nome_turma'].tolist(), key="mov_dest_v6")
            
            if t_origem:
                alunos_mov = df_cat[(df_cat['etapa'] == t_origem) & (df_cat['status'] == 'ATIVO')]
                if not alunos_mov.empty:
                    # Lógica de sincronização v6
                    def toggle_all_v6():
                        for _, al in alunos_mov.iterrows():
                            st.session_state[f"mov_al_v6_{al['id_catequizando']}"] = st.session_state.chk_mov_todos_v6

                    st.checkbox("Selecionar todos os catequizandos", key="chk_mov_todos_v6", on_change=toggle_all_v6)
                    
                    lista_ids_selecionados = []
                    cols = st.columns(2)
                    for i, (_, al) in enumerate(alunos_mov.iterrows()):
                        with cols[i % 2]:
                            if st.checkbox(f"{al['nome_completo']}", key=f"mov_al_v6_{al['id_catequizando']}"):
                                lista_ids_selecionados.append(al['id_catequizando'])
                    
                    st.divider()
                    if st.button(f"🚀 MOVER {len(lista_ids_selecionados)} CATEQUIZANDOS", key="btn_exec_mov_v6", use_container_width=True):
                        if t_destino and t_origem != t_destino and lista_ids_selecionados:
                            if mover_catequizandos_em_massa(lista_ids_selecionados, t_destino):
                                st.success(f"✅ Sucesso! {len(lista_ids_selecionados)} movidos para {t_destino}."); st.cache_data.clear(); time.sleep(2); st.rerun()
                        else: st.error("Selecione um destino válido e ao menos um catequizando.")

# ==============================================================================
# BLOCO INTEGRAL: GESTÃO DE SACRAMENTOS (CORREÇÃO DE CENSO E AUDITORIA)
# ==============================================================================
elif menu == "🕊️ Gestão de Sacramentos":
    st.title("🕊️ Auditoria e Gestão de Sacramentos")
    tab_dash, tab_reg, tab_hist = st.tabs(["📊 Auditoria Sacramental", "✍️ Registrar Sacramento", "📜 Histórico"])
    
    with tab_dash:
        # 1. Censo de Batismos realizados NO SISTEMA (Aba sacramentos_recebidos)
        total_batismos_ano = 0
        df_recebidos = ler_aba("sacramentos_recebidos")
        
        if not df_recebidos.empty:
            try:
                # Tenta identificar a coluna de data (pode ser 'data' ou 'data_recebimento')
                col_dt = 'data' if 'data' in df_recebidos.columns else 'data_recebimento'
                df_recebidos['data_dt'] = pd.to_datetime(df_recebidos[col_dt], errors='coerce')
                # Filtra batismos do ano atual (2026 conforme seu sistema)
                total_batismos_ano = len(df_recebidos[
                    (df_recebidos['tipo'].str.upper().str.contains('BATISMO')) & 
                    (df_recebidos['data_dt'].dt.year == 2026)
                ])
            except: pass

        st.markdown(f"""
            <div style='background-color:#f8f9f0; padding:20px; border-radius:10px; border:1px solid #e03d11; text-align:center; margin-bottom:20px;'>
                <h3 style='margin:0; color:#e03d11;'>🕊️ Frutos da Evangelização 2026</h3>
                <p style='font-size:22px; color:#417b99; margin:5px 0;'><b>{total_batismos_ano} Batismos realizados este ano</b></p>
                <p style='font-size:14px; color:#666;'>Registros de novos sacramentos efetuados através do sistema.</p>
            </div>
        """, unsafe_allow_html=True)

        # 2. Segmentação de Público por IDADE (Correção do Denominador)
        if not df_cat.empty:
            # Criamos uma cópia para não afetar o DF global e calculamos a idade real
            df_censo = df_cat.copy()
            df_censo['idade_real'] = df_censo['data_nascimento'].apply(calcular_idade)
            
            df_kids = df_censo[df_censo['idade_real'] < 18]
            df_adults = df_censo[df_censo['idade_real'] >= 18]
            
            st.subheader("📊 Quadro Geral de Sacramentos (Censo Paroquial)")
            col_k, col_a = st.columns(2)
            
            with col_k:
                st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'><b>PÚBLICO INFANTIL / JUVENIL</b></div>", unsafe_allow_html=True)
                total_k = len(df_kids)
                if total_k > 0:
                    k_bat = len(df_kids[df_kids['batizado_sn'].str.upper() == 'SIM'])
                    perc_k = (k_bat / total_k) * 100
                    st.metric("Batizados (Kids)", f"{k_bat} / {total_k}", f"{perc_k:.1f}% batizados")
                else: st.write("Nenhum registro infantil.")

            with col_a:
                st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'><b>PÚBLICO ADULTOS</b></div>", unsafe_allow_html=True)
                total_a = len(df_adults)
                if total_a > 0:
                    a_bat = len(df_adults[df_adults['batizado_sn'].str.upper() == 'SIM'])
                    perc_a = (a_bat / total_a) * 100
                    st.metric("Batizados (Adultos)", f"{a_bat} / {total_a}", f"{perc_a:.1f}% batizados")
                else: st.write("Nenhum registro de adultos.")
        else:
            st.warning("Base de catequizandos vazia.")

        st.divider()
        st.subheader("🏫 Auditoria Nominal e Pastoral por Turma")
        
        analise_detalhada_ia = []
        if not df_turmas.empty:
            for _, t in df_turmas.iterrows():
                # Filtro robusto: remove espaços extras e converte para maiúsculo
                nome_t = str(t['nome_turma']).strip().upper()
                alunos_t = df_cat[df_cat['etapa'].str.strip().str.upper() == nome_t] if not df_cat.empty else pd.DataFrame()
                
                if not alunos_t.empty:
                    pres_t = df_pres[df_pres['id_turma'] == t['nome_turma']] if not df_pres.empty else pd.DataFrame()
                    freq_media = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100) if not pres_t.empty else 0
                    
                    idades = [calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
                    # Impedimentos baseados em situação matrimonial (para adultos)
                    impedimentos = len(alunos_t[alunos_t['estado_civil_pais_ou_proprio'].isin(['DIVORCIADO(A)', 'CASADO(A) CIVIL', 'CONVIVEM'])])
                    
                    batizados_list = alunos_t[alunos_t['batizado_sn'].str.upper() == 'SIM']
                    pendentes_list = alunos_t[alunos_t['batizado_sn'].str.upper() != 'SIM']
                    
                    with st.expander(f"📍 {t['nome_turma']} ({t['etapa']}) - Frequência: {freq_media:.1f}%"):
                        col_p1, col_p2 = st.columns([2, 1])
                        with col_p1:
                            st.write(f"**Faixa Etária:** {min(idades)} a {max(idades)} anos")
                            if impedimentos > 0 and min(idades) >= 18: 
                                st.warning(f"⚠️ {impedimentos} adultos com situação matrimonial a regularizar.")
                            
                            st.markdown("---")
                            cb1, cb2 = st.columns(2)
                            with cb1:
                                st.success(f"✅ Batizados ({len(batizados_list)})")
                                for n_bat in batizados_list['nome_completo'].tolist(): st.write(f"· {n_bat}")
                            with cb2:
                                st.error(f"❌ Pendentes ({len(pendentes_list)})")
                                for n_pend in pendentes_list['nome_completo'].tolist(): st.write(f"· {n_pend}")
                        
                        with col_p2:
                            st.markdown("**Previsões:**")
                            st.write(f"Eucaristia: `{t.get('previsao_eucaristia', 'N/A')}`")
                            st.write(f"Crisma: `{t.get('previsao_crisma', 'N/A')}`")

                    analise_detalhada_ia.append({
                        "turma": t['nome_turma'], "etapa": t['etapa'], "freq": f"{freq_media:.1f}%",
                        "batizados": len(batizados_list), "pendentes": len(pendentes_list),
                        "nomes_pendentes": pendentes_list['nome_completo'].tolist(),
                        "impedimentos_civel": impedimentos
                    })

        st.divider()
        st.subheader("🏛️ Relatório Oficial de Auditoria")
        
        if "pdf_sac_tecnico" in st.session_state:
            st.success("✅ Auditoria Diocesana pronta para download!")
            st.download_button(
                label="📥 BAIXAR AUDITORIA SACRAMENTAL (PDF)",
                data=st.session_state.pdf_sac_tecnico,
                file_name=f"Auditoria_Pastoral_Fatima_{date.today().year}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            if st.button("🔄 Gerar Novo Relatório (Atualizar)"):
                del st.session_state.pdf_sac_tecnico
                st.rerun()
        else:
            if st.button("✨ GERAR AUDITORIA PASTORAL COMPLETA", key="btn_disparar_ia_sac_v3", use_container_width=True):
                with st.spinner("O Auditor IA está sincronizando os dados reais..."):
                    try:
                        # Recalcula estatísticas para o PDF usando a lógica de idade
                        df_censo_pdf = df_cat.copy()
                        df_censo_pdf['idade_real'] = df_censo_pdf['data_nascimento'].apply(calcular_idade)
                        
                        df_k_pdf = df_censo_pdf[df_censo_pdf['idade_real'] < 18]
                        df_a_pdf = df_censo_pdf[df_censo_pdf['idade_real'] >= 18]

                        stats_gerais = {
                            'bat_k': len(df_k_pdf[df_k_pdf['batizado_sn'].str.upper() == 'SIM']),
                            'bat_a': len(df_a_pdf[df_a_pdf['batizado_sn'].str.upper() == 'SIM']),
                            'total_k': len(df_k_pdf),
                            'total_a': len(df_a_pdf),
                            'euca_k': df_k_pdf['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum(),
                            'euca_a': df_a_pdf['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum(),
                            'crisma_a': df_a_pdf['sacramentos_ja_feitos'].str.contains("CRISMA", na=False).sum()
                        }

                        analise_ia_sac = gerar_relatorio_sacramentos_ia(str(stats_gerais))
                        st.session_state.pdf_sac_tecnico = gerar_relatorio_sacramentos_tecnico_v2(
                            stats_gerais, analise_detalhada_ia, [], analise_ia_sac
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na sincronização: {e}")

    # --- ABAS DE REGISTRO E HISTÓRICO ---
    with tab_reg:
        st.subheader("✍️ Registro de Sacramento")
        modo_reg = st.radio("Como deseja registrar?", ["Individual (Busca por Nome)", "Por Turma (Mutirão)"], horizontal=True)
        
        if modo_reg == "Individual (Busca por Nome)":
            nome_busca = st.text_input("🔍 Digite o nome do catequizando:").upper()
            if nome_busca:
                sugestoes = df_cat[df_cat['nome_completo'].str.contains(nome_busca)] if not df_cat.empty else pd.DataFrame()
                if not sugestoes.empty:
                    escolhido = st.selectbox("Selecione o catequizando:", sugestoes['nome_completo'].tolist())
                    dados_c = sugestoes[sugestoes['nome_completo'] == escolhido].iloc[0]
                    with st.form("form_sac_individual"):
                        st.write(f"Registrando para: **{escolhido}**")
                        c1, c2 = st.columns(2)
                        tipo_s = c1.selectbox("Sacramento", ["BATISMO", "EUCARISTIA", "CRISMA"])
                        data_s = c2.date_input("Data", date.today())
                        if st.form_submit_button("💾 SALVAR REGISTRO"):
                            id_ev = f"IND-{int(time.time())}"
                            if registrar_evento_sacramento_completo([id_ev, tipo_s, str(data_s), dados_c['etapa'], st.session_state.usuario['nome']], [[id_ev, dados_c['id_catequizando'], escolhido, tipo_s, str(data_s)]], tipo_s):
                                st.success("Registrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                else: st.warning("Não encontrado.")
        else:
            turmas_s = st.multiselect("Selecione as Turmas:", df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])
            if turmas_s:
                with st.form("form_sac_lote"):
                    tipo_s = st.selectbox("Tipo de Sacramento", ["BATISMO", "EUCARISTIA", "CRISMA"])
                    data_s = st.date_input("Data da Celebração", date.today())
                    alunos_f = df_cat[df_cat['etapa'].isin(turmas_s)].sort_values('nome_completo')
                    sel_ids = []
                    if not alunos_f.empty:
                        cols = st.columns(2)
                        for i, (_, r) in enumerate(alunos_f.iterrows()):
                            with cols[i % 2]:
                                if st.checkbox(f"{r['nome_completo']}", key=f"chk_sac_{r['id_catequizando']}"): sel_ids.append(r)
                    if st.form_submit_button("💾 SALVAR EM LOTE"):
                        id_ev = f"SAC-{int(time.time())}"
                        lista_p = [[id_ev, r['id_catequizando'], r['nome_completo'], tipo_s, str(data_s)] for r in sel_ids]
                        if registrar_evento_sacramento_completo([id_ev, tipo_s, str(data_s), ", ".join(turmas_s), st.session_state.usuario['nome']], lista_p, tipo_s):
                            st.success("Registrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    with tab_hist:
        st.subheader("📜 Histórico de Eventos")
        df_eventos = ler_aba("sacramentos_eventos")
        if not df_eventos.empty:
            st.dataframe(df_eventos.sort_values(by=df_eventos.columns[2], ascending=False), use_container_width=True, hide_index=True)
        else: st.info("Nenhum evento registrado.")

# --- PÁGINA: FAZER CHAMADA (FILTRO DINÂMICO PARA MULTI-TURMAS) ---
elif menu == "✅ Fazer Chamada":
    st.title("✅ Chamada Inteligente")
    
    # 1. Identificação de Permissões (Mesma lógica robusta)
    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    if eh_gestor or vinculo_raw == "TODAS":
        turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
    else:
        turmas_permitidas = [t.strip() for t in vinculo_raw.split(',') if t.strip()]

    if not turmas_permitidas:
        st.error("❌ Você não possui turmas vinculadas para realizar chamada.")
        st.stop()

    # 2. MECANISMO DE ESCOLHA DA TURMA PARA CHAMADA
    if len(turmas_permitidas) > 1 or eh_gestor or vinculo_raw == "TODAS":
        turma_selecionada = st.selectbox("Selecione a Turma para a Chamada:", turmas_permitidas, key="sel_turma_chamada_v7")
    else:
        turma_selecionada = turmas_permitidas[0]
        st.info(f"📋 Realizando chamada para: **{turma_selecionada}**")

    # 3. Configuração do Encontro
    c1, c2 = st.columns(2)
    data_encontro = c1.date_input("Data do Encontro", date.today(), key="data_chamada_v7")
    
    tema_encontrado = buscar_encontro_por_data(turma_selecionada, data_encontro)
    tema_dia = c2.text_input("Tema do Encontro:", value=tema_encontrado if tema_encontrado else "", key="tema_chamada_v7").upper()
    
    # 4. Lista de Chamada
    lista_chamada = df_cat[(df_cat['etapa'] == turma_selecionada) & (df_cat['status'] == 'ATIVO')]
    
    if lista_chamada.empty:
        st.warning(f"Nenhum catequizando ativo na turma {turma_selecionada}.")
    else:
        st.divider()
        def toggle_presenca_total():
            for _, row in lista_chamada.iterrows():
                st.session_state[f"pres_v7_{row['id_catequizando']}_{data_encontro}"] = st.session_state.chk_marcar_todos_v7

        st.checkbox("✅ MARCAR TODOS COMO PRESENTES", key="chk_marcar_todos_v7", on_change=toggle_presenca_total)
        
        with st.form("form_chamada_v7_final"):
            registros_presenca = []
            for _, row in lista_chamada.iterrows():
                col_nome, col_check, col_niver = st.columns([3, 1, 2])
                col_nome.write(row['nome_completo'])
                presente = col_check.checkbox("P", key=f"pres_v7_{row['id_catequizando']}_{data_encontro}")
                
                if eh_aniversariante_da_semana(row['data_nascimento']):
                    col_niver.success("🎂 NIVER NA SEMANA!")
                
                registros_presenca.append([
                    str(data_encontro), row['id_catequizando'], row['nome_completo'], 
                    turma_selecionada, "PRESENTE" if presente else "AUSENTE", 
                    tema_dia, st.session_state.usuario['nome']
                ])
            
            if st.form_submit_button("🚀 FINALIZAR CHAMADA E SALVAR"):
                if not tema_dia:
                    st.error("⚠️ Informe o TEMA do encontro.")
                else:
                    if salvar_presencas(registros_presenca):
                        st.success("✅ Chamada salva!"); st.balloons(); time.sleep(1); st.rerun()

# ==============================================================================
# BLOCO INTEGRAL: GESTÃO DE CATEQUISTAS (DASHBOARD COMPLETO + EDIÇÃO + CADASTRO)
# ==============================================================================
elif menu == "👥 Gestão de Catequistas":
    st.title("👥 Gestão de Catequistas e Formação")
    
    df_formacoes = ler_aba("formacoes")
    df_pres_form = ler_aba("presenca_formacao")
    
    tab_dash, tab_lista, tab_novo, tab_formacao = st.tabs([
        "📊 Dashboard de Equipe", "📋 Lista e Perfil", 
        "➕ Novo Acesso", "🎓 Registro de Formação"
    ])

    with tab_dash:
        st.subheader("📊 Qualificação da Equipe Catequética")
        if not equipe_tecnica.empty:
            # 1. Métricas Principais (Excluindo ADMIN da contagem pastoral)
            total_e = len(equipe_tecnica)
            bat_e = equipe_tecnica['data_batismo'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
            euc_e = equipe_tecnica['data_eucaristia'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
            cri_e = equipe_tecnica['data_crisma'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
            min_e = equipe_tecnica['data_ministerio'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Equipe", total_e)
            m2.metric("Batizados", bat_e)
            m3.metric("Eucaristia", euc_e)
            m4.metric("Crismados", cri_e)
            m5.metric("Ministros", min_e)

            st.divider()

            # 2. Status Ministerial (Regra Diocesana: 5 anos + Sacramentos)
            st.markdown("### 🛡️ Maturidade Ministerial")
            status_data = []
            for _, row in equipe_tecnica.iterrows():
                status, anos = verificar_status_ministerial(
                    str(row.get('data_inicio_catequese', '')),
                    str(row.get('data_batismo', '')),
                    str(row.get('data_eucaristia', '')),
                    str(row.get('data_crisma', '')),
                    str(row.get('data_ministerio', ''))
                )
                status_data.append({
                    "Nome": row['nome'], 
                    "Status": status, 
                    "Anos de Missão": anos,
                    "Turmas": row['turma_vinculada']
                })
            
            df_status = pd.DataFrame(status_data)
            c_apt, c_cam = st.columns(2)
            
            with c_apt:
                st.success("**✅ Aptos / Ministros de Catequese**")
                st.dataframe(df_status[df_status['Status'].isin(['MINISTRO', 'APTO'])], use_container_width=True, hide_index=True)
            
            with c_cam:
                st.warning("**⏳ Em Caminhada de Formação**")
                st.dataframe(df_status[df_status['Status'] == 'EM_CAMINHADA'], use_container_width=True, hide_index=True)

            st.divider()
            if st.button("🗂️ GERAR DOSSIÊ COMPLETO DA EQUIPE (PDF)"):
                with st.spinner("Consolidando currículos..."):
                    pdf_equipe = gerar_fichas_catequistas_lote(equipe_tecnica, df_pres_form, df_formacoes)
                    st.session_state.pdf_lote_equipe = pdf_equipe
            if "pdf_lote_equipe" in st.session_state:
                st.download_button("📥 BAIXAR DOSSIÊ DA EQUIPE", st.session_state.pdf_lote_equipe, "Dossie_Equipe_Catequetica.pdf", use_container_width=True)
        else:
            st.info("Nenhum catequista cadastrado para análise.")

    with tab_lista:
        st.subheader("📋 Relação e Perfil Individual")
        if not equipe_tecnica.empty:
            busca_c = st.text_input("🔍 Pesquisar catequista por nome:", key="busca_cat_v13").upper()
            df_c_filtrado = equipe_tecnica[equipe_tecnica['nome'].str.contains(busca_c, na=False)] if busca_c else equipe_tecnica
            st.dataframe(df_c_filtrado[['nome', 'email', 'turma_vinculada', 'papel']], use_container_width=True, hide_index=True)
            
            st.divider()
            escolha_c = st.selectbox("Selecione para ver Perfil ou Editar:", [""] + df_c_filtrado['nome'].tolist(), key="sel_cat_v13")
            
            if escolha_c:
                u = equipe_tecnica[equipe_tecnica['nome'] == escolha_c].iloc[0]
                col_perfil, col_edit = st.tabs(["👤 Perfil e Ficha", "✏️ Editar Cadastro"])
                
                with col_perfil:
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"### {u['nome']}")
                        st.write(f"**E-mail:** {u['email']}")
                        st.write(f"**Telefone:** {u.get('telefone', 'N/A')}")
                        st.write(f"**Nascimento:** {formatar_data_br(u.get('data_nascimento', ''))}")
                        st.write(f"**Início na Catequese:** {formatar_data_br(u.get('data_inicio_catequese', ''))}")
                        st.write(f"**Turmas Vinculadas:** {u['turma_vinculada']}")
                    with c2:
                        if st.button(f"📄 Gerar Ficha PDF de {escolha_c}"):
                            st.session_state.pdf_catequista = gerar_ficha_catequista_pdf(u.to_dict(), pd.DataFrame())
                        if "pdf_catequista" in st.session_state:
                            st.download_button("📥 Baixar Ficha", st.session_state.pdf_catequista, f"Ficha_{escolha_c}.pdf")

                with col_edit:
                    with st.form(f"form_edit_cat_v13_{u['email']}"):
                        c1, c2, c3 = st.columns(3)
                        ed_nome = c1.text_input("Nome Completo", value=str(u.get('nome', ''))).upper()
                        ed_senha = c2.text_input("Senha de Acesso", value=str(u.get('senha', '')), type="password")
                        ed_tel = c3.text_input("Telefone / WhatsApp", value=str(u.get('telefone', '')))
                        
                        ed_nasc = st.date_input("Data de Nascimento", value=converter_para_data(u.get('data_nascimento', '')))
                        
                        lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else []
                        ed_turmas = st.multiselect("Vincular às Turmas:", lista_t_nomes, default=[t.strip() for t in str(u.get('turma_vinculada', '')).split(",") if t.strip() in lista_t_nomes])
                        
                        st.markdown("**Datas Sacramentais e Início:**")
                        d1, d2, d3, d4, d5 = st.columns(5)
                        dt_ini = d1.text_input("Início Catequese", value=str(u.get('data_inicio_catequese', '')))
                        dt_bat = d2.text_input("Data Batismo", value=str(u.get('data_batismo', '')))
                        dt_euc = d3.text_input("Data Eucaristia", value=str(u.get('data_eucaristia', '')))
                        dt_cri = d4.text_input("Data Crisma", value=str(u.get('data_crisma', '')))
                        dt_min = d5.text_input("Data Ministério", value=str(u.get('data_ministerio', '')))

                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES E SINCRONIZAR"):
                            with st.spinner("Sincronizando..."):
                                # Atualiza a aba 'usuarios' (12 colunas)
                                dados_up = [
                                    ed_nome, u['email'], ed_senha, str(u.get('papel', 'CATEQUISTA')), 
                                    ", ".join(ed_turmas), ed_tel, str(ed_nasc),
                                    dt_ini, dt_bat, dt_euc, dt_cri, dt_min
                                ]
                                if atualizar_usuario(u['email'], dados_up):
                                    # Sincronização Reversa com aba 'turmas'
                                    planilha = conectar_google_sheets()
                                    aba_t = planilha.worksheet("turmas")
                                    for _, t_row in df_turmas.iterrows():
                                        t_nome = t_row['nome_turma']
                                        cats_na_turma = [c.strip() for c in str(t_row['catequista_responsavel']).split(',') if c.strip()]
                                        mudou = False
                                        if t_nome in ed_turmas:
                                            if ed_nome not in cats_na_turma: cats_na_turma.append(ed_nome); mudou = True
                                        else:
                                            if ed_nome in cats_na_turma: cats_na_turma.remove(ed_nome); mudou = True
                                            if u['nome'] in cats_na_turma: cats_na_turma.remove(u['nome']); mudou = True
                                        if mudou:
                                            cel_t = aba_t.find(str(t_row['id_turma']))
                                            if cel_t: aba_t.update_cell(cel_t.row, 5, ", ".join(cats_na_turma))
                                    st.success("✅ Perfil e Turmas sincronizados!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    with tab_novo:
        st.subheader("➕ Criar Novo Acesso para Equipe")
        with st.form("form_novo_cat_v13", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_nome = c1.text_input("Nome Completo").upper()
            n_email = c2.text_input("E-mail (Login)")
            
            c3, c4, c5 = st.columns(3)
            n_senha = c3.text_input("Senha Inicial", type="password")
            n_tel = c4.text_input("Telefone / WhatsApp")
            n_nasc = c5.date_input("Data de Nascimento", value=date(1980, 1, 1))
            
            n_papel = st.selectbox("Papel / Nível de Acesso", ["CATEQUISTA", "COORDENADOR", "ADMIN"])
            lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else []
            n_turmas = st.multiselect("Vincular às Turmas:", lista_t_nomes)
            
            if st.form_submit_button("🚀 CRIAR ACESSO E DEFINIR PERMISSÕES"):
                if n_nome and n_email and n_senha:
                    try:
                        planilha = conectar_google_sheets()
                        # Ordem das 12 colunas da aba 'usuarios'
                        novo_user = [n_nome, n_email, n_senha, n_papel, ", ".join(n_turmas), n_tel, str(n_nasc), "", "", "", "", ""]
                        planilha.worksheet("usuarios").append_row(novo_user)
                        
                        # Sincroniza a aba turmas para incluir o novo catequista
                        if n_turmas:
                            aba_t = planilha.worksheet("turmas")
                            for t_nome in n_turmas:
                                cel_t = aba_t.find(t_nome)
                                if cel_t:
                                    v_atual = aba_t.cell(cel_t.row, 5).value or ""
                                    aba_t.update_cell(cel_t.row, 5, f"{v_atual}, {n_nome}".strip(", "))
                        
                        st.success(f"✅ {n_nome} cadastrado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Erro ao salvar: {e}")
                else: st.warning("⚠️ Nome, E-mail e Senha são obrigatórios.")

    with tab_formacao:
        st.subheader("🎓 Registro de Formação Continuada")
        with st.form("form_nova_form_v13"):
            f_tema = st.text_input("Tema da Formação").upper()
            f_data = st.date_input("Data", value=date.today())
            f_formador = st.text_input("Formador").upper()
            dict_equipe = dict(zip(equipe_tecnica['nome'], equipe_tecnica['email']))
            participantes = st.multiselect("Catequistas Presentes:", list(dict_equipe.keys()))
            if st.form_submit_button("💾 REGISTRAR FORMAÇÃO"):
                if f_tema and participantes:
                    id_f = f"FOR-{int(time.time())}"
                    if salvar_formacao([id_f, f_tema, str(f_data), f_formador, "", ""]):
                        lista_p = [[id_f, dict_equipe[nome]] for nome in participantes]
                        if salvar_presenca_formacao(lista_p):
                            st.success("Formação registrada!"); st.cache_data.clear(); time.sleep(1); st.rerun()
# --- FIM DO BLOCO: GESTÃO DE CATEQUISTAS ---

# ==============================================================================
# PÁGINA: 👨‍👩‍👧‍👦 GESTÃO FAMILIAR (VERSÃO INTEGRAL COM TERMO DE AUTORIZAÇÃO)
# ==============================================================================
elif menu == "👨‍👩‍👧‍👦 Gestão Familiar":
    st.title("👨‍👩‍👧‍👦 Gestão Familiar e Igreja Doméstica")
    st.markdown("---")

# --- FUNÇÃO INTERNA: CARD DE CONTATO (VERSÃO SUPER-CLEAN DDD 73) ---
    def exibir_card_contato_pastoral(aluno_row):
        def limpar_whatsapp(tel):
            if not tel or str(tel).strip() in ["N/A", "", "None"]:
                return None
            
            # 1. Mantém apenas os números
            num = "".join(filter(str.isdigit, str(tel)))
            
            # 2. Remove o zero inicial se o catequista digitou (ex: 073...)
            if num.startswith("0"):
                num = num[1:]
            
            # 3. Lógica Inteligente de Prefixo:
            # Se o número começa com 55
            if num.startswith("55"):
                sobra = num[2:]
                # Se o que sobrou tem 10 ou 11 dígitos, já tem DDD. Retorna o número como está.
                if len(sobra) >= 10:
                    return num
                # Se o que sobrou tem 8 ou 9 dígitos, falta o DDD. Coloca o 73 de Itabuna.
                else:
                    return f"5573{sobra}"
            
            # Se o número NÃO começa com 55
            else:
                # Se tem 10 ou 11 dígitos, já tem DDD. Só adiciona o 55.
                if len(num) >= 10:
                    return f"55{num}"
                # Se tem 8 ou 9 dígitos, é número local. Adiciona 55 + 73.
                else:
                    return f"5573{num}"

        with st.container():
            st.markdown(f"""
                <div style='background-color:#f8f9f0; padding:15px; border-radius:10px; border-left:8px solid #417b99; margin-bottom:10px;'>
                    <h3 style='margin:0; color:#417b99;'>👤 {aluno_row['nome_completo']}</h3>
                    <p style='margin:0; color:#666;'><b>Turma:</b> {aluno_row['etapa']} | <b>Status:</b> {aluno_row['status']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([2, 2, 1.5])
            
            with c1:
                st.markdown("**👩‍🦱 MÃE:** " + str(aluno_row['nome_mae']))
                link_mae = limpar_whatsapp(aluno_row['tel_mae'])
                if link_mae:
                    st.markdown(f"""<a href="https://wa.me/{link_mae}" target="_blank"><button style="background-color:#25d366; color:white; border:none; padding:10px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📲 WhatsApp Mãe</button></a>""", unsafe_allow_html=True)
                else:
                    st.caption("⚠️ Sem telefone")

            with c2:
                st.markdown("**👨‍🦱 PAI:** " + str(aluno_row['nome_pai']))
                link_pai = limpar_whatsapp(aluno_row['tel_pai'])
                if link_pai:
                    st.markdown(f"""<a href="https://wa.me/{link_pai}" target="_blank"><button style="background-color:#128c7e; color:white; border:none; padding:10px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📲 WhatsApp Pai</button></a>""", unsafe_allow_html=True)
                else:
                    st.caption("⚠️ Sem telefone")

            with c3:
                if str(aluno_row['toma_medicamento_sn']).upper() != "NÃO":
                    st.error(f"💊 MEDICAMENTO: {aluno_row['toma_medicamento_sn']}")
                if str(aluno_row['tgo_sn']).upper() == "SIM":
                    st.warning("🧠 TGO / TEA")
            st.markdown("<br>", unsafe_allow_html=True)

    if eh_gestor:
        tab_censo, tab_agenda, tab_busca, tab_ia = st.tabs([
            "📊 Censo Familiar", "📞 Agenda de Emergência", "🔍 Localizar e Registrar Visita", "✨ Auditoria IA"
        ])

        with tab_censo:
            st.subheader("Realidade Sacramental e Social dos Pais")
            if not df_cat.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**💍 Situação Matrimonial dos Pais**")
                    st.bar_chart(df_cat['est_civil_pais'].value_counts())
                with c2:
                    st.markdown("**⛪ Sacramentos dos Pais**")
                    sac_series = df_cat['sac_pais'].str.split(', ').explode()
                    st.bar_chart(sac_series.value_counts())

        with tab_agenda:
            st.subheader("📞 Agenda Geral de Emergência")
            busca_geral = st.text_input("🔍 Digite o nome do catequizando:", key="busca_emerg_gestor").upper()
            if busca_geral:
                res = df_cat[df_cat['nome_completo'].str.contains(busca_geral, na=False)]
                for _, row in res.iterrows(): exibir_card_contato_pastoral(row)

        with tab_busca:
            st.subheader("🔍 Localizar Núcleo Familiar e Registrar Relato")
            busca_pais = st.text_input("Nome da Mãe ou Pai para localizar família:").upper()
            
            if busca_pais:
                fam = df_cat[(df_cat['nome_mae'].str.contains(busca_pais, na=False)) | (df_cat['nome_pai'].str.contains(busca_pais, na=False))]
                
                if not fam.empty:
                    dados_f = fam.iloc[0]
                    st.success(f"✅ Família Localizada: {dados_f['nome_mae']} & {dados_f['nome_pai']}")
                    
                    # --- RELATO PASTORAL (COLUNA AD / 30) ---
                    st.markdown("#### 📝 Relato de Visita e Necessidades da Família")
                    obs_atual = dados_f.get('obs_pastoral_familia', '')
                    if obs_atual == "N/A": obs_atual = ""
                    
                    novo_relato = st.text_area("Descreva aqui o que foi conversado ou as carências detectadas:", 
                                             value=obs_atual, height=150, key="txt_relato_familia")
                    
                    if st.button("💾 SALVAR ANOTAÇÕES NO HISTÓRICO"):
                        with st.spinner("Gravando relato..."):
                            sucesso = True
                            for _, filho in fam.iterrows():
                                lista_up = filho.tolist()
                                while len(lista_up) < 30: lista_up.append("N/A")
                                lista_up[29] = novo_relato # Coluna AD
                                if not atualizar_catequizando(filho['id_catequizando'], lista_up):
                                    sucesso = False
                            if sucesso:
                                st.success("✅ Relato salvo com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()

                    st.divider()
                    st.markdown("#### 👦 Filhos na Catequese")
                    filhos_pdf = []
                    for _, f in fam.iterrows():
                        st.write(f"· **{f['nome_completo']}** - Turma: `{f['etapa']}`")
                        filhos_pdf.append({'nome': f['nome_completo'], 'etapa': f['etapa'], 'status': f['status']})
                    
                    # --- SEÇÃO DE DOCUMENTOS (FICHA + TERMO DE SAÍDA) ---
                    st.divider()
                    st.markdown("#### 📄 Documentos para Impressão")
                    
                    # 1. Seleção de quem assina o termo
                    opcoes_resp = ["Mãe", "Pai", "Outro (Digitar Nome)"]
                    resp_selecionado = st.selectbox("Quem assina como responsável no Termo de Saída?", opcoes_resp, key="sel_resp_termo")
                    
                    nome_final_resp = ""
                    if resp_selecionado == "Mãe":
                        nome_final_resp = dados_f.get('nome_mae', '________________')
                    elif resp_selecionado == "Pai":
                        nome_final_resp = dados_f.get('nome_pai', '________________')
                    else:
                        nome_final_resp = st.text_input("Digite o nome do Responsável:", key="nome_manual_resp").upper()

                    col_doc_fam1, col_doc_fam2 = st.columns(2)
                    
                    with col_doc_fam1:
                        if st.button("📄 FICHA DE VISITAÇÃO (PDF)", use_container_width=True, key="btn_pdf_visita"):
                            dados_p = dados_f.to_dict()
                            dados_p['obs_pastoral_familia'] = novo_relato
                            st.session_state.pdf_fam_v = gerar_relatorio_familia_pdf(dados_p, filhos_pdf)
                        
                        if "pdf_fam_v" in st.session_state:
                            st.download_button("📥 BAIXAR FICHA", st.session_state.pdf_fam_v, f"Visita_{busca_pais}.pdf", use_container_width=True)

                    with col_doc_fam2:
                        if st.button("📜 TERMO DE AUTORIZAÇÃO DE SAÍDA", use_container_width=True, key="btn_pdf_termo_saida"):
                            if not nome_final_resp or nome_final_resp == "________________":
                                st.error("Por favor, identifique o nome do responsável.")
                            else:
                                with st.spinner("Gerando termo oficial..."):
                                    info_t_termo = df_turmas[df_turmas['nome_turma'] == dados_f['etapa']].iloc[0].to_dict() if not df_turmas.empty else {}
                                    # Passa o nome selecionado para a função
                                    st.session_state.pdf_termo_saida = gerar_termo_saida_pdf(dados_f.to_dict(), info_t_termo, nome_final_resp)
                        
                        if "pdf_termo_saida" in st.session_state:
                            st.download_button("📥 BAIXAR TERMO (PDF)", st.session_state.pdf_termo_saida, f"Termo_Saida_{dados_f['nome_completo'].replace(' ', '_')}.pdf", use_container_width=True)

        with tab_ia:
            if st.button("🚀 EXECUTAR DIAGNÓSTICO PASTORAL"):
                resumo = f"Civis: {df_cat['est_civil_pais'].value_counts().to_dict()}. Sacramentos: {df_cat['sac_pais'].value_counts().to_dict()}."
                st.info(analisar_saude_familiar_ia(resumo))

    else:
        # VISÃO CATEQUISTA
        st.subheader(f"📞 Agenda de Emergência - Turma: {turma_do_catequista}")
        meus_alunos = df_cat[df_cat['etapa'] == turma_do_catequista]
        if not meus_alunos.empty:
            for _, row in meus_alunos.iterrows(): exibir_card_contato_pastoral(row)
        else:
            st.info("Nenhum catequizando vinculado a esta turma.")
# ==============================================================================

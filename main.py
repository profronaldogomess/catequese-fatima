# ==============================================================================
# ARQUIVO: main.py
# VERSÃO: 4.0.0 - UI/UX MODERNIZADA, MOBILE-FIRST E BLINDAGEM DE DADOS
# ==============================================================================
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import datetime as dt_module
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
    return stx.CookieManager(key="catequese_fatima_cookies_v4")

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

# Banner de Homologação
if IS_HOMOLOGACAO:
    st.warning("🧪 **AMBIENTE DE TESTES (HOMOLOGAÇÃO)** - As alterações feitas aqui podem não ser definitivas.")

# Lógica de Bloqueio de Manutenção
if status_sistema == "MANUTENCAO" and not is_admin:
    from utils import exibir_tela_manutencao
    exibir_tela_manutencao()
    
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

# --- 4. INJEÇÃO DE CSS (ESTILIZAÇÃO MOBILE-FIRST) ---
cor_sidebar = "#417b99" if not IS_HOMOLOGACAO else "#5d4037"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; color: #333333; }}
    .stTextInput input, .stDateInput input, .stNumberInput input, .stTextArea textarea {{
        background-color: #f0f2f6 !important; color: #000000 !important; border: 1px solid #ccc; border-radius: 8px;
    }}
    div[data-baseweb="select"] > div {{ background-color: #f0f2f6 !important; color: #000000 !important; border-radius: 8px; }}
    input, textarea, select {{ color: black !important; -webkit-text-fill-color: black !important; }}
    [data-testid="stSidebar"] {{ background-color: {cor_sidebar}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    h1, h2, h3, h4 {{ color: {cor_sidebar} !important; font-family: 'Helvetica', sans-serif; }}
    label, .stMarkdown p {{ color: {cor_sidebar} !important; font-weight: 600; }}
    p, li {{ color: #333333; }}
    div.stButton > button {{
        background-color: #e03d11; color: white !important; border: none;
        font-weight: bold; border-radius: 8px; padding: 10px 20px; transition: 0.3s;
    }}
    div.stButton > button:hover {{ background-color: #c0320d; color: white !important; transform: scale(1.02); }}
    [data-testid="stMetricValue"] {{ color: #e03d11 !important; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 5rem; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. IMPORTAÇÕES DE MOTORES INTERNOS ---
from database import (
    ler_aba, salvar_lote_catequizandos, atualizar_catequizando, 
    conectar_google_sheets, atualizar_turma, salvar_presencas, 
    salvar_encontro, salvar_tema_cronograma, 
    buscar_encontro_por_data, atualizar_usuario, salvar_formacao, 
    salvar_presenca_formacao, mover_catequizandos_em_massa, excluir_turma,
    registrar_evento_sacramento_completo, salvar_reuniao_pais, salvar_presenca_reuniao_pais, atualizar_reuniao_pais
)
from utils import (
    calcular_idade, sugerir_etapa, eh_aniversariante_da_semana, 
    obter_aniversariantes_mes, converter_para_data, verificar_status_ministerial, 
    obter_aniversariantes_hoje, obter_aniversariantes_mes_unificado, 
    gerar_ficha_cadastral_catequizando, gerar_ficha_catequista_pdf, 
    gerar_fichas_turma_completa, formatar_data_br, gerar_relatorio_familia_pdf,
    gerar_fichas_catequistas_lote, gerar_card_aniversario, gerar_termo_saida_pdf, 
    gerar_auditoria_lote_completa, gerar_fichas_paroquia_total, gerar_relatorio_evasao_pdf,
    processar_alertas_evasao, gerar_lista_secretaria_pdf, gerar_declaracao_pastoral_pdf,
    gerar_lista_assinatura_reuniao_pdf, gerar_relatorio_diocesano_pdf, 
    gerar_relatorio_pastoral_pdf, gerar_relatorio_local_turma_pdf,
    gerar_relatorio_sacramentos_tecnico_pdf
)
from ai_engine import (
    gerar_analise_pastoral, gerar_mensagem_whatsapp, 
    analisar_turma_local, gerar_relatorio_sacramentos_ia, analisar_saude_familiar_ia, 
    gerar_mensagem_reacolhida_ia, gerar_mensagem_cobranca_doc_ia, gerar_mensagem_atualizacao_cadastral_ia
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
if not st.session_state.logado and not st.session_state.get('logout_em_curso', False):
    auth_cookie = cookie_manager.get("fatima_auth_v4")
    if auth_cookie:
        user = verificar_login(auth_cookie['email'], auth_cookie['senha'])
        if user:
            new_sid = str(uuid.uuid4())
            if atualizar_session_id(user['email'], new_sid):
                st.session_state.logado = True
                st.session_state.usuario = user
                st.session_state.session_id = new_sid
                st.rerun()

if st.session_state.logado and st.session_state.usuario:
    sid_no_db = obter_session_id_db(st.session_state.usuario['email'])
    if sid_no_db and sid_no_db != st.session_state.session_id:
        st.session_state.sessao_derrubada = True
        st.session_state.logado = False
        try: cookie_manager.delete("fatima_auth_v4")
        except: pass

if st.session_state.get('sessao_derrubada'):
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error("🚨 **ACESSO ENCERRADO: CONEXÃO DUPLICADA**")
    st.markdown(f"""
        <div style='background-color:#fff5f5; padding:20px; border-radius:10px; border:2px solid #e03d11;'>
            <h3 style='color:#e03d11; margin-top:0;'>Sessão Encerrada</h3>
            <p style='color:#333;'>Identificamos que sua conta foi conectada em <b>outro dispositivo ou navegador</b>.</p>
            <p style='color:#333;'>Por segurança, esta conexão foi finalizada.</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("VOLTAR PARA A TELA DE LOGIN", use_container_width=True):
        st.session_state.sessao_derrubada = False
        st.session_state.usuario = None
        st.session_state.session_id = None
        st.rerun()
    st.stop()

if not st.session_state.logado:
    if st.session_state.get('logout_em_curso'):
        st.session_state.logout_em_curso = False
        
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        mostrar_logo_login()
        st.markdown(f"<h2 style='text-align: center; color: {cor_sidebar};'>Acesso Restrito</h2>", unsafe_allow_html=True)
        email_login = st.text_input("E-mail")
        senha_login = st.text_input("Senha", type="password")
        lembrar = st.checkbox("Manter conectado por 30 dias")
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            user = verificar_login(email_login, senha_login)
            if user:
                new_sid = str(uuid.uuid4())
                if atualizar_session_id(email_login, new_sid):
                    st.session_state.logado = True
                    st.session_state.usuario = user
                    st.session_state.session_id = new_sid
                    if lembrar:
                        cookie_manager.set("fatima_auth_v4", {"email": email_login, "senha": senha_login}, expires_at=dt_module.datetime.now() + timedelta(days=30))
                    st.rerun()
                else: st.error("Erro ao validar sessão única.")
            else: st.error("🚫 Acesso negado.")
    st.stop()

# --- 8. CARREGAMENTO GLOBAL DE DADOS ---
df_cat = ler_aba("catequizandos")
df_turmas = ler_aba("turmas")
df_pres = ler_aba("presencas")
df_usuarios = ler_aba("usuarios") 
df_sac_eventos = ler_aba("sacramentos_eventos")
df_pres_reuniao = ler_aba("presenca_reuniao") 

equipe_tecnica = df_usuarios[df_usuarios['papel'] != 'ADMIN'] if not df_usuarios.empty else pd.DataFrame()

# --- 9. BARRA LATERAL E DEFINIÇÃO DE MENU ---
mostrar_logo_sidebar() 
st.sidebar.markdown(f"📅 **{date.today().strftime('%d/%m/%Y')}**")

if st.session_state.logado and st.session_state.usuario:
    nome_exibicao = st.session_state.usuario.get('nome', 'Usuário')
    st.sidebar.success(f"Bem-vindo(a),\n**{nome_exibicao}**")

if IS_HOMOLOGACAO: st.sidebar.info("🧪 MODO HOMOLOGAÇÃO")
if status_sistema == "MANUTENCAO": st.sidebar.warning("⚠️ MANUTENÇÃO ATIVA")

st.sidebar.divider()

if st.sidebar.button("🔄 Atualizar Dados", key="btn_refresh_global"):
    st.cache_data.clear(); st.toast("Dados atualizados!", icon="✅"); time.sleep(1); st.rerun()

if st.sidebar.button("🚪 Sair / Logoff", key="btn_logout_global"):
    st.session_state.logout_em_curso = True
    cookie_manager.delete("fatima_auth_v4")
    st.session_state.logado = False
    st.session_state.session_id = None
    st.session_state.usuario = None
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

# ==============================================================================
# PÁGINA 1: DASHBOARD DE INTELIGÊNCIA PASTORAL
# ==============================================================================
if menu == "🏠 Início / Dashboard":
    st.title("📊 Radar de Gestão Pastoral")

    st.markdown("### 🎂 Mural de Celebração")
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    aniversariantes_agora = obter_aniversariantes_hoje(df_cat, df_usuarios)
    df_niver_mes_geral = obter_aniversariantes_mes_unificado(df_cat, df_usuarios)

    if aniversariantes_agora:
        for item in aniversariantes_agora:
            partes = item.split(" | ")
            papel = partes[1]
            nome_completo = partes[2]
            icone = "🛡️" if papel == "CATEQUISTA" else "😇"
            
            st.balloons()
            st.success(f"🌟 **HOJE É ANIVERSÁRIO!** {icone} {papel}: **{nome_completo}**")
            
            if st.button(f"🎨 Gerar Card de Parabéns para {nome_completo.split()[0]}", key=f"btn_hoje_dash_{nome_completo}"):
                card_img = gerar_card_aniversario(item, tipo="DIA")
                if card_img:
                    st.image(card_img, use_container_width=True)
                    st.download_button("📥 Baixar Card", card_img, f"Parabens_Hoje_{nome_completo}.png", "image/png")
    
    with st.expander("📅 Ver todos os aniversariantes do mês (Paróquia)", expanded=not aniversariantes_agora):
        if not df_niver_mes_geral.empty:
            if st.button("🖼️ GERAR CARD COLETIVO DO MÊS (GERAL)", use_container_width=True):
                lista_para_card = [f"{int(row['dia'])} | {row['tipo']} | {row['nome']}" for _, row in df_niver_mes_geral.iterrows()]
                card_coletivo = gerar_card_aniversario(lista_para_card, tipo="MES")
                if card_coletivo:
                    st.image(card_coletivo, caption="Aniversariantes do Mês - Paróquia de Fátima")
                    st.download_button("📥 Baixar Card Coletivo", card_coletivo, "Aniversariantes_do_Mes_Geral.png", "image/png")
            
            st.write("")
            st.markdown("---")
            
            cols_dash = st.columns(4)
            for i, (_, niver) in enumerate(df_niver_mes_geral.iterrows()):
                with cols_dash[i % 4]:
                    icone_m = "🛡️" if niver['tipo'] == 'CATEQUISTA' else "🎁"
                    st.markdown(f"""
                        <div style='background-color:#f0f2f6; padding:8px; border-radius:10px; border-left:4px solid #417b99; margin-bottom:5px; min-height:80px;'>
                            <small style='color:#666;'>Dia {int(niver['dia'])}</small><br>
                            <b style='font-size:13px;'>{icone_m} {niver['nome'].split()[0]} {niver['nome'].split()[-1] if len(niver['nome'].split()) > 1 else ''}</b>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🎨 Card", key=f"btn_indiv_dash_{i}"):
                        dados_envio = f"{int(niver['dia'])} | {niver['tipo']} | {niver['nome']}"
                        card_indiv = gerar_card_aniversario(dados_envio, tipo="DIA")
                        if card_indiv:
                            st.image(card_indiv, use_container_width=True)
                            st.download_button(f"📥 Baixar", card_indiv, f"Niver_{niver['nome']}.png", "image/png", key=f"dl_dash_{i}")
        else:
            st.write("Nenhum aniversariante este mês nos registros.")

    st.divider()

    st.subheader("🚩 Radar de Atenção Imediata")
    r1, r2, r3, r4 = st.columns(4)

    df_ativos = df_cat[df_cat['status'] == 'ATIVO'] if not df_cat.empty else pd.DataFrame()
    
    pend_doc = len(df_ativos[~df_ativos['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])])
    r1.metric("📄 Doc. Pendente", pend_doc, delta="Ação Necessária", delta_color="inverse")

    risco_c, _ = processar_alertas_evasao(df_pres)
    r2.metric("🚩 Risco de Evasão", len(risco_c), delta="Visita Urgente", delta_color="inverse")

    sem_batismo = len(df_ativos[df_ativos['batizado_sn'] == 'NÃO'])
    r3.metric("🕊️ Sem Batismo", sem_batismo, delta="Regularizar", delta_color="inverse")

    fam_reg = len(df_cat[df_cat['est_civil_pais'].isin(['CONVIVEM', 'CASADO(A) CIVIL', 'DIVORCIADO(A)'])])
    r4.metric("🏠 Famílias Irregulares", fam_reg, delta="Pastoral Familiar", delta_color="inverse")

    st.divider()

    tab_censo, tab_equipe, tab_evasao = st.tabs(["📈 Censo Sacramental", "👥 Saúde da Equipe", "🚩 Cuidado e Evasão"])

    with tab_censo:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### 🕊️ Cobertura de Batismo (Ativos)")
            if not df_ativos.empty:
                bat_sim = len(df_ativos[df_ativos['batizado_sn'] == 'SIM'])
                bat_nao = len(df_ativos[df_ativos['batizado_sn'] == 'NÃO'])
                fig_bat = px.pie(values=[bat_sim, bat_nao], names=['Batizados', 'Não Batizados'], 
                                 color_discrete_sequence=['#417b99', '#e03d11'], hole=0.5)
                fig_bat.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                st.plotly_chart(fig_bat, use_container_width=True)
            else: st.info("Sem dados ativos.")

        with c2:
            st.markdown("#### 🍞 1ª Eucaristia (Ativos)")
            if not df_ativos.empty:
                euc_sim = df_ativos['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False, case=False).sum()
                euc_nao = len(df_ativos) - euc_sim
                fig_euc = px.pie(values=[euc_sim, euc_nao], names=['Já Receberam', 'Em Preparação'], 
                                 color_discrete_sequence=['#2e7d32', '#ffa000'], hole=0.5)
                fig_euc.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                st.plotly_chart(fig_euc, use_container_width=True)
            else: st.info("Sem dados ativos.")

        st.markdown("#### 📊 Frequência por Turma (%)")
        if not df_pres.empty:
            df_pres['status_num'] = df_pres['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
            freq_turma = df_pres.groupby('id_turma')['status_num'].mean() * 100
            freq_turma = freq_turma.reset_index().rename(columns={'status_num': 'Freq %', 'id_turma': 'Turma'})
            fig_freq = px.bar(freq_turma, x='Turma', y='Freq %', color='Freq %', color_continuous_scale='RdYlGn')
            fig_freq.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig_freq, use_container_width=True)

    with tab_equipe:
        st.markdown("#### 🛡️ Maturidade Ministerial da Equipe")
        if not equipe_tecnica.empty:
            col_e1, col_e2 = st.columns(2)
            status_list = []
            for _, row in equipe_tecnica.iterrows():
                status, _ = verificar_status_ministerial(row.get('data_inicio_catequese', ''), row.get('data_batismo', ''), 
                                                        row.get('data_eucaristia', ''), row.get('data_crisma', ''), 
                                                        row.get('data_ministerio', ''))
                status_list.append(status)
            
            df_maturidade = pd.DataFrame({"Status": status_list})
            fig_mat = px.bar(df_maturidade['Status'].value_counts().reset_index(), x='Status', y='count', 
                             color='Status', color_discrete_map={'MINISTRO': '#2e7d32', 'APTO': '#417b99', 'EM_CAMINHADA': '#ffa000'})
            col_e1.plotly_chart(fig_mat, use_container_width=True)
            
            with col_e2:
                st.write("**Resumo da Equipe:**")
                st.write(f"✅ Ministros: {status_list.count('MINISTRO')}")
                st.write(f"🎓 Aptos: {status_list.count('APTO')}")
                st.write(f"⏳ Em Formação: {status_list.count('EM_CAMINHADA')}")
                if st.button("🗂️ Gerar Dossiê da Equipe", use_container_width=True):
                    st.session_state.pdf_equipe = gerar_fichas_catequistas_lote(equipe_tecnica, ler_aba("presenca_formacao"), ler_aba("formacoes"))
                if "pdf_equipe" in st.session_state:
                    st.download_button("📥 Baixar Dossiê", st.session_state.pdf_equipe, "Equipe.pdf", use_container_width=True)

    with tab_evasao:
        st.subheader("🚩 Diagnóstico de Interrupção de Itinerário")
        df_fora = df_cat[df_cat['status'].isin(['DESISTENTE', 'TRANSFERIDO', 'INATIVO'])]
        if df_fora.empty:
            st.success("Glória a Deus! Não há registros de evasão no momento.")
        else:
            st.dataframe(df_fora[['nome_completo', 'status', 'etapa', 'contato_principal']], use_container_width=True, hide_index=True)
            if st.button("📄 Gerar Relatório de Evasão (PDF)", use_container_width=True):
                st.session_state.pdf_evasao = gerar_relatorio_evasao_pdf(df_fora)
            if "pdf_evasao" in st.session_state:
                st.download_button("📥 Baixar Diagnóstico", st.session_state.pdf_evasao, "Evasao.pdf", use_container_width=True)

    st.divider()

    st.subheader("🏛️ Estação de Impressão e Auditoria")
    col_doc_sec, col_doc_past, col_doc_lote = st.columns(3)
    
    with col_doc_sec:
        st.markdown("**🏛️ Secretaria**")
        if st.button("🏛️ Relatório Diocesano", use_container_width=True):
            st.session_state.pdf_diocesano = gerar_relatorio_diocesano_pdf(df_turmas, df_cat, df_usuarios)
        if "pdf_diocesano" in st.session_state:
            st.download_button("📥 Baixar Diocesano", st.session_state.pdf_diocesano, "Diocesano.pdf", use_container_width=True)

    with col_doc_past:
        st.markdown("**📋 Pastoral**")
        if st.button("📋 Relatório Pastoral", use_container_width=True):
            st.session_state.pdf_pastoral = gerar_relatorio_pastoral_pdf(df_turmas, df_cat, df_pres, df_pres_reuniao)
        if "pdf_pastoral" in st.session_state:
            st.download_button("📥 Baixar Pastoral", st.session_state.pdf_pastoral, "Pastoral.pdf", use_container_width=True)

    with col_doc_lote:
        st.markdown("**📦 Processamento em Lote**")
        if st.button("🗂️ Todas as Fichas (Lote)", use_container_width=True):
            st.session_state.pdf_lote_f = gerar_fichas_paroquia_total(df_cat)
        if "pdf_lote_f" in st.session_state:
            st.download_button("📥 Baixar Fichas", st.session_state.pdf_lote_f, "Fichas_Lote.pdf", use_container_width=True)

# ==============================================================================
# PÁGINA: 📚 MINHA TURMA (COCKPIT DO CATEQUISTA)
# ==============================================================================
elif menu == "📚 Minha Turma":
    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    if eh_gestor or vinculo_raw == "TODAS":
        turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
    else:
        turmas_permitidas = [t.strip() for t in vinculo_raw.split(',') if t.strip()]

    if not turmas_permitidas:
        st.warning("⚠️ Nenhuma turma vinculada ao seu perfil."); st.stop()

    if len(turmas_permitidas) > 1 or eh_gestor:
        turma_ativa = st.selectbox("🔍 Selecione a Turma para Visualizar:", turmas_permitidas, key="sel_t_minha")
    else:
        turma_ativa = turmas_permitidas[0]

    st.title(f"📚 Painel: {turma_ativa}")

    meus_alunos = df_cat[df_cat['etapa'] == turma_ativa] if not df_cat.empty else pd.DataFrame()
    minhas_pres = df_pres[df_pres['id_turma'] == turma_ativa] if not df_pres.empty else pd.DataFrame()
    df_cron_t = ler_aba("cronograma")
    df_enc_t = ler_aba("encontros")
    df_reu_t = ler_aba("presenca_reuniao")

    st.markdown("### 🎂 Mural de Celebração")
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    df_niver_t = obter_aniversariantes_mes(meus_alunos)
    
    niver_hoje = []
    if not meus_alunos.empty:
        for _, r in meus_alunos.iterrows():
            d_nasc = formatar_data_br(r['data_nascimento'])
            if d_nasc != "N/A":
                try:
                    dt_n = dt_module.datetime.strptime(d_nasc, "%d/%m/%Y")
                    if dt_n.day == hoje.day and dt_n.month == hoje.month:
                        niver_hoje.append(r['nome_completo'])
                except: pass

    if niver_hoje:
        for nome_n in niver_hoje:
            st.balloons()
            st.success(f"🌟 **HOJE É ANIVERSÁRIO DE: {nome_n}**")
            if st.button(f"🎨 Gerar Card de Parabéns para {nome_n.split()[0]}", key=f"btn_niver_hoje_{nome_n}"):
                card_img = gerar_card_aniversario(f"{hoje.day} | CATEQUIZANDO | {nome_n}", tipo="DIA")
                if card_img:
                    st.image(card_img, use_container_width=True)
                    st.download_button("📥 Baixar Card", card_img, f"Parabens_{nome_n}.png", "image/png")
    
    with st.expander("📅 Ver todos os aniversariantes do mês", expanded=not niver_hoje):
        if not df_niver_t.empty:
            if st.button("🖼️ GERAR CARD COLETIVO DA TURMA", use_container_width=True):
                lista_card = [f"{int(row['dia'])} | CATEQUIZANDO | {row['nome']}" for _, row in df_niver_t.iterrows()]
                card_col = gerar_card_aniversario(lista_card, tipo="MES")
                if card_col:
                    st.image(card_col, use_container_width=True)
                    st.download_button("📥 Baixar Card Coletivo", card_col, "Aniversariantes_Mes_Turma.png", "image/png")
            
            st.write("")
            st.markdown("---")
            
            cols_n = st.columns(2) 
            for i, (_, niver) in enumerate(df_niver_t.iterrows()):
                with cols_n[i % 2]:
                    st.markdown(f"""
                        <div style='background-color:#f0f2f6; padding:10px; border-radius:10px; border-left:5px solid #417b99; margin-bottom:5px;'>
                            <b style='color:#417b99;'>Dia {int(niver['dia'])}</b> - {niver['nome']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🎨 Gerar Card Individual", key=f"btn_indiv_t_{i}"):
                        card_indiv = gerar_card_aniversario(f"{int(niver['dia'])} | CATEQUIZANDO | {niver['nome']}", tipo="DIA")
                        if card_indiv:
                            st.image(card_indiv, use_container_width=True)
                            st.download_button(f"📥 Baixar Card de {niver['nome'].split()[0]}", card_indiv, f"Niver_{niver['nome']}.png", "image/png", key=f"dl_indiv_t_{i}")
                    st.write("")
        else:
            st.write("Nenhum aniversariante este mês nesta turma.")

    st.divider()

    c1, c2, c3 = st.columns(3)
    total_planejado = len(df_cron_t[df_cron_t['etapa'] == turma_ativa]) if not df_cron_t.empty else 0
    total_feito = len(df_enc_t[df_enc_t['turma'] == turma_ativa]) if not df_enc_t.empty else 0
    progresso = (total_feito / (total_feito + total_planejado)) if (total_feito + total_planejado) > 0 else 0
    c1.metric("Caminhada da Fé", f"{total_feito} temas", f"{progresso*100:.0f}% concluído")

    if not minhas_pres.empty:
        freq = (minhas_pres['status'] == 'PRESENTE').mean() * 100
        c2.metric("Frequência Média", f"{freq:.1f}%")
    else:
        c2.metric("Frequência Média", "0%")

    if not df_reu_t.empty and not meus_alunos.empty:
        pais_presentes = df_reu_t[df_reu_t.iloc[:, 3] == turma_ativa].iloc[:, 1].nunique()
        perc_pais = (pais_presentes / len(meus_alunos)) * 100
        c3.metric("Engajamento Pais", f"{perc_pais:.0f}%")
    else:
        c3.metric("Engajamento Pais", "0%")

    st.divider()

    st.subheader("🚩 Radar de Atenção")
    risco_c, atencao_p = processar_alertas_evasao(minhas_pres)
    
    if risco_c:
        with st.expander(f"🔴 {len(risco_c)} em Risco Crítico (3+ faltas)"):
            for r in risco_c: st.write(f"• {r}")
    
    df_pend_doc = meus_alunos[~meus_alunos['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])]
    if not df_pend_doc.empty:
        with st.expander(f"⚠️ {len(df_pend_doc)} com Documentos Pendentes"):
            for n in df_pend_doc['nome_completo'].tolist(): st.write(f"• {n}")
    
    df_sem_batismo = meus_alunos[meus_alunos['batizado_sn'] == 'NÃO']
    if not df_sem_batismo.empty:
        with st.expander(f"🕊️ {len(df_sem_batismo)} sem registro de Batismo"):
            for n in df_sem_batismo['nome_completo'].tolist(): st.write(f"• {n}")

    if not risco_c and df_pend_doc.empty and df_sem_batismo.empty:
        st.success("✨ Turma em caminhada estável. Nenhum alerta crítico.")

    st.divider()

    st.subheader("👥 Consulta Individual")
    lista_nomes = sorted(meus_alunos['nome_completo'].tolist())
    nome_sel = st.selectbox("🔍 Selecione um catequizando para ver detalhes:", [""] + lista_nomes, key="busca_indiv_t", help="Busque pelo nome para ver o dossiê rápido.")

    if nome_sel:
        row = meus_alunos[meus_alunos['nome_completo'] == nome_sel].iloc[0]
        bat = "💧" if row['batizado_sn'] == "SIM" else "⚪"
        euc = "🍞" if "EUCARISTIA" in str(row['sacramentos_ja_feitos']).upper() else "⚪"
        cri = "🔥" if "CRISMA" in str(row['sacramentos_ja_feitos']).upper() else "⚪"
        tem_reu = "👪 Ativos" if not df_reu_t.empty and row['id_catequizando'] in df_reu_t.iloc[:, 1].values else "👪 Ausentes"
        
        st.markdown(f"""
            <div style='background-color:#ffffff; padding:20px; border-radius:15px; border-left:10px solid #417b99; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='margin:0; color:#417b99;'>{row['nome_completo']}</h3>
                <p style='margin:5px 0; color:#666;'>{bat} Batismo | {euc} Eucaristia | {cri} Crisma</p>
                <p style='margin:0; font-size:14px;'><b>Situação Familiar:</b> {tem_reu}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📋 Dossiê Rápido")
        idade_c = calcular_idade(row['data_nascimento'])
        c_d1, c_d2 = st.columns(2)
        c_d1.write(f"🎂 **Idade:** {idade_c} anos")
        c_d1.write(f"🏥 **Saúde:** {row.get('toma_medicamento_sn', 'NÃO')}")
        c_d2.write(f"📄 **Docs:** {row.get('doc_em_falta', 'OK')}")
        
        st.info(f"📝 **Última Obs. Pastoral:**\n{row.get('obs_pastoral_familia', 'Sem registros.')}")
        
        num_limpo = "".join(filter(str.isdigit, str(row['contato_principal'])))
        if num_limpo:
            st.markdown(f'''<a href="https://wa.me/5573{num_limpo[-9:]}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; text-align:center; padding:12px; border-radius:8px; font-weight:bold;">📲 Falar com Responsável</div></a>''', unsafe_allow_html=True)
        
        # --- NOVO: EXTRATO DE CAMINHADA ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📜 Ver Extrato de Caminhada (Presenças e Temas)"):
            pres_aluno = minhas_pres[minhas_pres['id_catequizando'] == row['id_catequizando']].copy()
            if not pres_aluno.empty:
                pres_aluno['data_dt'] = pd.to_datetime(pres_aluno['data_encontro'], errors='coerce')
                pres_aluno = pres_aluno.sort_values('data_dt', ascending=False)
                
                for _, p in pres_aluno.iterrows():
                    icone_p = "✅" if p['status'] == "PRESENTE" else "❌"
                    cor_p = "#2e7d32" if p['status'] == "PRESENTE" else "#e03d11"
                    data_f = formatar_data_br(p['data_encontro'])
                    tema_f = p.get('tema_do_dia', 'Tema não registrado')
                    st.markdown(f"<div style='padding:5px; border-bottom:1px solid #eee;'><span style='color:{cor_p};'>{icone_p}</span> <b>{data_f}</b> | {tema_f} <i>({p['status']})</i></div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum registro de presença/falta para este catequizando.")

    else:
        st.info("👆 Use a busca acima para ver a ficha de um catequizando específico.")

    st.divider()

    st.subheader("🎯 Itinerário")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.info("**Último Tema Dado:**")
        if not df_enc_t.empty:
            ultimo = df_enc_t[df_enc_t['turma'] == turma_ativa].sort_values('data', ascending=False)
            if not ultimo.empty: st.write(ultimo.iloc[0]['tema'])
            else: st.write("Nenhum registro.")
    with col_p2:
        st.success("**Próximo Tema Planejado:**")
        if not df_cron_t.empty:
            proximo = df_cron_t[(df_cron_t['etapa'] == turma_ativa) & (df_cron_t.get('status', '') != 'REALIZADO')]
            if not proximo.empty: st.write(proximo.iloc[0]['titulo_tema'])
            else: st.write("Cronograma em dia!")

# ==============================================================================
# PÁGINA: 📖 DIÁRIO DE ENCONTROS
# ==============================================================================
elif menu == "📖 Diário de Encontros":
    st.title("📖 Central de Itinerário e Encontros")
    
    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    if eh_gestor or vinculo_raw == "TODAS":
        turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
    else:
        turmas_permitidas = [t.strip() for t in vinculo_raw.split(',') if t.strip()]

    if not turmas_permitidas:
        st.error("⚠️ Nenhuma turma vinculada."); st.stop()

    turma_focal = st.selectbox("🔍 Selecione a Turma para Gerenciar:", turmas_permitidas)

    df_cron_p = ler_aba("cronograma")
    if not df_cron_p.empty:
        cron_turma = df_cron_p[df_cron_p['etapa'] == turma_focal]
        if not cron_turma.empty:
            total_temas = len(cron_turma)
            realizados = len(cron_turma[cron_turma['status'] == 'REALIZADO']) if 'status' in cron_turma.columns else 0
            progresso = realizados / total_temas if total_temas > 0 else 0
            st.write(f"**Progresso do Itinerário: {realizados} de {total_temas} temas concluídos**")
            st.progress(progresso)

    df_pres_local = ler_aba("presencas")
    df_enc_local = ler_aba("encontros")
    
    if not df_pres_local.empty:
        chamadas_turma = df_pres_local[df_pres_local['id_turma'] == turma_focal]['data_encontro'].unique().tolist()
        temas_turma = df_enc_local[df_enc_local['turma'] == turma_focal]['data'].unique().tolist() if not df_enc_local.empty else []
        pendencias = [d for d in chamadas_turma if d not in temas_turma]
        
        if pendencias:
            pendencias.sort()
            st.warning(f"⚠️ **Atenção:** Identificamos {len(pendencias)} encontro(s) com chamada realizada, mas sem tema registrado.")
            for p_data in pendencias:
                data_br = formatar_data_br(p_data)
                with st.expander(f"📝 Registrar tema pendente para o dia {data_br}"):
                    with st.form(f"form_pendencia_{p_data}"):
                        t_pend = st.text_input("Título do Tema Ministrado").upper()
                        o_pend = st.text_area("Observações Pastorais")
                        if st.form_submit_button(f"💾 SALVAR REGISTRO DE {data_br}"):
                            if t_pend:
                                if salvar_encontro([str(p_data), turma_focal, t_pend, st.session_state.usuario['nome'], o_pend]):
                                    st.success("Registrado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    st.divider()

    col_plan, col_reg = st.columns([1, 1])

    with col_plan:
        st.subheader("📅 Planejar Próximos Temas")
        with st.form("form_plan_diario", clear_on_submit=True):
            novo_tema = st.text_input("Título do Tema", help="Ex: Encontro 01 - Deus nos ama").upper()
            detalhes_tema = st.text_area("Objetivo (Opcional)", height=100)
            if st.form_submit_button("📌 ADICIONAR AO CRONOGRAMA"):
                if novo_tema:
                    if salvar_tema_cronograma([f"PLAN-{int(time.time())}", turma_focal, novo_tema, detalhes_tema, "PENDENTE"]):
                        st.success("Planejado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    with col_reg:
        st.subheader("✅ Registrar Encontro de Hoje")
        temas_sugeridos = [""]
        if not df_cron_p.empty:
            if 'status' in df_cron_p.columns:
                temas_sugeridos += df_cron_p[(df_cron_p['etapa'] == turma_focal) & (df_cron_p['status'] != 'REALIZADO')]['titulo_tema'].tolist()
            else:
                temas_sugeridos += df_cron_p[df_cron_p['etapa'] == turma_focal]['titulo_tema'].tolist()

        with st.form("form_reg_diario", clear_on_submit=True):
            data_e = st.date_input("Data do Encontro", date.today(), format="DD/MM/YYYY")
            tema_selecionado = st.selectbox("Selecionar do Cronograma:", temas_sugeridos)
            tema_manual = st.text_input("Ou digite o Tema:", value=tema_selecionado).upper()
            obs_e = st.text_area("Observações", height=68, help="Anotações sobre o comportamento da turma ou avisos dados.")
            
            if st.form_submit_button("💾 SALVAR NO DIÁRIO"):
                if tema_manual:
                    if salvar_encontro([str(data_e), turma_focal, tema_manual, st.session_state.usuario['nome'], obs_e]):
                        from database import marcar_tema_realizado_cronograma
                        marcar_tema_realizado_cronograma(turma_sel=turma_focal, tema=tema_manual)
                        st.success("Encontro registrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    st.divider()
    st.subheader(f"📜 Linha do Tempo: {turma_focal}")
    
    if not df_enc_local.empty:
        hist_turma = df_enc_local[df_enc_local['turma'] == turma_focal].sort_values(by='data', ascending=False)
        busca_h = st.text_input("🔍 Pesquisar tema no histórico:").upper()
        if busca_h: hist_turma = hist_turma[hist_turma['tema'].str.contains(busca_h, na=False)]

        for _, row in hist_turma.iterrows():
            data_val = row['data']
            data_br_h = formatar_data_br(data_val)
            
            with st.expander(f"📅 {data_br_h} - {row['tema']}"):
                st.write(f"**Catequista:** {row['catequista']}")
                obs_val = row.get('obs', row.get('observações', row.get('observacoes', 'Sem relato')))
                st.write(f"**Relato:** {obs_val}")
                
                dias_p = (date.today() - converter_para_data(data_val)).days
                if eh_gestor or dias_p <= 7:
                    if st.button(f"✏️ Editar", key=f"ed_{data_val}_{turma_focal}"):
                        st.session_state[f"edit_{data_val}"] = True
                    
                    if st.session_state.get(f"edit_{data_val}", False):
                        with st.form(f"f_ed_{data_val}_{turma_focal}"):
                            nt = st.text_input("Tema", value=row['tema']).upper()
                            no = st.text_area("Relato", value=obs_val)
                            if st.form_submit_button("💾 SALVAR"):
                                from database import atualizar_encontro_existente
                                if atualizar_encontro_existente(data_val, turma_focal, [str(data_val), turma_focal, nt, row['catequista'], no]):
                                    st.success("Atualizado!"); del st.session_state[f"edit_{data_val}"]
                                    st.cache_data.clear(); time.sleep(1); st.rerun()
    else:
        st.info("Nenhum encontro registrado ainda.")

# ==================================================================================
# PÁGINA: 📝 CADASTRAR CATEQUIZANDO (COM TOOLTIPS E AJUDA)
# ==================================================================================
elif menu == "📝 Cadastrar Catequizando":
    st.title("📝 Cadastro de Catequizandos")
    
    with st.expander("💡 GUIA DE PREENCHIMENTO (LEIA ANTES DE COMEÇAR)", expanded=True):
        st.markdown("""
            *   **Nomes:** Escreva sempre em **MAIÚSCULAS** (Ex: JOÃO DA SILVA).
            *   **Endereço:** Siga o padrão: **Rua/Avenida, Número, Bairro** (Ex: RUA SÃO JOÃO, 500, FÁTIMA).
            *   **WhatsApp:** Coloque apenas o **DDD + Número**. Não precisa do 55 (Ex: 73988887777).
            *   **Documentos:** Marque no checklist apenas o que a pessoa **entregou a cópia (Xerox)** hoje.
        """)

    tab_manual, tab_csv = st.tabs(["📄 Cadastro Individual", "📂 Importar via CSV"])

    with tab_manual:
        tipo_ficha = st.radio("Tipo de Inscrição:", ["Infantil/Juvenil", "Adulto"], horizontal=True)
        
        st.info("**📋 Documentação Necessária (Xerox para a Pasta):** ✔ RG ou Certidão | ✔ Comprovante de Residência | ✔ Batistério | ✔ Certidão de Eucaristia")

        st.subheader("📍 1. Identificação")
        c1, c2, c3 = st.columns([2, 1, 1])
        nome = c1.text_input("Nome Completo", help="Digite em MAIÚSCULAS sem abreviações.").upper()
        data_nasc = c2.date_input("Data de Nascimento", value=date(2010, 1, 1), format="DD/MM/YYYY")
        
        lista_turmas = ["CATEQUIZANDOS SEM TURMA"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])
        etapa_inscricao = c3.selectbox("Turma/Etapa", lista_turmas, help="Selecione a turma onde o catequizando será alocado.")

        c4, c5, c6 = st.columns([1.5, 1, 1.5])
        label_fone = "WhatsApp do Catequizando" if tipo_ficha == "Adulto" else "WhatsApp do Responsável"
        contato = c4.text_input(label_fone, help="Apenas números com DDD. Ex: 73988887777")
        batizado = c5.selectbox("Já é Batizado?", ["SIM", "NÃO"])
        endereco = c6.text_input("Endereço", help="Ex: RUA SÃO JOÃO, 123, FÁTIMA").upper()

        st.divider()
        if tipo_ficha == "Adulto":
            st.subheader("🚨 2. Contato de Emergência")
            ce1, ce2, ce3 = st.columns([2, 1, 1])
            nome_emergencia = ce1.text_input("Nome do Contato (Cônjuge, Filho, Amigo)").upper()
            vinculo_emergencia = ce2.selectbox("Vínculo", ["CÔNJUGE", "FILHO(A)", "IRMÃO/Ã", "PAI/MÃE", "AMIGO(A)", "OUTRO"])
            tel_emergencia = ce3.text_input("Telefone de Emergência", help="Apenas números com DDD.")
            
            nome_mae, prof_mae, tel_mae = "N/A", "N/A", "N/A"
            nome_pai, prof_pai, tel_pai = "N/A", "N/A", "N/A"
            responsavel_nome, vinculo_resp, tel_responsavel = nome_emergencia, vinculo_emergencia, tel_emergencia
        else:
            st.subheader("👪 2. Filiação e Responsáveis")
            col_mae, col_pai = st.columns(2)
            with col_mae:
                st.markdown("##### 👩‍🦱 Dados da Mãe")
                nome_mae = st.text_input("Nome da Mãe").upper()
                prof_mae = st.text_input("Profissão da Mãe").upper()
                tel_mae = st.text_input("WhatsApp da Mãe", help="Apenas números com DDD.")
            with col_pai:
                st.markdown("##### 👨‍ Dados do Pai")
                nome_pai = st.text_input("Nome do Pai").upper()
                prof_pai = st.text_input("Profissão do Pai").upper()
                tel_pai = st.text_input("WhatsApp do Pai", help="Apenas números com DDD.")

            st.info("🛡️ **Responsável Legal / Cuidador (Caso não more com os pais)**")
            cr1, cr2, cr3 = st.columns([2, 1, 1])
            responsavel_nome = cr1.text_input("Nome do Cuidador").upper()
            vinculo_resp = cr2.selectbox("Vínculo", ["NENHUM", "AVÓS", "TIOS", "IRMÃOS", "PADRINHOS", "OUTRO"])
            tel_responsavel = cr3.text_input("Telefone do Cuidador")

        st.divider()
        st.subheader("⛪ 3. Vida Eclesial e Engajamento")
        fe1, fe2 = st.columns(2)
        
        if tipo_ficha == "Adulto":
            estado_civil = fe1.selectbox("Seu Estado Civil", ["SOLTEIRO(A)", "CONVIVEM", "CASADO(A) IGREJA", "CASADO(A) CIVIL", "DIVORCIADO(A)", "VIÚVO(A)"])
            sacramentos_list = fe2.multiselect("Sacramentos que VOCÊ já possui:", ["BATISMO", "EUCARISTIA", "MATRIMÔNIO"])
            sacramentos = ", ".join(sacramentos_list)
            est_civil_pais, sac_pais, tem_irmaos, qtd_irmaos = "N/A", "N/A", "NÃO", 0
        else:
            est_civil_pais = fe1.selectbox("Estado Civil dos Pais", ["CASADOS", "UNIÃO DE FACTO", "SEPARADOS", "SOLTEIROS", "VIÚVO(A)"])
            sac_pais_list = fe2.multiselect("Sacramentos dos Pais:", ["BATISMO", "CRISMA", "EUCARISTIA", "MATRIMÔNIO"])
            sac_pais = ", ".join(sac_pais_list)
            tem_irmaos = fe1.radio("Tem irmãos na catequese?", ["NÃO", "SIM"], horizontal=True)
            qtd_irmaos = fe2.number_input("Quantos?", min_value=0, step=1) if tem_irmaos == "SIM" else 0
            estado_civil, sacramentos = "N/A", "N/A"

        part_grupo = st.radio("Participa (ou a família participa) de algum Grupo/Pastoral?", ["NÃO", "SIM"], horizontal=True)
        qual_grupo = "N/A"
        if part_grupo == "SIM":
            qual_grupo = st.text_input("Qual grupo/pastoral e quem participa?").upper()

        st.divider()
        st.subheader("🏥 4. Saúde e Documentação")
        s1, s2 = st.columns(2)
        
        tem_med = s1.radio("Toma algum medicamento ou tem alergia?", ["NÃO", "SIM"], horizontal=True)
        medicamento = "NÃO"
        if tem_med == "SIM":
            medicamento = s1.text_input("Descreva o medicamento/alergia:").upper()
            
        tgo = s2.selectbox("Possui TGO (Transtorno Global do Desenvolvimento)?", ["NÃO", "SIM"], help="Marque SIM para autismo, TDAH ou outras necessidades de inclusão.")
        
        st.markdown("---")
        st.markdown("**📁 Checklist de Documentos Entregues (Xerox):**")
        docs_obrigatorios = ["RG/CERTIDÃO", "COMPROVANTE RESIDÊNCIA", "BATISTÉRIO", "CERTIDÃO EUCARISTIA"]
        docs_entregues = st.multiselect("Marque o que foi entregue HOJE:", docs_obrigatorios, help="Só marque o que você já tem em mãos.")
        
        faltando = [d for d in docs_obrigatorios if d not in docs_entregues]
        doc_status_k = ", ".join(faltando) if faltando else "COMPLETO"

        c_pref1, c_pref2 = st.columns(2)
        turno = c_pref1.selectbox("Turno de preferência", ["MANHÃ (M)", "TARDE (T)", "NOITE (N)"])
        local_enc = c_pref2.text_input("Local do Encontro (Sala/Setor)").upper()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 FINALIZAR E SALVAR INSCRIÇÃO", use_container_width=True):
            if nome and contato and etapa_inscricao != "CATEQUIZANDOS SEM TURMA":
                with st.spinner("Gravando no Banco de Dados..."):
                    novo_id = f"CAT-{int(time.time())}"
                    
                    if tipo_ficha == "Adulto":
                        resp_final = nome_emergencia
                        obs_familia = f"EMERGÊNCIA: {vinculo_emergencia} - TEL: {tel_emergencia}"
                    else:
                        resp_final = responsavel_nome if responsavel_nome else f"{nome_mae} / {nome_pai}"
                        obs_familia = f"CUIDADOR: {responsavel_nome} ({vinculo_resp}). TEL: {tel_responsavel}" if responsavel_nome else "Mora com os pais."

                    registro = [[
                        novo_id, etapa_inscricao, nome, str(data_nasc), batizado, 
                        contato, endereco, nome_mae, nome_pai, resp_final, 
                        doc_status_k, qual_grupo, "ATIVO", medicamento, tgo, 
                        estado_civil, sacramentos, prof_mae, tel_mae, prof_pai, 
                        tel_pai, est_civil_pais, sac_pais, part_grupo, qual_grupo, 
                        tem_irmaos, qtd_irmaos, turno, local_enc, obs_familia
                    ]]
                    
                    if salvar_lote_catequizandos(registro):
                        st.success(f"✅ {nome} CADASTRADO COM SUCESSO!"); st.balloons(); time.sleep(1); st.rerun()
            else:
                st.error("⚠️ Por favor, preencha o Nome, WhatsApp e selecione uma Turma.")

    with tab_csv:
        st.subheader("📂 Importação em Massa (CSV)")
        with st.expander("📖 LEIA AS INSTRUÇÕES DE FORMATAÇÃO", expanded=True):
            st.markdown("""
                **Para que a importação funcione corretamente, seu arquivo CSV deve seguir estas regras:**
                1. **Colunas Obrigatórias:** `nome_completo` e `etapa`.
                2. **Formato de Data:** Use o padrão `DD/MM/AAAA`.
                3. **Turmas:** Se a turma escrita no CSV não existir no sistema, o catequizando será movido para **'CATEQUIZANDOS SEM TURMA'**.
            """)

        arquivo_csv = st.file_uploader("Selecione o arquivo .csv", type="csv", key="uploader_csv_cadastro")
        
        if arquivo_csv:
            try:
                df_import = pd.read_csv(arquivo_csv, encoding='utf-8').fillna("N/A")
                df_import.columns = [c.strip().lower() for c in df_import.columns]
                
                col_nome = 'nome_completo' if 'nome_completo' in df_import.columns else ('nome' if 'nome' in df_import.columns else None)
                col_etapa = 'etapa' if 'etapa' in df_import.columns else None

                if not col_nome or not col_etapa:
                    st.error("❌ Erro: O arquivo precisa ter as colunas 'nome_completo' e 'etapa'.")
                else:
                    turmas_cadastradas = [str(t).upper() for t in df_turmas['nome_turma'].tolist()] if not df_turmas.empty else []
                    st.markdown("### 🔍 Revisão dos Dados")
                    st.write(f"Total de registros: {len(df_import)}")
                    st.dataframe(df_import.head(10), use_container_width=True)

                    if st.button("🚀 CONFIRMAR IMPORTAÇÃO E GRAVAR NO BANCO", use_container_width=True):
                        with st.spinner("Processando 30 colunas..."):
                            lista_final = []
                            for i, linha in df_import.iterrows():
                                t_csv = str(linha.get(col_etapa, 'CATEQUIZANDOS SEM TURMA')).upper().strip()
                                t_final = t_csv if t_csv in turmas_cadastradas else "CATEQUIZANDOS SEM TURMA"
                                
                                registro = [
                                    f"CAT-CSV-{int(time.time()) + i}", t_final, str(linha.get(col_nome, 'SEM NOME')).upper(), 
                                    str(linha.get('data_nascimento', '01/01/2000')), str(linha.get('batizado_sn', 'NÃO')).upper(), 
                                    str(linha.get('contato_principal', 'N/A')), str(linha.get('endereco_completo', 'N/A')).upper(), 
                                    str(linha.get('nome_mae', 'N/A')).upper(), str(linha.get('nome_pai', 'N/A')).upper(), 
                                    str(linha.get('nome_responsavel', 'N/A')).upper(), str(linha.get('doc_em_falta', 'NADA')).upper(), 
                                    str(linha.get('engajado_grupo', 'N/A')).upper(), "ATIVO", 
                                    str(linha.get('toma_medicamento_sn', 'NÃO')).upper(), str(linha.get('tgo_sn', 'NÃO')).upper(), 
                                    str(linha.get('estado_civil_pais_ou_proprio', 'N/A')).upper(), str(linha.get('sacramentos_ja_feitos', 'N/A')).upper(), 
                                    str(linha.get('profissao_mae', 'N/A')).upper(), str(linha.get('tel_mae', 'N/A')), 
                                    str(linha.get('profissao_pai', 'N/A')).upper(), str(linha.get('tel_pai', 'N/A')), 
                                    str(linha.get('est_civil_pais', 'N/A')).upper(), str(linha.get('sac_pais', 'N/A')).upper(), 
                                    str(linha.get('participa_grupo', 'NÃO')).upper(), str(linha.get('qual_grupo', 'N/A')).upper(), 
                                    str(linha.get('tem_irmaos', 'NÃO')).upper(), linha.get('qtd_irmaos', 0), 
                                    str(linha.get('turno', 'N/A')).upper(), str(linha.get('local_encontro', 'N/A')).upper(), 
                                    f"Importado via CSV em {date.today().strftime('%d/%m/%Y')}"
                                ]
                                lista_final.append(registro)
                            
                            if salvar_lote_catequizandos(lista_final):
                                st.success(f"✅ {len(lista_final)} catequizandos importados!"); st.balloons(); time.sleep(2); st.rerun()
            except Exception as e:
                st.error(f"❌ Erro: {e}")

# ==============================================================================
# PÁGINA: 👤 PERFIL INDIVIDUAL
# ==============================================================================
elif menu == "👤 Perfil Individual":
    st.title("👤 Gestão de Perfis e Documentação")
    
    if df_cat.empty:
        st.warning("⚠️ Base de dados vazia. Cadastre catequizandos para acessar esta área.")
    else:
        tab_individual, tab_auditoria_geral, tab_evasao_gestao = st.tabs([
            "👤 Consulta e Edição Individual", "🚩 Auditoria de Documentos por Turma", "📄 Gestão de Evasão e Declarações"
        ])

        with tab_individual:
            st.subheader("🔍 Localizar e Visualizar Perfil")
            c1, c2 = st.columns([2, 1])
            busca = c1.text_input("Pesquisar por nome:", key="busca_perfil").upper()
            lista_t = ["TODAS"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])
            filtro_t = c2.selectbox("Filtrar por Turma:", lista_t, key="filtro_turma_perfil")

            df_f = df_cat.copy()
            if busca: df_f = df_f[df_f['nome_completo'].str.contains(busca, na=False)]
            if filtro_t != "TODAS": df_f = df_f[df_f['etapa'] == filtro_t]
            
            cols_necessarias = ['nome_completo', 'etapa', 'status']
            st.dataframe(df_f[cols_necessarias], use_container_width=True, hide_index=True)
            
            st.divider()

            df_f['display_select'] = df_f['nome_completo'] + " | Turma: " + df_f['etapa'] + " | ID: " + df_f['id_catequizando']
            escolha_display = st.selectbox("Selecione para VER PRÉVIA, EDITAR ou GERAR FICHA:", [""] + df_f['display_select'].tolist(), key="sel_catequizando_perfil")

            if escolha_display:
                id_sel = escolha_display.split(" | ID: ")[-1]
                filtro_dados = df_cat[df_cat['id_catequizando'] == id_sel]
                
                if not filtro_dados.empty:
                    dados = filtro_dados.iloc[0]
                    nome_sel = dados['nome_completo']
                    status_atual = str(dados['status']).upper()

                    obs_p = str(dados.get('obs_pastoral_familia', ''))
                    tel_e = obs_p.split('TEL: ')[-1] if 'TEL: ' in obs_p else "Não informado"
                    st.warning(f"🚨 **CONTATO DE EMERGÊNCIA:** {dados['nome_responsavel']} | **TEL:** {tel_e}")
                    
                    icone = "🟢" if status_atual == "ATIVO" else "🔴" if status_atual == "DESISTENTE" else "🔵" if status_atual == "TRANSFERIDO" else "⚪"
                    st.markdown(f"### {icone} {dados['nome_completo']} ({status_atual})")

                    # --- NOVO: ADICIONADA A ABA DE EXTRATO ---
                    sub_tab_edit, sub_tab_doc, sub_tab_hist = st.tabs(["✏️ Editar Cadastro", "📄 Gerar Documentos (PDF)", "📜 Extrato de Caminhada"])
                    
                    with sub_tab_edit:
                        st.subheader("✏️ Atualizar Dados do Catequizando")
                        idade_atual = calcular_idade(dados['data_nascimento'])
                        is_adulto = idade_atual >= 18

                        st.markdown("#### 📍 1. Identificação e Status")
                        ce1, ce2 = st.columns([2, 1])
                        ed_nome = ce1.text_input("Nome Completo", value=dados['nome_completo']).upper()
                        
                        opcoes_status = ["ATIVO", "TRANSFERIDO", "DESISTENTE", "INATIVO"]
                        idx_status = opcoes_status.index(status_atual) if status_atual in opcoes_status else 0
                        ed_status = ce2.selectbox("Alterar Status para:", opcoes_status, index=idx_status, help="Se mudar para Desistente, ele sairá das listas de chamada.")

                        c3, c4, c5 = st.columns([1, 1, 2])
                        ed_nasc = c3.date_input("Nascimento", value=converter_para_data(dados['data_nascimento']), format="DD/MM/YYYY")
                        ed_batizado = c4.selectbox("Batizado?", ["SIM", "NÃO"], index=0 if dados['batizado_sn'] == "SIM" else 1)
                        
                        lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else [dados['etapa']]
                        try: idx_turma_banco = lista_t_nomes.index(dados['etapa'])
                        except: idx_turma_banco = 0
                        ed_etapa = c5.selectbox("Turma Atual", lista_t_nomes, index=idx_turma_banco)

                        st.divider()

                        if is_adulto:
                            st.markdown("#### 🚨 2. Contato de Emergência / Vínculo")
                            cx1, cx2, cx3 = st.columns([2, 1, 1])
                            ed_contato = cx1.text_input("WhatsApp do Catequizando", value=dados['contato_principal'])
                            ed_resp = cx2.text_input("Nome do Contato", value=dados['nome_responsavel']).upper()
                            ed_tel_resp = cx3.text_input("Telefone de Emergência", value=tel_e if tel_e != "Não informado" else "")
                            
                            ed_mae, ed_prof_m, ed_tel_m = dados['nome_mae'], dados.get('profissao_mae', 'N/A'), dados.get('tel_mae', 'N/A')
                            ed_pai, ed_prof_p, ed_tel_p = dados['nome_pai'], dados.get('profissao_pai', 'N/A'), dados.get('tel_pai', 'N/A')
                            ed_end = st.text_input("Endereço Completo", value=dados['endereco_completo']).upper()
                        else:
                            st.markdown("#### 👪 2. Contatos e Filiação")
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

                        st.markdown("#### ⛪ 3. Vida Eclesial e Engajamento")
                        fe1, fe2 = st.columns(2)
                        part_grupo_init = str(dados.get('participa_grupo', 'NÃO')).upper()
                        ed_part_grupo = fe1.radio("Participa de algum Grupo/Pastoral?", ["NÃO", "SIM"], index=0 if part_grupo_init == "NÃO" else 1, horizontal=True)
                        ed_qual_grupo = "N/A"
                        if ed_part_grupo == "SIM":
                            ed_qual_grupo = fe1.text_input("Qual grupo/pastoral?", value=dados.get('qual_grupo', '') if dados.get('qual_grupo') != "N/A" else "").upper()

                        if is_adulto:
                            opcoes_ec = ["SOLTEIRO(A)", "CONVIVEM", "CASADO(A) IGREJA", "CASADO(A) CIVIL", "DIVORCIADO(A)", "VIÚVO(A)"]
                            val_ec = str(dados.get('estado_civil_pais_ou_proprio', 'SOLTEIRO(A)')).upper()
                            idx_ec = opcoes_ec.index(val_ec) if val_ec in opcoes_ec else 0
                            ed_est_civil = fe2.selectbox("Estado Civil", opcoes_ec, index=idx_ec)
                            ed_est_civil_pais = "N/A"
                        else:
                            opcoes_ecp = ["CASADOS", "UNIÃO DE FACTO", "SEPARADOS", "SOLTEIROS", "VIÚVO(A)"]
                            val_ecp = str(dados.get('est_civil_pais', 'CASADOS')).upper()
                            idx_ecp = opcoes_ecp.index(val_ecp) if val_ecp in opcoes_ecp else 0
                            ed_est_civil_pais = fe2.selectbox("Estado Civil dos Pais", opcoes_ecp, index=idx_ecp)
                            ed_est_civil = "N/A"

                        st.divider()

                        st.markdown("#### 🏥 4. Saúde e Documentação")
                        s1, s2 = st.columns(2)
                        med_atual = str(dados.get('toma_medicamento_sn', 'NÃO')).upper()
                        ed_tem_med = s1.radio("Toma algum medicamento?", ["NÃO", "SIM"], index=0 if med_atual == "NÃO" else 1, horizontal=True)
                        ed_med = s1.text_input("Descreva:", value=med_atual if med_atual != "NÃO" else "").upper() if ed_tem_med == "SIM" else "NÃO"
                        ed_tgo = s2.selectbox("Possui TGO?", ["NÃO", "SIM"], index=0 if dados['tgo_sn'] == "NÃO" else 1)

                        st.markdown("**📁 Checklist de Documentos (Xerox):**")
                        docs_obrigatorios = ["RG/CERTIDÃO", "COMPROVANTE RESIDÊNCIA", "BATISTÉRIO", "CERTIDÃO EUCARISTIA"]
                        faltas_atuais = str(dados.get('doc_em_falta', '')).upper()
                        entregues_pre = [d for d in docs_obrigatorios if d not in faltas_atuais]
                        ed_docs_entregues = st.multiselect("Marque o que JÁ ESTÁ NA PASTA:", docs_obrigatorios, default=entregues_pre)
                        novas_faltas = [d for d in docs_obrigatorios if d not in ed_docs_entregues]
                        ed_doc_status_k = ", ".join(novas_faltas) if novas_faltas else "COMPLETO"

                        if st.button("💾 SALVAR ALTERAÇÕES NO BANCO DE DADOS", use_container_width=True):
                            obs_final = f"EMERGÊNCIA: {ed_resp} - TEL: {ed_tel_resp}" if is_adulto else dados.get('obs_pastoral_familia', '')
                            lista_up = [
                                dados['id_catequizando'], ed_etapa, ed_nome, str(ed_nasc), ed_batizado, 
                                ed_contato, ed_end, ed_mae, ed_pai, ed_resp, ed_doc_status_k, 
                                ed_qual_grupo, ed_status, ed_med, ed_tgo, ed_est_civil, 
                                dados.get('sacramentos_ja_feitos', 'N/A'), ed_prof_m, ed_tel_m, 
                                ed_prof_p, ed_tel_p, ed_est_civil_pais, dados.get('sac_pais', 'N/A'), 
                                ed_part_grupo, ed_qual_grupo, dados.get('tem_irmaos', 'NÃO'), 
                                dados.get('qtd_irmaos', 0), dados.get('turno', 'N/A'), 
                                dados.get('local_encontro', 'N/A'), obs_final
                            ]
                            if atualizar_catequizando(dados['id_catequizando'], lista_up):
                                st.success(f"✅ Cadastro de {ed_nome} atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

                    with sub_tab_doc:
                        st.subheader("📄 Documentação Cadastral e Oficial")
                        st.write(f"Gerar documentos para: **{nome_sel}**")
                        col_doc_a, col_doc_b = st.columns(2)
                        with col_doc_a:
                            if st.button("📑 Gerar Ficha de Inscrição Completa", key="btn_pdf_perfil", use_container_width=True):
                                st.session_state.pdf_catequizando = gerar_ficha_cadastral_catequizando(dados.to_dict())
                            if "pdf_catequizando" in st.session_state:
                                st.download_button("📥 BAIXAR FICHA PDF", st.session_state.pdf_catequizando, f"Ficha_{nome_sel}.pdf", "application/pdf", use_container_width=True)
                        with col_doc_b:
                            if st.button("📜 Gerar Declaração de Matrícula", key="btn_decl_matr_perfil", use_container_width=True):
                                st.session_state.pdf_decl_matr = gerar_declaracao_pastoral_pdf(dados.to_dict(), "Declaração de Matrícula")
                            if "pdf_decl_matr" in st.session_state:
                                st.download_button("📥 BAIXAR DECLARAÇÃO PDF", st.session_state.pdf_decl_matr, f"Declaracao_Matricula_{nome_sel}.pdf", "application/pdf", use_container_width=True)

                    # --- NOVO: CONTEÚDO DA ABA DE EXTRATO ---
                    with sub_tab_hist:
                        st.subheader("📜 Histórico de Encontros e Temas")
                        pres_aluno = df_pres[df_pres['id_catequizando'] == dados['id_catequizando']].copy()
                        if not pres_aluno.empty:
                            pres_aluno['data_dt'] = pd.to_datetime(pres_aluno['data_encontro'], errors='coerce')
                            pres_aluno = pres_aluno.sort_values('data_dt', ascending=False)
                            
                            for _, p in pres_aluno.iterrows():
                                icone_p = "✅" if p['status'] == "PRESENTE" else "❌"
                                cor_p = "#2e7d32" if p['status'] == "PRESENTE" else "#e03d11"
                                data_f = formatar_data_br(p['data_encontro'])
                                tema_f = p.get('tema_do_dia', 'Tema não registrado')
                                st.markdown(f"<div style='padding:8px; border-bottom:1px solid #eee;'><span style='color:{cor_p};'>{icone_p}</span> <b>{data_f}</b> | {tema_f} <i>({p['status']})</i></div>", unsafe_allow_html=True)
                        else:
                            st.info("Nenhum registro de presença/falta para este catequizando.")

        with tab_auditoria_geral:
            st.subheader("🚩 Diagnóstico de Pendências por Turma")
            lista_turmas_auditoria = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
            turma_auditoria = st.selectbox("🔍 Selecione a Turma para Diagnóstico:", lista_turmas_auditoria, key="sel_auditoria_doc_turma")

            if turma_auditoria:
                df_turma_focal = df_cat[df_cat['etapa'] == turma_auditoria]
                df_pendentes_turma = df_turma_focal[
                    (df_turma_focal['doc_em_falta'].str.len() > 2) & 
                    (~df_turma_focal['doc_em_falta'].isin(['NADA', 'N/A', 'OK', 'COMPLETO', 'NADA FALTANDO']))
                ]

                c_met1, c_met2, c_met3 = st.columns(3)
                total_t = len(df_turma_focal)
                pendentes_t = len(df_pendentes_turma)
                em_dia_t = total_t - pendentes_t
                
                c_met1.metric("Total na Turma", total_t)
                c_met2.metric("Pendentes", pendentes_t, delta=f"{pendentes_t} faltam docs", delta_color="inverse")
                c_met3.metric("Em Dia", em_dia_t)

                st.markdown("---")

                if df_pendentes_turma.empty:
                    st.success(f"✅ **Excelente!** Todos os {total_t} catequizandos da turma **{turma_auditoria}** estão com a documentação completa.")
                else:
                    st.markdown(f"#### 📋 Lista de Pendências: {turma_auditoria}")
                    for _, p in df_pendentes_turma.iterrows():
                        with st.container():
                            idade_p = calcular_idade(p['data_nascimento'])
                            is_adulto_p = idade_p >= 18
                            
                            if is_adulto_p:
                                nome_alvo, vinculo_alvo, tel_alvo = p['nome_completo'], "Próprio", p['contato_principal']
                            else:
                                if str(p['tel_mae']) not in ["N/A", "", "None"]:
                                    nome_alvo, vinculo_alvo, tel_alvo = p['nome_mae'], "Mãe", p['tel_mae']
                                elif str(p['tel_pai']) not in ["N/A", "", "None"]:
                                    nome_alvo, vinculo_alvo, tel_alvo = p['nome_pai'], "Pai", p['tel_pai']
                                else:
                                    nome_alvo, vinculo_alvo, tel_alvo = p['nome_responsavel'], "Responsável", p['contato_principal']

                            st.markdown(f"""
                                <div style='background-color:#fff5f5; padding:15px; border-radius:10px; border-left:8px solid #e03d11; margin-bottom:10px;'>
                                    <b style='color:#e03d11; font-size:16px;'>{p['nome_completo']}</b><br>
                                    <span style='font-size:13px; color:#333;'>⚠️ <b>FALTANDO:</b> {p['doc_em_falta']}</span><br>
                                    <span style='font-size:12px; color:#666;'>👤 <b>Cobrar de:</b> {nome_alvo} ({vinculo_alvo})</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
                            
                            if col_p1.button(f"✨ IA: Cobrar {vinculo_alvo}", key=f"msg_aud_{p['id_catequizando']}"):
                                msg_doc = gerar_mensagem_cobranca_doc_ia(p['nome_completo'], p['doc_em_falta'], p['etapa'], nome_alvo, vinculo_alvo)
                                st.info(f"**Mensagem para {nome_alvo}:**\n\n{msg_doc}")
                            
                            if col_p2.button("✅ Entregue", key=f"btn_ok_aud_{p['id_catequizando']}", use_container_width=True):
                                lista_up = p.tolist()
                                while len(lista_up) < 30: lista_up.append("N/A")
                                lista_up[10] = "COMPLETO"
                                if atualizar_catequizando(p['id_catequizando'], lista_up):
                                    st.success("Atualizado!"); time.sleep(0.5); st.rerun()

                            num_limpo = "".join(filter(str.isdigit, str(tel_alvo)))
                            if num_limpo:
                                if num_limpo.startswith("0"): num_limpo = num_limpo[1:]
                                if not num_limpo.startswith("55"):
                                    num_limpo = f"5573{num_limpo}" if len(num_limpo) <= 9 else f"55{num_limpo}"
                                col_p3.markdown(f'''<a href="https://wa.me/{num_limpo}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; text-align:center; padding:10px; border-radius:5px; font-weight:bold; font-size:12px;">📲 WhatsApp</div></a>''', unsafe_allow_html=True)
                            else:
                                col_p3.caption("Sem Tel.")
                            st.markdown("<br>", unsafe_allow_html=True)

        with tab_evasao_gestao:
            st.subheader("🚩 Gestão de Evasão e Documentos de Saída")
            df_saidas = df_cat[df_cat['status'] != 'ATIVO']
            c_ev1, c_ev2, c_ev3 = st.columns(3)
            c_ev1.metric("🔴 Desistentes", len(df_saidas[df_saidas['status'] == 'DESISTENTE']))
            c_ev2.metric("🔵 Transferidos", len(df_saidas[df_saidas['status'] == 'TRANSFERIDO']))
            c_ev3.metric("⚪ Inativos", len(df_saidas[df_saidas['status'] == 'INATIVO']))
            
            st.divider()
            
            if df_saidas.empty:
                st.success("Glória a Deus! Não há registros de evasão no momento.")
            else:
                st.markdown("#### 📋 Lista de Caminhadas Interrompidas")
                st.dataframe(df_saidas[['nome_completo', 'etapa', 'status', 'obs_pastoral_familia']], use_container_width=True, hide_index=True)
                
                st.divider()
                st.markdown("#### 📄 Gerar Declaração Oficial (Transferência ou Matrícula)")
                sel_cat_ev = st.selectbox("Selecione o Catequizando para o Documento:", [""] + df_saidas['nome_completo'].tolist(), key="sel_ev_doc")
                
                if sel_cat_ev:
                    dados_ev = df_saidas[df_saidas['nome_completo'] == sel_cat_ev].iloc[0]
                    col_d1, col_d2 = st.columns(2)
                    tipo_doc = col_d1.selectbox("Tipo de Documento:", ["Declaração de Transferência", "Declaração de Matrícula"])
                    paroquia_dest = ""
                    if "Transferência" in tipo_doc:
                        paroquia_dest = col_d2.text_input("Transferido para a Paróquia:", placeholder="Ex: Paróquia Santa Rita")

                    if st.button(f"📥 GERAR {tipo_doc.upper()}", use_container_width=True):
                        with st.spinner("Renderizando documento oficial..."):
                            pdf_ev_final = gerar_declaracao_pastoral_pdf(dados_ev.to_dict(), tipo_doc, paroquia_dest)
                            st.session_state.pdf_declaracao_saida = pdf_ev_final
                    
                    if "pdf_declaracao_saida" in st.session_state:
                        st.download_button("💾 BAIXAR DECLARAÇÃO (PDF)", st.session_state.pdf_declaracao_saida, f"Declaracao_{sel_cat_ev}.pdf", use_container_width=True)
                    
                    st.divider()
                    if st.button(f"🔄 REATIVAR {sel_cat_ev} (Voltou para a Catequese)", type="primary"):
                        lista_up_v = dados_ev.tolist()
                        while len(lista_up_v) < 30: lista_up_v.append("N/A")
                        lista_up_v[12] = "ATIVO"
                        if atualizar_catequizando(dados_ev['id_catequizando'], lista_up_v):
                            st.success(f"{sel_cat_ev} reativado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()

# ==============================================================================
# PÁGINA: 🏫 GESTÃO DE TURMAS
# ==============================================================================
elif menu == "🏫 Gestão de Turmas":
    st.title("🏫 Gestão de Turmas e Fila de Espera")
    
    t0, t1, t2, t3, t4, t5 = st.tabs([
        "⏳ Fila de Espera", "📋 Visualizar Turmas", "➕ Criar Nova Turma", 
        "✏️ Detalhes e Edição", "📊 Dashboard Local", "🚀 Movimentação em Massa"
    ])
    
    dias_opcoes =["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    etapas_lista =[
        "PRÉ", "PRIMEIRA ETAPA", "SEGUNDA ETAPA", "TERCEIRA ETAPA", 
        "PERSEVERANÇA", "ADULTOS TURMA EUCARISTIA/BATISMO", "ADULTOS CRISMA"
    ]

    with t0:
        st.subheader("⏳ Fila de Espera")
        if df_cat.empty:
            st.info("Nenhum catequizando cadastrado no sistema.")
        else:
            turmas_reais = df_turmas['nome_turma'].unique().tolist() if not df_turmas.empty else[]
            fila_espera = df_cat[(df_cat['etapa'] == "CATEQUIZANDOS SEM TURMA") | (~df_cat['etapa'].isin(turmas_reais))]
            
            if not fila_espera.empty:
                colunas_para_exibir =['nome_completo', 'etapa', 'contato_principal']
                cols_existentes =[c for c in colunas_para_exibir if c in fila_espera.columns]
                st.dataframe(fila_espera[cols_existentes], use_container_width=True, hide_index=True)
            else:
                st.success("Todos os catequizandos estão alocados em turmas válidas! 🎉")

    with t1:
        st.subheader("📋 Turmas Cadastradas")
        st.dataframe(df_turmas, use_container_width=True, hide_index=True)

    with t2:
        st.subheader("➕ Cadastrar Nova Turma")
        with st.form("form_criar_turma"):
            c1, c2 = st.columns(2)
            n_t = c1.text_input("Nome da Turma", help="Ex: PRÉ ETAPA 2026").upper()
            e_t = c1.selectbox("Etapa Base", etapas_lista)
            ano = c2.number_input("Ano Letivo", value=2026)
            n_dias = st.multiselect("Dias de Encontro", dias_opcoes)
            
            st.markdown("---")
            c3, c4 = st.columns(2)
            turno_t = c3.selectbox("Turno do Encontro",["MANHÃ", "TARDE", "NOITE"])
            local_t = c4.text_input("Local/Sala do Encontro", value="SALA").upper()
            
            cats_selecionados = st.multiselect("Catequistas Responsáveis (Opcional)", equipe_tecnica['nome'].tolist() if not equipe_tecnica.empty else[])
            
            if st.form_submit_button("🚀 SALVAR NOVA TURMA"):
                if n_t and n_dias:
                    try:
                        planilha = conectar_google_sheets()
                        if planilha:
                            nova_t =[f"TRM-{int(time.time())}", n_t, e_t, int(ano), ", ".join(cats_selecionados), ", ".join(n_dias), "", "", turno_t, local_t]
                            planilha.worksheet("turmas").append_row(nova_t)
                            
                            if cats_selecionados:
                                aba_u = planilha.worksheet("usuarios")
                                for c_nome in cats_selecionados:
                                    celula = aba_u.find(c_nome, in_column=1)
                                    if celula:
                                        v_atual = aba_u.cell(celula.row, 5).value or ""
                                        v_list =[x.strip() for x in v_atual.split(',') if x.strip()]
                                        if n_t not in v_list:
                                            v_list.append(n_t)
                                            aba_u.update_cell(celula.row, 5, ", ".join(v_list))
                            
                            st.success(f"✅ Turma '{n_t}' criada com sucesso!")
                            st.cache_data.clear(); time.sleep(1); st.rerun()
                    except Exception as e: st.error(f"Erro ao salvar: {e}")
                else: st.warning("⚠️ O Nome da Turma e os Dias de Encontro são obrigatórios.")

    with t3:
        st.subheader("✏️ Detalhes e Edição da Turma")
        if not df_turmas.empty:
            sel_t = st.selectbox("Selecione a turma para editar:", [""] + df_turmas['nome_turma'].tolist(), key="sel_edit_turma")
            
            if sel_t:
                d = df_turmas[df_turmas['nome_turma'] == sel_t].iloc[0]
                nome_turma_original = str(d['nome_turma'])
                
                c1, c2 = st.columns(2)
                en = c1.text_input("Nome da Turma", value=d['nome_turma'], key="edit_nome_turma").upper()
                ee = c1.selectbox("Etapa Base", etapas_lista, index=etapas_lista.index(d['etapa']) if d['etapa'] in etapas_lista else 0, key="edit_etapa_turma")
                ea = c2.number_input("Ano Letivo", value=int(d['ano']), key="edit_ano_turma")
                
                dias_atuais =[x.strip() for x in str(d.get('dias_semana', '')).split(',') if x.strip()]
                ed_dias = st.multiselect("Dias de Encontro", dias_opcoes, default=[d for d in dias_atuais if d in dias_opcoes], key="edit_dias_turma")
                
                st.markdown("---")
                c3, c4 = st.columns(2)
                opcoes_turno =["MANHÃ", "TARDE", "NOITE"]
                turno_atual = str(d.get('turno', 'MANHÃ')).upper()
                et = c3.selectbox("Turno", opcoes_turno, index=opcoes_turno.index(turno_atual) if turno_atual in opcoes_turno else 0, key="edit_turno_turma")
                el = c4.text_input("Local / Sala", value=d.get('local', 'SALA'), key="edit_local_turma").upper()
                
                pe = c1.text_input("Previsão Eucaristia", value=d.get('previsao_eucaristia', ''), key="edit_pe_turma")
                pc = c2.text_input("Previsão Crisma", value=d.get('previsao_crisma', ''), key="edit_pc_turma")
                
                lista_todos_cats = equipe_tecnica['nome'].tolist() if not equipe_tecnica.empty else []
                cats_atuais_lista =[c.strip() for c in str(d.get('catequista_responsavel', '')).split(',') if c.strip()]
                ed_cats = st.multiselect("Catequistas Responsáveis", options=lista_todos_cats, default=[c for c in cats_atuais_lista if c in lista_todos_cats], key="edit_cats_turma")
                
                col_btn_save, col_btn_del = st.columns([3, 1])
                
                with col_btn_save:
                    if st.button("💾 SALVAR ALTERAÇÕES E SINCRONIZAR", key="btn_save_edit_turma", use_container_width=True):
                        with st.spinner("Processando atualizações e movendo catequizandos..."):
                            lista_up = [str(d['id_turma']), en, ee, int(ea), ", ".join(ed_cats), ", ".join(ed_dias), pe, pc, et, el]
                            
                            if atualizar_turma(d['id_turma'], lista_up):
                                if en != nome_turma_original:
                                    from database import sincronizar_renomeacao_turma_catequizandos
                                    sincronizar_renomeacao_turma_catequizandos(nome_turma_original, en)
                                
                                planilha = conectar_google_sheets()
                                aba_u = planilha.worksheet("usuarios")
                                for _, cat_row in equipe_tecnica.iterrows():
                                    c_nome = cat_row['nome']
                                    celula = aba_u.find(c_nome, in_column=1)
                                    if celula:
                                        v_atual = aba_u.cell(celula.row, 5).value or ""
                                        v_list =[x.strip() for x in v_atual.split(',') if x.strip()]
                                        mudou = False
                                        if c_nome in ed_cats:
                                            if en not in v_list: v_list.append(en); mudou = True
                                            if nome_turma_original in v_list and en != nome_turma_original:
                                                v_list.remove(nome_turma_original); mudou = True
                                        else:
                                            if en in v_list: v_list.remove(en); mudou = True
                                            if nome_turma_original in v_list: v_list.remove(nome_turma_original); mudou = True
                                        if mudou: aba_u.update_cell(celula.row, 5, ", ".join(v_list))
                                
                                st.success(f"✅ Turma e Catequizandos atualizados para '{en}'!")
                                st.cache_data.clear(); time.sleep(1); st.rerun()

                st.markdown("<br><br>", unsafe_allow_html=True)
                with st.expander("🗑️ ZONA DE PERIGO: Excluir Turma"):
                    st.error(f"Atenção: Ao excluir a turma '{sel_t}', todos os catequizandos nela matriculados serão movidos para a Fila de Espera.")
                    confirmar_exclusao = st.checkbox(f"Confirmo a exclusão definitiva da turma {sel_t}", key="chk_del_turma")
                    
                    if st.button("🗑️ EXCLUIR TURMA AGORA", type="primary", disabled=not confirmar_exclusao, use_container_width=True):
                        with st.spinner("Movendo catequizandos e excluindo itinerário..."):
                            alunos_da_turma = df_cat[df_cat['etapa'] == sel_t]
                            if not alunos_da_turma.empty:
                                ids_para_mover = alunos_da_turma['id_catequizando'].tolist()
                                mover_catequizandos_em_massa(ids_para_mover, "CATEQUIZANDOS SEM TURMA")
                            
                            planilha = conectar_google_sheets()
                            aba_u = planilha.worksheet("usuarios")
                            for _, cat_row in equipe_tecnica.iterrows():
                                v_atual = str(cat_row.get('turma_vinculada', ''))
                                if sel_t in v_atual:
                                    v_list = [x.strip() for x in v_atual.split(',') if x.strip()]
                                    if sel_t in v_list:
                                        v_list.remove(sel_t)
                                        celula_u = aba_u.find(cat_row['nome'], in_column=1)
                                        if celula_u: aba_u.update_cell(celula_u.row, 5, ", ".join(v_list))
                            
                            if excluir_turma(d['id_turma']):
                                st.success(f"Turma excluída! {len(alunos_da_turma)} catequizandos movidos para a Fila de Espera.")
                                st.cache_data.clear(); time.sleep(2); st.rerun()

    with t4:
        st.subheader("📊 Inteligência Pastoral da Turma")
        if not df_turmas.empty:
            t_alvo = st.selectbox("Selecione a turma para auditoria:", df_turmas['nome_turma'].tolist(), key="sel_dash_turma")
            
            alunos_t = df_cat[df_cat['etapa'] == t_alvo] if not df_cat.empty else pd.DataFrame()
            info_t = df_turmas[df_turmas['nome_turma'] == t_alvo].iloc[0]
            pres_t = df_pres[df_pres['id_turma'] == t_alvo] if not df_pres.empty else pd.DataFrame()
            df_cron_local = ler_aba("cronograma")
            df_enc_local = ler_aba("encontros")
            df_pres_reu = ler_aba("presenca_reuniao")
            
            if not alunos_t.empty:
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                qtd_cats_real = len(str(info_t['catequista_responsavel']).split(','))
                m1.metric("Catequistas", qtd_cats_real)
                m2.metric("Catequizandos", len(alunos_t))
                
                freq_global = 0.0
                if not pres_t.empty:
                    pres_t['status_num'] = pres_t['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                    freq_global = round(pres_t['status_num'].mean() * 100, 1)
                m3.metric("Frequência", f"{freq_global}%")
                
                idades =[calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
                idade_media_val = round(sum(idades)/len(idades), 1) if idades else 0
                m4.metric("Idade Média", f"{idade_media_val}a")

                perc_pais = 0
                if not df_pres_reu.empty:
                    pais_presentes = df_pres_reu[df_pres_reu.iloc[:, 3] == t_alvo].iloc[:, 1].nunique()
                    perc_pais = int((pais_presentes / len(alunos_t)) * 100) if len(alunos_t) > 0 else 0
                m5.metric("Engajamento Pais", f"{perc_pais}%")

                total_p = len(df_cron_local[df_cron_local['etapa'] == t_alvo]) if not df_cron_local.empty else 0
                total_f = len(df_enc_local[df_enc_local['turma'] == t_alvo]) if not df_enc_local.empty else 0
                progresso = int((total_f / (total_f + total_p) * 100)) if (total_f + total_p) > 0 else 0
                m6.metric("Itinerário", f"{progresso}%")

                st.divider()
                st.markdown("#### 🚀 Radar de Enturmação (Sugestão de Movimentação)")
                etapa_base = str(info_t['etapa']).upper()
                faixas = {"PRÉ": (4, 6), "PRIMEIRA ETAPA": (7, 8), "SEGUNDA ETAPA": (9, 10), "TERCEIRA ETAPA": (11, 13), "PERSEVERANÇA": (14, 15), "ADULTOS": (16, 99)}
                min_ideal, max_ideal = faixas.get(etapa_base, (0, 99))
                
                fora_da_faixa =[]
                for _, r in alunos_t.iterrows():
                    idade_c = calcular_idade(r['data_nascimento'])
                    if idade_c < min_ideal: fora_da_faixa.append({"nome": r['nome_completo'], "idade": idade_c, "aviso": "🔽 Abaixo"})
                    elif idade_c > max_ideal: fora_da_faixa.append({"nome": r['nome_completo'], "idade": idade_c, "aviso": "🔼 Acima"})
                
                if fora_da_faixa:
                    st.warning(f"⚠️ {len(fora_da_faixa)} catequizandos fora da faixa etária para {etapa_base}.")
                    with st.expander("🔍 Ver quem precisa de atenção para movimentação"):
                        for item in fora_da_faixa: st.write(f"**{item['nome']}** - {item['idade']} anos ({item['aviso']})")
                else:
                    st.success(f"✅ Todos na faixa etária ideal.")

                st.divider()
                col_sac, col_sau = st.columns(2)
                with col_sac:
                    st.markdown("#### 🕊️ Prontidão Sacramental")
                    sem_batismo = len(alunos_t[alunos_t['batizado_sn'] != 'SIM'])
                    if sem_batismo > 0: st.error(f"🚨 **{sem_batismo}** catequizandos sem Batismo.")
                    else: st.success("✅ Todos os catequizandos são batizados.")
                    docs_pend = len(alunos_t[~alunos_t['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])])
                    if docs_pend > 0: st.warning(f"📄 **{docs_pend}** com pendência de documentos.")

                with col_sau:
                    st.markdown("#### 🏥 Cuidado e Inclusão")
                    tgo_count = len(alunos_t[alunos_t['tgo_sn'] == 'SIM'])
                    med_count = len(alunos_t[alunos_t['toma_medicamento_sn'] != 'NÃO'])
                    if tgo_count > 0: st.info(f"💙 **{tgo_count}** catequizando(s) com TGO (Inclusão).")
                    if med_count > 0: st.warning(f"💊 **{med_count}** fazem uso de medicamento/alergia.")
                    if tgo_count == 0 and med_count == 0: st.write("Nenhuma observação de saúde registrada.")

                st.divider()
                st.markdown("#### 📖 Itinerário Pedagógico")
                c_it1, c_it2 = st.columns(2)
                with c_it1:
                    st.caption("Últimos Temas Ministrados")
                    if not df_enc_local.empty:
                        ultimos = df_enc_local[df_enc_local['turma'] == t_alvo].sort_values('data', ascending=False).head(3)
                        for _, u in ultimos.iterrows(): st.write(f"✅ {formatar_data_br(u['data'])} - {u['tema']}")
                    else: st.write("Nenhum encontro registrado.")
                with c_it2:
                    st.caption("Próximos Temas Planejados")
                    if not df_cron_local.empty:
                        proximos = df_cron_local[(df_cron_local['etapa'] == t_alvo) & (df_cron_local.get('status','') != 'REALIZADO')].head(3)
                        for _, p in proximos.iterrows(): st.write(f"📌 {p['titulo_tema']}")
                    else: st.write("Cronograma concluído ou vazio.")

                st.divider()
                st.markdown("#### 📄 Documentação e Auditoria")
                col_doc1, col_doc2 = st.columns(2)
                
                with col_doc1:
                    if st.button(f"✨ GERAR AUDITORIA PASTORAL: {t_alvo}", use_container_width=True, key="btn_auditoria_turma"):
                        with st.spinner("Analisando prontidão da turma..."):
                            sem_batismo = len(alunos_t[alunos_t['batizado_sn'] != 'SIM'])
                            batizados = len(alunos_t) - sem_batismo
                            tgo_c = len(alunos_t[alunos_t['tgo_sn'] == 'SIM'])
                            saude_c = len(alunos_t[alunos_t['toma_medicamento_sn'] != 'NÃO'])
                            
                            perc_pais = 0
                            if not df_pres_reu.empty:
                                pais_presentes = df_pres_reu[df_pres_reu.iloc[:, 3] == t_alvo].iloc[:, 1].nunique()
                                perc_pais = int((pais_presentes / len(alunos_t)) * 100) if len(alunos_t) > 0 else 0

                            total_p = len(df_cron_local[df_cron_local['etapa'] == t_alvo]) if not df_cron_local.empty else 0
                            total_f = len(df_enc_local[df_enc_local['turma'] == t_alvo]) if not df_enc_local.empty else 0
                            prog_it = int((total_f / (total_f + total_p) * 100)) if (total_f + total_p) > 0 else 0

                            lista_geral =[]
                            for _, r in alunos_t.iterrows():
                                f = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')]) if not pres_t.empty else 0
                                has_euc = "SIM" if "EUCARISTIA" in str(r['sacramentos_ja_feitos']).upper() else "NÃO"
                                lista_geral.append({
                                    'nome': r['nome_completo'], 'faltas': f, 'batismo': r['batizado_sn'],
                                    'eucaristia': has_euc, 'status': r['status']
                                })

                            resumo_ia = f"Turma {t_alvo}: {len(alunos_t)} catequizandos. Freq: {freq_global}%. Pais: {perc_pais}%. Batizados: {batizados}. Pendentes Batismo: {sem_batismo}. TGO: {tgo_c}."
                            parecer_ia = analisar_turma_local(t_alvo, resumo_ia)

                            st.session_state[f"pdf_auditoria_{t_alvo}"] = gerar_relatorio_local_turma_pdf(
                                t_alvo, 
                                {
                                    'qtd_catequistas': qtd_cats_real, 'qtd_cat': len(alunos_t), 
                                    'freq_global': freq_global, 'idade_media': idade_media_val,
                                    'engaj_pais': perc_pais, 'progresso_it': prog_it,
                                    'batizados': batizados, 'pend_batismo': sem_batismo,
                                    'tgo': tgo_c, 'saude': saude_c
                                }, 
                                {'geral': lista_geral}, 
                                parecer_ia
                            )
                    if f"pdf_auditoria_{t_alvo}" in st.session_state:
                        st.write("")
                        st.download_button(
                            label=f"📥 BAIXAR AUDITORIA: {t_alvo}",
                            data=st.session_state[f"pdf_auditoria_{t_alvo}"],
                            file_name=f"Auditoria_Pastoral_{t_alvo.replace(' ', '_')}_{date.today().year}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                with col_doc2:
                    if st.button(f"📄 GERAR FICHAS DA TURMA (LOTE)", use_container_width=True, key="btn_fichas_turma"):
                        with st.spinner("Gerando fichas individuais..."):
                            pdf_fichas = gerar_fichas_turma_completa(t_alvo, alunos_t)
                            st.session_state[f"pdf_fichas_{t_alvo}"] = pdf_fichas
                    if f"pdf_fichas_{t_alvo}" in st.session_state:
                        st.download_button("📥 BAIXAR FICHAS (LOTE)", st.session_state[f"pdf_fichas_{t_alvo}"], f"Fichas_{t_alvo}.pdf", use_container_width=True)

                st.divider()
                st.markdown("### 📋 Lista Nominal de Caminhada")
                lista_preview =[]
                for _, r in alunos_t.iterrows():
                    f = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')]) if not pres_t.empty else 0
                    idade_c = calcular_idade(r['data_nascimento'])
                    lista_preview.append({'Catequizando': r['nome_completo'], 'Idade': f"{idade_c} anos", 'Faltas': f, 'Status': r['status']})
                st.dataframe(pd.DataFrame(lista_preview), use_container_width=True, hide_index=True)
            else:
                st.info("Selecione uma turma com catequizandos ativos.")

    with t5:
        st.subheader("🚀 Movimentação em Massa")
        if not df_turmas.empty and not df_cat.empty:
            c1, c2 = st.columns(2)
            opcoes_origem =["CATEQUIZANDOS SEM TURMA"] + sorted(df_cat['etapa'].unique().tolist())
            t_origem = c1.selectbox("1. Turma de ORIGEM (Sair de):", opcoes_origem, key="mov_orig_turma")
            t_destino = c2.selectbox("2. Turma de DESTINO (Ir para):", df_turmas['nome_turma'].tolist(), key="mov_dest_turma")
            
            if t_origem:
                alunos_mov = df_cat[(df_cat['etapa'] == t_origem) & (df_cat['status'] == 'ATIVO')]
                
                if not alunos_mov.empty:
                    def toggle_all_mov():
                        for _, al in alunos_mov.iterrows():
                            st.session_state[f"mov_al_{al['id_catequizando']}"] = st.session_state.chk_mov_todos

                    st.checkbox("Selecionar todos os catequizandos", key="chk_mov_todos", on_change=toggle_all_mov)
                    
                    lista_ids_selecionados =[]
                    cols = st.columns(2)
                    
                    for i, (_, al) in enumerate(alunos_mov.iterrows()):
                        idade_atual = calcular_idade(al['data_nascimento'])
                        with cols[i % 2]:
                            label_exibicao = f"{al['nome_completo']} ({idade_atual} anos)"
                            if st.checkbox(label_exibicao, key=f"mov_al_{al['id_catequizando']}"):
                                lista_ids_selecionados.append(al['id_catequizando'])
                    
                    st.divider()
                    if st.button(f"🚀 MOVER {len(lista_ids_selecionados)} CATEQUIZANDOS PARA {t_destino}", key="btn_exec_mov", use_container_width=True):
                        if t_destino and t_origem != t_destino and lista_ids_selecionados:
                            if mover_catequizandos_em_massa(lista_ids_selecionados, t_destino):
                                st.success(f"✅ Sucesso! {len(lista_ids_selecionados)} movidos para {t_destino}."); st.cache_data.clear(); time.sleep(2); st.rerun()
                        else: 
                            st.error("Selecione um destino válido e ao menos um catequizando.")
                else:
                    st.info("Não há catequizandos ativos nesta turma de origem.")

# ==============================================================================
# PÁGINA: 🕊️ GESTÃO DE SACRAMENTOS
# ==============================================================================
elif menu == "🕊️ Gestão de Sacramentos":
    st.title("🕊️ Auditoria e Gestão de Sacramentos")
    tab_dash, tab_plan, tab_reg, tab_hist = st.tabs([
        "📊 Auditoria Sacramental", "📅 Planejar sacramento", "✍️ Registrar Sacramento", "📜 Histórico"
    ])
    
    with tab_plan:
        st.subheader("📅 Planejamento de Cerimônias")
        if df_turmas.empty:
            st.warning("Cadastre turmas para planejar sacramentos.")
        else:
            c1, c2 = st.columns(2)
            t_plan = c1.selectbox("Selecione a Turma:", df_turmas['nome_turma'].tolist(), key="sel_t_plan")
            tipo_s_plan = c2.selectbox("Sacramento Previsto:", ["EUCARISTIA", "CRISMA"], key="sel_s_plan")
            
            info_t = df_turmas[df_turmas['nome_turma'] == t_plan].iloc[0]
            col_data = 'previsao_eucaristia' if tipo_s_plan == "EUCARISTIA" else 'previsao_crisma'
            data_atual_prevista = info_t.get(col_data, "")
            
            with st.expander("⚙️ Definir/Alterar Data da Cerimônia", expanded=not data_atual_prevista):
                nova_data_p = st.date_input("Data da Missa/Celebração:", 
                                          value=converter_para_data(data_atual_prevista) if data_atual_prevista else date.today())
                if st.button("📌 SALVAR DATA NO CRONOGRAMA DA TURMA"):
                    lista_up_t = info_t.tolist()
                    idx_col = 6 if tipo_s_plan == "EUCARISTIA" else 7
                    lista_up_t[idx_col] = str(nova_data_p)
                    if atualizar_turma(info_t['id_turma'], lista_up_t):
                        st.success("Data salva!"); st.cache_data.clear(); time.sleep(1); st.rerun()

            if data_atual_prevista:
                st.divider()
                st.info(f"🗓️ Celebração de **{tipo_s_plan}** prevista para: **{formatar_data_br(data_atual_prevista)}**")
                
                alunos_t = df_cat[(df_cat['etapa'] == t_plan) & (df_cat['status'] == 'ATIVO')]
                prontos = alunos_t[alunos_t['batizado_sn'] == 'SIM']
                pendentes = alunos_t[alunos_t['batizado_sn'] != 'SIM']
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total de Candidatos", len(alunos_t))
                m2.metric("✅ Prontos", len(prontos))
                m3.metric("⚠️ Sem Batismo", len(pendentes), delta_color="inverse")
                
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    st.markdown("##### ✅ Aptos para o Sacramento")
                    st.caption("Ativos e Batizados")
                    for n in prontos['nome_completo'].tolist(): st.write(f"· {n}")
                    
                    if st.button("📄 GERAR LISTA PARA SECRETARIA (PDF)", use_container_width=True):
                        st.session_state.pdf_secretaria = gerar_lista_secretaria_pdf(t_plan, data_atual_prevista, tipo_s_plan, prontos['nome_completo'].tolist())
                    
                    if "pdf_secretaria" in st.session_state:
                        st.download_button("📥 BAIXAR LISTA NOMINAL", st.session_state.pdf_secretaria, f"Lista_Secretaria_{t_plan}.pdf", use_container_width=True)

                with col_l2:
                    st.markdown("##### 🚨 Impedimentos (Atenção!)")
                    st.caption("Precisam de Batismo urgente")
                    if not pendentes.empty:
                        for n in pendentes['nome_completo'].tolist(): st.error(f"⚠️ {n}")
                    else:
                        st.success("Nenhum impedimento na turma!")

                st.divider()
                with st.expander("🏁 FINALIZAR PROCESSO (Pós-Celebração)"):
                    st.warning("CUIDADO: Esta ação registrará o sacramento para todos os APTOS acima e atualizará o histórico deles permanentemente.")
                    if st.button(f"🚀 CONFIRMAR QUE A CELEBRAÇÃO OCORREU"):
                        id_ev = f"PLAN-{int(time.time())}"
                        lista_p = [[id_ev, r['id_catequizando'], r['nome_completo'], tipo_s_plan, str(data_atual_prevista)] for _, r in prontos.iterrows()]
                        
                        if registrar_evento_sacramento_completo([id_ev, tipo_s_plan, str(data_atual_prevista), t_plan, st.session_state.usuario['nome']], lista_p, tipo_s_plan):
                            st.success("Glória a Deus! Todos os registros foram atualizados."); st.balloons(); time.sleep(2); st.rerun()

    with tab_dash:
        df_recebidos = ler_aba("sacramentos_recebidos")
        bat_ano, euc_ano, cri_ano = 0, 0, 0
        if not df_recebidos.empty:
            try:
                df_recebidos['data_dt'] = pd.to_datetime(df_recebidos['data'], errors='coerce')
                df_2026 = df_recebidos[df_recebidos['data_dt'].dt.year == 2026]
                bat_ano = len(df_2026[df_2026['tipo'].str.upper().str.contains('BATISMO')])
                euc_ano = len(df_2026[df_2026['tipo'].str.upper().str.contains('EUCARISTIA')])
                cri_ano = len(df_2026[df_2026['tipo'].str.upper().str.contains('CRISMA')])
            except: pass

        st.markdown(f"""
            <div style='background-color:#f8f9f0; padding:20px; border-radius:10px; border:1px solid #e03d11; text-align:center; margin-bottom:20px;'>
                <h3 style='margin:0; color:#e03d11;'>🕊️ Frutos da Evangelização 2026</h3>
                <p style='font-size:16px; color:#666; margin-bottom:15px;'>Sacramentos celebrados e registrados este ano:</p>
                <div style='display: flex; justify-content: space-around;'>
                    <div><b style='font-size:20px; color:#417b99;'>{bat_ano}</b><br><small>Batismos</small></div>
                    <div><b style='font-size:20px; color:#417b99;'>{euc_ano}</b><br><small>Eucaristias</small></div>
                    <div><b style='font-size:20px; color:#417b99;'>{cri_ano}</b><br><small>Crismas</small></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if not df_cat.empty:
            df_censo = df_cat.copy()
            df_censo['idade_real'] = df_censo['data_nascimento'].apply(calcular_idade)
            df_kids = df_censo[df_censo['idade_real'] < 18]
            df_adults = df_censo[df_censo['idade_real'] >= 18]
            
            st.subheader("📊 Censo Sacramental: Infantil / Juvenil")
            c1, c2, c3 = st.columns(3)
            with c1:
                total_k = len(df_kids)
                k_bat = len(df_kids[df_kids['batizado_sn'].str.upper() == 'SIM'])
                perc_k_bat = (k_bat / total_k * 100) if total_k > 0 else 0
                st.metric("Batizados", f"{k_bat} / {total_k}", f"{perc_k_bat:.1f}%")
            with c2:
                k_euc = df_kids['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
                perc_k_euc = (k_euc / total_k * 100) if total_k > 0 else 0
                st.metric("1ª Eucaristia", f"{k_euc} / {total_k}", f"{perc_k_euc:.1f}%")
            with c3:
                k_cri = df_kids['sacramentos_ja_feitos'].str.contains("CRISMA", na=False).sum()
                perc_k_cri = (k_cri / total_k * 100) if total_k > 0 else 0
                st.metric("Crismados", f"{k_cri} / {total_k}", f"{perc_k_cri:.1f}%")

            st.markdown("---")
            st.subheader("📊 Censo Sacramental: Adultos")
            a1, a2, a3 = st.columns(3)
            with a1:
                total_a = len(df_adults)
                a_bat = len(df_adults[df_adults['batizado_sn'].str.upper() == 'SIM'])
                perc_a_bat = (a_bat / total_a * 100) if total_a > 0 else 0
                st.metric("Batizados", f"{a_bat} / {total_a}", f"{perc_a_bat:.1f}%")
            with a2:
                a_euc = df_adults['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
                perc_a_euc = (a_euc / total_a * 100) if total_a > 0 else 0
                st.metric("Eucaristia", f"{a_euc} / {total_a}", f"{perc_a_euc:.1f}%")
            with a3:
                a_cri = df_adults['sacramentos_ja_feitos'].str.contains("CRISMA", na=False).sum()
                perc_a_cri = (a_cri / total_a * 100) if total_a > 0 else 0
                st.metric("Crismados", f"{a_cri} / {total_a}", f"{perc_a_cri:.1f}%")
        else:
            st.warning("Base de catequizandos vazia.")

        st.divider()
        st.subheader("🏫 Auditoria de Pendências por Turma")
        st.caption("Abaixo são listados apenas os catequizandos que possuem pendências sacramentais para sua etapa.")
        
        if not df_turmas.empty:
            for _, t in df_turmas.iterrows():
                nome_t = str(t['nome_turma']).strip().upper()
                etapa_base = str(t['etapa']).strip().upper()
                alunos_t = df_cat[df_cat['etapa'].str.strip().str.upper() == nome_t] if not df_cat.empty else pd.DataFrame()
                
                if not alunos_t.empty:
                    is_avancado_ou_adulto = any(x in etapa_base for x in ["3ª", "TERCEIRA", "ADULTO"])
                    pend_bat = alunos_t[alunos_t['batizado_sn'] != "SIM"]
                    pend_euc = pd.DataFrame()
                    pend_cri = pd.DataFrame()
                    
                    if is_avancado_ou_adulto:
                        pend_euc = alunos_t[~alunos_t['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False, case=False)]
                        pend_cri = alunos_t[~alunos_t['sacramentos_ja_feitos'].str.contains("CRISMA", na=False, case=False)]
                    
                    tem_pendencia = not pend_bat.empty or not pend_euc.empty or not pend_cri.empty
                    
                    if tem_pendencia:
                        with st.expander(f"🚨 {nome_t} ({etapa_base}) - Pendências Identificadas"):
                            cols_p = st.columns(3 if is_avancado_ou_adulto else 1)
                            with cols_p[0]:
                                st.markdown("**🕊️ Falta Batismo**")
                                if not pend_bat.empty:
                                    for n in pend_bat['nome_completo'].tolist(): st.markdown(f"<span style='color:#e03d11;'>❌ {n}</span>", unsafe_allow_html=True)
                                else: st.success("Tudo OK")
                            
                            if is_avancado_ou_adulto:
                                with cols_p[1]:
                                    st.markdown("**🍞 Falta Eucaristia**")
                                    if not pend_euc.empty:
                                        for n in pend_euc['nome_completo'].tolist(): st.markdown(f"<span style='color:#e03d11;'>❌ {n}</span>", unsafe_allow_html=True)
                                    else: st.success("Tudo OK")
                                        
                                with cols_p[2]:
                                    st.markdown("**🔥 Falta Crisma**")
                                    if not pend_cri.empty:
                                        for n in pend_cri['nome_completo'].tolist(): st.markdown(f"<span style='color:#e03d11;'>❌ {n}</span>", unsafe_allow_html=True)
                                    else: st.success("Tudo OK")
                    else:
                        st.markdown(f"<small style='color:green;'>✅ {nome_t}: Todos os sacramentos em dia.</small>", unsafe_allow_html=True)

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
            if st.button("✨ GERAR AUDITORIA PASTORAL COMPLETA", key="btn_disparar_ia_sac", use_container_width=True):
                with st.spinner("O Auditor IA está analisando impedimentos..."):
                    analise_detalhada_ia = []
                    for _, t in df_turmas.iterrows():
                        nome_t = str(t['nome_turma']).strip().upper()
                        alunos_t = df_cat[(df_cat['etapa'] == nome_t) & (df_cat['status'] == 'ATIVO')]
                        if not alunos_t.empty:
                            pend_bat = len(alunos_t[alunos_t['batizado_sn'] != "SIM"])
                            imp_count = len(alunos_t[(("3ª" in str(t['etapa'])) | ("ADULTO" in str(t['etapa']).upper())) & (alunos_t['batizado_sn'] != "SIM")])
                            analise_detalhada_ia.append({
                                "turma": nome_t, "etapa": t['etapa'], "batizados": len(alunos_t) - pend_bat, 
                                "pendentes": pend_bat, "impedimentos_civel": imp_count
                            })
                    
                    impedimentos_detalhados = []
                    for _, cat in df_cat[df_cat['status'] == 'ATIVO'].iterrows():
                        if ("3ª" in str(cat['etapa']) or "ADULTO" in str(cat['etapa']).upper()) and cat['batizado_sn'] != "SIM":
                            impedimentos_detalhados.append({"nome": cat['nome_completo'], "turma": cat['etapa'], "motivo": "Falta Batismo (Impedimento de Iniciação)"})
                    
                    resumo_ia = str({"turmas": analise_detalhada_ia, "impedimentos": impedimentos_detalhados})
                    analise_ia_sac = gerar_relatorio_sacramentos_ia(resumo_ia)
                    
                    st.session_state.pdf_sac_tecnico = gerar_relatorio_sacramentos_tecnico_pdf(analise_detalhada_ia, impedimentos_detalhados, analise_ia_sac)
                    st.rerun()

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
        st.subheader("📜 Histórico e Auditoria de Eventos")
        df_eventos = ler_aba("sacramentos_eventos")
        
        if not df_eventos.empty:
            st.markdown("#### 🔍 Filtrar Registros")
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            
            filtro_tipo = c1.selectbox("Sacramento:", ["TODOS", "BATISMO", "EUCARISTIA", "CRISMA"], key="f_sac")
            
            df_eventos['data_dt'] = pd.to_datetime(df_eventos['data'], errors='coerce')
            anos_disp = sorted(df_eventos['data_dt'].dt.year.dropna().unique().astype(int), reverse=True)
            filtro_ano = c2.selectbox("Ano:", ["TODOS"] + [str(a) for a in anos_disp], key="f_ano")
            
            meses_br = {
                "TODOS": "TODOS", "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
                "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto", "09": "Setembro",
                "10": "Outubro", "11": "Novembro", "12": "Dezembro"
            }
            filtro_mes = c3.selectbox("Mês:", list(meses_br.values()), key="f_mes")
            
            df_f = df_eventos.copy()
            if filtro_tipo != "TODOS": df_f = df_f[df_f['tipo'] == filtro_tipo]
            if filtro_ano != "TODOS": df_f = df_f[df_f['data_dt'].dt.year == int(filtro_ano)]
            if filtro_mes != "TODOS":
                mes_num = [k for k, v in meses_br.items() if v == filtro_mes][0]
                df_f = df_f[df_f['data_dt'].dt.strftime('%m') == mes_num]

            st.dataframe(df_f[['id_evento', 'tipo', 'data', 'turmas', 'catequista']].sort_values(by='data', ascending=False), use_container_width=True, hide_index=True)

            st.divider()
            with st.expander("✏️ Editar Registro de Evento"):
                st.info("Selecione um evento pelo ID para corrigir a data ou o tipo.")
                id_para_editar = st.selectbox("Selecione o ID do Evento:", [""] + df_f['id_evento'].tolist())
                
                if id_para_editar:
                    dados_atuais = df_eventos[df_eventos['id_evento'] == id_para_editar].iloc[0]
                    with st.form("form_edit_sac_evento"):
                        col_e1, col_e2 = st.columns(2)
                        ed_tipo = col_e1.selectbox("Tipo de Sacramento", ["BATISMO", "EUCARISTIA", "CRISMA"], index=["BATISMO", "EUCARISTIA", "CRISMA"].index(dados_atuais['tipo']))
                        ed_data = col_e2.date_input("Data Correta", value=pd.to_datetime(dados_atuais['data']).date())
                        ed_turmas = st.text_input("Turmas (Nomes separados por vírgula)", value=dados_atuais['turmas'])
                        
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            from database import atualizar_evento_sacramento
                            novos_dados = [id_para_editar, ed_tipo, str(ed_data), ed_turmas, dados_atuais['catequista']]
                            if atualizar_evento_sacramento(id_para_editar, novos_dados):
                                st.success("✅ Evento atualizado com sucesso!"); time.sleep(1); st.rerun()
                            else: st.error("❌ Erro ao atualizar. Verifique a conexão.")
        else:
            st.info("Nenhum evento registrado no histórico.")

# ==============================================================================
# PÁGINA: ✅ CHAMADA INTELIGENTE (MOBILE-FIRST)
# ==============================================================================
elif menu == "✅ Fazer Chamada":
    st.title("✅ Chamada Inteligente")

    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    if eh_gestor or vinculo_raw == "TODAS":
        turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
    else:
        turmas_permitidas = [t.strip() for t in vinculo_raw.split(',') if t.strip()]

    if not turmas_permitidas:
        st.error("❌ Você não possui turmas vinculadas."); st.stop()

    with st.container():
        c1, c2 = st.columns([1, 1])
        turma_sel = c1.selectbox("📋 Selecione a Turma:", turmas_permitidas, key="sel_t_chamada")
        data_enc = c2.date_input("📅 Data do Encontro:", date.today(), format="DD/MM/YYYY")

    df_cron_c = ler_aba("cronograma")
    sugestao_tema = ""
    if not df_cron_c.empty:
        filtro_cron = df_cron_c[(df_cron_c['etapa'] == turma_sel) & (df_cron_c.get('status', '') != 'REALIZADO')]
        if not filtro_cron.empty:
            sugestao_tema = filtro_cron.iloc[0]['titulo_tema']
            st.info(f"💡 **Sugestão do Cronograma:** {sugestao_tema}")
            if st.button(f"📌 Usar: {sugestao_tema}", use_container_width=True):
                st.session_state[f"tema_input_{turma_sel}"] = sugestao_tema

    tema_dia = st.text_input("📖 Tema do Encontro (Obrigatório):", 
                             value=st.session_state.get(f"tema_input_{turma_sel}", ""), 
                             key=f"tema_field_{turma_sel}", help="Digite o tema para liberar o botão de salvar.").upper()

    lista_cat = df_cat[(df_cat['etapa'] == turma_sel) & (df_cat['status'] == 'ATIVO')].sort_values('nome_completo')
    
    if lista_cat.empty:
        st.warning(f"Nenhum catequizando ativo na turma {turma_sel}.")
    else:
        st.divider()
        if st.button("✅ Marcar Todos como Presentes", use_container_width=True):
            for _, r in lista_cat.iterrows():
                st.session_state[f"p_{r['id_catequizando']}_{data_enc}"] = True
        
        st.markdown("---")
        
        registros_presenca = []
        contador_p = 0
        contador_a = 0
        contador_niver = 0

        st.markdown("""
            <style>
            .card-niver { border-left: 8px solid #ffa000 !important; background-color: #fff9e6 !important; }
            </style>
        """, unsafe_allow_html=True)

        for _, row in lista_cat.iterrows():
            is_niver = eh_aniversariante_da_semana(row['data_nascimento'])
            if is_niver: contador_niver += 1
            
            with st.container():
                col_info, col_check = st.columns([3, 1])
                with col_info:
                    niver_tag = "🎂 <b>NIVER!</b> " if is_niver else ""
                    st.markdown(f"{niver_tag}{row['nome_completo']}", unsafe_allow_html=True)
                    if is_niver:
                        if st.button(f"🎨 Card Parabéns", key=f"btn_niver_{row['id_catequizando']}"):
                            card_img = gerar_card_aniversario(f"{data_enc.day} | CATEQUIZANDO | {row['nome_completo']}", tipo="DIA")
                            if card_img: st.image(card_img, width=150)

                with col_check:
                    presente = st.toggle("P", key=f"p_{row['id_catequizando']}_{data_enc}")
                    if presente: contador_p += 1
                    else: contador_a += 1

                registros_presenca.append([
                    str(data_enc), row['id_catequizando'], row['nome_completo'], 
                    turma_sel, "PRESENTE" if presente else "AUSENTE", 
                    tema_dia, st.session_state.usuario['nome']
                ])
            st.markdown("---")

        st.subheader("📊 Resumo da Chamada")
        c_res1, c_res2, c_res3 = st.columns(3)
        c_res1.metric("✅ Presentes", contador_p)
        c_res2.metric("❌ Ausentes", contador_a)
        c_res3.metric("🎂 Aniversariantes", contador_niver)

        if st.button("🚀 FINALIZAR CHAMADA E SALVAR", use_container_width=True, type="primary", disabled=not tema_dia):
            if salvar_presencas(registros_presenca):
                if tema_dia == sugestao_tema:
                    from database import marcar_tema_realizado_cronograma
                    marcar_tema_realizado_cronograma(turma_sel, tema_dia)
                st.success(f"✅ Chamada de {turma_sel} salva com sucesso!"); st.balloons()
                st.cache_data.clear(); time.sleep(1); st.rerun()
        
        if not tema_dia:
            st.warning("⚠️ O botão de salvar será liberado após preencher o Tema do Encontro.")

# ==============================================================================
# PÁGINA: 👥 GESTÃO DE CATEQUISTAS
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
                status_data.append({"Nome": row['nome'], "Status": status, "Anos de Missão": anos, "Turmas": row['turma_vinculada']})
            
            df_status = pd.DataFrame(status_data)
            c_apt, c_cam = st.columns(2)
            with c_apt:
                st.success("**✅ Aptos / Ministros de Catequese**")
                st.dataframe(df_status[df_status['Status'].isin(['MINISTRO', 'APTO'])], use_container_width=True, hide_index=True)
            with c_cam:
                st.warning("**⏳ Em Caminhada de Formação**")
                st.dataframe(df_status[df_status['Status'] == 'EM_CAMINHADA'], use_container_width=True, hide_index=True)

            if st.button("🗂️ GERAR DOSSIÊ COMPLETO DA EQUIPE (PDF)"):
                st.session_state.pdf_lote_equipe = gerar_fichas_catequistas_lote(equipe_tecnica, df_pres_form, df_formacoes)
            if "pdf_lote_equipe" in st.session_state:
                st.download_button("📥 BAIXAR DOSSIÊ DA EQUIPE", st.session_state.pdf_lote_equipe, "Dossie_Equipe_Catequetica.pdf", use_container_width=True)
        else:
            st.info("Nenhum catequista cadastrado.")

    with tab_lista:
        st.subheader("📋 Relação e Perfil Individual")
        if not equipe_tecnica.empty:
            busca_c = st.text_input("🔍 Pesquisar catequista:", key="busca_cat").upper()
            df_c_filtrado = equipe_tecnica[equipe_tecnica['nome'].str.contains(busca_c, na=False)] if busca_c else equipe_tecnica
            st.dataframe(df_c_filtrado[['nome', 'email', 'turma_vinculada', 'papel']], use_container_width=True, hide_index=True)
            
            st.divider()
            escolha_c = st.selectbox("Selecione para ver Perfil ou Editar:", [""] + df_c_filtrado['nome'].tolist(), key="sel_cat")
            
            if escolha_c:
                u = equipe_tecnica[equipe_tecnica['nome'] == escolha_c].iloc[0]
                col_perfil, col_edit = st.tabs(["👤 Perfil e Ficha", "✏️ Editar Cadastro"])
                
                with col_perfil:
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"### {u['nome']}")
                        st.write(f"**E-mail:** {u['email']}")
                        st.write(f"**Telefone:** {u.get('telefone', 'N/A')}")
                        st.warning(f"🚨 **EMERGÊNCIA:** {u.iloc[12] if len(u) > 12 else 'Não cadastrado'}")
                        st.write(f"**Nascimento:** {formatar_data_br(u.get('data_nascimento', ''))}")
                        st.write(f"**Turmas:** {u['turma_vinculada']}")
                    with c2:
                        if st.button(f"📄 Gerar Ficha PDF"):
                            st.session_state.pdf_catequista = gerar_ficha_catequista_pdf(u.to_dict(), pd.DataFrame())
                        if "pdf_catequista" in st.session_state:
                            st.download_button("📥 Baixar Ficha", st.session_state.pdf_catequista, f"Ficha_{escolha_c}.pdf")

                with col_edit:
                    hoje = date.today()
                    d_min, d_max = date(1920, 1, 1), date(2050, 12, 31)

                    def converter_ou_none(valor):
                        if pd.isna(valor) or str(valor).strip() in ["", "N/A", "None"]: return None
                        try: return converter_para_data(valor)
                        except: return None

                    val_nasc = converter_ou_none(u.get('data_nascimento', '')) or hoje
                    val_ini = converter_ou_none(u.get('data_inicio_catequese', '')) or hoje
                    val_bat = converter_ou_none(u.get('data_batismo', ''))
                    val_euc = converter_ou_none(u.get('data_eucaristia', ''))
                    val_cri = converter_ou_none(u.get('data_crisma', ''))
                    val_min = converter_ou_none(u.get('data_ministerio', ''))
                    
                    # CORREÇÃO 1: O índice correto para Emergência é 13 (Coluna N). O 12 (Coluna M) é o UUID de segurança.
                    val_emerg = u.iloc[13] if len(u) > 13 else ""

                    with st.form(f"form_edit_cat_{u['email']}"):
                        st.markdown("#### 📍 Dados Cadastrais e Emergência")
                        c1, c2 = st.columns(2)
                        ed_nome = c1.text_input("Nome Completo", value=str(u.get('nome', ''))).upper()
                        ed_senha = c2.text_input("Senha de Acesso", value=str(u.get('senha', '')), type="password")
                        
                        c3, c4 = st.columns(2)
                        ed_tel = c3.text_input("Telefone / WhatsApp", value=str(u.get('telefone', '')))
                        ed_emergencia = c4.text_input("🚨 Contato de Emergência (Nome e Tel)", value=val_emerg).upper()
                        
                        c5, c6 = st.columns(2)
                        ed_papel = c5.selectbox("Papel",["CATEQUISTA", "COORDENADOR", "ADMIN"], index=["CATEQUISTA", "COORDENADOR", "ADMIN"].index(str(u.get('papel', 'CATEQUISTA')).upper()))
                        ed_nasc = c6.date_input("Data de Nascimento", value=val_nasc, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                        
                        lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else[]
                        ed_turmas = st.multiselect("Vincular às Turmas:", lista_t_nomes, default=[t.strip() for t in str(u.get('turma_vinculada', '')).split(",") if t.strip() in lista_t_nomes])
                        
                        st.divider()
                        st.markdown("#### ⛪ Itinerário Sacramental (Marque apenas se possuir)")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            has_ini = st.checkbox("Início na Catequese", value=True)
                            dt_ini = st.date_input("Data Início", value=val_ini, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_ini)
                        with col2:
                            has_bat = st.checkbox("Possui Batismo?", value=(val_bat is not None))
                            dt_bat = st.date_input("Data Batismo", value=val_bat if val_bat else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_bat)
                        with col3:
                            has_euc = st.checkbox("Possui 1ª Eucaristia?", value=(val_euc is not None))
                            dt_euc = st.date_input("Data Eucaristia", value=val_euc if val_euc else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_euc)

                        col4, col5 = st.columns(2)
                        with col4:
                            has_cri = st.checkbox("Possui Crisma?", value=(val_cri is not None))
                            dt_cri = st.date_input("Data Crisma", value=val_cri if val_cri else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_cri)
                        with col5:
                            has_min = st.checkbox("É Ministro de Catequese?", value=(val_min is not None))
                            dt_min = st.date_input("Data Ministério", value=val_min if val_min else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_min)

                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES E SINCRONIZAR"):
                            # CORREÇÃO 2: Converter as datas para string e respeitar os checkboxes
                            str_ini = str(dt_ini) if has_ini else ""
                            str_bat = str(dt_bat) if has_bat else ""
                            str_euc = str(dt_euc) if has_euc else ""
                            str_cri = str(dt_cri) if has_cri else ""
                            str_min = str(dt_min) if has_min else ""

                            dados_up = [
                                ed_nome, u['email'], ed_senha, ed_papel, ", ".join(ed_turmas), 
                                ed_tel, str(ed_nasc), str_ini, str_bat, str_euc, str_cri, str_min, 
                                str(u.iloc[12]) if len(u) > 12 else "", ed_emergencia
                            ]
                            if atualizar_usuario(u['email'], dados_up):
                                st.success("✅ Cadastro atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    with tab_novo:
        st.subheader("➕ Criar Novo Acesso para Equipe")
        with st.form("form_novo_cat", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_nome = c1.text_input("Nome Completo (EM MAIÚSCULAS)").upper()
            n_email = c2.text_input("E-mail (Login)")
            
            c3, c4, c5 = st.columns(3)
            n_senha = c3.text_input("Senha Inicial", type="password")
            n_tel = c4.text_input("Telefone / WhatsApp")
            n_nasc = c5.date_input("Data de Nascimento", value=date(1990, 1, 1), min_value=date(1930, 1, 1), max_value=date(2011, 12, 31), format="DD/MM/YYYY")
            
            c_papel, c_emerg = st.columns(2)
            n_papel = c_papel.selectbox("Papel / Nível de Acesso", ["CATEQUISTA", "COORDENADOR", "ADMIN"])
            n_emergencia = c_emerg.text_input("🚨 Contato de Emergência (Nome e Tel)")
            
            lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else []
            n_turmas = st.multiselect("Vincular às Turmas:", lista_t_nomes)
            
            if st.form_submit_button("🚀 CRIAR ACESSO E DEFINIR PERMISSÕES"):
                if n_nome and n_email and n_senha:
                    with st.spinner("Criando novo acesso..."):
                        novo_user_lista = [
                            n_nome, n_email, n_senha, n_papel, ", ".join(n_turmas), 
                            n_tel, str(n_nasc), "", "", "", "", "", "", n_emergencia
                        ]
                        from database import adicionar_novo_usuario
                        if adicionar_novo_usuario(novo_user_lista):
                            try:
                                planilha = conectar_google_sheets()
                                if n_turmas:
                                    aba_t = planilha.worksheet("turmas")
                                    for t_nome in n_turmas:
                                        cel_t = aba_t.find(t_nome)
                                        if cel_t:
                                            v_atual = aba_t.cell(cel_t.row, 5).value or ""
                                            nova_v = f"{v_atual}, {n_nome}".strip(", ")
                                            aba_t.update_cell(cel_t.row, 5, nova_v)
                            except: pass
                            st.success(f"✅ {n_nome} cadastrado com sucesso!"); st.balloons(); time.sleep(1); st.rerun()
                else:
                    st.warning("⚠️ Nome, E-mail e Senha são obrigatórios.")

    with tab_formacao:
        st.subheader("🎓 Itinerário de Formação Continuada")
        
        if not df_formacoes.empty:
            if 'status' in df_formacoes.columns: col_status = 'status'
            elif 'col_5' in df_formacoes.columns: col_status = 'col_5'
            else: col_status = df_formacoes.columns[5] if len(df_formacoes.columns) > 5 else None
        else: col_status = None

        sub_tab_plan, sub_tab_valida, sub_tab_hist = st.tabs(["📅 Planejar Formação", "✅ Validar Presença", "📜 Histórico e Edição"])

        with sub_tab_plan:
            with st.form("form_plan_formacao", clear_on_submit=True):
                f_tema = st.text_input("Tema da Formação").upper()
                c1, c2 = st.columns(2)
                f_data = c1.date_input("Data Prevista", value=date.today())
                f_formador = c2.text_input("Quem irá ministrar? (Formador)").upper()
                f_local = st.text_input("Local / Sala").upper()
                
                if st.form_submit_button("📌 AGENDAR FORMAÇÃO"):
                    if f_tema:
                        id_f = f"FOR-{int(time.time())}"
                        if salvar_formacao([id_f, f_tema, str(f_data), f_formador, f_local, "PENDENTE"]):
                            st.success(f"Formação '{f_tema}' agendada!"); st.cache_data.clear(); time.sleep(1); st.rerun()

        with sub_tab_valida:
            df_f_pendentes = pd.DataFrame()
            if col_status and not df_formacoes.empty:
                df_f_pendentes = df_formacoes[df_formacoes[col_status].str.upper() == "PENDENTE"]
            
            if df_f_pendentes.empty:
                st.info("Não há formações pendentes de validação.")
            else:
                st.warning("Selecione a formação realizada e marque os catequistas presentes.")
                escolha_f = st.selectbox("Formação para dar Baixa:", df_f_pendentes['tema'].tolist())
                dados_f = df_f_pendentes[df_f_pendentes['tema'] == escolha_f].iloc[0]
                
                st.divider()
                st.markdown(f"### Lista de Presença: {escolha_f}")
                
                dict_equipe = dict(zip(equipe_tecnica['nome'], equipe_tecnica['email']))
                selecionados = []
                
                cols = st.columns(2)
                for i, (nome, email) in enumerate(dict_equipe.items()):
                    with cols[i % 2]:
                        if st.checkbox(nome, key=f"pres_f_{dados_f['id_formacao']}_{email}"):
                            selecionados.append(email)
                
                if st.button("💾 FINALIZAR E REGISTRAR PRESENÇAS", use_container_width=True):
                    if selecionados:
                        lista_p = [[dados_f['id_formacao'], email] for email in selecionados]
                        if salvar_presenca_formacao(lista_p):
                            nova_lista_f = [dados_f['id_formacao'], dados_f['tema'], dados_f['data'], dados_f['formador'], dados_f['local'], "CONCLUIDA"]
                            from database import atualizar_formacao
                            atualizar_formacao(dados_f['id_formacao'], nova_lista_f)
                            st.success("Presenças registradas!"); st.balloons(); st.cache_data.clear(); time.sleep(1); st.rerun()
                    else:
                        st.error("Selecione ao menos um catequista.")

        with sub_tab_hist:
            if not df_formacoes.empty:
                st.markdown("#### 🔍 Consultar e Corrigir")
                df_formacoes['data_dt'] = pd.to_datetime(df_formacoes['data'], errors='coerce')
                anos = sorted(df_formacoes['data_dt'].dt.year.dropna().unique().astype(int), reverse=True)
                ano_sel = st.selectbox("Filtrar por Ano:", ["TODOS"] + [str(a) for a in anos])
                
                df_hist = df_formacoes.copy()
                if ano_sel != "TODOS": df_hist = df_hist[df_hist['data_dt'].dt.year == int(ano_sel)]
                
                cols_view = ['tema', 'data', 'formador', 'local']
                if col_status in df_hist.columns: cols_view.append(col_status)
                
                st.dataframe(df_hist[cols_view], use_container_width=True, hide_index=True)
                
                st.divider()
                with st.expander("✏️ Editar ou Excluir Formação"):
                    f_para_editar = st.selectbox("Selecione a Formação:", [""] + df_hist['tema'].tolist())
                    if f_para_editar:
                        d_edit = df_hist[df_hist['tema'] == f_para_editar].iloc[0]
                        with st.form("form_edit_f_real"):
                            ed_tema = st.text_input("Tema", value=d_edit['tema']).upper()
                            ed_data = st.date_input("Data", value=pd.to_datetime(d_edit['data']).date())
                            ed_formador = st.text_input("Formador", value=d_edit['formador']).upper()
                            ed_local = st.text_input("Local", value=d_edit['local']).upper()
                            
                            status_atual_val = str(d_edit[col_status]).upper() if col_status else "PENDENTE"
                            ed_status = st.selectbox("Status", ["PENDENTE", "CONCLUIDA"], index=0 if status_atual_val == "PENDENTE" else 1)
                            
                            c_btn1, c_btn2 = st.columns([3, 1])
                            if c_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                                from database import atualizar_formacao
                                if atualizar_formacao(d_edit['id_formacao'], [d_edit['id_formacao'], ed_tema, str(ed_data), ed_formador, ed_local, ed_status]):
                                    st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            
                            # Trava de Exclusão
                            st.markdown("---")
                            confirma_del = st.checkbox("Confirmo a exclusão desta formação")
                            if c_btn2.form_submit_button("🗑️ EXCLUIR", use_container_width=True):
                                if confirma_del:
                                    from database import excluir_formacao_completa
                                    if excluir_formacao_completa(d_edit['id_formacao']):
                                        st.success("Excluído!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                                else:
                                    st.error("Marque a caixa de confirmação para excluir.")
            else:
                st.info("Nenhuma formação registrada.")

# ==============================================================================
# PÁGINA: 👨‍👩‍👧‍👦 GESTÃO FAMILIAR
# ==============================================================================
elif menu == "👨‍👩‍👧‍👦 Gestão Familiar":
    st.title("👨‍👩‍👧‍👦 Gestão da Igreja Doméstica")
    
    def limpar_wa(tel):
        if not tel or str(tel).strip() in ["N/A", "", "None"]: return None
        num = "".join(filter(str.isdigit, str(tel)))
        if num.startswith("0"): num = num[1:]
        return f"5573{num}" if len(num) <= 9 else f"55{num}"

    def buscar_irmaos(nome_mae, nome_pai, id_atual):
        if df_cat.empty: return []
        irmaos = df_cat[(((df_cat['nome_mae'] == nome_mae) & (nome_mae != "N/A")) | 
                         ((df_cat['nome_pai'] == nome_pai) & (nome_pai != "N/A"))) & 
                        (df_cat['id_catequizando'] != id_atual)]
        return irmaos[['nome_completo', 'etapa']].to_dict('records')

    if eh_gestor:
        tab_reunioes, tab_censo, tab_agenda, tab_visitas, tab_ia = st.tabs([
            "📅 Reuniões de Pais", "📊 Censo Familiar", "📞 Agenda Geral", "🏠 Visitas", "✨ IA"
        ])

        with tab_reunioes:
            st.subheader("📅 Ciclo de Encontros com as Famílias")
            sub_r1, sub_r2, sub_r3, sub_r4 = st.tabs([
                "➕ Agendar", "📄 Lista Física (PDF)", "✅ Validar Presença (Digital)", "📜 Histórico e Edição"
            ])
            
            with sub_r1:
                with st.form("form_plan_reuniao", clear_on_submit=True):
                    r_tema = st.text_input("Tema da Reunião").upper()
                    c_r1, c_r2 = st.columns(2)
                    r_data = c_r1.date_input("Data Prevista", value=date.today(), format="DD/MM/YYYY")
                    r_turma = c_r2.selectbox("Turma Alvo", ["GERAL (TODAS)"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else []))
                    r_local = st.text_input("Local (Ex: Salão Paroquial)").upper()
                    if st.form_submit_button("📌 AGENDAR REUNIÃO"):
                        if r_tema:
                            if salvar_reuniao_pais([f"REU-{int(time.time())}", r_tema, str(r_data), r_turma, r_local, "PENDENTE"]):
                                st.success("Reunião agendada com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()

            with sub_r2:
                df_reunioes_v = ler_aba("reunioes_pais")
                if not df_reunioes_v.empty:
                    sel_r_pdf = st.selectbox("Selecione a Reunião para gerar PDF:", df_reunioes_v.iloc[:, 1].tolist(), key="sel_r_pdf")
                    dados_r = df_reunioes_v[df_reunioes_v.iloc[:, 1] == sel_r_pdf].iloc[0]
                    if st.button("📄 GERAR LISTA DE ASSINATURA (PDF)"):
                        t_alvo = dados_r.iloc[3]
                        df_f_lista = df_cat[df_cat['status'] == 'ATIVO']
                        if t_alvo != "GERAL (TODAS)": df_f_lista = df_f_lista[df_f_lista['etapa'] == t_alvo]
                        lista_pdf = [{'nome_cat': r['nome_completo'], 'responsavel': r['nome_responsavel']} for _, r in df_f_lista.iterrows()]
                        pdf_out = gerar_lista_assinatura_reuniao_pdf(dados_r.iloc[1], dados_r.iloc[2], dados_r.iloc[4], t_alvo, lista_pdf)
                        st.download_button("📥 Baixar Lista para Impressão", pdf_out, f"Lista_{sel_r_pdf}.pdf")
                else: st.info("Nenhuma reunião agendada.")

            with sub_r3:
                if not df_reunioes_v.empty:
                    sel_r_pres = st.selectbox("Selecione a Reunião para Chamada Digital:", df_reunioes_v.iloc[:, 1].tolist(), key="sel_r_pres")
                    dados_r_pres = df_reunioes_v[df_reunioes_v.iloc[:, 1] == sel_r_pres].iloc[0]
                    id_reuniao = dados_r_pres.iloc[0]
                    t_alvo_pres = dados_r_pres.iloc[3]

                    df_fam_pres = df_cat[df_cat['status'] == 'ATIVO']
                    if t_alvo_pres != "GERAL (TODAS)": df_fam_pres = df_fam_pres[df_fam_pres['etapa'] == t_alvo_pres]
                    
                    st.info(f"📋 Registrando presença para: {sel_r_pres}")
                    with st.form(f"form_pres_reu_{id_reuniao}"):
                        lista_presenca_reu = []
                        for _, r in df_fam_pres.sort_values('nome_completo').iterrows():
                            col_n, col_c = st.columns([3, 1])
                            col_n.write(f"**{r['nome_completo']}** (Resp: {r['nome_responsavel']})")
                            presente = col_c.toggle("Presente", key=f"reu_p_{id_reuniao}_{r['id_catequizando']}")
                            lista_presenca_reu.append([id_reuniao, r['id_catequizando'], r['nome_completo'], t_alvo_pres, "PRESENTE" if presente else "AUSENTE", str(date.today())])
                        
                        if st.form_submit_button("💾 SALVAR PRESENÇAS NO BANCO"):
                            if salvar_presenca_reuniao_pais(lista_presenca_reu):
                                novos_dados_reu = list(dados_r_pres); novos_dados_reu[5] = "CONCLUIDA"
                                atualizar_reuniao_pais(id_reuniao, novos_dados_reu)
                                st.success("Presenças registradas!"); st.balloons(); time.sleep(1); st.rerun()
                else: st.info("Nenhuma reunião para validar.")

            with sub_r4:
                if not df_reunioes_v.empty:
                    st.write("### ✏️ Editar Dados da Reunião")
                    sel_r_edit = st.selectbox("Selecione para alterar:", [""] + df_reunioes_v.iloc[:, 1].tolist(), key="sel_r_edit")
                    if sel_r_edit:
                        d_edit = df_reunioes_v[df_reunioes_v.iloc[:, 1] == sel_r_edit].iloc[0]
                        with st.form(f"form_edit_reu_{d_edit.iloc[0]}"):
                            ed_tema = st.text_input("Tema", value=d_edit.iloc[1]).upper()
                            ed_data = st.date_input("Data", value=converter_para_data(d_edit.iloc[2]))
                            ed_turma = st.selectbox("Turma", ["GERAL (TODAS)"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else []))
                            ed_local = st.text_input("Local", value=d_edit.iloc[4]).upper()
                            ed_status = st.selectbox("Status", ["PENDENTE", "CONCLUIDA"], index=0 if d_edit.iloc[5] == "PENDENTE" else 1)
                            if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                                if atualizar_reuniao_pais(d_edit.iloc[0], [d_edit.iloc[0], ed_tema, str(ed_data), ed_turma, ed_local, ed_status]):
                                    st.success("Reunião atualizada!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    st.divider()
                    st.write("### 📜 Histórico Geral")
                    st.dataframe(df_reunioes_v, use_container_width=True, hide_index=True)

        with tab_censo:
            st.subheader("📊 Diagnóstico da Igreja Doméstica")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**💍 Situação Matrimonial dos Pais**")
                st.bar_chart(df_cat['est_civil_pais'].value_counts())
            with c2:
                st.markdown("**⛪ Sacramentos dos Pais**")
                sac_series = df_cat['sac_pais'].str.split(', ').explode()
                st.bar_chart(sac_series.value_counts())

        with tab_agenda:
            busca_g = st.text_input("🔍 Pesquisar por nome (Catequizando ou Pais):", key="txt_busca_fam").upper()
            df_age = df_cat[df_cat['nome_completo'].str.contains(busca_g, na=False) | df_cat['nome_mae'].str.contains(busca_g, na=False)] if busca_g else df_cat
            
            for _, row in df_age.iterrows():
                with st.container():
                    st.markdown(f"""
                        <div style='background-color:#f8f9f0; padding:10px; border-radius:10px; border-left:5px solid #417b99; margin-bottom:5px;'>
                            <b style='color:#417b99;'>{row['nome_completo']}</b> | Turma: {row['etapa']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
                    
                    if c_btn1.button("✨ IA: Cobrar Docs", key=f"btn_cob_{row['id_catequizando']}"):
                        nome_alvo = row['nome_mae'] if row['nome_mae'] != "N/A" else row['nome_pai']
                        msg = gerar_mensagem_cobranca_doc_ia(row['nome_completo'], row['doc_em_falta'], row['etapa'], nome_alvo, "Responsável")
                        msg_segura = msg.replace("$", "\$") 
                        st.info(f"**Mensagem de Cobrança:**\n\n{msg_segura}")

                    if c_btn2.button("📝 IA: Atualizar Ficha", key=f"btn_upd_{row['id_catequizando']}"):
                        nome_alvo = row['nome_mae'] if row['nome_mae'] != "N/A" else row['nome_pai']
                        resumo = f"Endereço: {row['endereco_completo']} | Saúde: {row['toma_medicamento_sn']}"
                        msg = gerar_mensagem_atualizacao_cadastral_ia(row['nome_completo'], resumo, nome_alvo)
                        msg_segura = msg.replace("$", "\$")
                        st.info(f"**Mensagem de Atualização:**\n\n{msg_segura}")
                    
                    tel_limpo = limpar_wa(row['contato_principal'])
                    if tel_limpo:
                        c_btn3.markdown(f'''<a href="https://wa.me/{tel_limpo}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; text-align:center; padding:8px; border-radius:5px; font-weight:bold; font-size:12px;">📲 Abrir WhatsApp</div></a>''', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

        with tab_visitas:
            st.subheader("🏠 Acompanhamento Familiar")
            busca_v = st.text_input("Localizar Família para Relato:").upper()
            if busca_v:
                fam = df_cat[df_cat['nome_mae'].str.contains(busca_v, na=False) | df_cat['nome_pai'].str.contains(busca_v, na=False)]
                if not fam.empty:
                    dados_f = fam.iloc[0]
                    st.success(f"✅ Família: {dados_f['nome_mae']} & {dados_f['nome_pai']}")
                    novo_relato = st.text_area("Relato da Visita:", value=dados_f.get('obs_pastoral_familia', ''), height=150)
                    if st.button("💾 SALVAR RELATO"):
                        for _, filho in fam.iterrows():
                            lista_up = filho.tolist()
                            while len(lista_up) < 30: lista_up.append("N/A")
                            lista_up[29] = novo_relato
                            atualizar_catequizando(filho['id_catequizando'], lista_up)
                        st.success("Relato salvo!"); st.cache_data.clear(); time.sleep(1); st.rerun()

        with tab_ia:
            if st.button("🚀 EXECUTAR DIAGNÓSTICO FAMILIAR IA"):
                resumo_fam = str(df_cat['est_civil_pais'].value_counts().to_dict())
                st.info(analisar_saude_familiar_ia(resumo_fam))

    else:
        vinculo = str(st.session_state.usuario.get('turma_vinculada', '')).split(',')[0].strip()
        st.subheader(f"📱 Agenda Pastoral: {vinculo}")
        
        df_minha_fam = df_cat[df_cat['etapa'] == vinculo]
        busca_c = st.text_input("🔍 Buscar na minha turma:").upper()
        if busca_c: df_minha_fam = df_minha_fam[df_minha_fam['nome_completo'].str.contains(busca_c, na=False)]

        for _, row in df_minha_fam.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style='background-color:#ffffff; padding:12px; border-radius:12px; border-left:8px solid #417b99; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom:10px;'>
                        <b style='color:#417b99; font-size:16px;'>{row['nome_completo']}</b><br>
                        <small>Mãe: {row['nome_mae']} | Pai: {row['nome_pai']}</small>
                    </div>
                """, unsafe_allow_html=True)
                
                irmaos = buscar_irmaos(row['nome_mae'], row['nome_pai'], row['id_catequizando'])
                if irmaos:
                    with st.expander("🔗 IRMÃOS NA CATEQUESE"):
                        for ir in irmaos: st.write(f"👦 {ir['nome_completo']} ({ir['etapa']})")

                c1, c2, c3 = st.columns(3)
                lm = limpar_wa(row['tel_mae'])
                if lm: c1.markdown(f'''<a href="https://wa.me/{lm}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366; color:white; text-align:center; padding:8px; border-radius:5px; font-size:11px;">👩‍🦱 MÃE</div></a>''', unsafe_allow_html=True)
                lp = limpar_wa(row['tel_pai'])
                if lp: c2.markdown(f'''<a href="https://wa.me/{lp}" target="_blank" style="text-decoration:none;"><div style="background-color:#128c7e; color:white; text-align:center; padding:8px; border-radius:5px; font-size:11px;">👨‍🦱 PAI</div></a>''', unsafe_allow_html=True)
                
                obs_p = str(row.get('obs_pastoral_familia', ''))
                te = obs_p.split('TEL: ')[-1] if 'TEL: ' in obs_p else None
                le = limpar_wa(te)
                if le: c3.markdown(f'''<a href="https://wa.me/{le}" target="_blank" style="text-decoration:none;"><div style="background-color:#e03d11; color:white; text-align:center; padding:8px; border-radius:5px; font-size:11px;">🚨 EMERG.</div></a>''', unsafe_allow_html=True)
                
                with st.expander("📝 Anotar Visita/Conversa"):
                    with st.form(key=f"f_v_{row['id_catequizando']}"):
                        rel = st.text_area("Relato:", value=row.get('obs_pastoral_familia', ''))
                        if st.form_submit_button("💾 Salvar"):
                            lista_up = row.tolist()
                            while len(lista_up) < 30: lista_up.append("N/A")
                            lista_up[29] = rel
                            atualizar_catequizando(row['id_catequizando'], lista_up)
                            st.success("Salvo!"); st.cache_data.clear(); time.sleep(0.5); st.rerun()

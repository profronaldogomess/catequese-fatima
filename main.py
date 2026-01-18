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

# --- INJEÇÃO DE CSS (CORREÇÃO VISUAL DEFINITIVA) ---
st.markdown("""
    <style>
    /* 1. FORÇAR FUNDO BRANCO GERAL */
    .stApp {
        background-color: #ffffff;
        color: #333333;
    }

    /* 2. FORÇAR CAIXAS DE TEXTO (INPUTS) A SEREM CLARAS E LEGÍVEIS */
    .stTextInput input, .stDateInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #f0f2f6 !important; 
        color: #000000 !important; 
        border: 1px solid #ccc;
    }
    
    /* Corrigir Selectbox (Menu suspenso) */
    div[data-baseweb="select"] > div {
        background-color: #f0f2f6 !important;
        color: #000000 !important;
    }
    
    /* Garante que o texto digitado seja preto */
    input, textarea, select {
        color: black !important;
        -webkit-text-fill-color: black !important;
    }

    /* 3. BARRA LATERAL AZUL */
    [data-testid="stSidebar"] {
        background-color: #417b99;
    }
    [data-testid="stSidebar"] * {
        color: white !important; 
    }

    /* 4. TÍTULOS E ETIQUETAS */
    h1, h2, h3, h4 {
        color: #417b99 !important; 
        font-family: 'Helvetica', sans-serif;
    }
    
    label, .stMarkdown p {
        color: #417b99 !important; 
        font-weight: 600;
    }
    
    p, li {
        color: #333333;
    }

    /* 5. BOTÕES LARANJA */
    div.stButton > button {
        background-color: #e03d11;
        color: white !important;
        border: none;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 20px;
    }
    div.stButton > button:hover {
        background-color: #c0320d;
        color: white !important;
    }
    
    /* 6. MÉTRICAS */
    [data-testid="stMetricValue"] {
        color: #e03d11 !important;
    }
    
    /* Ajuste Mobile */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
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
    gerar_ficha_cadastral_catequizando, gerar_ficha_catequista_pdf, gerar_pdf_perfil_turma,
    gerar_relatorio_diocesano_pdf, gerar_relatorio_pastoral_interno_pdf,
    gerar_relatorio_sacramentos_tecnico_pdf
)
from ai_engine import (
    gerar_analise_pastoral, gerar_mensagem_whatsapp, 
    analisar_turma_local, gerar_relatorio_sacramentos_ia, gerar_relatorio_sacramentos_ia
)

# --- FUNÇÕES AUXILIARES DE LOGO ---
def mostrar_logo_sidebar():
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.sidebar.columns([1, 3, 1])
        with c2:
            st.image("logo.png", width=130)
    else:
        st.sidebar.title("Catequese Fátima")

def mostrar_logo_login():
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    else:
        st.markdown("<h1 style='text-align: center; color: #e03d11;'>✝️</h1>", unsafe_allow_html=True)

# --- CONTROLE DE SESSÃO (LOGIN) ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.container()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        col_vazia, col_conteudo, col_vazia2 = st.columns([0.2, 2, 0.2])
        with col_conteudo:
            st.markdown("<br>", unsafe_allow_html=True)
            mostrar_logo_login()
            st.markdown("<h2 style='text-align: center; color: #417b99;'>Acesso Restrito</h2>", unsafe_allow_html=True)
            
            email_login = st.text_input("E-mail")
            senha_login = st.text_input("Senha", type="password")
            
            st.write("") 
            if st.button("ENTRAR NO SISTEMA", use_container_width=True):
                try:
                    user = verificar_login(email_login, senha_login)
                    if user:
                        st.session_state.logado = True
                        st.session_state.usuario = user
                        st.success(f"Bem-vindo(a), {user['nome']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("🚫 Acesso negado. Verifique suas credenciais.")
                except Exception as e:
                    st.error("⚠️ Erro de conexão. Tente novamente.")
    st.stop() 

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ LOGADO ---

# --- CARREGAMENTO GLOBAL DE DADOS (PREVENÇÃO DE NAMEERROR E REGRESSÃO) ---
df_cat = ler_aba("catequizandos")
df_turmas = ler_aba("turmas")
df_pres = ler_aba("presencas")
df_usuarios = ler_aba("usuarios") 
df_sac_eventos = ler_aba("sacramentos_eventos")

# Filtro de Equipe Global: Remove ADMIN da contagem técnica e evita NameError
equipe_tecnica = df_usuarios[df_usuarios['papel'] != 'ADMIN'] if not df_usuarios.empty else pd.DataFrame()

# --- BARRA LATERAL (SIDEBAR) ---
mostrar_logo_sidebar() 

# 1. Data do Dia
hoje_str = date.today().strftime('%d/%m/%Y')
st.sidebar.markdown(f"📅 **{hoje_str}**")

# 2. Mensagem de Boas Vindas
nome_usuario = st.session_state.usuario['nome']
st.sidebar.success(f"Bem-vindo(a),\n**{nome_usuario}**")

st.sidebar.divider()

# 3. Botões de Ação
if st.sidebar.button("🔄 Atualizar Dados (Limpar Memória)"):
    st.cache_data.clear()
    st.toast("Memória limpa! Os dados foram atualizados.", icon="✅")
    time.sleep(1)
    st.rerun()

if st.sidebar.button("🚪 Sair / Logoff"):
    st.session_state.logado = False
    st.rerun()

# --- IDENTIFICAÇÃO DO PAPEL E TURMA ---
papel_usuario = st.session_state.usuario.get('papel', 'CATEQUISTA').upper()
turma_do_catequista = st.session_state.usuario.get('turma_vinculada', 'TODAS')

# Definimos quem tem poder de gestão
eh_gestor = papel_usuario in ["COORDENADOR", "ADMIN"]

if eh_gestor:
    menu = st.sidebar.radio("MENU PRINCIPAL", [
        "🏠 Início / Dashboard", 
        "🏠 Minha Turma",           
        "📖 Diário de Encontros",    
        "📝 Cadastrar Catequizando", 
        "👤 Perfil Individual", 
        "🏫 Gestão de Turmas", 
        "🕊️ Gestão de Sacramentos",
        "👥 Gestão de Catequistas",
        "✅ Fazer Chamada"
    ])
else:
    menu = st.sidebar.radio("MENU DO CATEQUISTA", [
        "🏠 Minha Turma", 
        "📖 Diário de Encontros",
        "✅ Fazer Chamada",
        "📝 Cadastrar Catequizando"
    ])

# --- PÁGINA 1: DASHBOARD (COORDENADOR) ---
if menu == "🏠 Início / Dashboard":
    import plotly.express as px
    st.title("📊 Painel de Gestão Pastoral")
    
    # --- ALERTA DE ANIVERSÁRIO DO DIA ---
    aniversariantes_agora = obter_aniversariantes_hoje(df_cat, df_usuarios)
    if aniversariantes_agora:
        for msg in aniversariantes_agora:
            st.success(f"🎂 **HOJE É ANIVERSÁRIO!** {msg}")
            st.balloons()

    if df_cat.empty:
        st.info("👋 Bem-vindo! Comece cadastrando turmas e catequizandos.")
    else:
        # --- SEÇÃO 1: MÉTRICAS PRINCIPAIS ---
        m1, m2, m3, m4 = st.columns(4)
        total_cat = len(df_cat)
        ativos = len(df_cat[df_cat['status'] == 'ATIVO'])
        total_t = len(df_turmas)
        total_equipe = len(equipe_tecnica)
        
        m1.metric("Catequizandos", total_cat)
        m2.metric("Ativos", ativos)
        m3.metric("Total de Turmas", total_t)
        m4.metric("Equipe Catequética", total_equipe)

        st.divider()

        # --- SEÇÃO 2: DESEMPENHO ---
        st.subheader("📈 Desempenho e Frequência")
        freq_global = 0.0
        temas_vistos = []

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
                temas_vistos = df_pres['tema_do_dia'].unique().tolist()
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
                for _, niver in df_niver_unificado.iterrows():
                    icone = "🛡️" if niver['tipo'] == 'CATEQUISTA' else "🎁"
                    st.markdown(f"{icone} **Dia {int(niver['dia'])}** - {niver['nome']} ({niver['info']})")
            else: st.write("Nenhum aniversariante este mês.")

        with col_evasao:
            st.subheader("🚨 Alerta de Evasão")
            if not df_pres.empty:
                faltas = df_pres[df_pres['status'] == 'AUSENTE'].groupby('nome_catequizando').size().reset_index(name='total_faltas')
                evasao = faltas[faltas['total_faltas'] >= 2].sort_values(by='total_faltas', ascending=False)
                if not evasao.empty:
                    st.warning(f"Existem {len(evasao)} catequizandos com 2 ou mais faltas!")
                    st.dataframe(evasao, use_container_width=True, hide_index=True)
                else: st.success("Nenhum alerta de evasão no momento.")

        # --- SEÇÃO IA E RELATÓRIOS OFICIAIS ---
        st.divider()
        st.subheader("🤖 Auditoria Pastoral e Documentação")
        c_ia, c_pdf = st.columns([2, 1])
        
        with c_ia:
            if st.button("✨ Gerar Auditoria Pastoral Inteligente"):
                with st.spinner("O Auditor IA está analisando os dados..."):
                    resumo_para_ia = f"Total: {total_cat}, Freq: {freq_global:.1f}%, Temas: {temas_vistos}"
                    st.session_state.analise_dashboard = gerar_analise_pastoral(resumo_para_ia)
            if "analise_dashboard" in st.session_state:
                st.info("Auditoria concluída! Utilize os botões ao lado para exportar o PDF oficial.")
        
        with c_pdf:
            st.write("📄 **Exportar Documentos Oficiais**")
            if st.button("🏛️ Gerar Relatório Diocesano"):
                with st.spinner("Preparando Censo..."):
                    df_kids = df_cat[df_cat['estado_civil_pais_ou_proprio'] == 'N/A']
                    df_adults = df_cat[df_cat['estado_civil_pais_ou_proprio'] != 'N/A']
                    dados_g = {'total_cat': total_cat, 'total_kids': len(df_kids), 'total_adults': len(df_adults), 'total_turmas': total_t, 'total_equipe': total_equipe}
                    
                    bat_sim = len(df_cat[df_cat['batizado_sn'] == 'SIM'])
                    euca_sim = df_cat['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
                    cris_sim = df_cat['sacramentos_ja_feitos'].str.contains("CRISMA", na=False).sum()
                    sac_stats = {'batismos': bat_sim, 'eucaristias': euca_sim, 'crismas': cris_sim}
                    
                    proj_list = []
                    if not df_sac_eventos.empty:
                        df_sac_eventos['data_dt'] = pd.to_datetime(df_sac_eventos['data'], errors='coerce').dt.date
                        futuros = df_sac_eventos[df_sac_eventos['data_dt'] > date.today()]
                        for _, f in futuros.iterrows(): proj_list.append(f"{f['tipo_sacramento']} agendado para {f['data']} (Turmas: {f['turmas_envolvidas']})")
                    
                    turmas_list = []
                    for _, t in df_turmas.iterrows():
                        qtd = len(df_cat[df_cat['etapa'] == t['nome_turma']])
                        publico = "ADULTOS" if "ADULTO" in str(t['etapa']).upper() else "INFANTIL/JUVENIL"
                        turmas_list.append({'nome': t['nome_turma'], 'publico': publico, 'dias': t.get('dias_semana', 'N/A'), 'qtd_alunos': qtd})
                    
                    resumo_censo = f"Censo: {dados_g}. Sacramentos: {sac_stats}. Projeções: {proj_list}"
                    analise_tecnica = gerar_analise_pastoral(resumo_censo) 
                    st.session_state.pdf_diocesano = gerar_relatorio_diocesano_pdf(dados_g, turmas_list, sac_stats, proj_list, analise_tecnica)
            
            if "pdf_diocesano" in st.session_state:
                st.download_button("📥 Baixar Relatório Diocesano", st.session_state.pdf_diocesano, "Relatorio_Diocesano.pdf", "application/pdf")

            if st.button("📋 Gerar Relatório Pastoral"):
                if "analise_dashboard" in st.session_state:
                    with st.spinner("Preparando Relatório Pastoral..."):
                        st.session_state.pdf_pastoral = gerar_relatorio_pastoral_interno_pdf({}, st.session_state.analise_dashboard)
                else:
                    st.warning("Gere a análise da IA primeiro.")
            
            if "pdf_pastoral" in st.session_state:
                st.download_button("📥 Baixar Relatório Pastoral", st.session_state.pdf_pastoral, "Relatorio_Pastoral_Interno.pdf", "application/pdf")

# --- PÁGINA: MINHA TURMA ---
elif menu == "🏠 Minha Turma":
    st.title(f"🏠 Painel da Turma: {turma_do_catequista}")
    
    df_cron = ler_aba("cronograma")
    meus_alunos = df_cat[df_cat['etapa'] == turma_do_catequista] if not df_cat.empty else pd.DataFrame()
    minhas_pres = df_pres[df_pres['id_turma'] == turma_do_catequista] if not df_pres.empty else pd.DataFrame()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Catequizandos", len(meus_alunos))
    
    if not minhas_pres.empty:
        minhas_pres['status_num'] = minhas_pres['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
        freq = minhas_pres['status_num'].mean() * 100
        c2.metric("Frequência Média", f"{freq:.1f}%")
        total_encontros = minhas_pres['data_encontro'].nunique()
        c3.metric("Encontros Realizados", total_encontros)

    st.divider()

    st.subheader("🚩 Revisão do Último Encontro")
    if not minhas_pres.empty:
        ultima_data = minhas_pres['data_encontro'].max()
        faltosos = minhas_pres[(minhas_pres['data_encontro'] == ultima_data) & (minhas_pres['status'] == 'AUSENTE')]
        
        if not faltosos.empty:
            st.warning(f"No último encontro ({ultima_data}), os seguintes catequizandos faltaram. Que tal enviar uma mensagem de carinho?")
            for _, f in faltosos.iterrows():
                st.write(f"❌ {f['nome_catequizando']}")
        else:
            st.success(f"Parabéns! No último encontro ({ultima_data}), todos estavam presentes! 🎉")
    else:
        st.info("Ainda não houve encontros registrados para esta turma.")

    st.divider()

    st.subheader("🎂 Aniversariantes do Mês")
    df_niver_mes = obter_aniversariantes_mes(meus_alunos)
    if not df_niver_mes.empty:
        cols_n = st.columns(len(df_niver_mes) if len(df_niver_mes) < 4 else 4)
        for i, (_, niver) in enumerate(df_niver_mes.iterrows()):
            with cols_n[i % 4]:
                st.info(f"**Dia {int(niver['dia'])}**\n\n{niver['nome_completo']}")
    else:
        st.write("Nenhum aniversariante este mês.")

    st.divider()

    col_passado, col_futuro = st.columns(2)
    with col_passado:
        st.subheader("📖 Temas já Ministrados")
        if not minhas_pres.empty:
            historico = minhas_pres[['data_encontro', 'tema_do_dia']].drop_duplicates().sort_values('data_encontro', ascending=False)
            st.dataframe(historico, use_container_width=True, hide_index=True)
        else:
            st.write("Nenhum tema registrado ainda.")

    with col_futuro:
        st.subheader("🎯 Próximo Encontro")
        if not df_cron.empty:
            temas_feitos = minhas_pres['tema_do_dia'].unique().tolist() if not minhas_pres.empty else []
            proximos = df_cron[~df_cron['titulo_tema'].isin(temas_feitos)]
            if not proximos.empty:
                proximo_tema = proximos.iloc[0]
                st.success(f"**Sugestão de Tema:**\n\n### {proximo_tema['titulo_tema']}")
                st.write(f"**Objetivo:** {proximo_tema.get('descricao_base', 'Consultar manual do catequista.')}")
            else:
                st.write("✅ Todos os temas do cronograma foram concluídos!")
        else:
            st.info("Dica: Peça para a coordenação cadastrar o Cronograma na planilha para ver os próximos temas aqui.")

    st.divider()
    with st.expander("👥 Ver Lista Completa de Contatos"):
        st.dataframe(meus_alunos[['nome_completo', 'contato_principal', 'status']], use_container_width=True)
    
    st.subheader("📱 Engajamento WhatsApp")
    if not minhas_pres.empty:
        ultima_data = minhas_pres['data_encontro'].max()
        dados_ultimo = minhas_pres[minhas_pres['data_encontro'] == ultima_data]
        
        tema_ultimo = dados_ultimo.iloc[0]['tema_do_dia']
        lista_presentes = dados_ultimo[dados_ultimo['status'] == 'PRESENTE']['nome_catequizando'].tolist()
        lista_faltosos = dados_ultimo[dados_ultimo['status'] == 'AUSENTE']['nome_catequizando'].tolist()

        with st.expander("✨ Gerar Mensagem para o Grupo da Turma"):
            st.write("A IA vai criar um texto baseado no último encontro para você copiar e colar.")
            
            if st.button("📝 Criar Texto Personalizado"):
                with st.spinner("Escrevendo mensagem..."):
                    from ai_engine import gerar_mensagem_whatsapp
                    texto_zap = gerar_mensagem_whatsapp(tema_ultimo, lista_presentes, lista_faltosos)
                    
                    st.markdown("---")
                    st.write("**Sugestão de Mensagem:**")
                    st.info(texto_zap)
                    
                    import urllib.parse
                    texto_url = urllib.parse.quote(texto_zap)
                    link_zap = f"https://wa.me/?text={texto_url}"
                    
                    st.markdown(f"""
                        <a href="{link_zap}" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#25d366; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; width:100%;">
                                📲 Enviar direto para o WhatsApp
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
    else:
        st.info("Faça a primeira chamada para liberar esta função.")

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

# --- PÁGINA: CADASTRAR CATEQUIZANDO ---
elif menu == "📝 Cadastrar Catequizando":
    st.title("📝 Cadastro de Catequizandos")
    tab_manual, tab_csv = st.tabs(["📄 Cadastro Individual", "📂 Importar via CSV"])

    with tab_manual:
        tipo_ficha = st.radio("Tipo de Inscrição:", ["Infantil/Juvenil", "Adulto"], horizontal=True)
        
        if papel_usuario == "CATEQUISTA":
            lista_turmas = [turma_do_catequista]
        else:
            lista_turmas = df_turmas['nome_turma'].tolist() if not df_turmas.empty else ["SEM TURMAS CADASTRADAS"]

        with st.form("form_cadastro_detalhado", clear_on_submit=True):
            st.subheader("📍 Informações Básicas")
            c1, c2, c3 = st.columns([2, 1, 1])
            nome = c1.text_input("Nome Completo").upper()
            data_nasc = c2.date_input("Data de Nascimento", value=date(2015, 1, 1), min_value=MIN_DATA, max_value=MAX_DATA)
            etapa_inscricao = c3.selectbox("Turma/Etapa", lista_turmas)

            c4, c5, c6 = st.columns(3)
            contato = c4.text_input("Telefone/WhatsApp")
            batizado = c5.selectbox("Já é Batizado?", ["SIM", "NÃO"])
            docs_faltando = c6.text_input("Documentos em Falta").upper()
            endereco = st.text_input("Endereço Completo").upper()

            if tipo_ficha == "Infantil/Juvenil":
                st.divider()
                st.subheader("👪 Filiação e Saúde")
                f1, f2 = st.columns(2)
                nome_mae = f1.text_input("Nome da Mãe").upper()
                nome_pai = f1.text_input("Nome do Pai").upper()
                responsavel = f1.text_input("Responsável Legal").upper()
                medicamento = f2.text_input("Medicamentos?").upper()
                tgo = f2.selectbox("Possui TGO?", ["NÃO", "SIM"])
                estado_civil, sacramentos, pastoral = "N/A", "N/A", "NÃO"
            else:
                st.divider()
                st.subheader("💍 Estado Civil e Caminhada")
                a1, a2 = st.columns(2)
                estado_civil = a1.selectbox("Estado Civil", ["SOLTEIRO(A)", "CASADO(A) IGREJA", "CASADO(A) CIVIL", "DIVORCIADO(A)", "VIÚVO(A)"])
                pastoral = a1.text_input("Participa de Pastoral? Qual?").upper()
                s_bat = a2.checkbox("Batismo"); s_euc = a2.checkbox("Eucaristia"); s_cri = a2.checkbox("Crisma"); s_mat = a2.checkbox("Matrimônio")
                sacramentos = ", ".join([s for s, m in zip(["BATISMO", "EUCARISTIA", "CRISMA", "MATRIMÔNIO"], [s_bat, s_euc, s_cri, s_mat]) if m])
                nome_mae, nome_pai, responsavel, medicamento, tgo = "N/A", "N/A", "N/A", "NÃO", "NÃO"

            if st.form_submit_button("💾 SALVAR INSCRIÇÃO"):
                if nome and contato and etapa_inscricao != "SEM TURMAS CADASTRADAS":
                    novo_id = f"CAT-{int(time.time())}"
                    registro = [[novo_id, etapa_inscricao, nome, str(data_nasc), batizado, contato, endereco, nome_mae, nome_pai, responsavel, docs_faltando, pastoral, "ATIVO", medicamento, tgo, estado_civil, sacramentos]]
                    if salvar_lote_catequizandos(registro):
                        st.success(f"✅ {nome} CADASTRADO COM SUCESSO NA TURMA {etapa_inscricao}!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Nome, Contato e Turma são obrigatórios.")

    with tab_csv:
        st.subheader("📥 Importação em Massa")
        modo_importacao = st.radio("Como definir as turmas?", ["Fixar uma única turma", "Usar a turma do CSV"], horizontal=True)
        turma_fixa = None
        
        if modo_importacao == "Fixar uma única turma":
            if not df_turmas.empty:
                turma_fixa = st.selectbox("Selecione a turma de destino:", df_turmas['nome_turma'].tolist())
            else:
                st.error("⚠️ Crie uma turma primeiro.")

        arquivo_csv = st.file_uploader("Selecione o arquivo .csv", type="csv")
        if arquivo_csv:
            df_import = pd.read_csv(arquivo_csv).fillna("")
            st.dataframe(df_import.head())
            if st.button("🚀 Confirmar Importação"):
                lista_final = []
                for i, linha in df_import.iterrows():
                    if modo_importacao == "Fixar uma única turma":
                        turma_final = turma_fixa
                    else:
                        turma_final = str(linha.get('etapa', 'NÃO INFORMADO')).upper()

                    lista_final.append([
                        f"CSV-{int(time.time()) + i}", turma_final, str(linha.get('nome', 'SEM NOME')).upper(),
                        str(linha.get('data_nasc', '2000-01-01')), "NÃO INFORMADO", str(linha.get('contato', '')), 
                        "", "N/A", "N/A", str(linha.get('responsavel', 'N/A')).upper(), "", "", "ATIVO", "NÃO", "NÃO", "N/A", "N/A"
                    ])
                if salvar_lote_catequizandos(lista_final):
                    st.success(f"✅ {len(lista_final)} importados!"); st.balloons(); st.rerun()

# --- PÁGINA: PERFIL INDIVIDUAL ---
elif menu == "👤 Perfil Individual":
    st.title("👤 Perfil e Ficha do Catequizando")
    
    if df_cat.empty:
        st.warning("⚠️ Nenhum catequizando encontrado na base de dados.")
    else:
        c1, c2 = st.columns([2, 1])
        busca = c1.text_input("🔍 Pesquisar por nome:").upper()
        
        lista_t = ["TODAS"] + df_turmas['nome_turma'].tolist() if not df_turmas.empty else ["TODAS"]
        filtro_t = c2.selectbox("Filtrar por Turma:", lista_t)

        df_f = df_cat.copy()
        if busca: df_f = df_f[df_f['nome_completo'].str.contains(busca)]
        if filtro_t != "TODAS": df_f = df_f[df_f['etapa'] == filtro_t]

        st.dataframe(df_f[['nome_completo', 'etapa', 'status']], use_container_width=True)
        
        st.divider()
        
        df_f['display_select'] = df_f['nome_completo'] + " (" + df_f['etapa'] + ")"
        escolha_display = st.selectbox("Selecione um catequizando para EDITAR ou gerar PDF:", [""] + df_f['display_select'].tolist())

        if escolha_display:
            nome_sel = escolha_display.split(" (")[0]
            turma_sel = escolha_display.split(" (")[1].replace(")", "")
            dados = df_cat[(df_cat['nome_completo'] == nome_sel) & (df_cat['etapa'] == turma_sel)].iloc[0]
            
            tab_edit, tab_doc = st.tabs(["✏️ Editar Dados Cadastrais", "📄 Documentação e PDF"])
            
            with tab_edit:
                st.subheader(f"📍 Editando: {nome_sel}")
                with st.form("form_edicao_individual"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    ed_nome = c1.text_input("Nome Completo", value=dados['nome_completo']).upper()
                    ed_nasc = c2.date_input("Data de Nascimento", value=converter_para_data(dados['data_nascimento']), min_value=MIN_DATA, max_value=MAX_DATA)
                    
                    lista_turmas_edit = df_turmas['nome_turma'].tolist() if not df_turmas.empty else [dados['etapa']]
                    idx_turma = lista_turmas_edit.index(dados['etapa']) if dados['etapa'] in lista_turmas_edit else 0
                    ed_etapa = c3.selectbox("Turma/Etapa", lista_turmas_edit, index=idx_turma)

                    c4, c5, c6 = st.columns(3)
                    ed_contato = c4.text_input("Telefone/WhatsApp", value=dados['contato_principal'])
                    ed_batizado = c5.selectbox("Já é Batizado?", ["SIM", "NÃO"], index=0 if dados['batizado_sn'] == "SIM" else 1)
                    ed_status = c6.selectbox("Status no Sistema", ["ATIVO", "INATIVO", "TRANSFERIDO"], index=["ATIVO", "INATIVO", "TRANSFERIDO"].index(dados['status']) if dados['status'] in ["ATIVO", "INATIVO", "TRANSFERIDO"] else 0)
                    
                    ed_endereco = st.text_input("Endereço Completo", value=dados['endereco_completo']).upper()
                    
                    st.divider()
                    f1, f2, f3 = st.columns(3)
                    ed_mae = f1.text_input("Nome da Mãe", value=dados['nome_mae']).upper()
                    ed_pai = f2.text_input("Nome do Pai", value=dados['nome_pai']).upper()
                    ed_resp = f3.text_input("Responsável Legal", value=dados['nome_responsavel']).upper()
                    
                    st.divider()
                    s1, s2, s3 = st.columns(3)
                    ed_med = s1.text_input("Medicamentos/Alergias", value=dados['toma_medicamento_sn']).upper()
                    ed_tgo = s2.selectbox("Possui TGO?", ["NÃO", "SIM"], index=0 if dados['tgo_sn'] == "NÃO" else 1)
                    ed_docs = s3.text_input("Documentos em Falta", value=dados['doc_em_falta']).upper()
                    
                    st.divider()
                    a1, a2, a3 = st.columns([1, 1, 2])
                    ed_est_civil = a1.text_input("Estado Civil (Pais ou Próprio)", value=dados['estado_civil_pais_ou_proprio']).upper()
                    ed_pastoral = a2.text_input("Engajado em Pastoral?", value=dados['engajado_grupo']).upper()
                    ed_sacramentos = a3.text_input("Sacramentos já realizados", value=dados['sacramentos_ja_feitos']).upper()

                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        lista_atualizada = [
                            dados['id_catequizando'], ed_etapa, ed_nome, str(ed_nasc), 
                            ed_batizado, ed_contato, ed_endereco, ed_mae, ed_pai, 
                            ed_resp, ed_docs, ed_pastoral, ed_status, ed_med, 
                            ed_tgo, ed_est_civil, ed_sacramentos
                        ]
                        if atualizar_catequizando(dados['id_catequizando'], lista_atualizada):
                            st.success("✅ Dados atualizados com sucesso!")
                            time.sleep(1)
                            st.rerun()

            with tab_doc:
                col_info, col_pdf = st.columns([2, 1])
                with col_info:
                    st.subheader("Resumo Atual")
                    st.write(f"**Nome:** {dados['nome_completo']}")
                    st.write(f"**Turma:** {dados['etapa']}")
                    st.write(f"**Status:** {dados['status']}")
                    st.info("💡 Os dados acima refletem o que sairá no PDF. Se houver erros, corrija na aba 'Editar Dados Cadastrais'.")

                with col_pdf:
                    st.subheader("Gerar Documento")
                    if st.button(f"Gerar Ficha de Inscrição PDF"):
                        with st.spinner("Preparando PDF..."):
                            st.session_state.pdf_catequizando = gerar_ficha_cadastral_catequizando(dados.to_dict())
                    
                    if "pdf_catequizando" in st.session_state:
                        st.download_button(
                            label="📥 Baixar Ficha PDF",
                            data=st.session_state.pdf_catequizando,
                            file_name=f"Ficha_{nome_sel}.pdf",
                            mime="application/pdf"
                        )

# --- PÁGINA: GESTÃO DE TURMAS ---
# --- INÍCIO DO BLOCO INTEGRAL: GESTÃO DE TURMAS (VERSÃO ARQUITETURA FINAL) ---
elif menu == "🏫 Gestão de Turmas":
    st.title("🏫 Gestão de Turmas")
    
    t1, t2, t3, t4, t5 = st.tabs([
        "Visualizar Turmas", "➕ Criar Nova Turma", 
        "✏️ Detalhes e Edição", "📊 Dashboard Local", "🚀 Movimentação em Massa"
    ])
    
    dias_opcoes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    etapas_lista = [
        "PRÉ", "PRIMEIRA ETAPA", "SEGUNDA ETAPA", "TERCEIRA ETAPA", 
        "PERSEVERANÇA", "ADULTOS TURMA EUCARISTIA/BATISMO", "ADULTOS CRISMA"
    ]

    with t1:
        st.subheader("📋 Turmas Cadastradas")
        if not df_turmas.empty:
            # Filtra colunas técnicas para exibição limpa
            cols_show = [c for c in df_turmas.columns if not c.startswith('col_')]
            st.dataframe(df_turmas[cols_show], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma turma encontrada. Vá na aba 'Criar Nova Turma' para começar.")

    with t2:
        st.subheader("➕ Cadastrar Nova Turma")
        c1, c2 = st.columns(2)
        n_t = c1.text_input("Nome da Turma (Ex: TURMA SANTA RITA)", key="n_t_criar_v4").upper()
        e_t = c1.selectbox("Etapa Base", etapas_lista, key="e_t_criar_v4")
        ano = c2.number_input("Ano Letivo", value=2026, key="ano_criar_v4")
        n_dias = st.multiselect("Dias de Encontro:", dias_opcoes, key="dias_criar_v4")
        
        st.markdown("---")
        p_euca, p_crisma = "", ""
        if e_t in ["TERCEIRA ETAPA", "ADULTOS TURMA EUCARISTIA/BATISMO"]:
            p_euca = st.text_input("📅 Previsão da Eucaristia (Ex: Outubro/2026)", key="p_euca_criar_v4")
        elif e_t == "ADULTOS CRISMA":
            p_crisma = st.text_input("🕊️ Previsão da Crisma (Ex: Novembro/2026)", key="p_cris_criar_v4")
        else:
            st.info("ℹ️ Etapa de base: O Batismo é tratado individualmente.")

        lista_nomes_disponiveis = equipe_tecnica['nome'].astype(str).unique().tolist() if not equipe_tecnica.empty else []
        selecao_catequistas = st.multiselect("Catequistas Responsáveis:", lista_nomes_disponiveis, key="cats_criar_v4")

        if st.button("🚀 SALVAR NOVA TURMA", key="btn_salvar_t_v4"):
            nomes_existentes = [str(n).strip().upper() for n in df_turmas['nome_turma'].tolist()] if not df_turmas.empty else []
            if not n_t or not selecao_catequistas or not n_dias:
                st.error("Preencha Nome, Catequistas e Dias da Semana.")
            elif n_t.strip().upper() in nomes_existentes:
                st.error(f"⚠️ Já existe uma turma com o nome '{n_t}'.")
            else:
                catequistas_str = ", ".join(selecao_catequistas)
                dias_str = ", ".join(n_dias)
                if conectar_google_sheets().worksheet("turmas").append_row([
                    f"TRM-{int(time.time())}", n_t, e_t, ano, catequistas_str, dias_str, p_euca, p_crisma
                ]):
                    st.success(f"Turma {n_t} criada com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

    with t3:
        st.subheader("✏️ Detalhes e Edição")
        if not df_turmas.empty:
            turma_para_editar = st.selectbox("Selecione a turma para editar:", [""] + df_turmas['nome_turma'].tolist(), key="sel_edit_t_v4")
            if turma_para_editar:
                dados_t = df_turmas[df_turmas['nome_turma'] == turma_para_editar].iloc[0]
                c1, c2 = st.columns(2)
                ed_nome = c1.text_input("Nome da Turma", value=str(dados_t['nome_turma']), key="n_t_edit_v4").upper()
                idx_etapa = etapas_lista.index(dados_t['etapa']) if dados_t['etapa'] in etapas_lista else 0
                ed_etapa = c1.selectbox("Etapa Base", etapas_lista, index=idx_etapa, key="e_t_edit_v4")
                ed_ano = c2.number_input("Ano Letivo", value=int(dados_t['ano']), key="ano_edit_v4")
                ed_p_euca = c2.text_input("Previsão Eucaristia", value=str(dados_t.get('previsao_eucaristia', '')), key="p_euca_edit_v4")
                ed_p_crisma = c2.text_input("Previsão Crisma", value=str(dados_t.get('previsao_crisma', '')), key="p_cris_edit_v4")

                dias_atuais = str(dados_t.get('dias_semana', '')).split(", ")
                ed_dias = st.multiselect("Dias de Encontro:", dias_opcoes, default=[d for d in dias_atuais if d in dias_opcoes], key="dias_edit_v4")
                
                lista_nomes = equipe_tecnica['nome'].astype(str).unique().tolist() if not equipe_tecnica.empty else []
                cats_salvos = str(dados_t.get('catequista_responsavel', ''))
                cats_atuais = [c.strip() for c in cats_salvos.split(",")] if cats_salvos else []
                ed_selecao_cats = st.multiselect("Equipe de Catequistas:", lista_nomes, default=[c for c in cats_atuais if c in lista_nomes], key="cats_edit_v4")

                if st.button("💾 SALVAR ALTERAÇÕES", key="btn_edit_t_v4"):
                    lista_up = [str(dados_t['id_turma']), ed_nome, ed_etapa, ed_ano, ", ".join(ed_selecao_cats), ", ".join(ed_dias), ed_p_euca, ed_p_crisma]
                    if atualizar_turma(dados_t['id_turma'], lista_up):
                        st.success("Turma atualizada!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                
                st.divider()
                with st.expander("⚠️ ZONA DE PERIGO"):
                    if st.button(f"🔥 EXCLUIR TURMA: {turma_para_editar}", key="btn_del_t_v4"):
                        if excluir_turma(dados_t['id_turma']):
                            st.success("Turma removida!"); st.cache_data.clear(); time.sleep(1); st.rerun()
        else:
            st.info("Nenhuma turma para editar.")

    with t4:
        st.subheader("📊 Inteligência Pastoral da Turma")
        
        if not df_turmas.empty:
            # 1. Seleção da Turma
            t_alvo = st.selectbox("Selecione a turma para análise profunda:", df_turmas['nome_turma'].tolist(), key="sel_dash_t_v_final")
            
            # 2. Filtragem de Dados Específicos
            dados_t_ref = df_turmas[df_turmas['nome_turma'] == t_alvo].iloc[0]
            alunos_t = df_cat[df_cat['etapa'] == t_alvo] if not df_cat.empty else pd.DataFrame()
            pres_t = df_pres[df_pres['id_turma'] == t_alvo] if not df_pres.empty else pd.DataFrame()
            
            if not alunos_t.empty:
                # --- CÁLCULOS DE MÉTRICAS ---
                total_alunos = len(alunos_t)
                idades = [calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
                media_idade = sum(idades) / len(idades)
                
                # Frequência
                freq_media = 0.0
                if not pres_t.empty:
                    freq_media = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100)
                
                # Cobertura Sacramental
                batizados_t = len(alunos_t[alunos_t['batizado_sn'] == 'SIM'])
                perc_batismo = (batizados_t / total_alunos) * 100

                # --- LINHA 1: MÉTRICAS PRINCIPAIS ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Catequizandos", total_alunos)
                m2.metric("Idade Média", f"{media_idade:.1f} anos")
                m3.metric("Frequência Média", f"{freq_media:.1f}%")
                m4.metric("Cobertura Batismo", f"{perc_batismo:.0f}%")

                st.divider()

                # --- LINHA 2: GRÁFICOS E ALERTAS ---
                col_graf, col_alertas = st.columns([2, 1])
                
                with col_graf:
                    st.markdown("**📈 Evolução de Presença por Encontro**")
                    if not pres_t.empty:
                        # Agrupa presença por data
                        df_graf = pres_t.groupby('data_encontro')['status'].value_counts(normalize=True).unstack().fillna(0)
                        if 'PRESENTE' in df_graf.columns:
                            df_graf = df_graf[['PRESENTE']] * 100
                            fig_pres = px.line(df_graf, y='PRESENTE', labels={'PRESENTE': 'Presença %', 'data_encontro': 'Data'},
                                             color_discrete_sequence=['#417b99'])
                            fig_pres.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                            st.plotly_chart(fig_pres, use_container_width=True)
                        else: st.info("Dados insuficientes para gráfico.")
                    else: st.info("Nenhum encontro registrado para gerar gráfico.")

                with col_alertas:
                    st.markdown("**🚨 Alertas de Atenção**")
                    # Alerta de Evasão (Faltou nos últimos 2 encontros)
                    if not pres_t.empty:
                        ultimas_datas = sorted(pres_t['data_encontro'].unique())[-2:]
                        faltosos_recorrentes = []
                        for nome in alunos_t['nome_completo'].unique():
                            faltas = pres_t[(pres_t['nome_catequizando'] == nome) & 
                                           (pres_t['data_encontro'].isin(ultimas_datas)) & 
                                           (pres_t['status'] == 'AUSENTE')]
                            if len(faltas) >= 2:
                                faltosos_recorrentes.append(nome)
                        
                        if faltosos_recorrentes:
                            for f in faltosos_recorrentes:
                                st.error(f"Evasão: {f}")
                        else: st.success("Nenhum risco de evasão detectado.")
                    
                    # Alerta de Batismo para Etapas Finais
                    if "TERCEIRA" in t_alvo or "ADULTO" in t_alvo:
                        pendentes = alunos_t[alunos_t['batizado_sn'] != 'SIM']
                        if not pendentes.empty:
                            st.warning(f"{len(pendentes)} pendentes de Batismo para a Eucaristia.")

                st.divider()

                # --- LINHA 3: AUDITORIA NOMINAL E IA ---
                col_nom, col_ia = st.columns([1, 1])
                
                with col_nom:
                    st.markdown("**📜 Relação Nominal e Status**")
                    st.dataframe(alunos_t[['nome_completo', 'batizado_sn', 'status']], 
                                 use_container_width=True, hide_index=True)
                    
                    # Sacramentos feitos no ano (Frutos da Turma)
                    df_recebidos = ler_aba("sacramentos_recebidos")
                    if not df_recebidos.empty:
                        meus_ids = alunos_t['id_catequizando'].tolist()
                        frutos = df_recebidos[df_recebidos['id_catequizando'].isin(meus_ids)]
                        if not frutos.empty:
                            st.markdown("**✨ Sacramentos Recebidos este Ano:**")
                            for _, f in frutos.iterrows():
                                st.write(f"· {f['nome_catequizando']} ({f['tipo_sacramento']})")

                with col_ia:
                    st.markdown("**🤖 Diagnóstico Pastoral Inteligente**")
                    if st.button(f"✨ Analisar Perfil de {t_alvo}", key="btn_ia_local"):
                        with st.spinner("IA analisando perfil da turma..."):
                            # Prepara resumo para IA
                            resumo_ia_local = {
                                "turma": t_alvo, "etapa": dados_t_ref['etapa'],
                                "total": total_alunos, "freq": f"{freq_media:.1f}%",
                                "idades": f"{min(idades)}-{max(idades)}",
                                "batizados": f"{batizados_t}/{total_alunos}",
                                "prev_euca": dados_t_ref.get('previsao_eucaristia', 'N/A'),
                                "impedimentos": len(alunos_t[alunos_t['estado_civil_pais_ou_proprio'].isin(['DIVORCIADO(A)', 'CASADO(A) CIVIL'])])
                            }
                            diagnostico = analisar_turma_local(t_alvo, str(resumo_ia_local))
                            st.info(diagnostico)
                            st.session_state[f"ia_dash_{t_alvo}"] = diagnostico
                    
                    if f"ia_dash_{t_alvo}" in st.session_state:
                        if st.button("📄 Exportar Perfil em PDF"):
                            metricas_pdf = {
                                "Total": total_alunos, "Frequência": f"{freq_media:.1f}%",
                                "Batizados": f"{batizados_t}/{total_alunos}",
                                "Catequistas": dados_t_ref['catequista_responsavel']
                            }
                            pdf_turma = gerar_pdf_perfil_turma(t_alvo, metricas_pdf, st.session_state[f"ia_dash_{t_alvo}"], alunos_t['nome_completo'].tolist())
                            st.download_button("📥 Baixar PDF", pdf_turma, f"Perfil_{t_alvo}.pdf")

            else:
                st.warning("Esta turma ainda não possui catequizandos cadastrados.")
        else:
            st.info("Cadastre uma turma primeiro.")

    with t5:
        st.subheader("🚀 Movimentação em Massa")
        st.write("Use esta ferramenta para mover alunos de uma turma para outra (ex: avanço de etapa).")
        
        if not df_turmas.empty and not df_cat.empty:
            col_origem, col_destino = st.columns(2)
            turma_origem = col_origem.selectbox("1. Turma de ORIGEM:", [""] + df_turmas['nome_turma'].tolist(), key="mov_origem_v4")
            turma_destino = col_destino.selectbox("2. Turma de DESTINO:", [""] + df_turmas['nome_turma'].tolist(), key="mov_destino_v4")
            
            if turma_origem:
                alunos_origem = df_cat[(df_cat['etapa'] == turma_origem) & (df_cat['status'] == 'ATIVO')]
                
                if not alunos_origem.empty:
                    st.markdown(f"**Catequizandos ativos em {turma_origem}:**")
                    selecionar_todos = st.checkbox("Selecionar todos os alunos", key="chk_mov_todos_v4")
                    
                    lista_ids_mover = []
                    cols_alunos = st.columns(2)
                    for i, (_, aluno) in enumerate(alunos_origem.iterrows()):
                        with cols_alunos[i % 2]:
                            if st.checkbox(f"{aluno['nome_completo']}", value=selecionar_todos, key=f"mov_aluno_{aluno['id_catequizando']}"):
                                lista_ids_mover.append(aluno['id_catequizando'])
                    
                    st.divider()
                    if st.button(f"🚀 EXECUTAR MOVIMENTAÇÃO ({len(lista_ids_mover)} ALUNOS)", key="btn_executar_mov_v4"):
                        if not turma_destino:
                            st.error("Selecione a turma de destino.")
                        elif turma_origem == turma_destino:
                            st.error("A turma de destino deve ser diferente da origem.")
                        elif not lista_ids_mover:
                            st.warning("Selecione ao menos um aluno.")
                        else:
                            with st.spinner("Movimentando catequizandos..."):
                                if mover_catequizandos_em_massa(lista_ids_mover, turma_destino):
                                    st.success(f"✅ Sucesso! {len(lista_ids_mover)} movidos para {turma_destino}.")
                                    st.cache_data.clear(); time.sleep(2); st.rerun()
                else:
                    st.info(f"Não há catequizandos ativos na turma {turma_origem}.")
        else:
            st.warning("Certifique-se de ter turmas e catequizandos cadastrados.")
# --- FIM DO BLOCO: GESTÃO DE TURMAS ---


# --- BLOCO INTEGRAL: GESTÃO DE SACRAMENTOS (VERSÃO ARQUITETURA FINAL) ---
elif menu == "🕊️ Gestão de Sacramentos":
    st.title("🕊️ Auditoria e Gestão de Sacramentos")
    tab_dash, tab_reg, tab_hist = st.tabs(["📊 Auditoria Sacramental", "✍️ Registrar Sacramento", "📜 Histórico"])
    
    with tab_dash:
        # 1. Inicialização de Variáveis de Segurança e Censo
        k_bat, a_bat, total_batismos_ano = 0, 0, 0
        df_recebidos = ler_aba("sacramentos_recebidos")
        
        # Cálculo de Batismos do Ano (Frutos da Evangelização)
        if not df_recebidos.empty:
            cols_rec = df_recebidos.columns.tolist()
            c_tipo = 'tipo_sacramento' if 'tipo_sacramento' in cols_rec else None
            c_data = 'data_recebimento' if 'data_recebimento' in cols_rec else ('data' if 'data' in cols_rec else None)
            if c_tipo and c_data:
                try:
                    df_recebidos['data_dt'] = pd.to_datetime(df_recebidos[c_data], errors='coerce')
                    total_batismos_ano = len(df_recebidos[
                        (df_recebidos[c_tipo].str.upper() == 'BATISMO') & 
                        (df_recebidos['data_dt'].dt.year == date.today().year)
                    ])
                except: pass

        st.markdown(f"""
            <div style='background-color:#f8f9f0; padding:20px; border-radius:10px; border:1px solid #e03d11; text-align:center; margin-bottom:20px;'>
                <h3 style='margin:0; color:#e03d11;'>🕊️ Frutos da Evangelização {date.today().year}</h3>
                <p style='font-size:22px; color:#417b99; margin:5px 0;'><b>{total_batismos_ano} Batismos realizados</b></p>
                <p style='font-size:14px; color:#666;'>Total de novos cristãos inseridos na comunidade este ano.</p>
            </div>
        """, unsafe_allow_html=True)

        # 2. Segmentação de Público (Kids vs Adultos)
        df_kids = df_cat[df_cat['estado_civil_pais_ou_proprio'] == 'N/A'] if not df_cat.empty else pd.DataFrame()
        df_adults = df_cat[df_cat['estado_civil_pais_ou_proprio'] != 'N/A'] if not df_cat.empty else pd.DataFrame()

        st.subheader("📊 Quadro Geral de Sacramentos")
        col_k, col_a = st.columns(2)
        with col_k:
            st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'><b>PÚBLICO INFANTIL / JUVENIL</b></div>", unsafe_allow_html=True)
            if not df_kids.empty:
                k_bat = len(df_kids[df_kids['batizado_sn'] == 'SIM'])
                st.metric("Batizados (Kids)", f"{k_bat}/{len(df_kids)}")
            else: st.write("Nenhum registro infantil.")

        with col_a:
            st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'><b>PÚBLICO ADULTOS</b></div>", unsafe_allow_html=True)
            if not df_adults.empty:
                a_bat = len(df_adults[df_adults['batizado_sn'] == 'SIM'])
                st.metric("Batizados (Adultos)", f"{a_bat}/{len(df_adults)}")
            else: st.write("Nenhum registro de adultos.")

        st.divider()
        st.subheader("🏫 Auditoria Nominal e Pastoral por Turma")
        
        analise_detalhada_ia = []
        if not df_turmas.empty:
            for _, t in df_turmas.iterrows():
                alunos_t = df_cat[df_cat['etapa'] == t['nome_turma']] if not df_cat.empty else pd.DataFrame()
                if not alunos_t.empty:
                    # Cálculo de Frequência
                    pres_t = df_pres[df_pres['id_turma'] == t['nome_turma']] if not df_pres.empty else pd.DataFrame()
                    freq_media = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100) if not pres_t.empty else 0
                    
                    idades = [calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
                    impedimentos = len(alunos_t[alunos_t['estado_civil_pais_ou_proprio'].isin(['DIVORCIADO(A)', 'CASADO(A) CIVIL'])])
                    
                    batizados_list = alunos_t[alunos_t['batizado_sn'] == 'SIM']
                    pendentes_list = alunos_t[alunos_t['batizado_sn'] != 'SIM']
                    
                    # Limpeza de datas vazias
                    p_euca = t.get('previsao_eucaristia', 'N/A')
                    p_euca = p_euca if p_euca and str(p_euca).strip() != "" else "N/A"
                    p_cris = t.get('previsao_crisma', 'N/A')
                    p_cris = p_cris if p_cris and str(p_cris).strip() != "" else "N/A"
                    
                    with st.expander(f"📍 {t['nome_turma']} ({t['etapa']}) - Frequência: {freq_media:.1f}%"):
                        col_p1, col_p2 = st.columns([2, 1])
                        with col_p1:
                            st.write(f"**Faixa Etária:** {min(idades)} a {max(idades)} anos")
                            if impedimentos > 0: 
                                st.warning(f"⚠️ {impedimentos} adultos com situação matrimonial a regularizar para Eucaristia.")
                            
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
                            st.write(f"Eucaristia: `{p_euca}`")
                            st.write(f"Crisma: `{p_cris}`")

                    analise_detalhada_ia.append({
                        "turma": t['nome_turma'], "etapa": t['etapa'], "freq": f"{freq_media:.1f}%",
                        "idades": f"{min(idades)}-{max(idades)}", "impedimentos_civel": impedimentos,
                        "batizados": len(batizados_list), "pendentes": len(pendentes_list),
                        "total": len(alunos_t), "prev_e": p_euca, "prev_c": p_cris
                    })

        st.divider()
        # 3. Geração de PDF com Persistência de Estado
        if st.button("🏛️ Gerar Auditoria Pastoral Completa (PDF)", key="btn_gerar_pdf_sac_final"):
            with st.spinner("O Auditor IA está analisando impedimentos e engajamento..."):
                try:
                    resumo_ia = f"Batismos no Ano: {total_batismos_ano}. Detalhes: {analise_detalhada_ia}"
                    analise_ia_sac = gerar_relatorio_sacramentos_ia(resumo_ia)
                    
                    stats_pdf = {
                        'bat_ano': total_batismos_ano,
                        'bat_k': k_bat, 'euca_k': 0,
                        'bat_a': a_bat, 'euca_a': 0, 'cris_a': 0
                    }
                    
                    pdf_data = gerar_relatorio_sacramentos_tecnico_pdf(stats_pdf, analise_detalhada_ia, analise_ia_sac)
                    if pdf_data:
                        st.session_state.pdf_sac_tecnico = pdf_data
                        st.success("✅ Relatório gerado! O botão de download apareceu abaixo.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro na geração do PDF: {e}")

        if "pdf_sac_tecnico" in st.session_state:
            st.download_button(
                label="📥 BAIXAR AUDITORIA SACRAMENTAL (PDF)",
                data=st.session_state.pdf_sac_tecnico,
                file_name=f"Auditoria_Pastoral_Fatima_{date.today().year}.pdf",
                mime="application/pdf",
                key="btn_download_sac_definitivo"
            )

    with tab_reg:
        st.subheader("✍️ Registro de Sacramento")
        modo_reg = st.radio("Como deseja registrar?", ["Individual (Busca por Nome)", "Por Turma (Mutirão)"], horizontal=True, key="modo_reg_sac_v2")
        
        if modo_reg == "Individual (Busca por Nome)":
            nome_busca = st.text_input("🔍 Digite o nome do catequizando:", key="busca_sac_ind_v2").upper()
            if nome_busca:
                sugestoes = df_cat[df_cat['nome_completo'].str.contains(nome_busca)] if not df_cat.empty else pd.DataFrame()
                if not sugestoes.empty:
                    escolhido = st.selectbox("Selecione o catequizando:", sugestoes['nome_completo'].tolist(), key="sel_sac_ind_v2")
                    dados_c = sugestoes[sugestoes['nome_completo'] == escolhido].iloc[0]
                    
                    with st.form("form_sac_individual_v3"):
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
            turmas_s = st.multiselect("Selecione as Turmas:", df_turmas['nome_turma'].tolist() if not df_turmas.empty else [], key="sel_turmas_lote_v2")
            if turmas_s:
                with st.form("form_sac_lote_v3"):
                    tipo_s = st.selectbox("Tipo de Sacramento", ["BATISMO", "EUCARISTIA", "CRISMA"])
                    data_s = st.date_input("Data", date.today())
                    alunos_f = df_cat[df_cat['etapa'].isin(turmas_s)].sort_values('nome_completo')
                    sel_ids = []
                    if not alunos_f.empty:
                        cols = st.columns(2)
                        for i, (_, r) in enumerate(alunos_f.iterrows()):
                            with cols[i % 2]:
                                if st.checkbox(f"{r['nome_completo']}", key=f"lote_chk_v2_{r['id_catequizando']}"): sel_ids.append(r)
                    if st.form_submit_button("💾 SALVAR EM LOTE"):
                        id_ev = f"SAC-{int(time.time())}"
                        lista_p = [[id_ev, r['id_catequizando'], r['nome_completo'], tipo_s, str(data_s)] for r in sel_ids]
                        if registrar_evento_sacramento_completo([id_ev, tipo_s, str(data_s), ", ".join(turmas_s), st.session_state.usuario['nome']], lista_p, tipo_s):
                            st.success("Registrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    with tab_hist:
        st.subheader("📜 Histórico")
        if not df_sac_eventos.empty:
            st.dataframe(df_sac_eventos.sort_values(by=df_sac_eventos.columns[2], ascending=False), use_container_width=True, hide_index=True)
        else: st.info("Nenhum evento registrado.")

# --- PÁGINA: FAZER CHAMADA ---
elif menu == "✅ Fazer Chamada":
    st.title("✅ Chamada Inteligente")
    if eh_gestor:
        lista_t = df_turmas['nome_turma'].tolist()
        idx_sugerido = lista_t.index(turma_do_catequista) if turma_do_catequista in lista_t else 0
        turma_selecionada = st.selectbox("Selecione a Turma para a Chamada:", lista_t, index=idx_sugerido)
    else:
        turma_selecionada = turma_do_catequista
        st.subheader(f"Turma: {turma_selecionada}")    
    
    if df_turmas.empty or df_cat.empty:
        st.warning("⚠️ Certifique-se de ter turmas e catequizandos cadastrados.")
    else:
        col1, col2 = st.columns(2)
        data_encontro = col2.date_input("Data do Encontro", date.today(), min_value=MIN_DATA, max_value=MAX_DATA)
        tema_encontrado = buscar_encontro_por_data(turma_selecionada, data_encontro)
        tema_sugerido = tema_encontrado if tema_encontrado else ""
        tema_dia = st.text_input("Tema do Encontro (Confirme ou altere):", value=tema_sugerido).upper()
        lista_chamada = df_cat[(df_cat['etapa'] == turma_selecionada) & (df_cat['status'] == 'ATIVO')]
        
        if lista_chamada.empty:
            st.info(f"Nenhum catequizando ativo na turma {turma_selecionada}.")
        else:
            st.subheader(f"Lista de Presença - {len(lista_chamada)} Catequizandos")
            with st.form("form_chamada_v2"):
                registros_presenca = []
                for _, row in lista_chamada.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 2])
                    c1.write(row['nome_completo'])
                    presente = c2.checkbox("P", key=f"pres_{row['id_catequizando']}_{data_encontro}", value=True)
                    if eh_aniversariante_da_semana(row['data_nascimento']): c3.success("🎂 NIVER!")
                    registros_presenca.append([str(data_encontro), row['id_catequizando'], row['nome_completo'], turma_selecionada, "PRESENTE" if presente else "AUSENTE", tema_dia, st.session_state.usuario['nome']])
                if st.form_submit_button("🚀 FINALIZAR CHAMADA E SALVAR"):
                    if not tema_dia: st.error("⚠️ Informe o tema antes de salvar.")
                    else:
                        if salvar_presencas(registros_presenca): st.success(f"✅ Chamada salva!"); st.balloons()

# --- PÁGINA: GESTÃO DE CATEQUISTAS ---
elif menu == "👥 Gestão de Catequistas":
    st.title("👥 Gestão de Catequistas e Formação")
    df_formacoes = ler_aba("formacoes")
    df_pres_form = ler_aba("presenca_formacao")
    
    tab_dash, tab_lista, tab_novo, tab_formacao = st.tabs(["📊 Dashboard de Equipe", "📋 Lista e Perfil", "➕ Novo Acesso", "🎓 Registro de Formação"])

# --- INÍCIO DA SUBSTITUIÇÃO: ABA tab_dash (AUDITORIA SACRAMENTAL) ---
    with tab_dash:
        # 1. Censo de Batismos do Ano Vigente
        df_recebidos = ler_aba("sacramentos_recebidos")
        total_batismos_ano = 0
        if not df_recebidos.empty:
            cols_rec = df_recebidos.columns.tolist()
            c_tipo = 'tipo_sacramento' if 'tipo_sacramento' in cols_rec else None
            c_data = 'data_recebimento' if 'data_recebimento' in cols_rec else ('data' if 'data' in cols_rec else None)
            if c_tipo and c_data:
                try:
                    df_recebidos['data_dt'] = pd.to_datetime(df_recebidos[c_data], errors='coerce')
                    total_batismos_ano = len(df_recebidos[(df_recebidos[c_tipo].str.upper() == 'BATISMO') & (df_recebidos['data_dt'].dt.year == date.today().year)])
                except: pass

        st.markdown(f"""
            <div style='background-color:#f8f9f0; padding:20px; border-radius:10px; border:1px solid #e03d11; text-align:center; margin-bottom:20px;'>
                <h3 style='margin:0; color:#e03d11;'>🕊️ Frutos da Evangelização {date.today().year}</h3>
                <p style='font-size:22px; color:#417b99; margin:5px 0;'><b>{total_batismos_ano} Batismos realizados</b></p>
            </div>
        """, unsafe_allow_html=True)

        # 2. Segmentação de Público
        df_kids = df_cat[df_cat['estado_civil_pais_ou_proprio'] == 'N/A'] if not df_cat.empty else pd.DataFrame()
        df_adults = df_cat[df_cat['estado_civil_pais_ou_proprio'] != 'N/A'] if not df_cat.empty else pd.DataFrame()

        st.subheader("📊 Quadro Geral de Sacramentos")
        c1, c2 = st.columns(2)
        
        # Inicializa variáveis para evitar erro no PDF
        k_bat, a_bat = 0, 0

        with c1:
            st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'><b>PÚBLICO INFANTIL / JUVENIL</b></div>", unsafe_allow_html=True)
            if not df_kids.empty:
                k_bat = len(df_kids[df_kids['batizado_sn'] == 'SIM'])
                st.metric("Batizados (Kids)", f"{k_bat}/{len(df_kids)}")
            else: st.write("Nenhum registro.")

        with c2:
            st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:5px;'><b>PÚBLICO ADULTOS</b></div>", unsafe_allow_html=True)
            if not df_adults.empty:
                a_bat = len(df_adults[df_adults['batizado_sn'] == 'SIM'])
                st.metric("Batizados (Adultos)", f"{a_bat}/{len(df_adults)}")
            else: st.write("Nenhum registro.")

        st.divider()
        st.subheader("🏫 Auditoria Nominal e Pastoral por Turma")
        
        analise_detalhada_ia = []
        if not df_turmas.empty:
            for _, t in df_turmas.iterrows():
                alunos_t = df_cat[df_cat['etapa'] == t['nome_turma']] if not df_cat.empty else pd.DataFrame()
                if not alunos_t.empty:
                    pres_t = df_pres[df_pres['id_turma'] == t['nome_turma']] if not df_pres.empty else pd.DataFrame()
                    freq_media = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100) if not pres_t.empty else 0
                    idades = [calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
                    impedimentos = len(alunos_t[alunos_t['estado_civil_pais_ou_proprio'].isin(['DIVORCIADO(A)', 'CASADO(A) CIVIL'])])
                    
                    batizados = alunos_t[alunos_t['batizado_sn'] == 'SIM']
                    nao_batizados = alunos_t[alunos_t['batizado_sn'] != 'SIM']
                    
                    prev_e = t.get('previsao_eucaristia', 'N/A')
                    prev_c = t.get('previsao_crisma', 'N/A')
                    
                    with st.expander(f"📍 {t['nome_turma']} ({t['etapa']}) - Frequência: {freq_media:.1f}%"):
                        col_p1, col_p2 = st.columns([2, 1])
                        with col_p1:
                            st.write(f"**Faixa Etária:** {min(idades)} a {max(idades)} anos")
                            if impedimentos > 0: st.warning(f"⚠️ {impedimentos} adultos com situação matrimonial a regularizar.")
                            st.markdown("---")
                            cb1, cb2 = st.columns(2)
                            cb1.success(f"✅ Batizados ({len(batizados)})")
                            for n in batizados['nome_completo'].tolist(): st.write(f"· {n}")
                            cb2.error(f"❌ Pendentes ({len(nao_batizados)})")
                            for n in nao_batizados['nome_completo'].tolist(): st.write(f"· {n}")
                        with col_p2:
                            st.markdown("**Previsões:**")
                            st.write(f"Eucaristia: `{prev_e if prev_e else 'N/A'}`")
                            st.write(f"Crisma: `{prev_c if prev_c else 'N/A'}`")

                    analise_detalhada_ia.append({
                        "turma": t['nome_turma'], "etapa": t['etapa'], "freq": f"{freq_media:.1f}%",
                        "idades": f"{min(idades)}-{max(idades)}", "impedimentos_civel": impedimentos,
                        "batizados": len(batizados), "pendentes": len(nao_batizados),
                        "total": len(alunos_t), "prev_e": prev_e, "prev_c": prev_c
                    })

        st.divider()
        # BOTÃO DE GERAR
        if st.button("🏛️ Gerar Auditoria Pastoral Completa (PDF)", key="btn_pdf_sac_v_final"):
            with st.spinner("O Auditor IA está analisando impedimentos e engajamento..."):
                resumo_ia = f"Batismos no Ano: {total_batismos_ano}. Detalhes: {analise_detalhada_ia}"
                analise_ia_sac = gerar_relatorio_sacramentos_ia(resumo_ia)
                
                stats_pdf = {
                    'bat_ano': total_batismos_ano,
                    'bat_k': k_bat, 'euca_k': 0,
                    'bat_a': a_bat, 'euca_a': 0, 'cris_a': 0
                }
                # Gera o PDF e guarda na sessão
                st.session_state.pdf_sac_tecnico = gerar_relatorio_sacramentos_tecnico_pdf(stats_pdf, analise_detalhada_ia, analise_ia_sac)
                st.success("Relatório gerado com sucesso! Clique no botão abaixo para baixar.")

        # BOTÃO DE BAIXAR (Aparece apenas se o PDF já foi gerado)
        if "pdf_sac_tecnico" in st.session_state:
            st.download_button(
                label="📥 Baixar Auditoria Sacramental PDF",
                data=st.session_state.pdf_sac_tecnico,
                file_name=f"Auditoria_Pastoral_Fatima_{date.today().year}.pdf",
                mime="application/pdf",
                key="btn_download_sac_final"
            )
# --- FIM DA SUBSTITUIÇÃO: ABA tab_dash ---

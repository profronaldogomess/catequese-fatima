# ARQUIVO: main.py
import streamlit as st
import pandas as pd
from datetime import date
import time
import os 
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Catequese Fátima", 
    layout="wide", 
    page_icon="✝️",
    initial_sidebar_state="expanded"
)

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
from database import ler_aba, salvar_lote_catequizandos, atualizar_catequizando, conectar_google_sheets, atualizar_turma, salvar_presencas, verificar_login, salvar_encontro, salvar_tema_cronograma, buscar_encontro_por_data, atualizar_usuario, salvar_formacao, salvar_presenca_formacao
from utils import calcular_idade, sugerir_etapa, eh_aniversariante_da_semana, obter_aniversariantes_mes, converter_para_data, verificar_status_ministerial, obter_aniversariantes_hoje, obter_aniversariantes_mes_unificado, gerar_ficha_cadastral_catequizando, gerar_ficha_catequista_pdf

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
        "⚙️ Gestão e Movimentação", 
        "🏫 Gestão de Turmas", 
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
    
    # 1. CARREGAMENTO DE DADOS
    df_cat = ler_aba("catequizandos")
    df_turmas = ler_aba("turmas")
    df_pres = ler_aba("presencas")
    df_usuarios = ler_aba("usuarios") 

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
        total_catequistas = len(df_usuarios) if not df_usuarios.empty else 0
        
        m1.metric("Catequizandos", total_cat)
        m2.metric("Ativos", ativos)
        m3.metric("Total de Turmas", total_t)
        m4.metric("Equipe", total_catequistas)

        st.divider()

        # --- SEÇÃO 2: DESEMPENHO ---
        st.subheader("📈 Desempenho e Frequência")
        if df_pres.empty:
            st.info("Ainda não há registros de presença.")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                df_pres['status_num'] = df_pres['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                freq_turma = df_pres.groupby('id_turma')['status_num'].mean() * 100
                freq_turma = freq_turma.reset_index().rename(columns={'status_num': 'Frequência %', 'id_turma': 'Turma'})
                
                # GRÁFICO COM TEXTO PRETO
                fig = px.bar(freq_turma, x='Turma', y='Frequência %', color='Frequência %', color_continuous_scale=['#e03d11', '#ccd628', '#417b99'])
                fig.update_layout(
                    font=dict(color="#000000"), # Texto Preto
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
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
                for _, niver in df_niver_unificado.iterrows():
                    icone = "🛡️" if niver['tipo'] == 'CATEQUISTA' else "🎁"
                    st.markdown(f"{icone} **Dia {int(niver['dia'])}** - {niver['nome']} ({niver['info']})")
            else:
                st.write("Nenhum aniversariante este mês.")

        with col_evasao:
            st.subheader("🚨 Alerta de Evasão")
            if not df_pres.empty:
                faltas = df_pres[df_pres['status'] == 'AUSENTE'].groupby('nome_catequizando').size().reset_index(name='total_faltas')
                evasao = faltas[faltas['total_faltas'] >= 2].sort_values(by='total_faltas', ascending=False)
                if not evasao.empty:
                    st.warning(f"Existem {len(evasao)} catequizandos com 2 ou mais faltas!")
                    st.dataframe(evasao, use_container_width=True, hide_index=True)
                else:
                    st.success("Nenhum alerta de evasão no momento.")

        # --- SEÇÃO IA ---
        st.divider()
        st.subheader("🤖 Assistente Pastoral (IA Gemini)")
        if st.button("✨ Gerar Relatório Inteligente com IA"):
            with st.spinner("O Gemini está analisando os dados..."):
                temas_vistos = df_pres['tema_do_dia'].unique().tolist() if not df_pres.empty else []
                resumo_para_ia = f"Total: {total_cat}, Freq: {freq_global:.1f}%, Temas: {temas_vistos}"
                from ai_engine import gerar_analise_pastoral
                st.markdown(gerar_analise_pastoral(resumo_para_ia))

# --- PÁGINA: MINHA TURMA ---
elif menu == "🏠 Minha Turma":
    st.title(f"🏠 Painel da Turma: {turma_do_catequista}")
    
    df_cat = ler_aba("catequizandos")
    df_pres = ler_aba("presencas")
    df_enc = ler_aba("encontros")
    df_cron = ler_aba("cronograma")

    meus_alunos = df_cat[df_cat['etapa'] == turma_do_catequista] if not df_cat.empty else pd.DataFrame()
    minhas_pres = df_pres[df_pres['id_turma'] == turma_do_catequista] if not df_pres.empty else pd.DataFrame()
    meus_encontros = df_enc[df_enc['turma'] == turma_do_catequista] if not df_enc.empty else pd.DataFrame()

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
            data_e = st.date_input("Data", date.today())
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
        df_t = ler_aba("turmas")
        
        if papel_usuario == "CATEQUISTA":
            lista_turmas = [turma_do_catequista]
        else:
            lista_turmas = df_t['nome_turma'].tolist() if not df_t.empty else ["SEM TURMAS CADASTRADAS"]

        with st.form("form_cadastro_detalhado"):
            st.subheader("📍 Informações Básicas")
            c1, c2, c3 = st.columns([2, 1, 1])
            nome = c1.text_input("Nome Completo").upper()
            data_nasc = c2.date_input("Data de Nascimento", min_value=date(1930, 1, 1))
            etapa = c3.selectbox("Turma/Etapa", lista_turmas)

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
                if nome and contato:
                    novo_id = f"CAT-{int(time.time())}"
                    registro = [[novo_id, etapa, nome, str(data_nasc), batizado, contato, endereco, nome_mae, nome_pai, responsavel, docs_faltando, pastoral, "ATIVO", medicamento, tgo, estado_civil, sacramentos]]
                    if salvar_lote_catequizandos(registro):
                        st.success(f"✅ {nome} CADASTRADO!")
                        st.balloons()
                else:
                    st.warning("Nome e Contato são obrigatórios.")

    with tab_csv:
        st.subheader("📥 Importação em Massa")
        modo_importacao = st.radio("Como definir as turmas?", ["Fixar uma única turma", "Usar a turma do CSV"], horizontal=True)
        df_t = ler_aba("turmas")
        turma_fixa = None
        
        if modo_importacao == "Fixar uma única turma":
            if not df_t.empty:
                turma_fixa = st.selectbox("Selecione a turma de destino:", df_t['nome_turma'].tolist())
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

# --- PÁGINA: GESTÃO E MOVIMENTAÇÃO ---
elif menu == "⚙️ Gestão e Movimentação":
    st.title("⚙️ Gestão e Movimentação")
    df_cat = ler_aba("catequizandos")
    df_turmas = ler_aba("turmas")
    
    if df_cat.empty:
        st.warning("⚠️ Nenhum catequizando encontrado.")
    else:
        c1, c2 = st.columns(2)
        busca = c1.text_input("🔍 Buscar por nome:").upper()
        lista_t = ["TODAS"] + df_turmas['nome_turma'].tolist() if not df_turmas.empty else ["TODAS"]
        filtro_t = c2.selectbox("Filtrar por Turma:", lista_t)

        df_f = df_cat
        if busca: df_f = df_f[df_f['nome_completo'].astype(str).str.contains(busca)]
        if filtro_t != "TODAS": df_f = df_f[df_f['etapa'] == filtro_t]

        st.dataframe(df_f[['id_catequizando', 'nome_completo', 'etapa', 'status']], use_container_width=True)
        st.divider()
        escolha = st.selectbox("Selecione um catequizando para EDITAR COMPLETAMENTE:", [""] + df_f['nome_completo'].tolist())

        if escolha:
            dados = df_cat[df_cat['nome_completo'] == escolha].iloc[0]
            idade = calcular_idade(dados.get('data_nascimento', ''))
            sugestao = sugerir_etapa(dados.get('data_nascimento', ''))
            st.info(f"💡 **Análise:** Idade: {idade} anos | Sugestão de Etapa: {sugestao}")

            # --- BOTÃO DE GERAR FICHA PDF (CATEQUIZANDO) ---
            if st.button(f"📄 Baixar Ficha de {escolha}"):
                pdf_bytes = gerar_ficha_cadastral_catequizando(dados.to_dict())
                st.download_button("📥 Download PDF", pdf_bytes, f"Ficha_{escolha}.pdf", "application/pdf")
            # -----------------------------------------------

            with st.form("edicao_completa_catequizando"):
                st.subheader("📍 1. Informações de Cadastro e Turma")
                col1, col2, col3 = st.columns([2, 1, 1])
                n_nome = col1.text_input("Nome Completo", value=str(dados.get('nome_completo', ''))).upper()
                n_etapa = col2.selectbox("Turma Atual", df_turmas['nome_turma'].tolist(), 
                                        index=df_turmas['nome_turma'].tolist().index(dados['etapa']) if dados['etapa'] in df_turmas['nome_turma'].tolist() else 0)
                n_status = col3.selectbox("Status no Sistema", ["ATIVO", "INATIVO", "DESISTENTE", "SACRAMENTADO"],
                                         index=["ATIVO", "INATIVO", "DESISTENTE", "SACRAMENTADO"].index(dados['status']) if dados['status'] in ["ATIVO", "INATIVO", "DESISTENTE", "SACRAMENTADO"] else 0)

                st.divider()
                st.subheader("⛪ 2. Vida Sacramental e Religiosa")
                col4, col5, col6 = st.columns(3)
                n_batizado = col4.selectbox("Já é Batizado?", ["SIM", "NÃO"], 
                                           index=0 if str(dados.get('batizado_sn', 'NÃO')).upper() == "SIM" else 1)
                n_pastoral = col5.text_input("Participa de Pastoral?", value=str(dados.get('engajado_grupo', ''))).upper()
                
                sac_atuais = str(dados.get('sacramentos_ja_feitos', '')).upper()
                st.write("Sacramentos já realizados:")
                c_bat = col6.checkbox("Batismo", value="BATISMO" in sac_atuais)
                c_euc = col6.checkbox("Eucaristia", value="EUCARISTIA" in sac_atuais)
                c_cri = col6.checkbox("Crisma", value="CRISMA" in sac_atuais)
                
                lista_s = []
                if c_bat: lista_s.append("BATISMO")
                if c_euc: lista_s.append("EUCARISTIA")
                if c_cri: lista_s.append("CRISMA")
                n_sacramentos = ", ".join(lista_s)

                st.divider()
                st.subheader("📞 3. Contatos e Família")
                col7, col8 = st.columns(2)
                n_contato = col7.text_input("Telefone/WhatsApp Principal", value=str(dados.get('contato_principal', '')))
                n_endereco = col8.text_input("Endereço Completo", value=str(dados.get('endereco_completo', ''))).upper()
                
                col9, col10, col11 = st.columns(3)
                n_mae = col9.text_input("Nome da Mãe", value=str(dados.get('nome_mae', ''))).upper()
                n_pai = col10.text_input("Nome do Pai", value=str(dados.get('nome_pai', ''))).upper()
                n_resp = col11.text_input("Responsável Legal", value=str(dados.get('nome_responsavel', ''))).upper()

                st.divider()
                st.subheader("🏥 4. Saúde e Observações")
                col12, col13 = st.columns(2)
                n_med = col12.text_input("Medicamentos / Alergias", value=str(dados.get('toma_medicamento_sn', ''))).upper()
                n_tgo = col12.selectbox("Possui TGO?", ["NÃO", "SIM"], 
                                       index=0 if str(dados.get('tgo_sn', 'NÃO')).upper() == "NÃO" else 1)
                n_docs = col13.text_area("Documentos em Falta / Observações", value=str(dados.get('doc_em_falta', ''))).upper()
                
                n_est_civil = str(dados.get('estado_civil_pais_ou_proprio', 'N/A'))

                if st.form_submit_button("💾 SALVAR TODAS AS ALTERAÇÕES"):
                    lista_atualizada = [
                        str(dados['id_catequizando']), n_etapa, n_nome, str(dados['data_nascimento']),
                        n_batizado, n_contato, n_endereco, n_mae, n_pai, n_resp, n_docs, n_pastoral,
                        n_status, n_med, n_tgo, n_est_civil, n_sacramentos
                    ]
                    if atualizar_catequizando(dados['id_catequizando'], lista_atualizada):
                        st.success(f"✅ Os dados de {n_nome} foram atualizados com sucesso!")
                        time.sleep(1)
                        st.rerun()

# --- PÁGINA: GESTÃO DE TURMAS ---
elif menu == "🏫 Gestão de Turmas":
    import plotly.express as px
    st.title("🏫 Gestão de Turmas")
    
    df_turmas = ler_aba("turmas")
    df_cat = ler_aba("catequizandos")
    df_pres = ler_aba("presencas")
    df_usuarios = ler_aba("usuarios")
    
    t1, t2, t3, t4 = st.tabs(["Visualizar Turmas", "➕ Criar Nova Turma", "✏️ Detalhes e Edição", "📊 Dashboard Local"])
    dias_opcoes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

    with t1:
        if not df_turmas.empty: st.dataframe(df_turmas, use_container_width=True)
        else: st.info("Nenhuma turma cadastrada.")
            
    with t2:
        st.subheader("Cadastrar Nova Turma")
        with st.form("nova_turma_v3"):
            c1, c2 = st.columns(2)
            n_t = c1.text_input("Nome da Turma (Ex: PRÉ 2025)").upper()
            e_t = c1.selectbox("Etapa Base", ["PRÉ", "PRIMEIRA ETAPA", "SEGUNDA ETAPA", "TERCEIRA ETAPA", "PERSEVERANÇA", "ADULTOS"])
            ano = c2.number_input("Ano Letivo", value=2025)
            n_dias = st.multiselect("Dias de Encontro:", dias_opcoes)
            
            lista_nomes_disponiveis = df_usuarios['nome'].astype(str).unique().tolist() if not df_usuarios.empty else []
            selecao_catequistas = st.multiselect("Catequistas Responsáveis:", lista_nomes_disponiveis)

            if st.form_submit_button("CRIAR TURMA"):
                if n_t and selecao_catequistas and n_dias:
                    catequistas_str = ", ".join(selecao_catequistas)
                    dias_str = ", ".join(n_dias)
                    conectar_google_sheets().worksheet("turmas").append_row([f"TRM-{int(time.time())}", n_t, e_t, ano, catequistas_str, dias_str])
                    st.success(f"Turma {n_t} criada!")
                    st.rerun()
                else:
                    st.error("Preencha Nome, Catequistas e Dias da Semana.")

    with t3:
        if not df_turmas.empty:
            st.subheader("✏️ Editar Turma Existente")
            turma_para_editar = st.selectbox("Selecione a turma:", [""] + df_turmas['nome_turma'].tolist())
            if turma_para_editar:
                dados_t = df_turmas[df_turmas['nome_turma'] == turma_para_editar].iloc[0]
                with st.form("form_edicao_turma_v3"):
                    c1, c2 = st.columns(2)
                    ed_nome = c1.text_input("Nome da Turma", value=str(dados_t['nome_turma'])).upper()
                    ed_ano = c2.number_input("Ano Letivo", value=int(dados_t['ano']))
                    
                    dias_atuais = str(dados_t.get('dias_semana', '')).split(", ")
                    ed_dias = st.multiselect("Dias de Encontro:", dias_opcoes, default=[d for d in dias_atuais if d in dias_opcoes])
                    
                    lista_nomes = df_usuarios['nome'].astype(str).unique().tolist() if not df_usuarios.empty else []
                    cats_salvos = str(dados_t.get('catequista_responsavel', ''))
                    cats_atuais = [c.strip() for c in cats_salvos.split(",")] if cats_salvos else []
                    ed_selecao_cats = st.multiselect("Equipe de Catequistas:", lista_nomes, default=[c for c in cats_atuais if c in lista_nomes])

                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        lista_up = [str(dados_t['id_turma']), ed_nome, str(dados_t['etapa']), ed_ano, ", ".join(ed_selecao_cats), ", ".join(ed_dias)]
                        if atualizar_turma(dados_t['id_turma'], lista_up):
                            st.success("Turma atualizada!")
                            time.sleep(1)
                            st.rerun()

    with t4:
        if not df_turmas.empty:
            st.subheader("📊 Inteligência de Turma")
            turma_alvo = st.selectbox("Selecione a turma para análise profunda:", df_turmas['nome_turma'].tolist())
            dados_t = df_turmas[df_turmas['nome_turma'] == turma_alvo].iloc[0]
            df_cat_t = df_cat[df_cat['etapa'] == turma_alvo] if not df_cat.empty else pd.DataFrame()
            df_pres_t = df_pres[df_pres['id_turma'] == turma_alvo] if not df_pres.empty else pd.DataFrame()
            
            c1, c2, c3, c4 = st.columns(4)
            total_cat = len(df_cat_t)
            ativos = len(df_cat_t[df_cat_t['status'] == 'ATIVO']) if not df_cat_t.empty else 0
            encontros = df_pres_t['data_encontro'].nunique() if not df_pres_t.empty else 0
            freq_local = 0
            if not df_pres_t.empty:
                df_pres_t['status_num'] = df_pres_t['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                freq_local = df_pres_t['status_num'].mean() * 100
            c4.metric("Taxa de Presença", f"{freq_local:.1f}%")

            st.divider()
            col_graf, col_evasao = st.columns([2, 1])
            with col_graf:
                st.write("📈 **Frequência por Encontro**")
                if not df_pres_t.empty:
                    evolucao = df_pres_t.groupby('data_encontro')['status_num'].mean() * 100
                    fig = px.line(evolucao.reset_index(), x='data_encontro', y='status_num', markers=True)
                    fig.update_traces(line_color='#e03d11')
                    fig.update_layout(font=dict(color="#000000"), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            with col_evasao:
                st.write("🚨 **Alerta de Evasão Local**")
                if not df_pres_t.empty:
                    faltas = df_pres_t[df_pres_t['status'] == 'AUSENTE'].groupby('nome_catequizando').size().reset_index(name='faltas')
                    criticos = faltas[faltas['faltas'] >= 2]
                    if not criticos.empty: st.dataframe(criticos, hide_index=True)
                    else: st.success("Nenhum risco detectado")

            st.divider()
            if st.button(f"✨ Gerar Perfil Completo de {turma_alvo}"):
                with st.spinner("A IA está analisando a turma e preparando o PDF..."):
                    temas = df_pres_t['tema_do_dia'].unique().tolist() if not df_pres_t.empty else []
                    resumo = f"Freq: {freq_local:.1f}%, Alunos: {total_cat}, Encontros: {encontros}, Temas: {temas}"
                    from ai_engine import analisar_turma_local
                    analise_ia = analisar_turma_local(turma_alvo, resumo)
                    
                    metricas_pdf = {"Total de Catequizandos": total_cat, "Alunos Ativos": ativos, "Frequência Média": f"{freq_local:.1f}%", "Encontros Realizados": encontros, "Equipe Responsável": dados_t['catequista_responsavel']}
                    lista_alunos_pdf = df_cat_t['nome_completo'].tolist() if not df_cat_t.empty else []
                    
                    from utils import gerar_pdf_perfil_turma
                    pdf_bytes = gerar_pdf_perfil_turma(turma_alvo, metricas_pdf, analise_ia, lista_alunos_pdf)
                    
                    st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"Perfil_{turma_alvo}.pdf", mime="application/pdf")

# --- PÁGINA: FAZER CHAMADA ---
elif menu == "✅ Fazer Chamada":
    st.title("✅ Chamada Inteligente")
    df_turmas = ler_aba("turmas")
    df_cat = ler_aba("catequizandos")
    
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
        data_encontro = col2.date_input("Data do Encontro", date.today())
        
        tema_encontrado = buscar_encontro_por_data(turma_selecionada, data_encontro)
        tema_sugerido = ""
        if tema_encontrado:
            tema_sugerido = tema_encontrado
            st.info(f"📖 Tema recuperado do Diário para o dia {data_encontro}")
        else:
            df_pres = ler_aba("presencas")
            df_cron = ler_aba("cronograma")
            if not df_cron.empty:
                temas_feitos = df_pres[df_pres['id_turma'] == turma_selecionada]['tema_do_dia'].unique().tolist() if not df_pres.empty else []
                proximos = df_cron[(df_cron['etapa'] == turma_selecionada) & (~df_cron['titulo_tema'].isin(temas_feitos))]
                if not proximos.empty:
                    tema_sugerido = proximos.iloc[0]['titulo_tema']
                    st.info(f"💡 Sugestão baseada no seu cronograma: {tema_sugerido}")

        tema_dia = st.text_input("Tema do Encontro (Confirme ou altere):", value=tema_sugerido).upper()
        lista_chamada = df_cat[(df_cat['etapa'] == turma_selecionada) & (df_cat['status'] == 'ATIVO')]
        
        if lista_chamada.empty:
            st.info(f"Nenhum catequizando ativo na turma {turma_selecionada}.")
        else:
            st.subheader(f"Lista de Presença - {len(lista_chamada)} Catequizandos")
            with st.form("form_chamada_v2"):
                registros_presenca = []
                h1, h2, h3 = st.columns([3, 1, 2])
                h1.write("**Nome**"); h2.write("**Presença**"); h3.write("**Avisos**")
                st.divider()

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
    df_usuarios = ler_aba("usuarios")
    df_turmas = ler_aba("turmas")
    df_formacoes = ler_aba("formacoes")
    df_pres_form = ler_aba("presenca_formacao")
    
    tab_dash, tab_lista, tab_novo, tab_formacao = st.tabs(["📊 Dashboard de Equipe", "📋 Lista e Perfil", "➕ Novo Acesso", "🎓 Registro de Formação"])

    with tab_dash:
        if not df_usuarios.empty:
            df_usuarios.columns = [c.strip().lower() for c in df_usuarios.columns]
            catequistas_so = df_usuarios[df_usuarios['papel'].isin(['CATEQUISTA', 'COORDENADOR', 'ADMIN'])]
            total_c = len(catequistas_so)
            cont_ministros, cont_aptos, cont_caminhada = 0, 0, 0
            
            for _, row in catequistas_so.iterrows():
                status, _ = verificar_status_ministerial(str(row.get('data_inicio_catequese', '')), str(row.get('data_batismo', '')), str(row.get('data_eucaristia', '')), str(row.get('data_crisma', '')), str(row.get('data_ministerio', '')))
                if status == "MINISTRO": cont_ministros += 1
                elif status == "APTO": cont_aptos += 1
                else: cont_caminhada += 1

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Catequistas", total_c)
            m2.metric("Ministros", cont_ministros)
            m3.metric("Aptos", cont_aptos)
            m4.metric("Em Caminhada", cont_caminhada)

            st.divider()
            
            # --- LISTA DE FORMAÇÕES DO ANO VIGENTE (NOVO) ---
            st.subheader(f"🎓 Formações Realizadas em {date.today().year}")
            if not df_formacoes.empty:
                # Filtra pelo ano atual
                df_formacoes['data_dt'] = pd.to_datetime(df_formacoes['data'], errors='coerce')
                forms_ano = df_formacoes[df_formacoes['data_dt'].dt.year == date.today().year]
                if not forms_ano.empty:
                    st.dataframe(forms_ano[['tema', 'data', 'formador', 'local']], use_container_width=True)
                else: st.info("Nenhuma formação registrada este ano.")
            else: st.info("Sem registros de formação.")
            # ------------------------------------------------

            st.divider()
            st.subheader("🎓 Engajamento Geral")
            if not df_formacoes.empty:
                total_f = len(df_formacoes)
                participacao_total = len(df_pres_form) if not df_pres_form.empty else 0
                potencial = total_c * total_f
                porcentagem = (participacao_total / potencial) * 100 if potencial > 0 else 0
                f1, f2 = st.columns(2)
                f1.metric("Formações Totais", total_f)
                f2.metric("Presença Média", f"{porcentagem:.1f}%")
                st.progress(porcentagem / 100)

    with tab_lista:
        if not df_usuarios.empty:
            busca_c = st.text_input("🔍 Buscar Catequista por nome:").upper()
            df_c_filtrado = df_usuarios[df_usuarios['nome'].astype(str).str.contains(busca_c)] if busca_c else df_usuarios
            st.dataframe(df_c_filtrado[['nome', 'email', 'turma_vinculada', 'papel']], use_container_width=True)
            
            st.divider()
            escolha_c = st.selectbox("Selecione um Catequista para EDITAR:", [""] + df_c_filtrado['nome'].tolist())
            
            if escolha_c:
                u = df_usuarios[df_usuarios['nome'] == escolha_c].iloc[0]
                status_min, tempo = verificar_status_ministerial(str(u.get('data_inicio_catequese', '')), str(u.get('data_batismo', '')), str(u.get('data_eucaristia', '')), str(u.get('data_crisma', '')), str(u.get('data_ministerio', '')))
                if status_min == "MINISTRO": st.success(f"📜 **MINISTRO INSTITUÍDO** (Desde: {u.get('data_ministerio')})")
                elif status_min == "APTO": st.warning(f"🌟 **APTO AO MINISTÉRIO** ({tempo} anos)")
                else: st.info(f"🌱 Caminhada: {tempo} anos.")

                # --- HISTÓRICO DE FORMAÇÕES (COM CORREÇÃO DE ERRO) ---
                st.divider()
                st.subheader("🎓 Histórico de Formações Realizadas")
                forms_participadas = pd.DataFrame() # Inicializa vazio
                
                if not df_pres_form.empty and not df_formacoes.empty:
                    # CORREÇÃO DO ERRO KEYERROR:
                    # Se a planilha não tiver cabeçalho, renomeamos as colunas na força bruta
                    if 'email_participante' not in df_pres_form.columns:
                        if len(df_pres_form.columns) >= 2:
                            # Assume que a coluna 0 é ID e a 1 é Email
                            df_pres_form.columns.values[0] = 'id_formacao'
                            df_pres_form.columns.values[1] = 'email_participante'
                    
                    # Agora tentamos filtrar com segurança
                    if 'email_participante' in df_pres_form.columns:
                        minhas_forms = df_pres_form[df_pres_form['email_participante'] == u['email']]
                        if not minhas_forms.empty:
                            # Padroniza colunas de formações para o merge
                            if len(df_formacoes.columns) >= 5:
                                df_formacoes.columns.values[0] = 'id_formacao'
                                df_formacoes.columns.values[1] = 'tema'
                                df_formacoes.columns.values[2] = 'data'
                                df_formacoes.columns.values[4] = 'formador'
                            
                            # Garante que a coluna de junção tem o mesmo nome
                            cols_f = df_formacoes.columns.tolist()
                            if 'id_formacao' not in cols_f: 
                                df_formacoes.rename(columns={cols_f[0]: 'id_formacao'}, inplace=True)

                            forms_participadas = minhas_forms.merge(df_formacoes, on='id_formacao', how='inner')
                            st.table(forms_participadas[['data', 'tema', 'formador']])
                        else:
                            st.info("Este catequista ainda não participou de formações registradas.")
                    else:
                        st.warning("Aviso: A aba 'presenca_formacao' na planilha parece estar vazia ou sem cabeçalho.")
                else:
                    st.info("Sem registros de formação no sistema.")
                
                # --- BOTÃO PDF CATEQUISTA ---
                if st.button(f"📄 Baixar Ficha de {escolha_c}"):
                    pdf_bytes = gerar_ficha_catequista_pdf(u.to_dict(), forms_participadas)
                    st.download_button("📥 Download Ficha Catequista", pdf_bytes, f"Ficha_{escolha_c}.pdf", "application/pdf")
                # ----------------------------
                st.divider()

                with st.form("edicao_catequista_final"):
                    st.subheader("📍 Informações e Acesso")
                    c1, c2, c3 = st.columns(3)
                    ed_nome = c1.text_input("Nome Completo", value=str(u.get('nome', ''))).upper()
                    ed_email = c2.text_input("E-mail (Login)", value=str(u.get('email', '')), disabled=True)
                    ed_senha = c3.text_input("Senha", value=str(u.get('senha', '')), type="password")
                    
                    c4, c5 = st.columns(2)
                    ed_tel = c4.text_input("Telefone", value=str(u.get('telefone', '')))
                    ed_nasc = c5.date_input("Nascimento", value=converter_para_data(str(u.get('data_nascimento', ''))))
                    
                    lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else []
                    turmas_atuais = str(u.get('turma_vinculada', '')).split(", ")
                    ed_turmas = st.multiselect("Turmas Vinculadas", lista_t_nomes, default=[t for t in turmas_atuais if t in lista_t_nomes])
                    
                    st.divider()
                    st.subheader("⛪ Vida Sacramental")
                    d1, d2, d3, d4 = st.columns(4)
                    ed_inicio = d1.date_input("Início Catequese", value=converter_para_data(str(u.get('data_inicio_catequese', ''))))
                    ed_batismo = d2.date_input("Batismo", value=converter_para_data(str(u.get('data_batismo', ''))))
                    ed_euca = d3.date_input("Eucaristia", value=converter_para_data(str(u.get('data_eucaristia', ''))))
                    ed_crisma = d4.date_input("Crisma", value=converter_para_data(str(u.get('data_crisma', ''))))
                    
                    st.divider()
                    st.subheader("🎖️ Ministério")
                    m1, m2 = st.columns([1, 2])
                    ja_e_min = m1.checkbox("Já é Ministro?", value=(status_min == "MINISTRO"))
                    ed_data_min = m2.date_input("Data Instituição", value=converter_para_data(str(u.get('data_ministerio', '')))) if ja_e_min else ""

                    if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                        dados_up = [ed_nome, ed_email, ed_senha, str(u.get('papel', 'CATEQUISTA')), ", ".join(ed_turmas), ed_tel, str(ed_nasc), str(ed_inicio), str(ed_batismo), str(ed_euca), str(ed_crisma), str(ed_data_min) if ja_e_min else ""]
                        if atualizar_usuario(ed_email, dados_up):
                            st.success("Atualizado!"); time.sleep(1); st.rerun()

    with tab_novo:
        st.subheader("➕ Criar Novo Acesso")
        with st.form("form_novo_usuario_completo"):
            c1, c2, c3 = st.columns(3)
            n_nome = c1.text_input("Nome Completo").upper()
            n_email = c2.text_input("E-mail (Login)")
            n_senha = c3.text_input("Senha Inicial")
            
            c4, c5, c6 = st.columns(3)
            n_papel = c4.selectbox("Papel", ["CATEQUISTA", "COORDENADOR"])
            n_tel = c5.text_input("Telefone")
            n_nasc = c6.date_input("Nascimento", value=date(1990, 1, 1))
            
            n_turmas = st.multiselect("Vincular às Turmas", df_turmas['nome_turma'].tolist() if not df_turmas.empty else [])
            n_inicio = st.date_input("Início como Catequista", value=date.today())
            
            if st.form_submit_button("🚀 CRIAR ACESSO"):
                if n_nome and n_email and n_senha:
                    conectar_google_sheets().worksheet("usuarios").append_row([n_nome, n_email, n_senha, n_papel, ", ".join(n_turmas), n_tel, str(n_nasc), str(n_inicio), "", "", "", ""])
                    st.success("Criado!"); st.rerun()

    with tab_formacao:
        st.subheader("🎓 Registro de Formação e Presenças")
        with st.form("nova_formacao_presenca"):
            f_tema = st.text_input("Tema da Formação").upper()
            f_data = st.date_input("Data")
            f_local = st.text_input("Local").upper()
            f_formador = st.text_input("Formador").upper()
            
            st.write("👥 **Quem participou?**")
            todos_usuarios = df_usuarios[df_usuarios['papel'].isin(['CATEQUISTA', 'COORDENADOR', 'ADMIN'])]
            dict_cat = dict(zip(todos_usuarios['nome'], todos_usuarios['email']))
            participantes = st.multiselect("Selecione os presentes (Catequistas e Coordenação):", list(dict_cat.keys()))
            
            f_obs = st.text_area("Observações")
            
            if st.form_submit_button("💾 REGISTRAR FORMAÇÃO"):
                if f_tema and participantes:
                    id_f = f"FOR-{int(time.time())}"
                    if salvar_formacao([id_f, f_tema, str(f_data), f_local, f_formador, f_obs]):
                        lista_p = [[id_f, dict_cat[nome]] for nome in participantes]
                        if salvar_presenca_formacao(lista_p):
                            st.success("Formação e Presenças registradas!"); st.balloons(); st.rerun()

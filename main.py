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
# Inicialização direta sem cache para evitar o CachedWidgetWarning (tarja amarela)
cookie_manager = stx.CookieManager(key="catequese_fatima_cookies_v4")

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
    registrar_evento_sacramento_completo, salvar_reuniao_pais, salvar_presenca_reuniao_pais, 
    atualizar_reuniao_pais, sincronizar_logistica_turma_nos_catequizandos, sincronizar_renomeacao_turma_geral,
    marcar_tema_realizado_cronograma, carregar_dados_globais, sincronizar_edicao_catequizando, 
    salvar_com_seguranca, atualizar_encontro_global, excluir_encontro_cascata,
    gerenciar_edicao_evento_sacramento, excluir_evento_sacramento_cascata
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
    gerar_relatorio_sacramentos_tecnico_pdf,gerar_auditoria_chamadas_pendentes,gerar_pdf_auditoria_chamadas, obter_data_ultimo_sabado, obter_ultima_chamada_turma, gerar_livro_sacramentos_pdf
)
from ai_engine import (
    gerar_analise_pastoral, gerar_mensagem_whatsapp, 
    analisar_turma_local, gerar_relatorio_sacramentos_ia, analisar_saude_familiar_ia, 
    gerar_mensagem_reacolhida_ia, gerar_mensagem_cobranca_doc_ia, gerar_mensagem_atualizacao_cadastral_ia
)

# --- 6. FUNÇÕES AUXILIARES DE INTERFACE ---
def montar_botoes_whatsapp(dados):
    """Monta dinamicamente os botões de WhatsApp baseados no perfil."""
    idade = calcular_idade(dados['data_nascimento'])
    botoes = []
    
    # Função auxiliar para limpar e formatar tel
    def formatar_wa(tel):
        if not tel or str(tel).strip() in ["N/A", "", "None"]: return None
        num = "".join(filter(str.isdigit, str(tel)))
        if num.startswith("0"): num = num[1:]
        return f"5573{num}" if len(num) <= 9 else f"55{num}"

    if idade >= 18:
        # Adulto: Próprio, Emergência
        if (tel := formatar_wa(dados.get('contato_principal'))): botoes.append(("👤 Próprio", tel))
        if (tel := formatar_wa(dados.get('obs_pastoral_familia', '').split('TEL: ')[-1] if 'TEL: ' in dados.get('obs_pastoral_familia', '') else None)):
            botoes.append(("🚨 Emerg.", tel))
    else:
        # Criança: Mãe, Pai, Cuidador/Emergência
        if (tel := formatar_wa(dados.get('tel_mae'))): botoes.append(("👩‍🦱 Mãe", tel))
        if (tel := formatar_wa(dados.get('tel_pai'))): botoes.append(("👨‍🦱 Pai", tel))
        # O Emergência/Cuidador está no índice 13 (Coluna N)
        if (tel := formatar_wa(dados.get('nome_responsavel', '').split('TEL: ')[-1] if 'TEL: ' in dados.get('nome_responsavel', '') else None)):
             botoes.append(("🛡️ Resp.", tel))

    # Renderização dos botões (Clean UI Mobile-First)
    cols = st.columns(len(botoes) if botoes else 1)
    for i, (label, tel) in enumerate(botoes):
        cols[i].markdown(f'''<a href="https://wa.me/{tel}" target="_blank" style="text-decoration:none;"><div style="border: 1px solid #417b99; color:#417b99; text-align:center; padding:8px; border-radius:5px; font-weight:600; font-size:13px; transition: 0.3s;">💬 Contatar {label}</div></a>''', unsafe_allow_html=True)

def mostrar_logo_sidebar():
    if os.path.exists("logo.png"):
        c1, c2, c3 = st.sidebar.columns([1, 3, 1])
        with c2: st.image("logo.png", width=130)
    else: st.sidebar.title("Catequese Fátima")

def mostrar_logo_login():
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    else: st.markdown("<h1 style='text-align: center; color: #e03d11;'>✝️</h1>", unsafe_allow_html=True)

# --- 7. LÓGICA DE PERSISTÊNCIA E SESSÃO ÚNICA (BLINDADA) ---

# 1. Tentativa de Restauração via Cookie (Resiliência a Quedas de Internet)
# Adicionamos a trava "logout_em_curso" para impedir que o sistema puxe o cookie fantasma logo após o clique em Sair
if not st.session_state.get('logado', False) and not st.session_state.get('logout_em_curso', False):
    # O CookieManager pode demorar milissegundos para carregar. 
    # Se ele retornar None, mas o navegador tiver o cookie, ele vai forçar um rerun automático.
    auth_cookie = cookie_manager.get("fatima_auth_v4")
    if auth_cookie and isinstance(auth_cookie, dict) and auth_cookie.get('email'):
        with st.spinner("🔄 Restaurando sua conexão segura..."):
            user = verificar_login(auth_cookie.get('email'), auth_cookie.get('senha'))
            if user:
                st.session_state.logado = True
                st.session_state.usuario = user
                # Adota o ID atual do banco para não se auto-derrubar
                sid_atual = obter_session_id_db(user['email'])
                if not sid_atual:
                    sid_atual = str(uuid.uuid4())
                    atualizar_session_id(user['email'], sid_atual)
                st.session_state.session_id = sid_atual
                st.rerun()

# 2. Verificação de Concorrência (Sessão Única)
if st.session_state.get('logado') and st.session_state.get('usuario'):
    sid_no_db = obter_session_id_db(st.session_state.usuario['email'])
    # Se o ID no banco for diferente do ID da sessão atual, alguém logou em outro lugar
    if sid_no_db and sid_no_db != st.session_state.session_id:
        st.session_state.sessao_derrubada = True
        st.session_state.logado = False
        try: cookie_manager.delete("fatima_auth_v4")
        except: pass

# 3. Tela Informativa de Desconexão
if st.session_state.get('sessao_derrubada'):
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.error("🚨 **ACESSO ENCERRADO: NOVA CONEXÃO DETECTADA**")
    st.markdown(f"""
        <div style='background-color:#fff5f5; padding:20px; border-radius:10px; border:2px solid #e03d11; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color:#e03d11; margin-top:0;'>Sessão Interrompida por Segurança</h3>
            <p style='color:#333; font-size:16px;'>Identificamos que a conta <b>{st.session_state.usuario.get('email', '') if st.session_state.get('usuario') else 'sua conta'}</b> acabou de ser conectada em <b>outro dispositivo ou navegador</b>.</p>
            <p style='color:#333; font-size:15px;'>O sistema Catequese Fátima permite apenas <b>um acesso ativo por usuário</b>. Isso garante a integridade do banco de dados e evita que duas pessoas editem a mesma chamada ou cadastro ao mesmo tempo.</p>
            <hr style='border-color:#fbd5d5;'>
            <p style='color:#666; font-size:13px;'><i>💡 <b>Dica:</b> Se a sua internet caiu e voltou, o sistema pode ter gerado uma nova conexão. Basta fazer o login novamente. Se não foi você quem acessou, avise a coordenação.</i></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 FAZER LOGIN NOVAMENTE", use_container_width=True, type="primary"):
        st.session_state.sessao_derrubada = False
        st.session_state.usuario = None
        st.session_state.session_id = None
        st.rerun()
    st.stop()

# 4. Tela de Login
if not st.session_state.logado:
    if st.session_state.get('logout_em_curso'):
        st.session_state.logout_em_curso = False
        
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        mostrar_logo_login()
        st.markdown(f"<h2 style='text-align: center; color: {cor_sidebar};'>Acesso Restrito</h2>", unsafe_allow_html=True)
        
        # Verifica se o cookie manager ainda está inicializando (dicionário vazio no primeiro milissegundo)
        if cookie_manager.get_all() == {}:
            st.info("⏳ Verificando credenciais salvas...")
            
        email_login = st.text_input("E-mail")
        senha_login = st.text_input("Senha", type="password")
        lembrar = st.checkbox("Manter conectado (Reconecta automático se a internet cair)", value=True)
        
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
                else: st.error("Erro ao validar sessão única. Tente novamente.")
            else: st.error("🚫 E-mail ou senha incorretos.")
    st.stop()

# --- 8. CARREGAMENTO GLOBAL DE DADOS ---
dados_globais = carregar_dados_globais()

# Gatekeeper: Verifica se os dados vieram vazios devido ao Erro 429 (Quota Exceeded)
if dados_globais and not dados_globais["turmas"].empty and not dados_globais["catequizandos"].empty:
    df_cat = dados_globais["catequizandos"]
    df_turmas = dados_globais["turmas"]
    df_pres = dados_globais["presencas"]
    df_usuarios = dados_globais["usuarios"]
    df_sac_eventos = dados_globais["sacramentos_eventos"]
    df_pres_reuniao = dados_globais["presenca_reuniao"]
else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.warning("⏳ **SISTEMA EM SINCRONIZAÇÃO (ALTO TRÁFEGO)**")
    st.info("""
    **O que aconteceu?** Muitos catequistas estão acessando o sistema neste exato segundo e o servidor do Google atingiu o limite de leituras por minuto.
    
    **Meus dados foram perdidos?** NÃO! Se você acabou de salvar uma chamada ou cadastro, **os dados foram salvos com sucesso no banco**. O sistema apenas pausou a tela para não sobrecarregar.
    
    **O que fazer?** Aguarde cerca de 30 segundos e clique no botão abaixo para recarregar a tela com seus dados atualizados.
    """)
    if st.button("🔄 RECARREGAR SISTEMA", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

equipe_tecnica = df_usuarios[~df_usuarios['papel'].isin(['ADMIN', 'SECRETARIA'])] if not df_usuarios.empty else pd.DataFrame()

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
    # Sobrescrevemos o cookie com vazio para matá-lo instantaneamente no navegador
    cookie_manager.set("fatima_auth_v4", "", expires_at=dt_module.datetime.now())
    try: cookie_manager.delete("fatima_auth_v4")
    except: pass
    
    st.session_state.logado = False
    st.session_state.session_id = None
    st.session_state.usuario = None
    
    # Dá meio segundo para o navegador processar a exclusão antes de recarregar
    time.sleep(0.5) 
    st.rerun()

papel_usuario = st.session_state.usuario.get('papel', 'CATEQUISTA').upper()
turma_do_catequista = st.session_state.usuario.get('turma_vinculada', 'TODAS')
eh_gestor = papel_usuario in["COORDENADOR", "ADMIN"]
eh_secretaria = papel_usuario == "SECRETARIA"

# Lista de menus para catequistas comuns
menu_catequista =[
    "📚 Minha Turma", 
    "👤 Perfil Individual",
    "👨‍👩‍👧‍👦 Gestão Familiar", 
    "📖 Diário de Encontros", 
    "✅ Fazer Chamada", 
    "📝 Inscrever Catequizando",
    "⚙️ Meu Cadastro"
]

if eh_gestor:
    menu = st.sidebar.radio("MENU PRINCIPAL",[
        "🏠 Início / Dashboard", "📚 Minha Turma", "👨‍👩‍👧‍👦 Gestão Familiar", 
        "📖 Diário de Encontros", "📝 Inscrever Catequizando", "👤 Perfil Individual", 
        "🏫 Gestão de Turmas", "🕊️ Gestão de Sacramentos", "👥 Gestão de Catequistas", "✅ Fazer Chamada", "⚙️ Meu Cadastro"
    ])
elif eh_secretaria:
    menu = st.sidebar.radio("MENU DA SECRETARIA",[
        "📊 Painel da Secretaria", "🏫 Visão de Turmas e Equipe", "👤 Perfil Individual", 
        "📝 Inscrever Catequizando", "🕊️ Acervo de Sacramentos", "📖 Consulta de Encontros", "⚙️ Meu Cadastro"
    ])
else:
    menu = st.sidebar.radio("MENU DO CATEQUISTA", menu_catequista)

# ==============================================================================
# PÁGINA 1: DASHBOARD DE INTELIGÊNCIA PASTORAL (TORRE DE CONTROLE)
# ==============================================================================
if menu == "🏠 Início / Dashboard":
    st.title("📊 Torre de Controle Pastoral")
    
    # Helpers locais do Calendário Paroquial
    def registrar_recesso_lote(data_rec, motivo, turmas_lista, nome_coord):
        planilha = conectar_google_sheets()
        if planilha:
            try:
                aba = planilha.worksheet("encontros")
                linhas = [[data_rec.strftime('%d/%m/%Y'), t, f"RECESSO: {motivo}", nome_coord, "Feriado/Recesso geral. Chamada não exigida."] for t in turmas_lista]
                aba.append_rows(linhas)
                st.cache_data.clear()
                return True
            except Exception as e: st.error(f"Erro: {e}"); return False
        return False

    def excluir_recesso_lote(data_alvo):
        planilha = conectar_google_sheets()
        if planilha:
            try:
                aba = planilha.worksheet("encontros")
                dados_enc = aba.get_all_values()
                data_str = str(data_alvo)
                linhas_del =[i + 1 for i, l in enumerate(dados_enc) if len(l) >= 3 and l[0] == data_str and "RECESSO" in str(l[2]).upper()]
                
                if linhas_del: # Usa Batch Update para não estourar o limite da API do Google
                    sheet_id = aba.id
                    requests =[{"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": r - 1, "endIndex": r}}} for r in sorted(linhas_del, reverse=True)]
                    planilha.batch_update({"requests": requests})
                st.cache_data.clear()
                return True
            except Exception as e: st.error(f"Erro: {e}"); return False
        return False

    tab_diaria, tab_global, tab_relatorios = st.tabs([
        "☀️ Visão Diária", "🌍 Visão Global (Radar)", "🖨️ Analytics e Relatórios"
    ])
    
    df_enc_local = ler_aba("encontros")
    hoje_data = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    
    # ==========================================================================
    # HUB 1: VISÃO DIÁRIA
    # ==========================================================================
    with tab_diaria:
        st.subheader("☀️ Bom dia, Coordenação!")
        st.markdown("Acompanhe os eventos de hoje e gerencie o calendário da paróquia.")
        
        c_dia1, c_dia2 = st.columns([2, 1])
        
        with c_dia1:
            st.markdown("#### 🎂 Aniversariantes de Hoje")
            aniversariantes_agora = obter_aniversariantes_hoje(df_cat, df_usuarios)
            
            if aniversariantes_agora:
                for item in aniversariantes_agora:
                    partes = item.split(" | ")
                    papel = partes[1]
                    nome_completo = partes[2]
                    icone = "🛡️" if papel == "CATEQUISTA" else "😇"
                    st.markdown(f"<div style='background-color:#e8f5e9; padding:10px; border-radius:8px; border-left:5px solid #2e7d32; margin-bottom:5px;'><b>{icone} {papel}:</b> {nome_completo}</div>", unsafe_allow_html=True)
                    
                    if st.button(f"🎨 Gerar Card para {nome_completo.split()[0]}", key=f"btn_hoje_dash_{nome_completo}"):
                        card_img = gerar_card_aniversario(item, tipo="DIA")
                        if card_img:
                            st.image(card_img, use_container_width=True)
                            st.download_button("📥 Baixar Card", card_img, f"Parabens_Hoje_{nome_completo}.png", "image/png")
            else:
                st.info("Nenhum aniversariante no dia de hoje.")
                
            with st.expander("📅 Ver Aniversariantes do Mês Inteiro"):
                df_niver_mes_geral = obter_aniversariantes_mes_unificado(df_cat, df_usuarios)
                if not df_niver_mes_geral.empty:
                    if st.button("🖼️ GERAR CARD COLETIVO DO MÊS", use_container_width=True):
                        lista_para_card = [f"{int(row['dia'])} | {row['tipo']} | {row['nome']}" for _, row in df_niver_mes_geral.iterrows()]
                        card_coletivo = gerar_card_aniversario(lista_para_card, tipo="MES")
                        if card_coletivo:
                            st.image(card_coletivo)
                            st.download_button("📥 Baixar Card Coletivo", card_coletivo, "Aniversariantes_Mes.png", "image/png")
                    for _, niver in df_niver_mes_geral.iterrows():
                        st.write(f"Dia {int(niver['dia'])} - {niver['nome']} ({niver['tipo']})")
                else:
                    st.write("Nenhum aniversariante este mês.")

        with c_dia2:
            st.markdown("#### ⏸️ Calendário Paroquial")
            st.markdown("Abono de faltas: registre ou remova feriados passados e futuros.")
            
            with st.expander("➕ Agendar Novo Recesso/Feriado", expanded=False):
                with st.form("form_add_recesso"):
                    data_rec = st.date_input("Data do Recesso", hoje_data, format="DD/MM/YYYY")
                    motivo_rec = st.text_input("Motivo (Ex: Semana Santa, Chuva)").upper()
                    
                    if st.form_submit_button("✅ Aplicar para Todas as Turmas", use_container_width=True, type="primary"):
                        if motivo_rec:
                            with st.spinner("Abonando o calendário..."):
                                turmas_ativas = df_turmas['nome_turma'].tolist() if not df_turmas.empty else[]
                                if registrar_recesso_lote(data_rec, motivo_rec, turmas_ativas, st.session_state.usuario['nome']):
                                    st.success("Recesso registrado!"); time.sleep(1); st.rerun()
                        else:
                            st.error("Digite o motivo.")
                            
            st.markdown("<br><b>📜 Histórico de Recessos:</b>", unsafe_allow_html=True)
            if not df_enc_local.empty:
                df_recessos = df_enc_local[df_enc_local['tema'].str.contains("RECESSO", na=False, case=False)].copy()
                if not df_recessos.empty:
                    # Agrupa por data e motivo para não repetir a mesma data 15 vezes (1 por turma)
                    df_recs_grouped = df_recessos.groupby(['data', 'tema']).size().reset_index()
                    df_recs_grouped['data_dt'] = pd.to_datetime(df_recs_grouped['data'], errors='coerce', dayfirst=True)
                    df_recs_grouped = df_recs_grouped.sort_values('data_dt', ascending=False)
                    
                    for idx, row in df_recs_grouped.iterrows():
                        data_r = row['data']
                        motivo_r = row['tema'].replace("RECESSO:", "").strip()
                        
                        c_r1, c_r2 = st.columns([5, 1])
                        c_r1.markdown(f"<div style='background-color:#fff3cd; padding:8px; border-radius:5px; border-left:4px solid #ffb300; margin-bottom:5px; font-size:13px;'><b style='color:#ffb300;'>{formatar_data_br(data_r)}</b> - {motivo_r}</div>", unsafe_allow_html=True)
                        
                        # A Lixeira Mágica
                        if c_r2.button("🗑️", key=f"del_rec_{data_r}_{idx}", help="Desfazer/Excluir este recesso para todas as turmas"):
                            with st.spinner("Limpando recesso..."):
                                if excluir_recesso_lote(data_r):
                                    st.success("Desfeito!"); time.sleep(1); st.rerun()
                else:
                    st.info("Nenhum recesso registrado no sistema.")
            else:
                st.info("Nenhum recesso registrado no sistema.")

    # ==========================================================================
    # HUB 2: VISÃO GLOBAL (RADAR DE ATENÇÃO)
    # ==========================================================================
    with tab_global:
        st.subheader("🌍 Visão Global (Radar de Atenção)")
        
        # --- AUDITORIA DE CHAMADAS COM BYPASS DE RECESSO ---
        st.markdown("#### 🚩 Auditoria de Chamadas (Últimos 7 Dias)")
        
        turmas_pendentes_bruto = gerar_auditoria_chamadas_pendentes(df_turmas, df_pres, dias_limite=7)
        
        # Lógica de Bypass: Remove turmas que tiveram RECESSO nos últimos 7 dias
        limite_aud = hoje_data - dt_module.timedelta(days=7)
        turmas_em_recesso =[]
        
        if not df_enc_local.empty:
            # BLINDAGEM: Cria a coluna de data formatada antes de tentar filtrar
            df_enc_local['data_dt'] = pd.to_datetime(df_enc_local['data'], errors='coerce', dayfirst=True)
            
            df_enc_recente = df_enc_local[df_enc_local['data_dt'].dt.date >= limite_aud]
            recessos_recentes = df_enc_recente[df_enc_recente['tema'].str.contains("RECESSO|FERIADO", na=False, case=False)]
            turmas_em_recesso = recessos_recentes['turma'].str.strip().str.upper().unique().tolist()
        
        # Filtra a lista final perdoando quem teve recesso
        turmas_pendentes =[t for t in turmas_pendentes_bruto if str(t).strip().upper() not in turmas_em_recesso]
        
        total_turmas = len(df_turmas)
        turmas_feitas = total_turmas - len(turmas_pendentes)
        
        c_aud1, c_aud2, c_aud3 = st.columns(3)
        c_aud1.metric("Turmas em Dia (ou em Recesso)", f"{turmas_feitas} / {total_turmas}")
        
        df_pres_recente = df_pres.copy()
        if not df_pres_recente.empty:
            df_pres_recente['data_dt'] = pd.to_datetime(df_pres_recente['data_encontro'], errors='coerce', dayfirst=True)
            df_recentes = df_pres_recente[df_pres_recente['data_dt'].dt.date >= limite_aud]
            total_faltosos = len(df_recentes[df_recentes['status'] == 'AUSENTE']) if not df_recentes.empty else 0
        else:
            total_faltosos = 0
            
        c_aud2.metric("Faltosos Recentes", total_faltosos)
        
        with c_aud3:
            if st.button("📥 Baixar Relatório de Auditoria (PDF)", use_container_width=True):
                pdf_aud = gerar_pdf_auditoria_chamadas(df_turmas, df_pres, df_cat, dias_limite=7)
                st.download_button("Clique para baixar", pdf_aud, f"Auditoria_Chamadas_{hoje_data}.pdf", "application/pdf", use_container_width=True)

        if turmas_pendentes:
            st.error("⚠️ **Atenção:** As seguintes turmas estão sem chamada registrada nos últimos 7 dias:")
            import urllib.parse
            for t_pendente in turmas_pendentes:
                info_t = df_turmas[df_turmas['nome_turma'] == t_pendente]
                cat_nome = "Não informado"
                btn_wa = ""
                
                if not info_t.empty:
                    cats_resp =[c.strip() for c in str(info_t.iloc[0].get('catequista_responsavel', '')).split(',') if c.strip()]
                    if cats_resp:
                        cat_nome = cats_resp[0]
                        tel_cat = ""
                        if not equipe_tecnica.empty:
                            cat_info = equipe_tecnica[equipe_tecnica['nome'].str.upper() == cat_nome.upper()]
                            if not cat_info.empty:
                                tel_cat = str(cat_info.iloc[0].get('telefone', ''))
                        
                        num_limpo = "".join(filter(str.isdigit, tel_cat))
                        if num_limpo:
                            if num_limpo.startswith("0"): num_limpo = num_limpo[1:]
                            if not num_limpo.startswith("55"): num_limpo = f"5573{num_limpo}" if len(num_limpo) <= 9 else f"55{num_limpo}"
                            
                            msg = f"Paz e Bem, {cat_nome}! Notei que o diário da turma {t_pendente} está pendente de atualização nos últimos 7 dias. Pode verificar, por favor? Deus abençoe!"
                            link_wa = f"https://wa.me/{num_limpo}?text={urllib.parse.quote(msg)}"
                            btn_wa = f"<a href='{link_wa}' target='_blank' style='text-decoration:none; background-color:#25d366; color:white; padding:4px 10px; border-radius:5px; font-size:12px; font-weight:bold; margin-left:10px;'>📲 Cobrar Catequista</a>"
                        else:
                            btn_wa = "<span style='color:#999; font-size:12px; margin-left:10px;'>(Sem telefone)</span>"
                            
                st.markdown(f"<div style='padding:5px 0; border-bottom:1px solid #fbd5d5;'>• <b>{t_pendente}</b> (Resp: {cat_nome}) {btn_wa}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ Todas as turmas estão com os diários em dia ou em recesso justificado.")

        st.divider()
        st.markdown("#### 🚩 Radar de Atenção Imediata")
        
        r1, r2, r3, r4, r5 = st.columns(5)

        df_ativos = df_cat[df_cat['status'] == 'ATIVO'] if not df_cat.empty else pd.DataFrame()
        
        df_pend_doc = df_ativos[~df_ativos['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])]
        r1.metric("📄 Doc. Pendente", len(df_pend_doc), delta="Ação Necessária", delta_color="inverse")

        df_risco_detalhado = pd.DataFrame()
        if not df_pres.empty and not df_ativos.empty:
            df_faltas = df_pres[df_pres['status'] == 'AUSENTE']
            if not df_faltas.empty:
                contagem_faltas = df_faltas.groupby('id_catequizando').size().reset_index(name='qtd_faltas')
                contagem_risco = contagem_faltas[contagem_faltas['qtd_faltas'] >= 3]
                df_risco_detalhado = pd.merge(contagem_risco, df_ativos[['id_catequizando', 'nome_completo', 'etapa', 'obs_pastoral_familia']], on='id_catequizando', how='inner')
                df_risco_detalhado = df_risco_detalhado[~df_risco_detalhado['obs_pastoral_familia'].str.contains(r'\[VISITA_CONCLUIDA\]', na=False, case=False)]
                df_risco_detalhado = df_risco_detalhado.sort_values(by='qtd_faltas', ascending=False)
        r2.metric("🚩 Risco de Evasão", len(df_risco_detalhado), delta="Visita Urgente", delta_color="inverse")

        df_sem_batismo = df_ativos[df_ativos['batizado_sn'] == 'NÃO']
        r3.metric("🕊️ Sem Batismo", len(df_sem_batismo), delta="Regularizar", delta_color="inverse")

        df_fam_reg = df_cat[df_cat['est_civil_pais'].isin(['CONVIVEM', 'CASADO(A) CIVIL', 'DIVORCIADO(A)'])]
        r4.metric("🏠 Famílias Irreg.", len(df_fam_reg), delta="Pastoral Familiar", delta_color="inverse")

        turmas_reais = df_turmas['nome_turma'].unique().tolist() if not df_turmas.empty else[]
        df_sem_turma = df_ativos[(df_ativos['etapa'] == "CATEQUIZANDOS SEM TURMA") | (~df_ativos['etapa'].isin(turmas_reais))]
        r5.metric("⏳ Sem Turma", len(df_sem_turma), delta="Fila de Espera", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        
        if not df_risco_detalhado.empty:
            with st.expander(f"🚩 Ver Detalhes: {len(df_risco_detalhado)} Catequizandos em Risco Crítico (3+ Faltas)"):
                st.dataframe(df_risco_detalhado[['nome_completo', 'etapa', 'qtd_faltas']].rename(columns={'nome_completo': 'Catequizando', 'etapa': 'Turma', 'qtd_faltas': 'Faltas Acumuladas'}), use_container_width=True, hide_index=True)

        if not df_pend_doc.empty:
            with st.expander(f"📄 Ver Detalhes: {len(df_pend_doc)} com Documentos Pendentes"):
                st.dataframe(df_pend_doc[['nome_completo', 'etapa', 'doc_em_falta']].rename(columns={'nome_completo': 'Catequizando', 'etapa': 'Turma', 'doc_em_falta': 'Faltando'}), use_container_width=True, hide_index=True)

        if not df_sem_batismo.empty:
            with st.expander(f"🕊️ Ver Detalhes: {len(df_sem_batismo)} sem registro de Batismo"):
                st.dataframe(df_sem_batismo[['nome_completo', 'etapa']].rename(columns={'nome_completo': 'Catequizando', 'etapa': 'Turma'}), use_container_width=True, hide_index=True)

    # ==========================================================================
    # HUB 3: ANALYTICS E RELATÓRIOS
    # ==========================================================================
    with tab_relatorios:
        st.subheader("🖨️ Analytics e Relatórios")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("#### 🕊️ Cobertura de Batismo (Ativos)")
            if not df_ativos.empty:
                bat_sim = len(df_ativos[df_ativos['batizado_sn'] == 'SIM'])
                bat_nao = len(df_ativos[df_ativos['batizado_sn'] == 'NÃO'])
                fig_bat = px.pie(values=[bat_sim, bat_nao], names=['Batizados', 'Não Batizados'], color_discrete_sequence=['#417b99', '#e03d11'], hole=0.5)
                fig_bat.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                st.plotly_chart(fig_bat, use_container_width=True)
            else: st.info("Sem dados ativos.")

        with c2:
            st.markdown("#### 🍞 1ª Eucaristia (Ativos)")
            if not df_ativos.empty:
                euc_sim = df_ativos['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False, case=False).sum()
                euc_nao = len(df_ativos) - euc_sim
                fig_euc = px.pie(values=[euc_sim, euc_nao], names=['Já Receberam', 'Em Preparação'], color_discrete_sequence=['#2e7d32', '#ffa000'], hole=0.5)
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
            
            st.markdown("#### 🌡️ Termômetro de Engajamento")
            if len(freq_turma) >= 3:
                top_3 = freq_turma.sort_values(by='Freq %', ascending=False).head(3)
                bottom_3 = freq_turma.sort_values(by='Freq %', ascending=True).head(3)
                
                c_top, c_bot = st.columns(2)
                with c_top:
                    st.success("🏆 **Top 3 - Mais Engajadas**")
                    for _, r in top_3.iterrows(): st.markdown(f"**{r['Turma']}** ({r['Freq %']:.1f}%)")
                with c_bot:
                    st.error("🚨 **Atenção - Menor Frequência**")
                    for _, r in bottom_3.iterrows(): st.markdown(f"**{r['Turma']}** ({r['Freq %']:.1f}%)")

        st.divider()
        st.markdown("#### 🏛️ Estação de Impressão e Auditoria")
        col_doc_sec, col_doc_past, col_doc_lote = st.columns(3)
        
        with col_doc_sec:
            if st.button("🏛️ Relatório Diocesano", use_container_width=True):
                st.session_state.pdf_diocesano = gerar_relatorio_diocesano_pdf(df_turmas, df_cat, df_usuarios)
            if "pdf_diocesano" in st.session_state:
                st.download_button("📥 Baixar Diocesano", st.session_state.pdf_diocesano, "Diocesano.pdf", use_container_width=True)

        with col_doc_past:
            if st.button("📋 Relatório Pastoral", use_container_width=True):
                st.session_state.pdf_pastoral = gerar_relatorio_pastoral_pdf(df_turmas, df_cat, df_pres, df_pres_reuniao)
            if "pdf_pastoral" in st.session_state:
                st.download_button("📥 Baixar Pastoral", st.session_state.pdf_pastoral, "Pastoral.pdf", use_container_width=True)

        with col_doc_lote:
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

    turma_ativa = st.selectbox("🔍 Selecione a Turma:", turmas_permitidas, key="sel_t_minha")
    st.title(f"📚 Painel: {turma_ativa}")

# --- CARREGAMENTO DE DADOS NORMALIZADOS ---
    df_cron_t = ler_aba("cronograma")
    df_enc_t = ler_aba("encontros")
    df_reu_t = ler_aba("presenca_reuniao")
    
    # --- BLINDAGEM DE DADOS (DATA SHIELDING) CONTRA KEYERROR ---
    if not df_cat.empty and 'etapa' in df_cat.columns:
        meus_alunos = df_cat[(df_cat['etapa'].astype(str).str.strip().str.upper() == turma_ativa.strip().upper()) & (df_cat['status'] == 'ATIVO')]
    else:
        meus_alunos = pd.DataFrame()
        
    if not df_pres.empty and 'id_turma' in df_pres.columns:
        minhas_pres = df_pres[df_pres['id_turma'].astype(str).str.strip().str.upper() == turma_ativa.strip().upper()]
    else:
        minhas_pres = pd.DataFrame()

    # --- 🕊️ VISÃO PASTORAL (POP-UP SÓBRIO E CORRIGIDO) ---
    @st.dialog("🕊️ Visão Pastoral Diária")
    def exibir_assistente_pastoral(turma, aniversariantes, status_chamada, faltosos, proximo_tema, chave_sessao):
        st.markdown(f"### Paz e Bem, Catequista.")
        st.write(f"Resumo da caminhada para a turma **{turma}**:")
        
        if aniversariantes:
            st.info(f"**Aniversariantes da Semana:**\n" + "\n".join([f"• {n}" for n in aniversariantes]))
        
        if status_chamada == "PENDENTE":
            st.error("**Atenção:** O diário do último encontro está pendente de preenchimento.")
        elif faltosos > 0:
            st.warning(f"**Cuidado Pastoral:** Tivemos **{faltosos} faltas** no último encontro. Lembre-se de buscar essas ovelhas.")
        else:
            st.success("**Frequência:** Excelente participação no último encontro.")
            
        if proximo_tema:
            st.success(f"**Próximo Encontro:** O tema planejado é '{proximo_tema}'.")
        else:
            st.warning("**Planejamento:** O cronograma está sem próximos temas definidos.")
            
        st.markdown("---")
        st.caption('"O catequista é um cristão que recebe o chamado de Deus para anunciar a Sua Palavra."')
        
        if st.button("✅ Ciente, iniciar missão", use_container_width=True):
            st.session_state[chave_sessao] = True
            st.rerun()

    hoje_str = date.today().strftime('%Y-%m-%d')
    key_assistente = f"assistente_visto_{turma_ativa}_{hoje_str}"
    
    ultima_data_chamada, chamada_recente = obter_ultima_chamada_turma(minhas_pres, turma_ativa)
    limite_t = date.today() - timedelta(days=7)
    status_chamada = "PENDENTE" if (not ultima_data_chamada or ultima_data_chamada < limite_t) else "OK"
    faltosos_qtd = len(chamada_recente[chamada_recente['status'] == 'AUSENTE']) if not chamada_recente.empty else 0
    
    proximo_tema_str = None
    if not df_cron_t.empty:
        col_status = 'status' if 'status' in df_cron_t.columns else ('col_4' if 'col_4' in df_cron_t.columns else None)
        proximo = df_cron_t[df_cron_t['etapa'].astype(str).str.strip().str.upper() == turma_ativa.strip().upper()]
        if col_status: proximo = proximo[proximo[col_status].astype(str).str.strip().str.upper() != 'REALIZADO']
        if not proximo.empty: proximo_tema_str = proximo.iloc[0]['titulo_tema']

    if key_assistente not in st.session_state:
        aniversariantes_semana = [r['nome_completo'] for _, r in meus_alunos.iterrows() if eh_aniversariante_da_semana(r['data_nascimento'], date.today())]
        exibir_assistente_pastoral(turma_ativa, aniversariantes_semana, status_chamada, faltosos_qtd, proximo_tema_str, key_assistente)

    # --- ALERTA DE REUNIÃO DE PAIS ---
    df_reunioes_agendadas = ler_aba("reunioes_pais")
    if not df_reunioes_agendadas.empty:
        reunioes_pendentes = df_reunioes_agendadas[
            (df_reunioes_agendadas.iloc[:, 5] == "PENDENTE") & 
            (df_reunioes_agendadas.iloc[:, 3].isin([turma_ativa.strip().upper(), "GERAL (TODAS)"]))
        ]
        if not reunioes_pendentes.empty:
            for _, reu in reunioes_pendentes.iterrows():
                st.markdown(f"""
                    <div style='background-color:#e3f2fd; padding:15px; border-radius:10px; border-left:6px solid #1976d2; margin-bottom:15px;'>
                        <h4 style='margin:0; color:#1976d2;'>📢 Lembrete: Reunião de Pais Agendada!</h4>
                        <p style='margin:5px 0 10px 0; color:#333; font-size:14px;'>
                            <b>Tema:</b> {reu.iloc[1]} <br>
                            <b>Data:</b> {reu.iloc[2]} &nbsp;|&nbsp; <b>Local:</b> {reu.iloc[4]}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                import urllib.parse
                msg_convite = f"Paz e Bem, famílias da turma {turma_ativa}! Teremos uma Reunião de Pais muito importante.\n\n📅 Data: {reu.iloc[2]}\n📍 Local: {reu.iloc[4]}\n📖 Tema: {reu.iloc[1]}\n\nContamos com a presença de um responsável por catequizando. Deus abençoe!"
                link_wa_grupo = f"https://wa.me/?text={urllib.parse.quote(msg_convite)}"
                st.markdown(f"<a href='{link_wa_grupo}' target='_blank' style='text-decoration:none;'><div style='background-color:#25d366; color:white; text-align:center; padding:10px; border-radius:8px; font-size:14px; font-weight:bold; margin-top:-10px; margin-bottom:20px; width: 300px;'>📲 Enviar Convite no Grupo do WhatsApp</div></a>", unsafe_allow_html=True)

    # --- PAINEL DE INDICADORES (CLEAN) ---
    st.markdown("#### 📊 Indicadores da Caminhada")
    c1, c2, c3 = st.columns(3)
    
    cron_turma = df_cron_t[df_cron_t['etapa'].astype(str).str.strip().str.upper() == turma_ativa.strip().upper()]
    total_temas = len(cron_turma)
    total_feito = len(df_enc_t[df_enc_t['turma'].astype(str).str.strip().str.upper() == turma_ativa.strip().upper()])
    progresso_seguro = min((total_feito / total_temas) if total_temas > 0 else 0.0, 1.0)
    
    c1.metric("Encontros Realizados", f"{total_feito}/{total_temas}", f"{progresso_seguro*100:.0f}% concluído")
    
    freq = (minhas_pres['status'] == 'PRESENTE').mean() * 100 if not minhas_pres.empty else 0
    c2.metric("Frequência Média", f"{freq:.1f}%")

    perc_pais = 0
    if not df_reu_t.empty and not meus_alunos.empty:
        pais_presentes = df_reu_t[df_reu_t.iloc[:, 3].astype(str).str.strip().str.upper() == turma_ativa.strip().upper()].iloc[:, 1].nunique()
        perc_pais = (pais_presentes / len(meus_alunos)) * 100
    c3.metric("Engajamento Familiar", f"{perc_pais:.0f}%")

    st.markdown("<br>", unsafe_allow_html=True)
    c_alerta1, c_alerta2 = st.columns(2)
    
    with c_alerta1:
        if status_chamada == "PENDENTE":
            st.error(f"**Diário Pendente** (Última chamada: {formatar_data_br(ultima_data_chamada) if ultima_data_chamada else 'Nenhuma'})")
        else:
            st.success(f"**Diário em Dia** (Último encontro: {formatar_data_br(ultima_data_chamada)})")
            faltosos = chamada_recente[chamada_recente['status'] == 'AUSENTE']
            if not faltosos.empty:
                with st.expander(f"🚩 {len(faltosos)} Faltosos no último encontro"):
                    for _, f in faltosos.iterrows():
                        cat_f = meus_alunos[meus_alunos['id_catequizando'] == f['id_catequizando']]
                        if not cat_f.empty:
                            c = cat_f.iloc[0]
                            st.write(f"• {c['nome_completo']}")
                            montar_botoes_whatsapp(c)

    with c_alerta2:
        if not proximo_tema_str:
            st.warning("**Planejamento:** Adicione o próximo tema no Diário.")
        else:
            st.info(f"**Próximo Tema:** {proximo_tema_str}")

    st.divider()

    # --- RADAR DE ATENÇÃO (TABS COMPACTAS) ---
    st.markdown("#### 🎯 Radar Pastoral")
    risco_c, atencao_p = processar_alertas_evasao(minhas_pres)
    df_pend_doc = meus_alunos[~meus_alunos['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])]
    df_sem_batismo = meus_alunos[meus_alunos['batizado_sn'] == 'NÃO']

    if not risco_c and df_pend_doc.empty and df_sem_batismo.empty:
        st.success("Turma em caminhada estável. Nenhum alerta crítico.")
    else:
        tab_risco, tab_doc, tab_sac = st.tabs([f"Risco de Evasão ({len(risco_c)})", f"Documentos ({len(df_pend_doc)})", f"Sacramentos ({len(df_sem_batismo)})"])
        with tab_risco:
            if risco_c:
                for r in risco_c: st.markdown(f"• {r}")
            else: st.write("Nenhum catequizando em risco.")
        with tab_doc:
            if not df_pend_doc.empty:
                for n in df_pend_doc['nome_completo'].tolist(): st.markdown(f"• {n}")
            else: st.write("Documentação em dia.")
        with tab_sac:
            if not df_sem_batismo.empty:
                for n in df_sem_batismo['nome_completo'].tolist(): st.markdown(f"• {n}")
            else: st.write("Todos batizados.")

    st.divider()

    # --- CONSULTA INDIVIDUAL (CARD MODERNO) ---
    st.markdown("#### 👤 Ficha do Catequizando")
    lista_nomes = sorted(meus_alunos['nome_completo'].tolist())
    nome_sel = st.selectbox("Selecione um catequizando para ver detalhes:", [""] + lista_nomes, key="busca_indiv_t")

    if nome_sel:
        row = meus_alunos[meus_alunos['nome_completo'] == nome_sel].iloc[0]
        bat = "Sim" if row['batizado_sn'] == "SIM" else "Não"
        euc = "Sim" if "EUCARISTIA" in str(row['sacramentos_ja_feitos']).upper() else "Não"
        cri = "Sim" if "CRISMA" in str(row['sacramentos_ja_feitos']).upper() else "Não"
        tem_reu = "Ativos" if not df_reu_t.empty and row['id_catequizando'] in df_reu_t.iloc[:, 1].values else "Ausentes"
        idade_c = calcular_idade(row['data_nascimento'])
        
        st.markdown(f"""
            <div style='background-color:#ffffff; padding:20px; border-radius:10px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                <h4 style='margin:0; color:#417b99;'>{row['nome_completo']}</h4>
                <p style='margin:5px 0; color:#666; font-size:14px;'>
                    <b>Idade:</b> {idade_c} anos &nbsp;|&nbsp; <b>Saúde:</b> {row.get('toma_medicamento_sn', 'NÃO')} &nbsp;|&nbsp; <b>Docs:</b> {row.get('doc_em_falta', 'OK')}
                </p>
                <hr style='margin: 10px 0; border-color: #f0f0f0;'>
                <p style='margin:0; font-size:13px; color:#555;'>
                    <b>Batismo:</b> {bat} &nbsp;|&nbsp; <b>Eucaristia:</b> {euc} &nbsp;|&nbsp; <b>Crisma:</b> {cri}
                </p>
                <p style='margin:5px 0 0 0; font-size:13px; color:#555;'>
                    <b>Família:</b> {tem_reu} &nbsp;|&nbsp; <b>Obs:</b> {row.get('obs_pastoral_familia', 'Sem registros.')}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        montar_botoes_whatsapp(row)
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Ver Extrato de Caminhada (Presenças e Temas)"):
            if not minhas_pres.empty and 'id_catequizando' in minhas_pres.columns:
                pres_aluno = minhas_pres[minhas_pres['id_catequizando'] == row['id_catequizando']].copy()
                pres_aluno['data_dt'] = pd.to_datetime(pres_aluno.get('data_encontro', ''), errors='coerce', dayfirst=True)
                pres_aluno = pres_aluno.sort_values('data_dt', ascending=False)
                for _, p in pres_aluno.iterrows():
                    icone_p = "✅" if p.get('status', '') == "PRESENTE" else "❌"
                    cor_p = "#2e7d32" if p.get('status', '') == "PRESENTE" else "#e03d11"
                    st.markdown(f"<div style='padding:5px; border-bottom:1px solid #eee;'><span style='color:{cor_p};'>{icone_p}</span> <b>{formatar_data_br(p.get('data_encontro', ''))}</b> | {p.get('tema_do_dia', 'Tema não registrado')}</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum registro de presença.")


# ==============================================================================
# PÁGINA: 📖 DIÁRIO DE ENCONTROS
# ==============================================================================
elif menu == "📖 Diário de Encontros":
    st.title("📖 Central de Itinerário e Encontros")
    
    with st.expander("💡 COMO FUNCIONA O DIÁRIO?", expanded=False):
        st.markdown("""
        1. **PLANEJAR:** Adicione temas no Cronograma.
        2. **REGISTRAR:** Use o formulário ao lado para registrar o encontro realizado.
        3. **LINHA DO TEMPO:** Edite temas e relatos diretamente nos registros abaixo.
        """)

    # --- CARREGAMENTO NORMALIZADO ---
    df_cron_p = ler_aba("cronograma")
    df_pres_local = ler_aba("presencas")
    df_enc_local = ler_aba("encontros") # <--- ESTA LINHA FALTAVA E CAUSOU O ERRO
    
    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    if eh_gestor or vinculo_raw == "TODAS":
        turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else []
    else:
        turmas_permitidas = [t.strip() for t in vinculo_raw.split(',') if t.strip()]

    if not turmas_permitidas:
        st.error("⚠️ Nenhuma turma vinculada."); st.stop()

    turma_focal = st.selectbox("🔍 Selecione a Turma para Gerenciar:", turmas_permitidas)
    turma_norm = turma_focal.strip().upper()

    # --- BARRA DE PROGRESSO ---
    if not df_cron_p.empty:
        cron_turma = df_cron_p[df_cron_p['etapa'].astype(str).str.strip().str.upper() == turma_norm]
        if not cron_turma.empty:
            total_temas = len(cron_turma)
            # Busca encontros realizados na aba presencas (fonte única)
            encontros_realizados = df_pres_local[df_pres_local['id_turma'].astype(str).str.strip().str.upper() == turma_norm]['data_encontro'].unique()
            realizados = len(encontros_realizados)
            
            # Trava de segurança: impede que o progresso passe de 1.0 (100%) e quebre o Streamlit
            progresso_bruto = realizados / total_temas if total_temas > 0 else 0.0
            progresso_seguro = min(progresso_bruto, 1.0)
            
            st.markdown(f"**Progresso do Itinerário: {realizados} encontros realizados (de {total_temas} planejados)**")
            st.progress(progresso_seguro)

    # --- COLUNAS DE AÇÃO ---
    col_plan, col_reg = st.columns(2)

    with col_plan:
        st.subheader("📅 1. Planejar Temas")
        with st.form(f"form_plan_{turma_focal}", clear_on_submit=True):
            novo_tema = st.text_input("Título do Tema").upper()
            detalhes_tema = st.text_area("Objetivo (Opcional)", height=100)
            if st.form_submit_button("📌 ADICIONAR AO CRONOGRAMA"):
                if novo_tema:
                    if salvar_tema_cronograma([f"PLAN-{int(time.time())}", turma_focal, novo_tema, detalhes_tema, "PENDENTE"]):
                        st.success("Tema planejado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    with col_reg:
        st.subheader("✅ 2. Registrar Encontro")
        with st.form(f"form_reg_{turma_focal}", clear_on_submit=True):
            data_e = st.date_input("Data do Encontro", date.today(), format="DD/MM/YYYY")
            
            # Verifica se já existe registro para esta data na aba presencas
            df_pres_local['data_dt'] = pd.to_datetime(df_pres_local['data_encontro'], errors='coerce', dayfirst=True)
            ja_registrado = not df_pres_local[
                (df_pres_local['id_turma'].astype(str).str.strip().str.upper() == turma_norm) & 
                (df_pres_local['data_dt'].dt.date == data_e)
            ].empty
            
            if ja_registrado:
                st.error(f"⚠️ Já existe um encontro registrado para {data_e.strftime('%d/%m/%Y')}. Edite abaixo.")
                st.form_submit_button("BLOQUEADO", disabled=True)
            else:
                temas_pendentes = [""] + df_cron_p[(df_cron_p['etapa'].astype(str).str.strip().str.upper() == turma_norm) & (df_cron_p.get('status', '') != 'REALIZADO')]['titulo_tema'].tolist()
                tema_selecionado = st.selectbox("Temas do Cronograma:", temas_pendentes)
                tema_manual = st.text_input("Título do Tema Ministrado:", value=tema_selecionado).upper()
                obs_e = st.text_area("Observações Pastorais", height=68)
                
                if st.form_submit_button("💾 SALVAR NO DIÁRIO"):
                    if tema_manual:
                        # Salva na aba encontros e marca no cronograma
                        if salvar_encontro([data_e.strftime('%d/%m/%Y'), turma_focal, tema_manual, st.session_state.usuario['nome'], obs_e]):
                            marcar_tema_realizado_cronograma(turma_focal, tema_manual)
                            st.success("Encontro registrado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

    st.divider()
    
    # --- MINI-DASHBOARD DO ITINERÁRIO ---
    st.subheader(f"📊 Visão Geral do Itinerário: {turma_focal}")
    
    qtd_realizados = 0
    qtd_pendentes = 0
    freq_media = 0.0
    
    if not df_cron_p.empty:
        cron_t = df_cron_p[df_cron_p['etapa'].astype(str).str.strip().str.upper() == turma_norm]
        col_status = 'status' if 'status' in cron_t.columns else ('col_4' if 'col_4' in cron_t.columns else None)
        if col_status:
            qtd_pendentes = len(cron_t[cron_t[col_status].astype(str).str.strip().str.upper() != 'REALIZADO'])
            
    if not df_enc_local.empty:
        enc_t = df_enc_local[df_enc_local['turma'].astype(str).str.strip().str.upper() == turma_norm]
        qtd_realizados = len(enc_t)
        
    pres_t = df_pres_local[df_pres_local['id_turma'].astype(str).str.strip().str.upper() == turma_norm]
    if not pres_t.empty:
        pres_t['status_num'] = pres_t['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
        freq_media = pres_t['status_num'].mean() * 100

    c_dash1, c_dash2, c_dash3 = st.columns(3)
    c_dash1.metric("✅ Encontros Realizados", qtd_realizados)
    c_dash2.metric("📌 Temas Pendentes", qtd_pendentes)
    c_dash3.metric("📈 Frequência Média", f"{freq_media:.1f}%")

    st.divider()
    st.subheader(f"📜 Linha do Tempo e Raio-X dos Encontros")
    
    if not df_enc_local.empty:
        # Filtro robusto e normalizado
        df_enc_local['turma_norm'] = df_enc_local['turma'].astype(str).str.strip().str.upper()
        # Ordena corretamente pelas datas
        df_enc_local['data_sort'] = pd.to_datetime(df_enc_local['data'], errors='coerce', dayfirst=True)
        hist_turma = df_enc_local[df_enc_local['turma_norm'] == turma_focal.strip().upper()].sort_values(by='data_sort', ascending=False)
        
        if not hist_turma.empty:
            for idx, row in hist_turma.iterrows():
                data_d = str(row['data'])
                tema_d = row.get('tema', 'Tema não registrado')
                obs_d = row.get('observacoes', '')
                cat_d = row.get('catequista', 'Não informado')
                
                # Buscar presenças exatas deste encontro
                pres_e = df_pres_local[(df_pres_local['id_turma'].astype(str).str.strip().str.upper() == turma_norm) & (df_pres_local['data_encontro'].astype(str) == data_d)]
                qtd_pres = len(pres_e[pres_e['status'] == 'PRESENTE'])
                qtd_aus = len(pres_e[pres_e['status'] == 'AUSENTE'])
                faltosos = pres_e[pres_e['status'] == 'AUSENTE']['nome_catequizando'].tolist()
                
                with st.expander(f"📅 {formatar_data_br(data_d)} - {tema_d}"):
                    # --- RAIO-X DO ENCONTRO ---
                    st.markdown(f"**👤 Catequista Responsável:** {cat_d}")
                    
                    c_met1, c_met2 = st.columns(2)
                    c_met1.metric("✅ Presentes", qtd_pres)
                    c_met2.metric("❌ Ausentes", qtd_aus)
                    
                    if faltosos:
                        st.error(f"**Faltosos neste dia:** {', '.join(faltosos)}")
                    else:
                        st.success("**Nenhuma falta registrada neste dia!**")
                        
                    st.markdown("---")
                    st.markdown("**✏️ Editar Registro do Encontro**")
                    
                    # Adicionamos o 'idx' (índice da linha) para garantir unicidade absoluta da key
                    with st.form(f"edit_enc_{data_d}_{turma_focal}_{idx}"):
                        ed_tema = st.text_input("Editar Tema:", value=tema_d).upper()
                        ed_obs = st.text_area("Observações Pastorais / Relato:", value=obs_d, height=100)
                        
                        c_btn1, c_btn2 = st.columns([3, 1])
                        btn_salvar = c_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)
                        btn_excluir = c_btn2.form_submit_button("🗑️ EXCLUIR ENCONTRO", use_container_width=True)
                        
                        st.markdown("---")
                        confirma_del = st.checkbox("⚠️ Confirmo a exclusão deste encontro e de todas as presenças do dia", key=f"chk_del_{data_d}_{idx}")
                        
                        if btn_salvar:
                            with st.spinner("Sincronizando Diário, Presenças e Cronograma..."):
                                if atualizar_encontro_global(turma_focal, data_d, ed_tema, ed_obs):
                                    st.success("✅ Tudo atualizado com sucesso!"); time.sleep(1); st.rerun()
                                    
                        if btn_excluir:
                            if confirma_del:
                                with st.spinner("Excluindo encontro e revertendo cronograma..."):
                                    if excluir_encontro_cascata(turma_focal, data_d, tema_d):
                                        st.success("✅ Encontro excluído com sucesso!"); time.sleep(1); st.rerun()
                            else:
                                st.error("⚠️ Marque a caixa de confirmação abaixo para excluir o encontro.")
        else:
            st.info("Nenhum encontro registrado na aba 'encontros' para esta turma.")
    else:
        st.info("O sistema ainda não possui registros de encontros.")



# ==================================================================================
# PÁGINA: 📝 INSCREVER CATEQUIZANDO (COM TOOLTIPS E AJUDA)
# ==================================================================================
elif menu == "📝 Inscrever Catequizando":
    st.title("📝 Inscrição de Catequizandos")
    
    with st.expander("💡 GUIA DE PREENCHIMENTO (LEIA ANTES DE COMEÇAR)", expanded=True):
        st.markdown("""
            *   **Nomes:** Escreva sempre em **MAIÚSCULAS** (Ex: JOÃO DA SILVA).
            *   **Endereço:** Siga o padrão: **Rua/Avenida, Número, Bairro** (Ex: RUA SÃO JOÃO, 500, FÁTIMA).
            *   **WhatsApp:** Coloque apenas o **DDD + Número**. Não precisa do 55 (Ex: 73988887777).
            *   **Documentos:** Marque no checklist apenas o que a pessoa **entregou a cópia (Xerox)** hoje.
        """)

    tab_manual, tab_csv = st.tabs(["📄 Cadastro Individual", "📂 Importar via CSV"])

    with tab_manual:
        # MOTOR DE LIMPEZA: Cria uma chave dinâmica que muda após cada salvamento
        if 'form_cad_key' not in st.session_state:
            st.session_state.form_cad_key = 0
        fk = st.session_state.form_cad_key

        tipo_ficha = st.radio("Tipo de Inscrição:", ["Infantil/Juvenil", "Adulto"], horizontal=True, key=f"tipo_ficha_{fk}")
        
        st.info("**📋 Documentação Necessária (Xerox para a Pasta):** ✔ RG ou Certidão | ✔ Comprovante de Residência | ✔ Batistério | ✔ Certidão de Eucaristia")

        st.subheader("📍 1. Identificação")
        c1, c2, c3 = st.columns([2, 1, 1])
        nome = c1.text_input("Nome Completo", help="Digite em MAIÚSCULAS sem abreviações.", key=f"nome_{fk}").upper()
        
        # Ajuste de intervalo: 100 anos para trás a partir de hoje
        hoje = date.today()
        data_min = date(hoje.year - 100, 1, 1)
        data_nasc = c2.date_input("Data de Nascimento", value=date(1980, 1, 1), min_value=data_min, max_value=hoje, format="DD/MM/YYYY", key=f"data_nasc_{fk}")
        
        lista_turmas = ["CATEQUIZANDOS SEM TURMA"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else[])
        etapa_inscricao = c3.selectbox("Turma/Etapa", lista_turmas, help="Selecione a turma onde o catequizando será alocado.", key=f"etapa_{fk}")

        c4, c5, c6 = st.columns([1.5, 1, 1.5])
        label_fone = "WhatsApp do Catequizando" if tipo_ficha == "Adulto" else "WhatsApp do Responsável"
        contato = c4.text_input(label_fone, help="Apenas números com DDD. Ex: 73988887777", key=f"contato_{fk}")
        batizado = c5.selectbox("Já é Batizado?", ["SIM", "NÃO"], key=f"batizado_{fk}")
        endereco = c6.text_input("Endereço", help="Ex: RUA SÃO JOÃO, 123, FÁTIMA", key=f"endereco_{fk}").upper()

        st.divider()
        if tipo_ficha == "Adulto":
            st.subheader("🚨 2. Contato de Emergência")
            ce1, ce2, ce3 = st.columns([2, 1, 1])
            nome_emergencia = ce1.text_input("Nome do Contato (Cônjuge, Filho, Amigo)", key=f"nome_emerg_{fk}").upper()
            vinculo_emergencia = ce2.selectbox("Vínculo",["CÔNJUGE", "FILHO(A)", "IRMÃO/Ã", "PAI/MÃE", "AMIGO(A)", "OUTRO"], key=f"vinc_emerg_{fk}")
            tel_emergencia = ce3.text_input("Telefone de Emergência", help="Apenas números com DDD.", key=f"tel_emerg_{fk}")
            
            nome_mae, prof_mae, tel_mae = "N/A", "N/A", "N/A"
            nome_pai, prof_pai, tel_pai = "N/A", "N/A", "N/A"
            responsavel_nome, vinculo_resp, tel_responsavel = nome_emergencia, vinculo_emergencia, tel_emergencia
        else:
            st.subheader("👪 2. Filiação e Responsáveis")
            col_mae, col_pai = st.columns(2)
            with col_mae:
                st.markdown("##### 👩‍🦱 Dados da Mãe")
                nome_mae = st.text_input("Nome da Mãe", key=f"nome_mae_{fk}").upper()
                prof_mae = st.text_input("Profissão da Mãe", key=f"prof_mae_{fk}").upper()
                tel_mae = st.text_input("WhatsApp da Mãe", help="Apenas números com DDD.", key=f"tel_mae_{fk}")
            with col_pai:
                st.markdown("##### 👨‍ Dados do Pai")
                nome_pai = st.text_input("Nome do Pai", key=f"nome_pai_{fk}").upper()
                prof_pai = st.text_input("Profissão do Pai", key=f"prof_pai_{fk}").upper()
                tel_pai = st.text_input("WhatsApp do Pai", help="Apenas números com DDD.", key=f"tel_pai_{fk}")

            st.info("🛡️ **Responsável Legal / Cuidador (Caso não more com os pais)**")
            cr1, cr2, cr3 = st.columns([2, 1, 1])
            responsavel_nome = cr1.text_input("Nome do Cuidador", key=f"resp_nome_{fk}").upper()
            vinculo_resp = cr2.selectbox("Vínculo",["NENHUM", "AVÓS", "TIOS", "IRMÃOS", "PADRINHOS", "OUTRO"], key=f"vinc_resp_{fk}")
            tel_responsavel = cr3.text_input("Telefone do Cuidador", key=f"tel_resp_{fk}")

        st.divider()
        st.subheader("⛪ 3. Vida Eclesial e Engajamento")
        fe1, fe2 = st.columns(2)
        
        if tipo_ficha == "Adulto":
            estado_civil = fe1.selectbox("Seu Estado Civil",["SOLTEIRO(A)", "CONVIVEM", "CASADO(A) IGREJA", "CASADO(A) CIVIL", "DIVORCIADO(A)", "VIÚVO(A)"], key=f"est_civil_{fk}")
            sacramentos_list = fe2.multiselect("Sacramentos que VOCÊ já possui:",["BATISMO", "EUCARISTIA", "MATRIMÔNIO"], key=f"sac_list_{fk}")
            sacramentos = ", ".join(sacramentos_list)
            est_civil_pais, sac_pais, tem_irmaos, qtd_irmaos = "N/A", "N/A", "NÃO", 0
        else:
            est_civil_pais = fe1.selectbox("Estado Civil dos Pais",["CASADOS", "UNIÃO DE FACTO", "SEPARADOS", "SOLTEIROS", "VIÚVO(A)"], key=f"est_civil_pais_{fk}")
            sac_pais_list = fe2.multiselect("Sacramentos dos Pais:",["BATISMO", "CRISMA", "EUCARISTIA", "MATRIMÔNIO"], key=f"sac_pais_list_{fk}")
            sac_pais = ", ".join(sac_pais_list)
            tem_irmaos = fe1.radio("Tem irmãos na catequese?",["NÃO", "SIM"], horizontal=True, key=f"tem_irmaos_{fk}")
            qtd_irmaos = fe2.number_input("Quantos?", min_value=0, step=1, key=f"qtd_irmaos_{fk}") if tem_irmaos == "SIM" else 0
            estado_civil, sacramentos = "N/A", "N/A"

        part_grupo = st.radio("Participa (ou a família participa) de algum Grupo/Pastoral?",["NÃO", "SIM"], horizontal=True, key=f"part_grupo_{fk}")
        qual_grupo = "N/A"
        if part_grupo == "SIM":
            qual_grupo = st.text_input("Qual grupo/pastoral e quem participa?", key=f"qual_grupo_{fk}").upper()

        st.divider()
        st.subheader("🕊️ 4. Histórico de Sacramentos")
        st.info("Se o catequizando já possui sacramentos, informe a data (se souber) e a paróquia de origem.")
        
        c_hist1, c_hist2, c_hist3 = st.columns(3)
        with c_hist1:
            dt_bat_hist_dt = st.date_input("Data do Batismo", value=None, format="DD/MM/YYYY", min_value=data_min, max_value=hoje, key=f"dt_bat_{fk}")
        with c_hist2:
            dt_euc_hist_dt = st.date_input("Data da Eucaristia", value=None, format="DD/MM/YYYY", min_value=data_min, max_value=hoje, key=f"dt_euc_{fk}")
        with c_hist3:
            dt_cri_hist_dt = st.date_input("Data da Crisma", value=None, format="DD/MM/YYYY", min_value=data_min, max_value=hoje, key=f"dt_cri_{fk}")
            
        paroq_hist = st.text_input("⛪ Paróquia de Origem (Se feito fora daqui)", placeholder="Ex: Paróquia São José - Ilhéus", key=f"paroq_hist_{fk}").upper()
        
        dt_bat_hist = dt_bat_hist_dt.strftime('%d/%m/%Y') if dt_bat_hist_dt else "N/A"
        dt_euc_hist = dt_euc_hist_dt.strftime('%d/%m/%Y') if dt_euc_hist_dt else "N/A"
        dt_cri_hist = dt_cri_hist_dt.strftime('%d/%m/%Y') if dt_cri_hist_dt else "N/A"
        
        # Sincroniza o status de batismo e sacramentos com as datas preenchidas
        if dt_bat_hist != "N/A": batizado = "SIM"
        
        sacs_marcados_novo =[]
        if dt_bat_hist != "N/A" or batizado == "SIM": sacs_marcados_novo.append("BATISMO")
        if dt_euc_hist != "N/A": sacs_marcados_novo.append("EUCARISTIA")
        if dt_cri_hist != "N/A": sacs_marcados_novo.append("CRISMA")
        if tipo_ficha == "Adulto" and "MATRIMÔNIO" in sacramentos: sacs_marcados_novo.append("MATRIMÔNIO")
        
        sacramentos = ", ".join(sacs_marcados_novo) if sacs_marcados_novo else "N/A"

        st.divider()
        st.subheader("🏥 5. Saúde e Documentação")
        s1, s2 = st.columns(2)
        
        tem_med = s1.radio("Toma algum medicamento ou tem alergia?",["NÃO", "SIM"], horizontal=True, key=f"tem_med_{fk}")
        medicamento = "NÃO"
        if tem_med == "SIM":
            medicamento = s1.text_input("Descreva o medicamento/alergia:", key=f"medicamento_{fk}").upper()
            
        tem_tgo = s2.radio("Possui TGO (Transtorno Global do Desenvolvimento)?", ["NÃO", "SIM"], horizontal=True, help="Autismo, TDAH, Dislexia, etc.", key=f"tem_tgo_{fk}")
        tgo_final = "NÃO"
        if tem_tgo == "SIM":
            tgo_final = s2.text_input("Qual transtorno? (Ex: TEA, TDAH, TOD, etc.)", help="Especifique o transtorno para melhor acompanhamento pastoral.", key=f"tgo_final_{fk}").upper()
        
        st.markdown("---")
        st.markdown("**📁 Checklist de Documentos Entregues (Xerox):**")
        docs_obrigatorios =["RG/CERTIDÃO", "COMPROVANTE RESIDÊNCIA", "BATISTÉRIO", "CERTIDÃO EUCARISTIA"]
        docs_entregues = st.multiselect("Marque o que foi entregue HOJE:", docs_obrigatorios, help="Só marque o que você já tem em mãos.", key=f"docs_entregues_{fk}")
        
        faltando =[d for d in docs_obrigatorios if d not in docs_entregues]
        doc_status_k = ", ".join(faltando) if faltando else "COMPLETO"

        # Lógica de Herança de Turma no Cadastro
        turno_sugerido = "MANHÃ (M)"
        local_sugerido = ""
        
        if etapa_inscricao != "CATEQUIZANDOS SEM TURMA" and not df_turmas.empty:
            info_t = df_turmas[df_turmas['nome_turma'] == etapa_inscricao]
            if not info_t.empty:
                # Mapeia o turno da aba Turmas para o padrão do selectbox
                t_base = str(info_t.iloc[0].get('turno', 'MANHÃ')).upper()
                if "TARDE" in t_base: turno_sugerido = "TARDE (T)"
                elif "NOITE" in t_base: turno_sugerido = "NOITE (N)"
                else: turno_sugerido = "MANHÃ (M)"
                
                local_sugerido = str(info_t.iloc[0].get('local', '')).upper()

        c_pref1, c_pref2 = st.columns(2)
        
        # O selectbox e o text_input agora herdam os valores da turma selecionada automaticamente
        opcoes_turno = ["MANHÃ (M)", "TARDE (T)", "NOITE (N)"]
        idx_turno = opcoes_turno.index(turno_sugerido)
        
        turno = c_pref1.selectbox("Turno (Herdado da Turma)", opcoes_turno, index=idx_turno, key=f"turno_{fk}")
        local_enc = c_pref2.text_input("Local (Herdado da Turma)", value=local_sugerido, key=f"local_enc_{fk}").upper()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 FINALIZAR E SALVAR INSCRIÇÃO", use_container_width=True):
            if nome and contato and etapa_inscricao != "CATEQUIZANDOS SEM TURMA":
                # 1. Preparar dados
                novo_id = f"CAT-{int(time.time())}"
                if tipo_ficha == "Adulto":
                    resp_final = nome_emergencia
                    obs_familia = f"EMERGÊNCIA: {vinculo_emergencia} - TEL: {tel_emergencia}"
                else:
                    resp_final = responsavel_nome if responsavel_nome else f"{nome_mae} / {nome_pai}"
                    obs_familia = f"CUIDADOR: {responsavel_nome} ({vinculo_resp}). TEL: {tel_responsavel}" if responsavel_nome else "Mora com os pais."

                registro = [[
                        novo_id, etapa_inscricao, nome, data_nasc.strftime('%d/%m/%Y'), batizado, 
                        contato, endereco, nome_mae, nome_pai, resp_final, 
                        doc_status_k, qual_grupo, "ATIVO", medicamento, tgo_final, 
                        estado_civil, sacramentos, prof_mae, tel_mae, prof_pai, 
                        tel_pai, est_civil_pais, sac_pais, part_grupo, qual_grupo, 
                        tem_irmaos, qtd_irmaos, turno, local_enc, obs_familia,
                        dt_bat_hist,
                        dt_euc_hist,
                        dt_cri_hist,
                        paroq_hist if paroq_hist else "N/A"
                    ]]

                # 2. Verificar duplicidade
                duplicatas = df_cat[df_cat['nome_completo'].str.upper() == nome.upper()]
                
                if not duplicatas.empty:
                    st.warning(f"⚠️ **ATENÇÃO:** Já existe um registro com o nome '{nome}'.")
                    col_a, col_b = st.columns(2)
                    if col_a.button("✅ SIM, ATUALIZAR CADASTRO"):
                        id_existente = duplicatas.iloc[0]['id_catequizando']
                        lista_up = registro[0]
                        lista_up[12] = "ATIVO" # Força status para ATIVO
                        if atualizar_catequizando(id_existente, lista_up):
                            st.success(f"✅ Cadastro de {nome} atualizado!"); time.sleep(1); st.rerun()
                    if col_b.button("🆕 NÃO, CADASTRAR COMO NOVO"):
                        if salvar_lote_catequizandos(registro):
                            st.success(f"✅ {nome} cadastrado como novo!"); time.sleep(1); st.rerun()
                else:
                    # 3. Salvar novo
                    if salvar_lote_catequizandos(registro):
                        st.success(f"✅ {nome} cadastrado com sucesso!"); st.balloons()
                        st.session_state.form_cad_key += 1
                        time.sleep(1); st.rerun()
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
                                
                                registro =[
                                    f"CAT-CSV-{int(time.time()) + i}", t_final, str(linha.get(col_nome, 'SEM NOME')).upper(), 
                                    formatar_data_br(linha.get('data_nascimento', '01/01/2000')), str(linha.get('batizado_sn', 'NÃO')).upper(), 
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
                                    f"Importado via CSV em {date.today().strftime('%d/%m/%Y')}",
                                    "N/A", "N/A", "N/A", "N/A" # Expansão das novas colunas históricas
                                ]
                                lista_final.append(registro)
                            
                            if salvar_lote_catequizandos(lista_final):
                                st.success(f"✅ {len(lista_final)} catequizandos importados!"); st.balloons(); time.sleep(2); st.rerun()
            except Exception as e:
                st.error(f"❌ Erro: {e}")



# ==============================================================================
# PÁGINA: 👤 PERFIL INDIVIDUAL (DOSSIÊ DIGITAL 360º)
# ==============================================================================
elif menu == "👤 Perfil Individual":
    st.title("👤 Dossiê Digital e Secretaria Pastoral")
    
    if df_cat.empty:
        st.warning("⚠️ Base de dados vazia.")
        st.stop()

    # --- ESTRUTURA DE ABAS CONDICIONAL ---
    eh_secretaria_perfil = st.session_state.usuario.get('papel', '').upper() == 'SECRETARIA'
    if eh_gestor or eh_secretaria_perfil:
        tabs = st.tabs([
            "🪪 Cartão de Identidade (Consulta/Edição)", 
            "📁 Maleta de Documentos (Auditoria)", 
            "🏛️ Secretaria Pastoral (Egressos/Transferências)"
        ])
        tab_individual = tabs[0]
        tab_auditoria_geral = tabs[1]
        tab_evasao_gestao = tabs[2]
    else:
        tab_individual = st.container()
        tab_auditoria_geral = None
        tab_evasao_gestao = None

    # ==========================================================================
    # HUB 1: CARTÃO DE IDENTIDADE PASTORAL
    # ==========================================================================
    with tab_individual:
        st.subheader("🔍 Localizar Catequizando")
        
        # BLINDAGEM: A Secretaria precisa da mesma visão global de busca que o Gestor
        if eh_gestor or eh_secretaria_perfil:
            c1, c2 = st.columns([2, 1])
            busca = c1.text_input("Pesquisar por nome:", key="busca_perfil").upper()
            lista_t = ["TODAS"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else[])
            filtro_t = c2.selectbox("Filtrar por Turma:", lista_t, key="filtro_turma_perfil")
            df_f = df_cat.copy()
            if busca: df_f = df_f[df_f['nome_completo'].str.contains(busca, na=False)]
            if filtro_t != "TODAS": df_f = df_f[df_f['etapa'] == filtro_t]
        else:
            nome_usuario = st.session_state.usuario.get('nome', '').strip()
            turma_vinculada = str(st.session_state.usuario.get('turma_vinculada', ''))
            turmas_responsavel = df_turmas[df_turmas['catequista_responsavel'].str.contains(nome_usuario, na=False, case=False)]['nome_turma'].tolist() if not df_turmas.empty else []
            turmas_lista = list(set([t.strip() for t in turma_vinculada.split(',') if t.strip()] + turmas_responsavel))
            
            df_f = df_cat[df_cat['etapa'].isin(turmas_lista)]
            if df_f.empty: st.info("⚠️ Nenhuma turma vinculada encontrada para o seu perfil.")
            
            busca = st.text_input("Pesquisar por nome na minha turma:", key="busca_perfil").upper()
            if busca: df_f = df_f[df_f['nome_completo'].str.contains(busca, na=False)]
        
        df_f['display_select'] = df_f['nome_completo'] + " | Turma: " + df_f['etapa'] + " | ID: " + df_f['id_catequizando']
        escolha_display = st.selectbox("Selecione o catequizando para abrir o Dossiê:", [""] + df_f['display_select'].tolist(), key="sel_catequizando_perfil")

        if escolha_display:
            id_sel = escolha_display.split(" | ID: ")[-1]
            filtro_dados = df_cat[df_cat['id_catequizando'] == id_sel]
            
            if not filtro_dados.empty:
                dados = filtro_dados.iloc[0]
                nome_sel = dados['nome_completo']
                status_atual = str(dados['status']).upper()
                idade_atual = calcular_idade(dados['data_nascimento'])
                is_adulto = idade_atual >= 18

                obs_p = str(dados.get('obs_pastoral_familia', ''))
                tel_e = obs_p.split('TEL: ')[-1] if 'TEL: ' in obs_p else "Não informado"
                
                # --- BUSCA HÍBRIDA DE DATAS (Passado + Presente) ---
                v_bat_hist = str(dados.iloc[30]).strip() if len(dados) > 30 else "N/A"
                v_euc_hist = str(dados.iloc[31]).strip() if len(dados) > 31 else "N/A"
                v_cri_hist = str(dados.iloc[32]).strip() if len(dados) > 32 else "N/A"
                v_paroq_hist = str(dados.iloc[33]).strip() if len(dados) > 33 else "N/A"

                data_bat = f" ({v_bat_hist})" if v_bat_hist not in ["N/A", "", "None", "()"] else ""
                data_euc = f" ({v_euc_hist})" if v_euc_hist not in["N/A", "", "None", "()"] else ""
                data_cri = f" ({v_cri_hist})" if v_cri_hist not in ["N/A", "", "None", "()"] else ""

                df_recebidos = ler_aba("sacramentos_recebidos")
                if not df_recebidos.empty:
                    rec_aluno = df_recebidos[df_recebidos.iloc[:, 1] == id_sel]
                    for _, r in rec_aluno.iterrows():
                        if r.iloc[3].upper() == 'BATISMO': data_bat = f" ({formatar_data_br(r.iloc[4])})"
                        if r.iloc[3].upper() == 'EUCARISTIA': data_euc = f" ({formatar_data_br(r.iloc[4])})"
                        if r.iloc[3].upper() == 'CRISMA': data_cri = f" ({formatar_data_br(r.iloc[4])})"

                qtd_faltas = len(df_pres[(df_pres['id_catequizando'] == id_sel) & (df_pres['status'] == 'AUSENTE')]) if not df_pres.empty else 0
                alerta_falta = f"<span style='color:#e03d11; font-weight:bold;'>{qtd_faltas} Faltas</span>" if qtd_faltas >= 3 else f"{qtd_faltas} Faltas"
                
                bat = f"💧 Batizado{data_bat}" if dados['batizado_sn'] == "SIM" else "⚪ Sem Batismo"
                euc = f"🍞 Eucaristia{data_euc}" if "EUCARISTIA" in str(dados['sacramentos_ja_feitos']).upper() else "⚪ Sem Eucaristia"
                cri = f"🔥 Crisma{data_cri}" if "CRISMA" in str(dados['sacramentos_ja_feitos']).upper() else "⚪ Sem Crisma"
                
                status_color = "#2e7d32" if status_atual == "ATIVO" else "#e03d11" if status_atual in ["DESISTENTE", "INATIVO"] else "#ffa000"
                
                # --- O CARTÃO DE IDENTIDADE VISUAL 4.0 ---
                st.markdown(f"""
                    <div style='background-color:#ffffff; padding:20px; border-radius:15px; border-left:10px solid {status_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; margin-top: 10px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;'>
                            <div style='flex: 1; min-width: 250px;'>
                                <h2 style='margin:0; color:#417b99; font-size: 24px;'>👤 {nome_sel}</h2>
                                <p style='margin:8px 0 0 0; font-size:15px; color:#555;'>
                                    <b>Turma:</b> {dados['etapa']} &nbsp;|&nbsp; <b>Idade:</b> {idade_atual} anos &nbsp;|&nbsp; <b>Histórico:</b> {alerta_falta} &nbsp;|&nbsp; 
                                    <span style='background-color:{status_color}; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold;'>{status_atual}</span>
                                </p>
                            </div>
                            <div style='text-align: right; flex: 1; min-width: 250px; margin-top: 10px;'>
                                <p style='margin:0; font-size:13px; color:#666;'><b>Selos Sacramentais:</b><br>{bat} <br> {euc} <br> {cri}</p>
                                <div style='margin-top:8px; background-color:#fff5f5; padding:8px; border-radius:8px; display:inline-block; border: 1px solid #fbd5d5;'>
                                    <span style='color:#e03d11; font-size:13px;'><b>🚨 Emergência:</b> {dados['nome_responsavel']} ({tel_e})</span>
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                sub_tab_edit, sub_tab_doc, sub_tab_hist = st.tabs(["✏️ Editar Cadastro", "📄 Gerar Documentos (PDF)", "📜 Extrato de Caminhada"])
                
                with sub_tab_edit:
                    st.markdown("#### ✏️ Atualizar Dados do Catequizando")
                    st.markdown("#### 📍 1. Identificação e Status")
                    ce1, ce2 = st.columns([2, 1])
                    ed_nome = ce1.text_input("Nome Completo", value=dados['nome_completo']).upper()
                    
                    opcoes_status =["ATIVO", "CONCLUÍDO", "TRANSFERIDO", "DESISTENTE", "INATIVO"]
                    idx_status = opcoes_status.index(status_atual) if status_atual in opcoes_status else 0
                    ed_status = ce2.selectbox("Alterar Status para:", opcoes_status, index=idx_status, help="CONCLUÍDO: Finalizou a Crisma. DESISTENTE: Saiu da catequese.")

                    c3, c5 = st.columns([1, 2])
                    hoje = date.today()
                    data_min = date(hoje.year - 100, 1, 1)
                    ed_nasc = c3.date_input("Nascimento", value=converter_para_data(dados['data_nascimento']), min_value=data_min, max_value=hoje, format="DD/MM/YYYY")
                    
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
                        opcoes_ec =["SOLTEIRO(A)", "CONVIVEM", "CASADO(A) IGREJA", "CASADO(A) CIVIL", "DIVORCIADO(A)", "VIÚVO(A)"]
                        val_ec = str(dados.get('estado_civil_pais_ou_proprio', 'SOLTEIRO(A)')).upper()
                        idx_ec = opcoes_ec.index(val_ec) if val_ec in opcoes_ec else 0
                        ed_est_civil = fe2.selectbox("Estado Civil", opcoes_ec, index=idx_ec)
                        ed_est_civil_pais = "N/A"
                    else:
                        opcoes_ecp =["CASADOS", "UNIÃO DE FACTO", "SEPARADOS", "SOLTEIROS", "VIÚVO(A)"]
                        val_ecp = str(dados.get('est_civil_pais', 'CASADOS')).upper()
                        idx_ecp = opcoes_ecp.index(val_ecp) if val_ecp in opcoes_ecp else 0
                        ed_est_civil_pais = fe2.selectbox("Estado Civil dos Pais", opcoes_ecp, index=idx_ecp)
                        ed_est_civil = "N/A"

                    st.markdown("#### 🕊️ Sacramentos Possuídos e Histórico")
                    st.info("Marque os sacramentos que o catequizando já possui. Se souber a data, preencha no calendário.")
                    
                    sac_atuais = str(dados.get('sacramentos_ja_feitos', '')).upper()
                    
                    def parse_hist_date(d_str):
                        if d_str in["N/A", "", "None", "()"]: return None
                        try: return dt_module.datetime.strptime(d_str, "%d/%m/%Y").date()
                        except: return None

                    d_bat_val = parse_hist_date(v_bat_hist)
                    d_euc_val = parse_hist_date(v_euc_hist)
                    d_cri_val = parse_hist_date(v_cri_hist)

                    has_bat_init = "BATISMO" in sac_atuais or dados.get('batizado_sn', '') == "SIM"
                    has_euc_init = "EUCARISTIA" in sac_atuais
                    has_cri_init = "CRISMA" in sac_atuais
                    has_mat_init = "MATRIMÔNIO" in sac_atuais

                    c_h1, c_h2, c_h3, c_h4 = st.columns(4)
                    with c_h1:
                        ed_has_bat = st.toggle("💧 Batismo", value=has_bat_init)
                        ed_bat_hist_dt = st.date_input("Data Batismo", value=d_bat_val, format="DD/MM/YYYY", min_value=data_min, max_value=hoje) if ed_has_bat else None
                    with c_h2:
                        ed_has_euc = st.toggle("🍞 Eucaristia", value=has_euc_init)
                        ed_euc_hist_dt = st.date_input("Data Eucaristia", value=d_euc_val, format="DD/MM/YYYY", min_value=data_min, max_value=hoje) if ed_has_euc else None
                    with c_h3:
                        ed_has_cri = st.toggle("🔥 Crisma", value=has_cri_init)
                        ed_cri_hist_dt = st.date_input("Data Crisma", value=d_cri_val, format="DD/MM/YYYY", min_value=data_min, max_value=hoje) if ed_has_cri else None
                    with c_h4:
                        ed_has_mat = st.toggle("💍 Matrimônio", value=has_mat_init)

                    ed_paroq_hist = st.text_input("⛪ Paróquia de Origem (Se feito fora daqui)", value="" if v_paroq_hist in ["N/A", "None"] else v_paroq_hist, help="Ex: Paróquia São José - Ilhéus").upper()
                    
                    sacs_marcados =[]
                    if ed_has_bat: sacs_marcados.append("BATISMO")
                    if ed_has_euc: sacs_marcados.append("EUCARISTIA")
                    if ed_has_cri: sacs_marcados.append("CRISMA")
                    if ed_has_mat: sacs_marcados.append("MATRIMÔNIO")
                    ed_sac_final = ", ".join(sacs_marcados)
                    
                    ed_batizado = "SIM" if ed_has_bat else "NÃO"
                    ed_bat_hist = ed_bat_hist_dt.strftime('%d/%m/%Y') if ed_bat_hist_dt else "N/A"
                    ed_euc_hist = ed_euc_hist_dt.strftime('%d/%m/%Y') if ed_euc_hist_dt else "N/A"
                    ed_cri_hist = ed_cri_hist_dt.strftime('%d/%m/%Y') if ed_cri_hist_dt else "N/A"

                    st.divider()

                    st.markdown("#### 🏥 4. Saúde e Documentação")
                    s1, s2 = st.columns(2)
                    med_atual = str(dados.get('toma_medicamento_sn', 'NÃO')).upper()
                    ed_tem_med = s1.radio("Toma algum medicamento?",["NÃO", "SIM"], index=0 if med_atual == "NÃO" else 1, horizontal=True)
                    ed_med = s1.text_input("Descreva o medicamento:", value=med_atual if med_atual != "NÃO" else "").upper() if ed_tem_med == "SIM" else "NÃO"
                    
                    tgo_atual = str(dados.get('tgo_sn', 'NÃO')).upper()
                    ed_tem_tgo = s2.radio("Possui TGO?", ["NÃO", "SIM"], index=0 if tgo_atual == "NÃO" else 1, horizontal=True)
                    ed_tgo_final = s2.text_input("Qual transtorno?", value=tgo_atual if tgo_atual != "NÃO" else "").upper() if ed_tem_tgo == "SIM" else "NÃO"

                    st.markdown("**📁 Checklist de Documentos (Xerox):**")
                    # --- Checklist Inteligente: Se tiver TGO, exige LAUDO MÉDICO ---
                    is_neuro = (ed_tem_tgo == "SIM") # ed_tem_tgo é definido logo acima no formulário
                    docs_obrigatorios = ["RG/CERTIDÃO", "COMPROVANTE RESIDÊNCIA", "BATISTÉRIO", "CERTIDÃO EUCARISTIA"]
                    if is_neuro: docs_obrigatorios.append("LAUDO MÉDICO")
                    
                    faltas_atuais = str(dados.get('doc_em_falta', '')).upper()
                    # Filtra o que já está entregue
                    entregues_pre = [d for d in docs_obrigatorios if d not in faltas_atuais]
                    
                    ed_docs_entregues = st.multiselect("Marque o que JÁ ESTÁ NA PASTA:", docs_obrigatorios, default=entregues_pre)
                    
                    novas_faltas = [d for d in docs_obrigatorios if d not in ed_docs_entregues]
                    ed_doc_status_k = ", ".join(novas_faltas) if novas_faltas else "COMPLETO"

                    if st.button("💾 SALVAR ALTERAÇÕES NO BANCO DE DADOS", use_container_width=True, type="primary"):
                        obs_final = f"EMERGÊNCIA: {ed_resp} - TEL: {ed_tel_resp}" if is_adulto else dados.get('obs_pastoral_familia', '')
                        lista_up =[
                            dados['id_catequizando'], ed_etapa, ed_nome, ed_nasc.strftime('%d/%m/%Y'), ed_batizado, 
                            ed_contato, ed_end, ed_mae, ed_pai, ed_resp, ed_doc_status_k, 
                            ed_qual_grupo, ed_status, ed_med, ed_tgo_final, ed_est_civil, 
                            ed_sac_final, ed_prof_m, ed_tel_m, ed_prof_p, ed_tel_p, 
                            ed_est_civil_pais, dados.get('sac_pais', 'N/A'), 
                            ed_part_grupo, ed_qual_grupo, dados.get('tem_irmaos', 'NÃO'), 
                            dados.get('qtd_irmaos', 0), dados.get('turno', 'N/A'), 
                            dados.get('local_encontro', 'N/A'), obs_final,
                            formatar_data_br(ed_bat_hist) if ed_bat_hist else "N/A",
                            formatar_data_br(ed_euc_hist) if ed_euc_hist else "N/A",
                            formatar_data_br(ed_cri_hist) if ed_cri_hist else "N/A",
                            ed_paroq_hist if ed_paroq_hist else "N/A"
                        ]
                        if atualizar_catequizando(dados['id_catequizando'], lista_up):
                            sincronizar_edicao_catequizando(dados['id_catequizando'], ed_nome, ed_etapa)
                            st.success(f"✅ Cadastro de {ed_nome} atualizado e histórico sincronizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()

                with sub_tab_doc:
                    st.markdown("#### 📄 Documentação Cadastral e Oficial")
                    col_doc_a, col_doc_b = st.columns(2)
                    with col_doc_a:
                        if st.button("📑 Gerar Ficha de Inscrição Completa", key="btn_pdf_perfil", use_container_width=True):
                            st.session_state.pdf_catequizando = gerar_ficha_cadastral_catequizando(dados.to_dict())
                        if "pdf_catequizando" in st.session_state:
                            st.download_button("📥 BAIXAR FICHA PDF", st.session_state.pdf_catequizando, f"Ficha_{nome_sel}.pdf", "application/pdf", use_container_width=True)
                    with col_doc_b:
                        if st.button("📜 Gerar Declaração de Inscrição", key="btn_decl_matr_perfil", use_container_width=True):
                            st.session_state.pdf_decl_matr = gerar_declaracao_pastoral_pdf(dados.to_dict(), "Declaração de Inscrição / Vínculo Pastoral")
                        if "pdf_decl_matr" in st.session_state:
                            st.download_button("📥 BAIXAR DECLARAÇÃO PDF", st.session_state.pdf_decl_matr, f"Declaracao_Inscricao_{nome_sel}.pdf", "application/pdf", use_container_width=True)

                with sub_tab_hist:
                    st.markdown("#### 📜 Extrato de Caminhada (Presenças e Temas)")
                    if not df_pres.empty and 'id_catequizando' in df_pres.columns:
                        pres_aluno = df_pres[df_pres['id_catequizando'] == dados['id_catequizando']].copy()
                    else:
                        pres_aluno = pd.DataFrame()
                        
                    if not pres_aluno.empty:
                        pres_aluno['data_dt'] = pd.to_datetime(pres_aluno.get('data_encontro', ''), errors='coerce', dayfirst=True)
                        pres_aluno = pres_aluno.sort_values('data_dt', ascending=False)
                        
                        for _, p in pres_aluno.iterrows():
                            icone_p = "✅" if p.get('status', '') == "PRESENTE" else "❌"
                            cor_p = "#2e7d32" if p.get('status', '') == "PRESENTE" else "#e03d11"
                            data_f = formatar_data_br(p.get('data_encontro', ''))
                            tema_f = p.get('tema_do_dia', 'Tema não registrado')
                            st.markdown(f"<div style='padding:10px; border-bottom:1px solid #eee; background-color:#f8f9f0; border-radius:5px; margin-bottom:5px;'><span style='color:{cor_p}; font-size:16px;'>{icone_p}</span> <b>{data_f}</b> | {tema_f} <i>({p.get('status', '')})</i></div>", unsafe_allow_html=True)
                    else:
                        st.info("Nenhum registro de presença/falta para este catequizando.")

    # ==========================================================================
    # HUB 2: MALETA DE DOCUMENTOS (AUDITORIA VISUAL)
    # ==========================================================================
    if (eh_gestor or eh_secretaria_perfil) and tab_auditoria_geral is not None:
        with tab_auditoria_geral:
            st.subheader("📁 Maleta de Documentos (Auditoria por Turma)")
            lista_turmas_auditoria = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else[]
            turma_auditoria = st.selectbox("🔍 Selecione a Turma para Diagnóstico:", lista_turmas_auditoria, key="sel_auditoria_doc_turma")

            if turma_auditoria:
                df_turma_focal = df_cat[(df_cat['etapa'] == turma_auditoria) & (df_cat['status'] == 'ATIVO')]
                df_pendentes_turma = df_turma_focal[
                    (df_turma_focal['doc_em_falta'].str.len() > 2) & 
                    (~df_turma_focal['doc_em_falta'].isin(['NADA', 'N/A', 'OK', 'COMPLETO', 'NADA FALTANDO']))
                ]

                total_t = len(df_turma_focal)
                pendentes_t = len(df_pendentes_turma)
                em_dia_t = total_t - pendentes_t
                
                # Barra de Progresso Visual
                progresso_docs = (em_dia_t / total_t) if total_t > 0 else 1.0
                st.markdown(f"**Progresso de Entrega da Turma: {em_dia_t} de {total_t} catequizandos estão em dia ({progresso_docs*100:.0f}%)**")
                st.progress(progresso_docs)
                st.markdown("<br>", unsafe_allow_html=True)

                if df_pendentes_turma.empty:
                    st.success(f"✅ **Excelente!** Todos os {total_t} catequizandos da turma **{turma_auditoria}** estão com a documentação completa na pasta.")
                else:
                    st.markdown(f"#### 📋 Lista de Pendências: {turma_auditoria}")
                    import urllib.parse
                    
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
                                <div style='background-color:#fff5f5; padding:15px; border-radius:10px; border-left:8px solid #e03d11; margin-bottom:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                                    <b style='color:#e03d11; font-size:16px;'>{p['nome_completo']}</b><br>
                                    <span style='font-size:14px; color:#333;'>⚠️ <b>FALTANDO:</b> {p['doc_em_falta']}</span><br>
                                    <span style='font-size:13px; color:#666;'>👤 <b>Cobrar de:</b> {nome_alvo} ({vinculo_alvo})</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            col_p1, col_p2 = st.columns([1, 1])
                            
                            # Botão de WhatsApp Automático (Sem custo de IA)
                            num_limpo = "".join(filter(str.isdigit, str(tel_alvo)))
                            if num_limpo:
                                if num_limpo.startswith("0"): num_limpo = num_limpo[1:]
                                if not num_limpo.startswith("55"): num_limpo = f"5573{num_limpo}" if len(num_limpo) <= 9 else f"55{num_limpo}"
                                
                                # A mensagem agora carrega dinamicamente o que falta, incluindo o LAUDO MÉDICO se for necessário
                                msg_doc = f"Paz e Bem, {nome_alvo}! Aqui é da Secretaria da Paróquia de Fátima. Verificamos que falta entregar a cópia do(s) seguinte(s) documento(s): {p['doc_em_falta']} para a pasta do(a) catequizando(a) {p['nome_completo']}. Poderia nos enviar ou levar na secretaria no próximo encontro? Deus abençoe!"                                
                                link_doc = f"https://wa.me/{num_limpo}?text={urllib.parse.quote(msg_doc)}"
                                col_p1.markdown(f"<a href='{link_doc}' target='_blank' style='text-decoration:none;'><div style='background-color:#25d366; color:white; text-align:center; padding:8px; border-radius:5px; font-size:13px; font-weight:bold;'>📲 Enviar Cobrança no WhatsApp</div></a>", unsafe_allow_html=True)
                            else:
                                col_p1.caption("Sem telefone válido.")
                            
                            if col_p2.button("✅ Marcar como Entregue", key=f"btn_ok_aud_{p['id_catequizando']}", use_container_width=True):
                                lista_up = p.tolist()
                                while len(lista_up) < 30: lista_up.append("N/A")
                                lista_up[10] = "COMPLETO"
                                if atualizar_catequizando(p['id_catequizando'], lista_up):
                                    st.success("Atualizado!"); time.sleep(0.5); st.rerun()

                            st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # HUB 3: SECRETARIA PASTORAL (EGRESSOS E TRANSFERÊNCIAS)
    # ==========================================================================
    if (eh_gestor or eh_secretaria_perfil) and tab_evasao_gestao is not None:
        with tab_evasao_gestao:
            st.subheader("🏛️ Secretaria Pastoral (Egressos e Transferências)")
            df_saidas = df_cat[df_cat['status'] != 'ATIVO']
            
            c_ev1, c_ev2, c_ev3, c_ev4 = st.columns(4)
            c_ev1.metric("🎓 Concluídos (Egressos)", len(df_saidas[df_saidas['status'] == 'CONCLUÍDO']))
            c_ev2.metric("🔴 Desistentes", len(df_saidas[df_saidas['status'] == 'DESISTENTE']))
            c_ev3.metric("🔵 Transferidos", len(df_saidas[df_saidas['status'] == 'TRANSFERIDO']))
            c_ev4.metric("⚪ Inativos", len(df_saidas[df_saidas['status'] == 'INATIVO']))
            
            st.divider()
            
            df_evasao_real = df_saidas[df_saidas['status'] != 'CONCLUÍDO']
            df_concluidos = df_saidas[df_saidas['status'] == 'CONCLUÍDO']
            
            col_lista1, col_lista2 = st.columns(2)
            
            with col_lista1:
                st.markdown("#### 🎓 Galeria de Egressos (Concluíram)")
                if not df_concluidos.empty:
                    st.dataframe(df_concluidos[['nome_completo', 'etapa']], use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum catequizando marcado como concluído ainda.")
                    
            with col_lista2:
                st.markdown("#### 🔄 Transferências e Desistências")
                if not df_evasao_real.empty:
                    st.dataframe(df_evasao_real[['nome_completo', 'status', 'obs_pastoral_familia']], use_container_width=True, hide_index=True)
                else:
                    st.success("Glória a Deus! Não há registros de evasão.")
                
            st.divider()
            
            if not df_saidas.empty:
                st.markdown("#### 📄 Gerar Declaração Oficial (Transferência ou Matrícula)")
                sel_cat_ev = st.selectbox("Selecione o Catequizando para o Documento:", [""] + df_saidas['nome_completo'].tolist(), key="sel_ev_doc")
                
                if sel_cat_ev:
                    dados_ev = df_saidas[df_saidas['nome_completo'] == sel_cat_ev].iloc[0]
                    col_d1, col_d2 = st.columns(2)
                    tipo_doc = col_d1.selectbox("Tipo de Documento:", ["Declaração de Transferência", "Declaração de Matrícula"])
                    paroquia_dest = ""
                    if "Transferência" in tipo_doc:
                        paroquia_dest = col_d2.text_input("Transferido para a Paróquia:", placeholder="Ex: Paróquia Santa Rita").upper()

                    if st.button(f"📥 GERAR {tipo_doc.upper()}", use_container_width=True, type="primary"):
                        with st.spinner("Renderizando documento oficial..."):
                            pdf_ev_final = gerar_declaracao_pastoral_pdf(dados_ev.to_dict(), tipo_doc, paroquia_dest)
                            st.session_state.pdf_declaracao_saida = pdf_ev_final
                    
                    if "pdf_declaracao_saida" in st.session_state:
                        st.download_button("💾 BAIXAR DECLARAÇÃO (PDF)", st.session_state.pdf_declaracao_saida, f"Declaracao_{sel_cat_ev}.pdf", use_container_width=True)
                    
                    st.markdown("---")
                    if st.button(f"🔄 REATIVAR {sel_cat_ev} (Voltou para a Catequese)"):
                        lista_up_v = dados_ev.tolist()
                        while len(lista_up_v) < 30: lista_up_v.append("N/A")
                        lista_up_v[12] = "ATIVO"
                        if atualizar_catequizando(dados_ev['id_catequizando'], lista_up_v):
                            st.success(f"{sel_cat_ev} reativado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()



# ==============================================================================
# PÁGINA: 🏫 GESTÃO DE TURMAS E FILA DE ESPERA (TORRE DE CONTROLE 3.0)
# ==============================================================================
elif menu == "🏫 Gestão de Turmas":
    st.title("🏫 Gestão de Turmas e Fila de Espera")
    
    # --- NOVA ARQUITETURA: 3 SUPER HUBS ---
    tab_visao, tab_painel, tab_logistica = st.tabs([
        "🗺️ Visão Global", "🏫 Painel da Turma (Raio-X)", "🔀 Logística e Alocação"
    ])
    
    dias_opcoes =["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    etapas_lista =[
        "PRÉ", "PRIMEIRA ETAPA", "SEGUNDA ETAPA", "TERCEIRA ETAPA", 
        "PERSEVERANÇA", "ADULTOS TURMA EUCARISTIA/BATISMO", "ADULTOS CRISMA"
    ]

    df_cron_local = ler_aba("cronograma")
    df_enc_local = ler_aba("encontros")
    df_pres_reu = ler_aba("presenca_reuniao")

    # ==========================================================================
    # HUB 1: VISÃO GLOBAL (MAPA DE PLANEJAMENTO)
    # ==========================================================================
    with tab_visao:
        st.subheader("🗺️ Mapa Global de Planejamento e Itinerários")
        st.markdown("Visão panorâmica de todas as turmas: saiba quem está planejando os encontros e quem está com o diário atrasado.")
        
        if not df_turmas.empty:
            dados_mapa =[]
            for _, t in df_turmas.iterrows():
                nome_t = str(t['nome_turma']).strip().upper()
                cats = str(t.get('catequista_responsavel', 'Não informado'))
                
                # 1. Encontros Realizados
                enc_t = df_enc_local[df_enc_local['turma'].astype(str).str.strip().str.upper() == nome_t] if not df_enc_local.empty else pd.DataFrame()
                qtd_realizados = len(enc_t)
                ultimo_tema = "Nenhum"
                if not enc_t.empty:
                    enc_t['data_dt'] = pd.to_datetime(enc_t['data'], errors='coerce')
                    enc_t = enc_t.sort_values(by='data_dt', ascending=False)
                    ultimo_tema = enc_t.iloc[0]['tema']
                
                # 2. Cronograma Planejado
                cron_t = df_cron_local[df_cron_local['etapa'].astype(str).str.strip().str.upper() == nome_t] if not df_cron_local.empty else pd.DataFrame()
                qtd_planejados = len(cron_t)
                proximo_tema = "Nenhum"
                status_plan = "🔴 Sem Planejamento"
                
                if not cron_t.empty:
                    col_status = 'status' if 'status' in cron_t.columns else ('col_4' if 'col_4' in cron_t.columns else None)
                    if col_status:
                        pendentes = cron_t[cron_t[col_status].astype(str).str.strip().str.upper() != 'REALIZADO']
                        if not pendentes.empty:
                            proximo_tema = pendentes.iloc[0]['titulo_tema']
                            status_plan = "🟢 Em Dia"
                        else:
                            status_plan = "🟡 Planejamento Esgotado"
                
                dados_mapa.append({
                    "Turma": nome_t, "Catequistas": cats, "Status": status_plan,
                    "Realizados": qtd_realizados, "Planejados": qtd_planejados,
                    "Último Tema Dado": ultimo_tema, "Próximo Tema": proximo_tema
                })
            
            df_mapa = pd.DataFrame(dados_mapa)
            
            c1, c2 = st.columns([1, 2])
            filtro_status = c1.selectbox("🔍 Filtrar por Status:",["TODOS", "🟢 Em Dia", "🟡 Planejamento Esgotado", "🔴 Sem Planejamento"])
            if filtro_status != "TODOS":
                df_mapa = df_mapa[df_mapa['Status'] == filtro_status]
                
            st.dataframe(df_mapa, use_container_width=True, hide_index=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            turmas_sem_plan = df_mapa[df_mapa['Status'] == "🔴 Sem Planejamento"]['Turma'].tolist()
            if turmas_sem_plan:
                st.error(f"⚠️ **Atenção Coordenação:** As seguintes turmas não possuem nenhum tema planejado no cronograma: {', '.join(turmas_sem_plan)}")
                
            turmas_esgotadas = df_mapa[df_mapa['Status'] == "🟡 Planejamento Esgotado"]['Turma'].tolist()
            if turmas_esgotadas:
                st.warning(f"⚠️ **Aviso:** As seguintes turmas já deram todos os temas planejados e precisam cadastrar novos: {', '.join(turmas_esgotadas)}")
        else:
            st.info("Nenhuma turma cadastrada.")

    # ==========================================================================
    # HUB 2: PAINEL DA TURMA (RAIO-X 360º)
    # ==========================================================================
    with tab_painel:
        st.subheader("🏫 Raio-X e Gestão Profunda da Turma")
        if not df_turmas.empty:
            t_alvo = st.selectbox("🔍 Selecione a turma para gerenciar:", df_turmas['nome_turma'].tolist(), key="sel_dash_turma_nova")
            
            if t_alvo:
                alunos_t_todos = df_cat[df_cat['etapa'] == t_alvo] if not df_cat.empty else pd.DataFrame()
                alunos_t = alunos_t_todos[alunos_t_todos['status'] == 'ATIVO']
                info_t = df_turmas[df_turmas['nome_turma'] == t_alvo].iloc[0]
                pres_t = df_pres[df_pres['id_turma'] == t_alvo] if not df_pres.empty else pd.DataFrame()
                
                # --- MÉTRICAS GERAIS ---
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
                m6.metric("Itinerário", f"{min(progresso, 100)}%")

                # --- ALERTAS DA TURMA ---
                with st.expander("🚨 Alertas de Enturmação, Sacramentos e Saúde", expanded=False):
                    c_al1, c_al2, c_al3 = st.columns(3)
                    
                    # Idade
                    etapa_base = str(info_t['etapa']).upper()
                    faixas = {"PRÉ": (4, 6), "PRIMEIRA ETAPA": (7, 8), "SEGUNDA ETAPA": (9, 10), "TERCEIRA ETAPA": (11, 13), "PERSEVERANÇA": (14, 15), "ADULTOS": (16, 99)}
                    min_ideal, max_ideal = faixas.get(etapa_base, (0, 99))
                    fora_da_faixa = [r['nome_completo'] for _, r in alunos_t.iterrows() if not (min_ideal <= calcular_idade(r['data_nascimento']) <= max_ideal)]
                    if fora_da_faixa: c_al1.warning(f"⚠️ {len(fora_da_faixa)} fora da faixa etária.")
                    else: c_al1.success("✅ Idades adequadas.")
                    
                    # Sacramentos
                    sem_batismo = len(alunos_t[alunos_t['batizado_sn'] != 'SIM'])
                    if sem_batismo > 0: c_al2.error(f"🚨 {sem_batismo} sem Batismo.")
                    else: c_al2.success("✅ Todos batizados.")
                    
                    # Saúde
                    tgo_count = len(alunos_t[alunos_t['tgo_sn'] != 'NÃO'])
                    med_count = len(alunos_t[alunos_t['toma_medicamento_sn'] != 'NÃO'])
                    if tgo_count > 0 or med_count > 0: c_al3.info(f"💙 {tgo_count} TGO | 💊 {med_count} Med.")
                    else: c_al3.success("✅ Sem alertas de saúde.")

                st.divider()
                
                # --- SUB-ABAS DE GESTÃO DA TURMA ---
                sub_edit, sub_plan, sub_hist, sub_doc = st.tabs([
                    "✏️ Editar Turma", "📅 Planejar Temas", "📜 Diário e Faltas", "📄 Documentos e Auditoria"
                ])
                
                with sub_edit:
                    st.markdown("#### ✏️ Detalhes e Edição da Turma")
                    nome_turma_original = str(info_t['nome_turma'])
                    with st.form(f"form_edit_turma_{info_t['id_turma']}"):
                        c1, c2 = st.columns(2)
                        en = c1.text_input("Nome da Turma", value=info_t['nome_turma']).upper()
                        ea = c2.number_input("Ano Letivo", value=int(info_t['ano']))
                        ee = st.selectbox("Etapa Base", etapas_lista, index=etapas_lista.index(info_t['etapa']) if info_t['etapa'] in etapas_lista else 0)
                        
                        c3, c4 = st.columns(2)
                        pe = c3.text_input("Previsão Eucaristia", value=info_t.get('previsao_eucaristia', ''))
                        pc = c4.text_input("Previsão Crisma", value=info_t.get('previsao_crisma', ''))
                        
                        dias_atuais =[x.strip() for x in str(info_t.get('dias_semana', '')).split(',') if x.strip()]
                        ed_dias = st.multiselect("Dias de Encontro", dias_opcoes, default=[d for d in dias_atuais if d in dias_opcoes])
                        
                        c5, c6 = st.columns(2)
                        opcoes_turno = ["MANHÃ", "TARDE", "NOITE"]
                        turno_atual = str(info_t.get('turno', 'MANHÃ')).upper()
                        et = c5.selectbox("Turno", opcoes_turno, index=opcoes_turno.index(turno_atual) if turno_atual in opcoes_turno else 0)
                        el = c6.text_input("Local / Sala", value=info_t.get('local', 'SALA')).upper()
                        
                        lista_todos_cats = equipe_tecnica['nome'].tolist() if not equipe_tecnica.empty else[]
                        cats_atuais_lista =[c.strip() for c in str(info_t.get('catequista_responsavel', '')).split(',') if c.strip()]
                        ed_cats = st.multiselect("Catequistas Responsáveis", options=lista_todos_cats, default=[c for c in cats_atuais_lista if c in lista_todos_cats])
                        
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES E SINCRONIZAR", use_container_width=True):
                            with st.spinner("Processando atualizações..."):
                                lista_up = [str(info_t['id_turma']), en, ee, int(ea), ", ".join(ed_cats), ", ".join(ed_dias), pe, pc, et, el]
                                if atualizar_turma(info_t['id_turma'], lista_up):
                                    if en != nome_turma_original: sincronizar_renomeacao_turma_geral(nome_turma_original, en)
                                    sincronizar_logistica_turma_nos_catequizandos(en, et, el)
                                    
                                    planilha = conectar_google_sheets()
                                    if planilha:
                                        aba_u = planilha.worksheet("usuarios")
                                        for _, cat_row in equipe_tecnica.iterrows():
                                            c_nome = cat_row['nome']
                                            cel_u = aba_u.find(c_nome, in_column=1)
                                            if cel_u:
                                                v_atual = aba_u.cell(cel_u.row, 5).value or ""
                                                v_list =[x.strip() for x in v_atual.split(',') if x.strip()]
                                                if c_nome in ed_cats and en not in v_list:
                                                    v_list.append(en); aba_u.update_cell(cel_u.row, 5, ", ".join(v_list))
                                                elif c_nome not in ed_cats and en in v_list:
                                                    v_list.remove(en); aba_u.update_cell(cel_u.row, 5, ", ".join(v_list))
                                    st.success(f"✅ Turma '{en}' atualizada!"); time.sleep(1); st.rerun()

                    with st.expander("🗑️ ZONA DE PERIGO: Excluir Turma"):
                        st.error(f"Atenção: Ao excluir a turma '{t_alvo}', todos os catequizandos nela matriculados serão movidos para a Fila de Espera.")
                        confirmar_exclusao = st.checkbox(f"Confirmo a exclusão definitiva da turma {t_alvo}", key=f"chk_del_{info_t['id_turma']}")
                        if st.button("🗑️ EXCLUIR TURMA AGORA", type="primary", disabled=not confirmar_exclusao, key=f"btn_del_{info_t['id_turma']}", use_container_width=True):
                            with st.spinner("Movendo catequizandos e limpando histórico..."):
                                if not alunos_t_todos.empty:
                                    ids_para_mover = alunos_t_todos['id_catequizando'].tolist()
                                    mover_catequizandos_em_massa(ids_para_mover, "CATEQUIZANDOS SEM TURMA")
                                
                                planilha = conectar_google_sheets()
                                if planilha:
                                    aba_u = planilha.worksheet("usuarios")
                                    for _, cat_row in equipe_tecnica.iterrows():
                                        v_atual = str(cat_row.get('turma_vinculada', ''))
                                        if t_alvo in v_atual:
                                            v_list =[x.strip() for x in v_atual.split(',') if x.strip()]
                                            if t_alvo in v_list:
                                                v_list.remove(t_alvo)
                                                celula_u = aba_u.find(cat_row['nome'], in_column=1)
                                                if celula_u: aba_u.update_cell(celula_u.row, 5, ", ".join(v_list))
                                
                                if excluir_turma(info_t['id_turma']):
                                    from database import limpar_lixo_turma_excluida
                                    limpar_lixo_turma_excluida(t_alvo)
                                    st.success(f"Turma excluída! Catequizandos movidos para a Fila de Espera."); st.cache_data.clear(); time.sleep(2); st.rerun()

                with sub_plan:
                    st.markdown("#### 📅 Adicionar novo tema ao Cronograma")
                    with st.form(f"form_plan_rx_{t_alvo}", clear_on_submit=True):
                        novo_tema_rx = st.text_input("Título do Tema").upper()
                        desc_tema_rx = st.text_area("Objetivo / Descrição Base (Opcional)", height=100)
                        if st.form_submit_button("📌 ADICIONAR AO CRONOGRAMA"):
                            if novo_tema_rx:
                                if salvar_tema_cronograma([f"PLAN-{int(time.time())}", t_alvo, novo_tema_rx, desc_tema_rx, "PENDENTE"]):
                                    st.success("Tema planejado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                    
                    st.markdown("---")
                    st.markdown("#### 📋 Temas Pendentes na Fila")
                    cron_t_rx = df_cron_local[(df_cron_local['etapa'].astype(str).str.strip().str.upper() == t_alvo.strip().upper())]
                    col_status_rx = 'status' if 'status' in cron_t_rx.columns else ('col_4' if 'col_4' in cron_t_rx.columns else None)
                    if col_status_rx and not cron_t_rx.empty:
                        pendentes_rx = cron_t_rx[cron_t_rx[col_status_rx].astype(str).str.strip().str.upper() != 'REALIZADO']
                        if not pendentes_rx.empty:
                            st.dataframe(pendentes_rx[['titulo_tema', 'descricao_base']], use_container_width=True, hide_index=True)
                        else: st.info("Nenhum tema pendente no momento.")
                    else: st.info("Nenhum tema cadastrado.")

                with sub_hist:
                    st.markdown("#### 📜 Histórico, Edição e Faltas (Diário)")
                    enc_t_rx = df_enc_local[df_enc_local['turma'].astype(str).str.strip().str.upper() == t_alvo.strip().upper()].copy()
                    if not enc_t_rx.empty:
                        enc_t_rx['data_dt'] = pd.to_datetime(enc_t_rx['data'], errors='coerce', dayfirst=True)
                        enc_t_rx = enc_t_rx.sort_values(by='data_dt', ascending=False)
                        
                        for idx, row in enc_t_rx.iterrows():
                            data_e = str(row['data'])
                            tema_e = row.get('tema', 'Sem tema')
                            cat_e = row.get('catequista', 'Não informado')
                            obs_e = row.get('observacoes', '')
                            
                            pres_e = df_pres[(df_pres['id_turma'].astype(str).str.strip().str.upper() == t_alvo.strip().upper()) & (df_pres['data_encontro'].astype(str) == data_e)]
                            qtd_pres = len(pres_e[pres_e['status'] == 'PRESENTE'])
                            qtd_aus = len(pres_e[pres_e['status'] == 'AUSENTE'])
                            faltosos = pres_e[pres_e['status'] == 'AUSENTE']['nome_catequizando'].tolist()
                            
                            with st.expander(f"📅 {formatar_data_br(data_e)} - {tema_e} | 👤 Resp: {cat_e}"):
                                c_met1, c_met2 = st.columns(2)
                                c_met1.metric("✅ Presentes", qtd_pres)
                                c_met2.metric("❌ Ausentes", qtd_aus)
                                
                                if faltosos: st.error(f"**Faltosos neste dia:** {', '.join(faltosos)}")
                                else: st.success("**Nenhuma falta registrada neste dia!**")
                                
                                st.markdown("---")
                                st.markdown("**✏️ Editar Registro do Encontro**")
                                with st.form(f"form_edit_rx_{data_e}_{idx}"):
                                    ed_tema_rx = st.text_input("Tema Ministrado:", value=tema_e).upper()
                                    ed_obs_rx = st.text_area("Observações / Relato:", value=obs_e, height=100)
                                    
                                    c_btn1, c_btn2 = st.columns([3, 1])
                                    btn_salvar = c_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)
                                    btn_excluir = c_btn2.form_submit_button("🗑️ EXCLUIR ENCONTRO", use_container_width=True)
                                    
                                    st.markdown("---")
                                    confirma_del = st.checkbox("⚠️ Confirmo a exclusão deste encontro e de todas as presenças do dia", key=f"chk_del_rx_{data_e}_{idx}")
                                    
                                    if btn_salvar:
                                        with st.spinner("Atualizando diário..."):
                                            if atualizar_encontro_global(t_alvo, data_e, ed_tema_rx, ed_obs_rx):
                                                st.success("Atualizado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                                    if btn_excluir:
                                        if confirma_del:
                                            with st.spinner("Excluindo encontro e revertendo cronograma..."):
                                                if excluir_encontro_cascata(t_alvo, data_e, tema_e):
                                                    st.success("Encontro excluído!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                                        else: st.error("⚠️ Marque a caixa de confirmação para excluir.")
                    else:
                        st.info("Nenhum encontro registrado para esta turma.")

                with sub_doc:
                    st.markdown("#### 📄 Documentação e Auditoria")
                    col_doc1, col_doc2 = st.columns(2)
                    with col_doc1:
                        if st.button(f"✨ GERAR AUDITORIA PASTORAL: {t_alvo}", use_container_width=True, key="btn_auditoria_turma"):
                            with st.spinner("Analisando prontidão da turma..."):
                                sem_batismo = len(alunos_t[alunos_t['batizado_sn'] != 'SIM'])
                                batizados = len(alunos_t) - sem_batismo
                                tgo_c = len(alunos_t[alunos_t['tgo_sn'] != 'NÃO'])
                                saude_c = len(alunos_t[alunos_t['toma_medicamento_sn'] != 'NÃO'])
                                
                                lista_geral =[]
                                for _, r in alunos_t.iterrows():
                                    f = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')]) if not pres_t.empty else 0
                                    has_euc = "SIM" if "EUCARISTIA" in str(r['sacramentos_ja_feitos']).upper() else "NÃO"
                                    lista_geral.append({'nome': r['nome_completo'], 'faltas': f, 'batismo': r['batizado_sn'], 'eucaristia': has_euc, 'status': r['status']})

                                resumo_ia = f"Turma {t_alvo}: {len(alunos_t)} catequizandos. Freq: {freq_global}%. Pais: {perc_pais}%. Batizados: {batizados}. Pendentes Batismo: {sem_batismo}. TGO: {tgo_c}."
                                parecer_ia = analisar_turma_local(t_alvo, resumo_ia)

                                st.session_state[f"pdf_auditoria_{t_alvo}"] = gerar_relatorio_local_turma_pdf(
                                    t_alvo, 
                                    {'qtd_catequistas': qtd_cats_real, 'qtd_cat': len(alunos_t), 'freq_global': freq_global, 'idade_media': idade_media_val, 'engaj_pais': perc_pais, 'progresso_it': progresso, 'batizados': batizados, 'pend_batismo': sem_batismo, 'tgo': tgo_c, 'saude': saude_c}, 
                                    {'geral': lista_geral}, parecer_ia
                                )
                        if f"pdf_auditoria_{t_alvo}" in st.session_state:
                            st.download_button(label=f"📥 BAIXAR AUDITORIA: {t_alvo}", data=st.session_state[f"pdf_auditoria_{t_alvo}"], file_name=f"Auditoria_{t_alvo}.pdf", mime="application/pdf", use_container_width=True)
                    
                    with col_doc2:
                        if st.button(f"📄 GERAR FICHAS DA TURMA (LOTE)", use_container_width=True, key="btn_fichas_turma"):
                            with st.spinner("Gerando fichas individuais..."):
                                st.session_state[f"pdf_fichas_{t_alvo}"] = gerar_fichas_turma_completa(t_alvo, alunos_t)
                        if f"pdf_fichas_{t_alvo}" in st.session_state:
                            st.download_button("📥 BAIXAR FICHAS (LOTE)", st.session_state[f"pdf_fichas_{t_alvo}"], f"Fichas_{t_alvo}.pdf", use_container_width=True)
        else:
            st.info("Nenhuma turma cadastrada.")

    # ==========================================================================
    # HUB 3: LOGÍSTICA E ALOCAÇÃO (RH DA CATEQUESE)
    # ==========================================================================
    with tab_logistica:
        st.subheader("🔀 Logística, Fila de Espera e Alocação")
        
        col_fila, col_nova = st.columns([2, 1])
        
        with col_fila:
            st.markdown("#### ⏳ Fila de Espera")
            if df_cat.empty:
                st.info("Nenhum catequizando cadastrado no sistema.")
            else:
                turmas_reais = df_turmas['nome_turma'].unique().tolist() if not df_turmas.empty else []
                fila_espera = df_cat[(df_cat['etapa'] == "CATEQUIZANDOS SEM TURMA") | (~df_cat['etapa'].isin(turmas_reais))]
                
                if not fila_espera.empty:
                    st.dataframe(fila_espera[['nome_completo', 'etapa', 'contato_principal']], use_container_width=True, hide_index=True)
                else:
                    st.success("Todos os catequizandos estão alocados em turmas válidas! 🎉")

        with col_nova:
            with st.expander("➕ Criar Nova Turma", expanded=False):
                with st.form("form_criar_turma"):
                    n_t = st.text_input("Nome da Turma", help="Ex: PRÉ ETAPA 2026").upper()
                    e_t = st.selectbox("Etapa Base", etapas_lista)
                    ano = st.number_input("Ano Letivo", value=2026)
                    n_dias = st.multiselect("Dias de Encontro", dias_opcoes)
                    turno_t = st.selectbox("Turno do Encontro",["MANHÃ", "TARDE", "NOITE"])
                    local_t = st.text_input("Local/Sala", value="SALA").upper()
                    cats_selecionados = st.multiselect("Catequistas Responsáveis", equipe_tecnica['nome'].tolist() if not equipe_tecnica.empty else[])
                    
                    if st.form_submit_button("🚀 SALVAR NOVA TURMA", use_container_width=True):
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
                                    st.success(f"✅ Turma '{n_t}' criada!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"Erro ao salvar: {e}")
                        else: st.warning("⚠️ Nome e Dias são obrigatórios.")

        st.divider()
        st.markdown("#### 🚀 Movimentação em Massa")
        if not df_turmas.empty and not df_cat.empty:
            c1, c2 = st.columns(2)
            opcoes_origem = ["CATEQUIZANDOS SEM TURMA"] + sorted(df_cat['etapa'].unique().tolist())
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
                            if st.checkbox(f"{al['nome_completo']} ({idade_atual} anos)", key=f"mov_al_{al['id_catequizando']}"):
                                lista_ids_selecionados.append(al['id_catequizando'])
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_mov1, col_mov2 = st.columns(2)
                    with col_mov1:
                        if st.button(f"🚀 MOVER {len(lista_ids_selecionados)} PARA {t_destino}", key="btn_exec_mov", use_container_width=True):
                            if t_destino and t_origem != t_destino and lista_ids_selecionados:
                                if mover_catequizandos_em_massa(lista_ids_selecionados, t_destino):
                                    st.success(f"✅ Sucesso! {len(lista_ids_selecionados)} movidos para {t_destino}."); st.cache_data.clear(); time.sleep(2); st.rerun()
                            else: st.error("Selecione um destino válido e ao menos um catequizando.")
                    
                    with col_mov2:
                        if st.button(f"🎓 CONCLUIR CAMINHADA DE {len(lista_ids_selecionados)} CATEQUIZANDOS", key="btn_exec_concluir", type="primary", use_container_width=True, help="Marca o status como CONCLUÍDO (Egresso) após a Crisma."):
                            if lista_ids_selecionados:
                                with st.spinner("Registrando conclusão e formatura..."):
                                    for cid in lista_ids_selecionados:
                                        cat_row = df_cat[df_cat['id_catequizando'] == cid].iloc[0]
                                        lista_up = cat_row.tolist()
                                        while len(lista_up) < 30: lista_up.append("N/A")
                                        lista_up[12] = "CONCLUÍDO"
                                        atualizar_catequizando(cid, lista_up)
                                    st.success(f"✅ Glória a Deus! {len(lista_ids_selecionados)} catequizandos formados com sucesso!"); st.balloons(); st.cache_data.clear(); time.sleep(2); st.rerun()
                            else: st.error("Selecione ao menos um catequizando.")
                else:
                    st.info("Não há catequizandos ativos nesta turma de origem.")




# ==============================================================================
# PÁGINA: 🕊️ GESTÃO DE SACRAMENTOS (CENTRAL DE INICIAÇÃO CRISTÃ 3.0)
# ==============================================================================
elif menu == "🕊️ Gestão de Sacramentos":
    st.title("🕊️ Central de Iniciação Cristã e Sacramentos")
    
    tab_auditoria, tab_mutirao, tab_cartorio = st.tabs([
        "📊 Auditoria Canônica (Radar)", "⛪ Celebrações e Mutirões", "👤 Cartório e Acervo Individual"
    ])
    
    # ==========================================================================
    # HUB 1: AUDITORIA CANÔNICA INTELIGENTE
    # ==========================================================================
    with tab_auditoria:
        st.subheader("📊 Censo Sacramental e Prontidão")
        st.markdown("O sistema audita automaticamente as pendências respeitando a idade e a etapa de cada catequizando.")
        
        df_recebidos = ler_aba("sacramentos_recebidos")
        bat_ano, euc_ano, cri_ano = 0, 0, 0
        ano_atual = date.today().year
        
        if not df_recebidos.empty:
            try:
                df_recebidos['data_dt'] = pd.to_datetime(df_recebidos['data'], errors='coerce', dayfirst=True)
                df_ano = df_recebidos[df_recebidos['data_dt'].dt.year == ano_atual]
                bat_ano = len(df_ano[df_ano['tipo'].str.upper().str.contains('BATISMO')])
                euc_ano = len(df_ano[df_ano['tipo'].str.upper().str.contains('EUCARISTIA')])
                cri_ano = len(df_ano[df_ano['tipo'].str.upper().str.contains('CRISMA')])
            except: pass

        st.markdown(f"""
            <div style='background-color:#f8f9f0; padding:20px; border-radius:10px; border:1px solid #417b99; text-align:center; margin-bottom:20px;'>
                <h3 style='margin:0; color:#417b99;'>🕊️ Frutos da Evangelização em {ano_atual}</h3>
                <p style='font-size:14px; color:#666; margin-bottom:15px;'>Sacramentos celebrados e registrados este ano na paróquia:</p>
                <div style='display: flex; justify-content: space-around;'>
                    <div><b style='font-size:24px; color:#e03d11;'>{bat_ano}</b><br><small>Batismos</small></div>
                    <div><b style='font-size:24px; color:#e03d11;'>{euc_ano}</b><br><small>Eucaristias</small></div>
                    <div><b style='font-size:24px; color:#e03d11;'>{cri_ano}</b><br><small>Crismas</small></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.subheader("🏫 Radar de Pendências por Turma")
        
        if not df_turmas.empty:
            for _, t in df_turmas.iterrows():
                nome_t = str(t['nome_turma']).strip().upper()
                etapa_base = str(t['etapa']).strip().upper()
                alunos_t = df_cat[(df_cat['etapa'].str.strip().str.upper() == nome_t) & (df_cat['status'] == 'ATIVO')] if not df_cat.empty else pd.DataFrame()
                
                if not alunos_t.empty:
                    # INTELIGÊNCIA CANÔNICA: O que cobrar de cada etapa?
                    audita_batismo = True
                    audita_eucaristia = any(x in etapa_base for x in["3ª", "TERCEIRA", "ADULTO", "PERSEVERANÇA", "CRISMA"])
                    # 3ª Etapa e Batismo/Eucaristia Adultos NÃO cobram Crisma
                    audita_crisma = any(x in etapa_base for x in ["CRISMA", "PERSEVERANÇA"]) 
                    
                    pend_bat = alunos_t[alunos_t['batizado_sn'] != "SIM"] if audita_batismo else pd.DataFrame()
                    pend_euc = alunos_t[~alunos_t['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False, case=False)] if audita_eucaristia else pd.DataFrame()
                    pend_cri = alunos_t[~alunos_t['sacramentos_ja_feitos'].str.contains("CRISMA", na=False, case=False)] if audita_crisma else pd.DataFrame()
                    
                    tem_pendencia = not pend_bat.empty or not pend_euc.empty or not pend_cri.empty
                    
                    if tem_pendencia:
                        with st.expander(f"🚨 {nome_t} ({etapa_base}) - Pendências Identificadas"):
                            cols_p = st.columns(3)
                            
                            with cols_p[0]:
                                st.markdown("**🕊️ Falta Batismo**")
                                if not pend_bat.empty:
                                    for n in pend_bat['nome_completo'].tolist(): st.markdown(f"<span style='color:#e03d11; font-size:13px;'>❌ {n}</span>", unsafe_allow_html=True)
                                else: st.markdown("<span style='color:green; font-size:13px;'>✅ Tudo OK</span>", unsafe_allow_html=True)
                            
                            with cols_p[1]:
                                if audita_eucaristia:
                                    st.markdown("**🍞 Falta Eucaristia**")
                                    if not pend_euc.empty:
                                        for n in pend_euc['nome_completo'].tolist(): st.markdown(f"<span style='color:#e03d11; font-size:13px;'>❌ {n}</span>", unsafe_allow_html=True)
                                    else: st.markdown("<span style='color:green; font-size:13px;'>✅ Tudo OK</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown("**🍞 Eucaristia**")
                                    st.caption("Não exigido nesta etapa.")
                                        
                            with cols_p[2]:
                                if audita_crisma:
                                    st.markdown("**🔥 Falta Crisma**")
                                    if not pend_cri.empty:
                                        for n in pend_cri['nome_completo'].tolist(): st.markdown(f"<span style='color:#e03d11; font-size:13px;'>❌ {n}</span>", unsafe_allow_html=True)
                                    else: st.markdown("<span style='color:green; font-size:13px;'>✅ Tudo OK</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown("**🔥 Crisma**")
                                    st.caption("Não exigido nesta etapa.")
                    else:
                        st.markdown(f"<div style='padding:8px; background-color:#e8f5e9; border-radius:5px; margin-bottom:5px;'><small style='color:#2e7d32;'>✅ <b>{nome_t}</b>: Todos os sacramentos exigidos para a etapa estão em dia.</small></div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("🏛️ Relatório Oficial de Auditoria")
        if "pdf_sac_tecnico" in st.session_state:
            st.success("✅ Auditoria Diocesana pronta para download!")
            st.download_button("📥 BAIXAR AUDITORIA SACRAMENTAL (PDF)", st.session_state.pdf_sac_tecnico, f"Auditoria_Sacramental_{ano_atual}.pdf", "application/pdf", use_container_width=True)
            if st.button("🔄 Gerar Novo Relatório (Atualizar)"):
                del st.session_state.pdf_sac_tecnico
                st.rerun()
        else:
            if st.button("✨ GERAR AUDITORIA PASTORAL COMPLETA", key="btn_disparar_ia_sac", use_container_width=True):
                with st.spinner("O Auditor IA está analisando impedimentos..."):
                    analise_detalhada_ia =[]
                    for _, t in df_turmas.iterrows():
                        nome_t = str(t['nome_turma']).strip().upper()
                        alunos_t = df_cat[(df_cat['etapa'] == nome_t) & (df_cat['status'] == 'ATIVO')]
                        if not alunos_t.empty:
                            pend_bat = len(alunos_t[alunos_t['batizado_sn'] != "SIM"])
                            imp_count = len(alunos_t[(("3ª" in str(t['etapa'])) | ("ADULTO" in str(t['etapa']).upper())) & (alunos_t['batizado_sn'] != "SIM")])
                            analise_detalhada_ia.append({"turma": nome_t, "etapa": t['etapa'], "batizados": len(alunos_t) - pend_bat, "pendentes": pend_bat, "impedimentos_civel": imp_count})
                    
                    impedimentos_detalhados =[]
                    for _, cat in df_cat[df_cat['status'] == 'ATIVO'].iterrows():
                        if ("3ª" in str(cat['etapa']) or "ADULTO" in str(cat['etapa']).upper()) and cat['batizado_sn'] != "SIM":
                            impedimentos_detalhados.append({"nome": cat['nome_completo'], "turma": cat['etapa'], "motivo": "Falta Batismo (Impedimento de Iniciação)"})
                    
                    resumo_ia = str({"turmas": analise_detalhada_ia, "impedimentos": impedimentos_detalhados})
                    analise_ia_sac = gerar_relatorio_sacramentos_ia(resumo_ia)
                    st.session_state.pdf_sac_tecnico = gerar_relatorio_sacramentos_tecnico_pdf(analise_detalhada_ia, impedimentos_detalhados, analise_ia_sac)
                    st.rerun()

    # ==========================================================================
    # HUB 2: CELEBRAÇÕES E MUTIRÕES (LINHA DE MONTAGEM)
    # ==========================================================================
    with tab_mutirao:
        st.subheader("⛪ Registrar Celebração em Lote")
        st.markdown("Selecione as turmas que participaram da Missa para registrar o sacramento e aplicar as automações de saída.")
        
        turmas_s = st.multiselect("1. Selecione as Turmas:", df_turmas['nome_turma'].tolist() if not df_turmas.empty else[])
        
        if turmas_s:
            with st.form("form_sac_lote"):
                c_sac1, c_sac2 = st.columns(2)
                tipo_s = c_sac1.selectbox("2. Sacramento Recebido", ["BATISMO", "EUCARISTIA", "CRISMA"])
                data_s = c_sac2.date_input("3. Data da Celebração", date.today(), format="DD/MM/YYYY")
                
                st.markdown("---")
                st.markdown("**📍 Local da Celebração**")
                local_celebra = st.radio("Onde ocorreu o sacramento?",["Nesta Paróquia (Fátima)", "Em Outra Paróquia (Com autorização)"], horizontal=True)
                nome_outra_paroquia = ""
                if local_celebra == "Em Outra Paróquia (Com autorização)":
                    nome_outra_paroquia = st.text_input("Qual o nome da Paróquia/Cidade?").upper()
                
                st.markdown("---")
                st.markdown("**⚙️ Automações de Saída (Opcional)**")
                mover_perseveranca = False
                concluir_caminhada = False
                
                if tipo_s == "EUCARISTIA":
                    mover_perseveranca = st.checkbox("Mover catequizandos marcados para a Fila de Espera da Perseverança?", help="Eles sairão da turma atual e aguardarão alocação na Perseverança.")
                elif tipo_s == "CRISMA":
                    concluir_caminhada = st.checkbox("Concluir caminhada dos catequizandos marcados?", help="O status deles mudará para CONCLUÍDO (Egresso) e eles sairão das listas de cobrança.")
                
                st.markdown("---")
                st.markdown("**👥 Selecione os Catequizandos que estavam presentes na Missa:**")
                alunos_f = df_cat[(df_cat['etapa'].isin(turmas_s)) & (df_cat['status'] == 'ATIVO')].sort_values('nome_completo')
                sel_ids =[]
                
                if not alunos_f.empty:
                    cols = st.columns(2)
                    for i, (_, r) in enumerate(alunos_f.iterrows()):
                        with cols[i % 2]:
                            if st.checkbox(f"{r['nome_completo']}", key=f"chk_sac_{r['id_catequizando']}"): 
                                sel_ids.append(r)
                else:
                    st.info("Nenhum catequizando ativo encontrado nestas turmas.")
                
                if st.form_submit_button("💾 REGISTRAR SACRAMENTO E APLICAR AUTOMAÇÕES", type="primary"):
                    if not sel_ids:
                        st.error("Selecione ao menos um catequizando.")
                    elif local_celebra == "Em Outra Paróquia (Com autorização)" and not nome_outra_paroquia:
                        st.error("Informe o nome da outra paróquia.")
                    else:
                        with st.spinner("Registrando sacramentos e atualizando históricos..."):
                            id_ev = f"SAC-{int(time.time())}"
                            lista_p = [[id_ev, r['id_catequizando'], r['nome_completo'], tipo_s, data_s.strftime('%d/%m/%Y')] for r in sel_ids]
                            
                            local_str = "Paróquia de Fátima" if local_celebra == "Nesta Paróquia (Fátima)" else f"Outra Paróquia: {nome_outra_paroquia}"
                            nome_responsavel_registro = f"{st.session_state.usuario['nome']} ({local_str})"
                            
                            if registrar_evento_sacramento_completo([id_ev, tipo_s, data_s.strftime('%d/%m/%Y'), ", ".join(turmas_s), nome_responsavel_registro], lista_p, tipo_s):
                                # Aplica as automações de saída
                                for r in sel_ids:
                                    cid = r['id_catequizando']
                                    cat_row = df_cat[df_cat['id_catequizando'] == cid].iloc[0]
                                    lista_up = cat_row.tolist()
                                    while len(lista_up) < 30: lista_up.append("N/A")
                                    
                                    mudou = False
                                    if tipo_s == "EUCARISTIA" and mover_perseveranca:
                                        lista_up[1] = "CATEQUIZANDOS SEM TURMA" # Move para a fila
                                        mudou = True
                                    elif tipo_s == "CRISMA" and concluir_caminhada:
                                        lista_up[12] = "CONCLUÍDO" # Muda o status
                                        mudou = True
                                        
                                    if mudou:
                                        atualizar_catequizando(cid, lista_up)
                                        
                                st.success(f"✅ Glória a Deus! {len(sel_ids)} sacramentos registrados com sucesso!"); st.balloons(); st.cache_data.clear(); time.sleep(2); st.rerun()

    # ==========================================================================
    # HUB 3: CARTÓRIO E ACERVO INDIVIDUAL
    # ==========================================================================
    with tab_cartorio:
        st.subheader("👤 Cartório: Registro Individual e Histórico")
        
        col_busca, col_hist = st.columns([1, 1])
        
        with col_busca:
            st.markdown("#### 🔍 Lançamento Avulso")
            st.markdown("Use para registrar um sacramento feito em outra cidade ou corrigir o acervo de um catequizando específico.")
            nome_busca = st.text_input("Digite o nome do catequizando:").upper()
            
            if nome_busca:
                sugestoes = df_cat[df_cat['nome_completo'].str.contains(nome_busca)] if not df_cat.empty else pd.DataFrame()
                if not sugestoes.empty:
                    escolhido = st.selectbox("Selecione o catequizando:", sugestoes['nome_completo'].tolist())
                    dados_c = sugestoes[sugestoes['nome_completo'] == escolhido].iloc[0]
                    
                    st.info(f"**Sacramentos Atuais:** {dados_c.get('sacramentos_ja_feitos', 'Nenhum')}")
                    
                    with st.form("form_sac_individual"):
                        c1, c2 = st.columns(2)
                        tipo_s_ind = c1.selectbox("Sacramento", ["BATISMO", "EUCARISTIA", "CRISMA"])
                        data_s_ind = c2.date_input("Data", date.today(), format="DD/MM/YYYY")
                        local_ind = st.text_input("Local (Ex: Paróquia São José - Ilhéus)").upper()
                        
                        if st.form_submit_button("💾 SALVAR REGISTRO AVULSO", use_container_width=True):
                            id_ev = f"IND-{int(time.time())}"
                            local_final = f"Avulso: {local_ind}" if local_ind else "Avulso"
                            if registrar_evento_sacramento_completo([id_ev, tipo_s_ind, data_s_ind.strftime('%d/%m/%Y'), dados_c['etapa'], f"{st.session_state.usuario['nome']} ({local_final})"], [[id_ev, dados_c['id_catequizando'], escolhido, tipo_s_ind, data_s_ind.strftime('%d/%m/%Y')]], tipo_s_ind):
                                st.success("Registrado no acervo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                else:
                    st.warning("Catequizando não encontrado.")

        with col_hist:
            st.markdown("#### 📜 Histórico de Eventos")
            df_eventos = ler_aba("sacramentos_eventos")
            if not df_eventos.empty:
                df_eventos['data_dt'] = pd.to_datetime(df_eventos['data'], errors='coerce', dayfirst=True)
                df_eventos = df_eventos.sort_values(by='data_dt', ascending=False)
                st.dataframe(df_eventos[['tipo', 'data', 'turmas', 'catequista']], use_container_width=True, hide_index=True)
                
                with st.expander("✏️ Gerenciar Evento (Corrigir, Adicionar Alunos ou Excluir)"):
                    id_para_editar = st.selectbox("Selecione o ID do Evento:", [""] + df_eventos['id_evento'].tolist())
                    if id_para_editar:
                        dados_atuais = df_eventos[df_eventos['id_evento'] == id_para_editar].iloc[0]
                        tipo_atual = dados_atuais['tipo']
                        turmas_str = dados_atuais['turmas']
                        
                        df_recebidos = ler_aba("sacramentos_recebidos")
                        participantes_atuais = df_recebidos[df_recebidos.iloc[:, 0] == id_para_editar].iloc[:, 1].tolist() if not df_recebidos.empty else []
                        
                        turmas_lista =[t.strip() for t in turmas_str.split(",") if t.strip()]
                        alunos_elegiveis = df_cat[(df_cat['etapa'].isin(turmas_lista))]
                        
                        with st.form("form_edit_sac_evento"):
                            st.markdown(f"**Evento:** {tipo_atual} | **Turmas:** {turmas_str}")
                            ed_data = st.date_input("Data Correta", value=pd.to_datetime(dados_atuais['data']).date(), format="DD/MM/YYYY")
                            
                            st.markdown("---")
                            st.markdown("**👥 Gerenciar Participantes:**")
                            opcoes_nomes = alunos_elegiveis['nome_completo'].tolist() if not alunos_elegiveis.empty else []
                            nomes_atuais = list(set(df_cat[df_cat['id_catequizando'].isin(participantes_atuais)]['nome_completo'].tolist())) if participantes_atuais else[]
                            
                            # Para eventos avulsos, garante que o nome exista na lista
                            for n in nomes_atuais:
                                if n not in opcoes_nomes: opcoes_nomes.append(n)
                                
                            ed_participantes = st.multiselect("Alunos Presentes no Sacramento:", options=opcoes_nomes, default=[n for n in nomes_atuais if n in opcoes_nomes])
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            c_btn1, c_btn2 = st.columns([3, 1])
                            btn_salvar = c_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)
                            btn_excluir = c_btn2.form_submit_button("🗑️ EXCLUIR EVENTO", use_container_width=True)
                            
                            st.markdown("---")
                            confirma_del = st.checkbox("⚠️ Confirmo a exclusão definitiva deste evento e de todos os seus registros", key=f"chk_del_sac_{id_para_editar}")
                            
                            if btn_salvar:
                                with st.spinner("Atualizando registros no cartório e nas fichas..."):
                                    novos_p_lista =[]
                                    for nome in ed_participantes:
                                        id_c = df_cat[df_cat['nome_completo'] == nome].iloc[0]['id_catequizando']
                                        novos_p_lista.append([id_para_editar, id_c, nome, tipo_atual, ed_data.strftime('%d/%m/%Y')])
                                    
                                    novos_dados_ev =[id_para_editar, tipo_atual, ed_data.strftime('%d/%m/%Y'), turmas_str, dados_atuais['catequista']]
                                    
                                    if gerenciar_edicao_evento_sacramento(id_para_editar, novos_dados_ev, novos_p_lista, tipo_atual):
                                        st.success("✅ Evento atualizado com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                                        
                            if btn_excluir:
                                if confirma_del:
                                    with st.spinner("Excluindo evento e revertendo selos sacramentais..."):
                                        if excluir_evento_sacramento_cascata(id_para_editar, tipo_atual):
                                            st.success("✅ Evento excluído e revertido!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                                else:
                                    st.error("⚠️ Marque a caixa de confirmação para excluir.")
            else:
                st.info("Nenhum evento registrado no histórico.")



# ==============================================================================
# PÁGINA: ✅ CHAMADA INTELIGENTE (MOBILE-FIRST)
# ==============================================================================
elif menu == "✅ Fazer Chamada":
    st.title("✅ Chamada Inteligente")

    # 1. DEFINIÇÃO DE PERMISSÕES
    vinculo_raw = str(st.session_state.usuario.get('turma_vinculada', '')).strip().upper()
    turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if (eh_gestor or vinculo_raw == "TODAS") else [t.strip() for t in vinculo_raw.split(',') if t.strip()]
    if not turmas_permitidas: st.error("❌ Nenhuma turma vinculada."); st.stop()

    # 2. INTERFACE DE TURMA E DATA
    c1, c2 = st.columns([1, 1])
    turma_sel = c1.selectbox("📋 Selecione a Turma:", turmas_permitidas, key="sel_t_chamada")
    data_enc = c2.date_input("📅 Data do Encontro:", date.today(), format="DD/MM/YYYY")

# 3. MURAL DE ANIVERSARIANTES
    lista_cat = df_cat[(df_cat['etapa'].astype(str).str.strip().str.upper() == turma_sel.strip().upper()) & (df_cat['status'] == 'ATIVO')].sort_values('nome_completo')
    aniversariantes =[]
    for _, row in lista_cat.iterrows():
        status_niver = eh_aniversariante_da_semana(row['data_nascimento'], data_enc)
        if status_niver: aniversariantes.append(f"{status_niver}: {row['nome_completo']}")
    
    if aniversariantes:
        with st.expander("🎂 Aniversariantes do Encontro", expanded=True):
            for niver in aniversariantes: st.info(niver)

    # 4. LÓGICA DE TEMA E ASSISTENTE DE CHAMADA
    df_enc_local = ler_aba("encontros")
    df_cron_local = ler_aba("cronograma")
    
    df_enc_local['data_dt'] = pd.to_datetime(df_enc_local['data'], errors='coerce', dayfirst=True)
    encontro_do_dia = df_enc_local[
        (df_enc_local['turma'].astype(str).str.strip().str.upper() == turma_sel.strip().upper()) & 
        (df_enc_local['data_dt'].dt.date == data_enc)
    ]

    # --- 💌 ASSISTENTE DE CHAMADA (POP-UP INTELIGENTE) ---
    @st.dialog("💡 Guia Rápido da Chamada")
    def exibir_guia_chamada(turma, data_str, lista_niver, ja_existe, chave_sessao):
        st.markdown(f"<h3 style='text-align: center; color: #417b99; margin-top: 0;'>Preparando a chamada...</h3>", unsafe_allow_html=True)
        
        if ja_existe:
            st.error(f"⚠️ **ATENÇÃO:** Já existe uma chamada salva para o dia **{data_str}**. Se você continuar, estará **editando** o registro existente.")
        
        if lista_niver:
            st.info(f"🎂 **Temos aniversariantes!** Não esqueça de parabenizar:\n" + "\n".join([f"• {n}" for n in lista_niver]))
            
        st.markdown("""
        <div style='background-color: #f8f9f0; padding: 15px; border-radius: 10px; border-left: 5px solid #e03d11; margin-bottom: 15px;'>
            <b style='color: #e03d11;'>📌 3 Passos para uma chamada perfeita:</b><br><br>
            1️⃣ <b>Tema:</b> Selecione um tema planejado na listinha abaixo ou digite um novo se for um encontro extra.<br>
            2️⃣ <b>Presenças:</b> Marque quem veio. O sistema salva suas marcações na tela mesmo se a internet oscilar!<br>
            3️⃣ <b>Diário:</b> Após salvar a chamada, vá na aba <i>Diário de Encontros</i> para escrever como foi a dinâmica nas observações.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ Entendido! Iniciar Chamada", use_container_width=True, type="primary"):
            # Agora usamos a chave exata passada de fora
            st.session_state[chave_sessao] = True
            st.rerun()

    # Gatilho do Pop-up (Aparece 1x por Turma + Data)
    key_guia = f"guia_chamada_{turma_sel}_{data_enc.strftime('%Y-%m-%d')}"
    if key_guia not in st.session_state:
        ja_tem_registro = not encontro_do_dia.empty
        # Passamos a key_guia como o 5º argumento para garantir a sincronia perfeita
        exibir_guia_chamada(turma_sel, data_enc.strftime('%d/%m/%Y'), aniversariantes, ja_tem_registro, key_guia)

    if not encontro_do_dia.empty:
        tema_dia = encontro_do_dia.iloc[0]['tema']
        st.success(f"📖 **Tema do Encontro já registrado no Diário:** {tema_dia}")
    else:
        # Busca temas pendentes no cronograma para facilitar a vida do catequista
        lista_temas_pendentes = [""]
        if not df_cron_local.empty:
            col_status = 'status' if 'status' in df_cron_local.columns else ('col_4' if 'col_4' in df_cron_local.columns else None)
            temas_turma = df_cron_local[df_cron_local['etapa'].astype(str).str.strip().str.upper() == turma_sel.strip().upper()]
            if col_status:
                temas_turma = temas_turma[temas_turma[col_status].astype(str).str.strip().str.upper() != 'REALIZADO']
            lista_temas_pendentes += temas_turma['titulo_tema'].tolist()
            
        tema_selecionado = st.selectbox("📌 Selecione um Tema Planejado no Cronograma (Opcional):", lista_temas_pendentes, key="sel_tema_chamada", help="Se escolher um tema aqui, ele preencherá o campo abaixo automaticamente.")
        tema_dia = st.text_input("📖 Digite o Tema do Encontro (Obrigatório):", value=tema_selecionado, key="txt_tema_chamada", help="Você pode digitar um tema livre caso tenha sido um encontro espontâneo.").upper()

    if lista_cat.empty:
        st.warning(f"Nenhum catequizando ativo na turma {turma_sel}.")
    else:
        st.divider()
        if st.button("✅ Marcar Todos como Presentes", use_container_width=True):
            for i, (_, r) in enumerate(lista_cat.iterrows()):
                st.session_state[f"p_{r['id_catequizando']}_{data_enc}_{i}"] = True
            st.rerun()
        
        st.markdown("---")
        
    # --- BUFFER DE CHAMADA (REATIVO) ---
        # Criamos uma chave única que inclui a data para forçar a recarga ao mudar o date_input
        buffer_key = f"chamada_buffer_{turma_sel}_{data_enc}"
        
        if buffer_key not in st.session_state:
            buffer = {}
            # Carrega do banco se já existir
            df_pres['data_dt'] = pd.to_datetime(df_pres['data_encontro'], errors='coerce', dayfirst=True)
            df_pres_existente = df_pres[(df_pres['id_turma'].astype(str).str.strip().str.upper() == turma_sel.strip().upper()) & (df_pres['data_dt'].dt.date == data_enc)]
            
            for _, row in lista_cat.iterrows():
                id_cat = row['id_catequizando']
                # Verifica se o aluno estava presente no banco
                foi_presente = False
                if not df_pres_existente.empty:
                    aluno_pres = df_pres_existente[df_pres_existente['id_catequizando'] == id_cat]
                    if not aluno_pres.empty and aluno_pres.iloc[0]['status'] == 'PRESENTE':
                        foi_presente = True
                buffer[id_cat] = foi_presente
            
            st.session_state[buffer_key] = buffer

        registros_presenca =[]
        contador_p = 0
        contador_a = 0
        
        st.markdown("### 📋 Lista de Presença")
        # Cria um grid de 2 colunas para turmas grandes ficarem mais compactas
        cols_chamada = st.columns(2)
        
        for i, (_, row) in enumerate(lista_cat.iterrows()):
            id_cat = row['id_catequizando']
            key_toggle = f"p_{id_cat}_{data_enc}_{i}"
            
            with cols_chamada[i % 2]:
                with st.container(border=True):
                    c_nome, c_tog = st.columns([3, 1])
                    c_nome.markdown(f"<span style='font-size:14px; font-weight:600; color:#417b99;'>{row['nome_completo']}</span>", unsafe_allow_html=True)
                    presente = c_tog.toggle("P", key=key_toggle, value=st.session_state[f"chamada_buffer_{turma_sel}_{data_enc}"][id_cat])
                    st.session_state[f"chamada_buffer_{turma_sel}_{data_enc}"][id_cat] = presente
                    
                    if presente: contador_p += 1
                    else: contador_a += 1

                    registros_presenca.append([data_enc.strftime('%d/%m/%Y'), id_cat, row['nome_completo'], turma_sel, "PRESENTE" if presente else "AUSENTE", tema_dia, st.session_state.usuario['nome']])

        st.markdown("---")
        st.markdown("### 📊 Resumo da Chamada")
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("✅ Presentes", contador_p)
        c_res2.metric("❌ Ausentes", contador_a)

        if st.button("🚀 FINALIZAR CHAMADA E SALVAR", use_container_width=True, type="primary", disabled=not tema_dia):
            # Salva presença e garante registro no Diário
            if salvar_com_seguranca(salvar_presencas, registros_presenca):
                # A função salvar_presencas no database.py JÁ FAZ a criação do encontro 
                # e a marcação no cronograma em cascata. Removemos a dupla escrita aqui.
                st.success(f"✅ Chamada salva e Diário atualizado!"); st.balloons()
                st.cache_data.clear(); time.sleep(1); st.rerun()
        
        if not tema_dia:
            st.warning("⚠️ Preencha o Tema do Encontro para salvar.")

# ==============================================================================
# PÁGINA: 👥 GESTÃO DE CATEQUISTAS (RH PASTORAL 3.0)
# ==============================================================================
elif menu == "👥 Gestão de Catequistas":
    st.title("👥 RH Pastoral e Universidade Catequética")
    
    df_formacoes = ler_aba("formacoes")
    df_pres_form = ler_aba("presenca_formacao")
    
    tab_radar, tab_univ, tab_cartorio = st.tabs([
        "📊 Radar do RH Pastoral", "🎓 Universidade Catequética", "⚙️ Central de Acessos e Perfis"
    ])

    # ==========================================================================
    # HUB 1: RADAR DO RH PASTORAL (ENGAJAMENTO E ACESSOS)
    # ==========================================================================
    with tab_radar:
        st.subheader("📊 Qualificação da Equipe Catequética")
        if not equipe_tecnica.empty:
            total_e = len(equipe_tecnica)
            bat_e = equipe_tecnica['data_batismo'].apply(lambda x: str(x).strip() not in["", "N/A", "None"]).sum()
            euc_e = equipe_tecnica['data_eucaristia'].apply(lambda x: str(x).strip() not in["", "N/A", "None"]).sum()
            cri_e = equipe_tecnica['data_crisma'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
            min_e = equipe_tecnica['data_ministerio'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Equipe", total_e)
            m2.metric("Batizados", bat_e)
            m3.metric("Eucaristia", euc_e)
            m4.metric("Crismados", cri_e)
            m5.metric("Ministros", min_e)

            st.divider()
            st.markdown("### 🛡️ Trilha Ministerial (Acompanhamento)")
            st.markdown("Veja o que falta para cada catequista alcançar o Ministério e envie uma mensagem de incentivo.")
            
            status_data =[]
            import urllib.parse
            
            for _, row in equipe_tecnica.iterrows():
                status, anos = verificar_status_ministerial(
                    str(row.get('data_inicio_catequese', '')),
                    str(row.get('data_batismo', '')),
                    str(row.get('data_eucaristia', '')),
                    str(row.get('data_crisma', '')),
                    str(row.get('data_ministerio', ''))
                )
                
                # Inteligência: Descobrir o que falta
                pendencias =[]
                if str(row.get('data_batismo', '')).strip() in ["", "N/A", "None"]: pendencias.append("Batismo")
                if str(row.get('data_eucaristia', '')).strip() in["", "N/A", "None"]: pendencias.append("Eucaristia")
                if str(row.get('data_crisma', '')).strip() in ["", "N/A", "None"]: pendencias.append("Crisma")
                if anos < 5: pendencias.append(f"Tempo ({anos}/5 anos)")
                
                motivo = ", ".join(pendencias) if pendencias else "Apto para o Ministério"
                if status == 'MINISTRO': motivo = "Ministério Concedido"
                
                status_data.append({
                    "Nome": row['nome'], "Status": status, "Anos": anos, 
                    "Turmas": row.get('turma_vinculada', ''), "Pendência": motivo, "Telefone": row.get('telefone', '')
                })
            
            df_status = pd.DataFrame(status_data)
            c_apt, c_cam = st.columns(2)
            
            with c_apt:
                st.success("**✅ Aptos / Ministros de Catequese**")
                st.dataframe(df_status[df_status['Status'].isin(['MINISTRO', 'APTO'])][['Nome', 'Turmas', 'Status']], use_container_width=True, hide_index=True)
                
                if st.button("🗂️ GERAR DOSSIÊ COMPLETO DA EQUIPE (PDF)", use_container_width=True):
                    st.session_state.pdf_lote_equipe = gerar_fichas_catequistas_lote(equipe_tecnica, df_pres_form, df_formacoes)
                if "pdf_lote_equipe" in st.session_state:
                    st.download_button("📥 BAIXAR DOSSIÊ DA EQUIPE", st.session_state.pdf_lote_equipe, "Dossie_Equipe_Catequetica.pdf", use_container_width=True)

            with c_cam:
                st.warning("**⏳ Em Caminhada de Formação**")
                df_caminhada = df_status[df_status['Status'] == 'EM_CAMINHADA']
                for _, c in df_caminhada.iterrows():
                    st.markdown(f"""
                        <div style='background-color:#fff8e1; padding:10px; border-radius:8px; border-left:4px solid #ffa000; margin-bottom:8px;'>
                            <b>{c['Nome']}</b><br>
                            <small style='color:#666;'>Falta: {c['Pendência']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    num_limpo = "".join(filter(str.isdigit, str(c['Telefone'])))
                    if num_limpo:
                        if num_limpo.startswith("0"): num_limpo = num_limpo[1:]
                        if not num_limpo.startswith("55"): num_limpo = f"5573{num_limpo}" if len(num_limpo) <= 9 else f"55{num_limpo}"
                        msg = f"Paz e Bem, {c['Nome'].split()[0]}! Passando para te incentivar na sua caminhada catequética. Vi que falta pouco para você alcançar os requisitos do Ministério (Falta: {c['Pendência']}). Conte com a coordenação! Deus abençoe."
                        link_wa = f"https://wa.me/{num_limpo}?text={urllib.parse.quote(msg)}"
                        st.markdown(f"<a href='{link_wa}' target='_blank' style='text-decoration:none;'><div style='background-color:#25d366; color:white; text-align:center; padding:4px; border-radius:5px; font-size:11px; font-weight:bold; margin-bottom:10px;'>📲 Enviar Incentivo</div></a>", unsafe_allow_html=True)

            # --- MONITORAMENTO DE ACESSOS ---
            st.divider()
            st.markdown("#### 📡 Monitoramento de Acessos (Último Login)")
            st.markdown("Acompanhe quais catequistas já estão utilizando o sistema e quem ainda não realizou o primeiro acesso.")
            
            lista_acessos =[]
            hoje_str = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).strftime("%d/%m/%Y")
            
            for _, u in df_usuarios.iterrows():
                if u['papel'] == 'ADMIN': continue
                
                nome = u['nome']
                turmas = u.get('turma_vinculada', 'Sem turma')
                sid = str(u.get('session_id', ''))
                
                if not sid or sid.strip() in["", "N/A", "None"]:
                    status = "🔴 Nunca acessou"
                    data_acesso = "Pendente"
                    ordem = 0
                elif "|" in sid:
                    data_acesso = sid.split("|")[1]
                    if data_acesso.startswith(hoje_str):
                        status = "🟢 Online Hoje"
                        ordem = 2
                    else:
                        status = "🟡 Já acessou"
                        ordem = 1
                else:
                    status = "🟡 Já acessou"
                    data_acesso = "Sessão Antiga"
                    ordem = 1
                    
                lista_acessos.append({"Catequista": nome, "Turmas": turmas, "Status": status, "Último Acesso": data_acesso, "ordem": ordem})
            
            if lista_acessos:
                df_acessos = pd.DataFrame(lista_acessos).sort_values(by=["ordem", "Catequista"], ascending=[False, True]).drop(columns=["ordem"])
                st.dataframe(df_acessos, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum catequista encontrado.")
        else:
            st.info("Nenhum catequista cadastrado.")

    # ==========================================================================
    # HUB 2: UNIVERSIDADE CATEQUÉTICA (FORMAÇÃO)
    # ==========================================================================
    with tab_univ:
        st.subheader("🎓 Universidade Catequética (Formação Continuada)")
        
        col_status = None
        if not df_formacoes.empty:
            if 'status' in df_formacoes.columns: col_status = 'status'
            elif 'col_5' in df_formacoes.columns: col_status = 'col_5'
            else: col_status = df_formacoes.columns[5] if len(df_formacoes.columns) > 5 else None

        # Calcula total de formações concluídas para a métrica de frequência
        total_formacoes_concluidas = len(df_formacoes[df_formacoes[col_status].str.upper() == "CONCLUIDA"]) if col_status and not df_formacoes.empty else 0

        sub_tab_plan, sub_tab_valida, sub_tab_hist = st.tabs(["📅 Planejar Formação", "✅ Validar Presença", "📜 Histórico e Edição"])

        with sub_tab_plan:
            with st.form("form_plan_formacao", clear_on_submit=True):
                f_tema = st.text_input("Tema da Formação").upper()
                c1, c2 = st.columns(2)
                f_data = c1.date_input("Data Prevista", value=date.today(), format="DD/MM/YYYY")
                f_formador = c2.text_input("Quem irá ministrar? (Formador)").upper()
                f_local = st.text_input("Local / Sala").upper()
                
                if st.form_submit_button("📌 AGENDAR FORMAÇÃO"):
                    if f_tema:
                        id_f = f"FOR-{int(time.time())}"
                        if salvar_formacao([id_f, f_tema, f_data.strftime('%d/%m/%Y'), f_formador, f_local, "PENDENTE"]):
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
                
                selecionados =[]
                cols = st.columns(2)
                
                for i, (_, cat) in enumerate(equipe_tecnica.iterrows()):
                    email_cat = cat['email']
                    nome_cat = cat['nome']
                    
                    # Calcula a frequência histórica do catequista
                    presencas_cat = len(df_pres_form[df_pres_form['email_participante'] == email_cat]) if not df_pres_form.empty else 0
                    freq_cat = (presencas_cat / total_formacoes_concluidas * 100) if total_formacoes_concluidas > 0 else 100.0
                    
                    # Alerta visual se a frequência for baixa
                    alerta_freq = "⚠️" if freq_cat < 50 and total_formacoes_concluidas > 0 else "✅"
                    
                    with cols[i % 2]:
                        if st.checkbox(f"{nome_cat} ({alerta_freq} Freq: {freq_cat:.0f}%)", key=f"pres_f_{dados_f['id_formacao']}_{email_cat}"):
                            selecionados.append(email_cat)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 FINALIZAR E REGISTRAR PRESENÇAS", use_container_width=True, type="primary"):
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
                df_formacoes['data_dt'] = pd.to_datetime(df_formacoes['data'], errors='coerce', dayfirst=True)
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
                            ed_data = st.date_input("Data", value=pd.to_datetime(d_edit['data']).date(), format="DD/MM/YYYY")
                            ed_formador = st.text_input("Formador", value=d_edit['formador']).upper()
                            ed_local = st.text_input("Local", value=d_edit['local']).upper()
                            
                            status_atual_val = str(d_edit[col_status]).upper() if col_status else "PENDENTE"
                            ed_status = st.selectbox("Status", ["PENDENTE", "CONCLUIDA"], index=0 if status_atual_val == "PENDENTE" else 1)
                            
                            c_btn1, c_btn2 = st.columns([3, 1])
                            if c_btn1.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                                from database import atualizar_formacao
                                if atualizar_formacao(d_edit['id_formacao'], [d_edit['id_formacao'], ed_tema, ed_data.strftime('%d/%m/%Y'), ed_formador, ed_local, ed_status]):
                                    st.success("Atualizado!"); st.cache_data.clear(); time.sleep(1); st.rerun()
                            
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

    # ==========================================================================
    # HUB 3: CENTRAL DE ACESSOS E PERFIS (CARTÓRIO)
    # ==========================================================================
    with tab_cartorio:
        st.subheader("⚙️ Central de Acessos e Perfis")
        
        sub_lista, sub_novo = st.tabs(["📋 Lista e Edição de Perfis", "➕ Criar Novo Acesso"])
        
        with sub_lista:
            if not equipe_tecnica.empty:
                busca_c = st.text_input("🔍 Pesquisar catequista:", key="busca_cat").upper()
                df_c_filtrado = equipe_tecnica[equipe_tecnica['nome'].str.contains(busca_c, na=False)] if busca_c else equipe_tecnica
                st.dataframe(df_c_filtrado[['nome', 'email', 'turma_vinculada', 'papel']], use_container_width=True, hide_index=True)
                
                st.divider()
                escolha_c = st.selectbox("Selecione para ver Perfil ou Editar:", [""] + df_c_filtrado['nome'].tolist(), key="sel_cat")
                
                if escolha_c:
                    u = equipe_tecnica[equipe_tecnica['nome'] == escolha_c].iloc[0]
                    
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"### {u['nome']}")
                        st.write(f"**E-mail:** {u['email']} | **Telefone:** {u.get('telefone', 'N/A')}")
                        st.warning(f"🚨 **EMERGÊNCIA:** {u.iloc[13] if len(u) > 13 else 'Não cadastrado'}")
                        st.write(f"**Turmas:** {u['turma_vinculada']}")
                    with c2:
                        if st.button(f"📄 Gerar Ficha PDF", use_container_width=True):
                            st.session_state.pdf_catequista = gerar_ficha_catequista_pdf(u.to_dict(), pd.DataFrame())
                        if "pdf_catequista" in st.session_state:
                            st.download_button("📥 Baixar Ficha", st.session_state.pdf_catequista, f"Ficha_{escolha_c}.pdf", use_container_width=True)

                    with st.expander("✏️ Editar Cadastro e Permissões", expanded=False):
                        hoje = date.today()
                        d_min, d_max = date(1920, 1, 1), date(2050, 12, 31)

                        def converter_ou_none(valor):
                            if pd.isna(valor) or str(valor).strip() in["", "N/A", "None"]: return None
                            try: return converter_para_data(valor)
                            except: return None

                        val_nasc = converter_ou_none(u.get('data_nascimento', '')) or hoje
                        val_ini = converter_ou_none(u.get('data_inicio_catequese', '')) or hoje
                        val_bat = converter_ou_none(u.get('data_batismo', ''))
                        val_euc = converter_ou_none(u.get('data_eucaristia', ''))
                        val_cri = converter_ou_none(u.get('data_crisma', ''))
                        val_min = converter_ou_none(u.get('data_ministerio', ''))
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
                            opcoes_papel = ["CATEQUISTA", "COORDENADOR", "ADMIN", "SECRETARIA"]
                            papel_atual = str(u.get('papel', 'CATEQUISTA')).upper()
                            ed_papel = c5.selectbox("Papel", opcoes_papel, index=opcoes_papel.index(papel_atual) if papel_atual in opcoes_papel else 0)
                            ed_nasc = c6.date_input("Data de Nascimento", value=val_nasc, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                            
                            lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else[]
                            ed_turmas = st.multiselect("Vincular às Turmas:", lista_t_nomes, default=[t.strip() for t in str(u.get('turma_vinculada', '')).split(",") if t.strip() in lista_t_nomes])
                            
                            st.divider()
                            st.markdown("#### ⛪ Itinerário Sacramental")
                            
                            if f"has_bat_{u['email']}" not in st.session_state: st.session_state[f"has_bat_{u['email']}"] = (val_bat is not None)
                            if f"has_euc_{u['email']}" not in st.session_state: st.session_state[f"has_euc_{u['email']}"] = (val_euc is not None)
                            if f"has_cri_{u['email']}" not in st.session_state: st.session_state[f"has_cri_{u['email']}"] = (val_cri is not None)
                            if f"has_min_{u['email']}" not in st.session_state: st.session_state[f"has_min_{u['email']}"] = (val_min is not None)

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                has_ini = st.checkbox("Início na Catequese", value=True)
                                dt_ini = st.date_input("Data Início", value=val_ini, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                            with col2:
                                has_bat = st.checkbox("Possui Batismo?", key=f"has_bat_{u['email']}")
                                dt_bat = st.date_input("Data Batismo", value=val_bat if val_bat else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_bat)
                            with col3:
                                has_euc = st.checkbox("Possui 1ª Eucaristia?", key=f"has_euc_{u['email']}")
                                dt_euc = st.date_input("Data Eucaristia", value=val_euc if val_euc else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_euc)

                            col4, col5 = st.columns(2)
                            with col4:
                                has_cri = st.checkbox("Possui Crisma?", key=f"has_cri_{u['email']}")
                                dt_cri = st.date_input("Data Crisma", value=val_cri if val_cri else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_cri)
                            with col5:
                                has_min = st.checkbox("É Ministro de Catequese?", key=f"has_min_{u['email']}")
                                dt_min = st.date_input("Data Ministério", value=val_min if val_min else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_min)

                            if st.form_submit_button("💾 SALVAR ALTERAÇÕES E SINCRONIZAR", use_container_width=True):
                                str_ini = dt_ini.strftime('%d/%m/%Y') if has_ini else ""
                                str_bat = dt_bat.strftime('%d/%m/%Y') if has_bat else ""
                                str_euc = dt_euc.strftime('%d/%m/%Y') if has_euc else ""
                                str_cri = dt_cri.strftime('%d/%m/%Y') if has_cri else ""
                                str_min = dt_min.strftime('%d/%m/%Y') if has_min else ""

                                dados_up =[
                                    ed_nome, u['email'], ed_senha, ed_papel, ", ".join(ed_turmas), 
                                    ed_tel, ed_nasc.strftime('%d/%m/%Y'), str_ini, str_bat, str_euc, str_cri, str_min, 
                                    str(u.iloc[12]) if len(u) > 12 else "", ed_emergencia
                                ]
                                
                                nome_cat_original = str(u.get('nome', ''))
                                
                                if atualizar_usuario(u['email'], dados_up):
                                    with st.spinner("Sincronizando catequista com as turmas e histórico..."):
                                        try:
                                            if ed_nome != nome_cat_original:
                                                from database import sincronizar_renomeacao_catequista
                                                sincronizar_renomeacao_catequista(nome_cat_original, ed_nome)
                                                
                                            planilha = conectar_google_sheets()
                                            if planilha:
                                                aba_t = planilha.worksheet("turmas")
                                                aba_u = planilha.worksheet("usuarios")
                                                nome_cat = ed_nome
                                                
                                                cel_u = aba_u.find(u['email'], in_column=2)
                                                if cel_u: aba_u.update_cell(cel_u.row, 5, ", ".join(ed_turmas))
                                                
                                                turmas_afetadas = set([t.strip() for t in str(u.get('turma_vinculada', '')).split(",") if t.strip()] + ed_turmas)
                                                
                                                for t_nome in turmas_afetadas:
                                                    cel_t = aba_t.find(t_nome, in_column=2)
                                                    if cel_t:
                                                        try: v_atual = aba_t.cell(cel_t.row, 5).value or ""
                                                        except: v_atual = ""
                                                        
                                                        v_list =[x.strip() for x in v_atual.split(',') if x.strip()]
                                                        mudou = False
                                                        
                                                        if t_nome in ed_turmas:
                                                            if nome_cat not in v_list:
                                                                v_list.append(nome_cat); mudou = True
                                                        else:
                                                            if nome_cat in v_list:
                                                                v_list.remove(nome_cat); mudou = True
                                                                
                                                        if mudou: aba_t.update_cell(cel_t.row, 5, ", ".join(v_list))
                                        except Exception as e:
                                            st.warning(f"Aviso: Erro ao sincronizar com a aba turmas: {e}")
                                    
                                    st.success("✅ Cadastro atualizado e sincronizado com as turmas!"); st.cache_data.clear(); time.sleep(1); st.rerun()

        with sub_novo:
            st.markdown("#### ➕ Criar Novo Acesso para Equipe")
            with st.form("form_novo_cat", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_nome = c1.text_input("Nome Completo (EM MAIÚSCULAS)").upper()
                n_email = c2.text_input("E-mail (Login)")
                
                c3, c4, c5 = st.columns(3)
                n_senha = c3.text_input("Senha Inicial", type="password")
                n_tel = c4.text_input("Telefone / WhatsApp")
                n_nasc = c5.date_input("Data de Nascimento", value=date(1990, 1, 1), min_value=date(1930, 1, 1), max_value=date(2011, 12, 31), format="DD/MM/YYYY")
                
                c_papel, c_emerg = st.columns(2)
                n_papel = c_papel.selectbox("Papel / Nível de Acesso",["CATEQUISTA", "COORDENADOR", "ADMIN", "SECRETARIA"])
                n_emergencia = c_emerg.text_input("🚨 Contato de Emergência (Nome e Tel)")
                
                lista_t_nomes = df_turmas['nome_turma'].tolist() if not df_turmas.empty else[]
                n_turmas = st.multiselect("Vincular às Turmas:", lista_t_nomes)
                
                if st.form_submit_button("🚀 CRIAR ACESSO E DEFINIR PERMISSÕES", use_container_width=True, type="primary"):
                    if n_nome and n_email and n_senha:
                        with st.spinner("Criando novo acesso..."):
                            novo_user_lista =[
                                n_nome, n_email, n_senha, n_papel, ", ".join(n_turmas), 
                                n_tel, n_nasc.strftime('%d/%m/%Y'), "", "", "", "", "", "", n_emergencia
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
        tab_reunioes, tab_censo, tab_agenda, tab_visitas = st.tabs([
            "📅 Reuniões de Pais", "📊 Censo Familiar", "📞 Agenda Geral", "🏠 Visitas"
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
                            df_reu_check = ler_aba("reunioes_pais")
                            ja_existe = False
                            if not df_reu_check.empty:
                                data_str = r_data.strftime('%d/%m/%Y')
                                duplicada = df_reu_check[(df_reu_check.iloc[:, 2] == data_str) & (df_reu_check.iloc[:, 3] == r_turma)]
                                if not duplicada.empty:
                                    ja_existe = True
                            
                            if ja_existe:
                                st.error(f"⚠️ Já existe uma reunião agendada para a turma {r_turma} no dia {r_data.strftime('%d/%m/%Y')}.")
                            else:
                                if salvar_reuniao_pais([f"REU-{int(time.time())}", r_tema, r_data.strftime('%d/%m/%Y'), r_turma, r_local, "PENDENTE"]):
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
                            ed_data = st.date_input("Data", value=converter_para_data(d_edit.iloc[2]), format="DD/MM/YYYY")
                            ed_turma = st.selectbox("Turma",["GERAL (TODAS)"] + (df_turmas['nome_turma'].tolist() if not df_turmas.empty else[]))
                            ed_local = st.text_input("Local", value=d_edit.iloc[4]).upper()
                            ed_status = st.selectbox("Status",["PENDENTE", "CONCLUIDA"], index=0 if d_edit.iloc[5] == "PENDENTE" else 1)
                            if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                                if atualizar_reuniao_pais(d_edit.iloc[0],[d_edit.iloc[0], ed_tema, ed_data.strftime('%d/%m/%Y'), ed_turma, ed_local, ed_status]):
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
            st.subheader("📞 Agenda Geral e Comunicação (CRM Pastoral)")
            st.markdown("Filtre as famílias e envie mensagens padronizadas pelo WhatsApp com apenas um clique.")
            
            c_filtro1, c_filtro2 = st.columns(2)
            filtro_turma_ag = c_filtro1.selectbox("Filtrar por Turma:", ["TODAS"] + df_turmas['nome_turma'].tolist() if not df_turmas.empty else ["TODAS"])
            filtro_pendencia = c_filtro2.checkbox("Mostrar apenas com Documentos Pendentes")
            
            busca_g = st.text_input("🔍 Pesquisar por nome (Catequizando ou Pais):", key="txt_busca_fam").upper()
            
            df_age = df_cat.copy()
            if filtro_turma_ag != "TODAS": df_age = df_age[df_age['etapa'] == filtro_turma_ag]
            if filtro_pendencia: df_age = df_age[~df_age['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])]
            if busca_g: df_age = df_age[df_age['nome_completo'].str.contains(busca_g, na=False) | df_age['nome_mae'].str.contains(busca_g, na=False) | df_age['nome_pai'].str.contains(busca_g, na=False)]
            
            st.write(f"**{len(df_age)} famílias encontradas.**")
            
            import urllib.parse
            for _, row in df_age.head(50).iterrows(): # Limita a 50 para não travar a tela
                with st.container():
                    st.markdown(f"""
                        <div style='background-color:#f8f9f0; padding:10px; border-radius:10px; border-left:5px solid #417b99; margin-bottom:5px;'>
                            <b style='color:#417b99;'>{row['nome_completo']}</b> | Turma: {row['etapa']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    c_btn1, c_btn2 = st.columns(2)
                    nome_alvo = row['nome_mae'] if row['nome_mae'] != "N/A" else (row['nome_pai'] if row['nome_pai'] != "N/A" else row['nome_responsavel'])
                    tel_alvo = row['tel_mae'] if row['tel_mae'] != "N/A" else (row['tel_pai'] if row['tel_pai'] != "N/A" else row['contato_principal'])
                    
                    num_limpo = "".join(filter(str.isdigit, str(tel_alvo)))
                    if num_limpo:
                        if num_limpo.startswith("0"): num_limpo = num_limpo[1:]
                        if not num_limpo.startswith("55"): num_limpo = f"5573{num_limpo}" if len(num_limpo) <= 9 else f"55{num_limpo}"
                        
                        # Mensagem de Documentos (Gerada pelo Python, sem custo de IA)
                        if row['doc_em_falta'] not in['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO']:
                            msg_doc = f"Paz e Bem, {nome_alvo}! Aqui é da Catequese da Paróquia de Fátima. Notamos que ainda falta entregar a cópia do(s) documento(s): {row['doc_em_falta']} do(a) catequizando(a) {row['nome_completo']}. Poderia nos enviar ou levar no próximo encontro? Deus abençoe!"
                            link_doc = f"https://wa.me/{num_limpo}?text={urllib.parse.quote(msg_doc)}"
                            c_btn1.markdown(f"<a href='{link_doc}' target='_blank' style='text-decoration:none;'><div style='background-color:#e03d11; color:white; text-align:center; padding:8px; border-radius:5px; font-size:12px; font-weight:bold;'>📄 Cobrar Documentos</div></a>", unsafe_allow_html=True)
                        else:
                            c_btn1.markdown("<div style='background-color:#e0e0e0; color:#666; text-align:center; padding:8px; border-radius:5px; font-size:12px;'>✅ Docs em dia</div>", unsafe_allow_html=True)
                            
                        # Mensagem de Atualização Cadastral
                        msg_upd = f"Paz e Bem, {nome_alvo}! Aqui é da Catequese. Estamos atualizando nossos cadastros para este ano. O endereço de vocês continua sendo: {row['endereco_completo']}? Deus abençoe!"
                        link_upd = f"https://wa.me/{num_limpo}?text={urllib.parse.quote(msg_upd)}"
                        c_btn2.markdown(f"<a href='{link_upd}' target='_blank' style='text-decoration:none;'><div style='background-color:#417b99; color:white; text-align:center; padding:8px; border-radius:5px; font-size:12px; font-weight:bold;'>🔄 Confirmar Cadastro</div></a>", unsafe_allow_html=True)
                    else:
                        st.caption("Sem telefone válido cadastrado.")
                    
                    st.markdown("<br>", unsafe_allow_html=True)

        with tab_visitas:
            st.subheader("🏠 Central de Resgate Pastoral (Visitas)")
            st.markdown("Identificação automática de famílias que necessitam de acompanhamento urgente devido à infrequência dos catequizandos.")
            
            df_ativos = df_cat[df_cat['status'] == 'ATIVO'] if not df_cat.empty else pd.DataFrame()
            df_risco_visita = pd.DataFrame()
            
            if not df_pres.empty and not df_ativos.empty:
                df_faltas = df_pres[df_pres['status'] == 'AUSENTE']
                if not df_faltas.empty:
                    contagem = df_faltas.groupby('id_catequizando').size().reset_index(name='qtd_faltas')
                    contagem_risco = contagem[contagem['qtd_faltas'] >= 3]
                    df_risco_visita = pd.merge(contagem_risco, df_ativos, on='id_catequizando', how='inner')
                    df_risco_visita = df_risco_visita.sort_values(by='qtd_faltas', ascending=False)
            
            # Separa quem já foi visitado de quem está pendente
            if not df_risco_visita.empty:
                df_pendentes = df_risco_visita[~df_risco_visita['obs_pastoral_familia'].str.contains(r'\[VISITA_CONCLUIDA\]', na=False, case=False)]
                df_visitados = df_risco_visita[df_risco_visita['obs_pastoral_familia'].str.contains(r'\[VISITA_CONCLUIDA\]', na=False, case=False)]
            else:
                df_pendentes = pd.DataFrame()
                df_visitados = pd.DataFrame()

            sub_pendentes, sub_historico = st.tabs([f"🚨 Fila de Resgate ({len(df_pendentes)})", f"✅ Visitas Realizadas ({len(df_visitados)})"])
            
            with sub_pendentes:
                if not df_pendentes.empty:
                    st.error(f"Temos **{len(df_pendentes)} catequizandos** em risco crítico de evasão aguardando visita familiar.")
                    for _, row in df_pendentes.iterrows():
                        with st.expander(f"🚩 {row['nome_completo']} ({row['etapa']}) - {row['qtd_faltas']} Faltas Acumuladas"):
                            c_v1, c_v2 = st.columns([2, 1])
                            with c_v1:
                                st.markdown(f"**👨‍👩‍👧 Pais/Responsáveis:** {row['nome_mae']} e {row['nome_pai']}")
                                st.markdown(f"**📍 Endereço:** {row['endereco_completo']}")
                                st.markdown(f"**📞 Contato Principal:** {row['contato_principal']}")
                                montar_botoes_whatsapp(row)
                            with c_v2:
                                st.markdown("**📄 Encaminhamento**")
                                if st.button("🖨️ Gerar Ficha para Pastoral Familiar", key=f"btn_pdf_visita_{row['id_catequizando']}", use_container_width=True):
                                    filhos_lista =[{'nome': row['nome_completo'], 'etapa': row['etapa'], 'status': f"{row['qtd_faltas']} Faltas (Risco de Evasão)"}]
                                    pdf_visita = gerar_relatorio_familia_pdf(row.to_dict(), filhos_lista)
                                    st.session_state[f"pdf_v_{row['id_catequizando']}"] = pdf_visita
                                if f"pdf_v_{row['id_catequizando']}" in st.session_state:
                                    st.download_button("📥 Baixar Ficha (PDF)", st.session_state[f"pdf_v_{row['id_catequizando']}"], f"Visita_{row['nome_completo']}.pdf", "application/pdf", use_container_width=True)
                            
                            st.markdown("---")
                            st.markdown("**📝 Registrar Baixa da Visita**")
                            with st.form(key=f"form_visita_{row['id_catequizando']}"):
                                data_v = st.date_input("Data da Visita", date.today(), format="DD/MM/YYYY")
                                status_v = st.selectbox("Resultado do Resgate:",["Comprometeu-se a retornar", "Desistiu da Catequese", "Problema de Saúde/Familiar", "Mudou-se"])
                                relato_v = st.text_area("Relato da Conversa:", height=80, help="Descreva o que foi conversado.")
                                
                                if st.form_submit_button("💾 CONCLUIR VISITA E REMOVER DO ALERTA"):
                                    if relato_v:
                                        # Monta a tag invisível
                                        tag_visita = f"\n[VISITA_CONCLUIDA] Data: {data_v.strftime('%d/%m/%Y')} | Status: {status_v} | Relato: {relato_v}"
                                        obs_atual = str(row.get('obs_pastoral_familia', '')).replace("N/A", "")
                                        novo_relato = f"{obs_atual}{tag_visita}".strip()
                                        
                                        lista_up = row.tolist()
                                        while len(lista_up) < 30: lista_up.append("N/A")
                                        lista_up[29] = novo_relato
                                        
                                        # Se desistiu ou mudou, já altera o status do catequizando
                                        if status_v in["Desistiu da Catequese", "Mudou-se"]:
                                            lista_up[12] = "DESISTENTE" if status_v == "Desistiu da Catequese" else "TRANSFERIDO"
                                            
                                        if atualizar_catequizando(row['id_catequizando'], lista_up):
                                            st.success("Visita registrada! O alerta foi removido do Dashboard."); st.cache_data.clear(); time.sleep(1.5); st.rerun()
                                    else:
                                        st.error("Por favor, preencha o relato da conversa.")
                else:
                    st.success("✅ Fila zerada! Nenhuma família aguardando visita no momento.")

            with sub_historico:
                if not df_visitados.empty:
                    for _, row in df_visitados.iterrows():
                        with st.expander(f"✅ {row['nome_completo']} ({row['etapa']})"):
                            st.info(f"**Histórico Pastoral:**\n{row.get('obs_pastoral_familia', '')}")
                else:
                    st.info("Nenhum histórico de visitas concluídas.")

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




# ==============================================================================
# PÁGINAS EXCLUSIVAS DA SECRETARIA PAROQUIAL
# ==============================================================================
elif menu == "📊 Painel da Secretaria":
    st.title("📊 Painel da Secretaria Paroquial")
    st.markdown("Visão administrativa e cartorial da catequese.")
    
    df_ativos = df_cat[df_cat['status'] == 'ATIVO'] if not df_cat.empty else pd.DataFrame()
    df_desistentes = df_cat[df_cat['status'].isin(['DESISTENTE', 'TRANSFERIDO', 'INATIVO'])] if not df_cat.empty else pd.DataFrame()
    df_concluidos = df_cat[df_cat['status'] == 'CONCLUÍDO'] if not df_cat.empty else pd.DataFrame()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Histórico (Inscritos)", len(df_cat))
    c2.metric("🟢 Em Caminhada (Ativos)", len(df_ativos))
    c3.metric("🔴 Evasão / Transferências", len(df_desistentes))
    c4.metric("🎓 Egressos (Concluídos)", len(df_concluidos))
    
    st.divider()
    
    col_alertas, col_print = st.columns([1.5, 1])
    
    with col_alertas:
        st.subheader("🚨 Alertas da Secretaria")
        
        # Documentos Pendentes
        df_pend_doc = df_ativos[~df_ativos['doc_em_falta'].isin(['COMPLETO', 'OK', 'NADA', 'NADA FALTANDO'])]
        if not df_pend_doc.empty:
            with st.expander(f"📄 {len(df_pend_doc)} Catequizandos com Documentos Pendentes", expanded=True):
                st.dataframe(df_pend_doc[['nome_completo', 'etapa', 'doc_em_falta']].rename(columns={'nome_completo': 'Catequizando', 'etapa': 'Turma', 'doc_em_falta': 'Faltando'}), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todos os catequizandos ativos estão com a documentação em dia!")
            
        # Fila de Espera
        turmas_reais = df_turmas['nome_turma'].unique().tolist() if not df_turmas.empty else[]
        df_sem_turma = df_ativos[(df_ativos['etapa'] == "CATEQUIZANDOS SEM TURMA") | (~df_ativos['etapa'].isin(turmas_reais))]
        if not df_sem_turma.empty:
            with st.expander(f"⏳ {len(df_sem_turma)} Catequizandos aguardando alocação em Turma"):
                st.dataframe(df_sem_turma[['nome_completo', 'contato_principal']].rename(columns={'nome_completo': 'Catequizando', 'contato_principal': 'Contato'}), use_container_width=True, hide_index=True)
                
    with col_print:
        st.subheader("🖨️ Central de Emissão")
        st.markdown("Emissão de documentos oficiais e relatórios em lote.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🏛️ Gerar Relatório Diocesano", use_container_width=True):
            st.session_state.pdf_diocesano = gerar_relatorio_diocesano_pdf(df_turmas, df_cat, df_usuarios)
        if "pdf_diocesano" in st.session_state:
            st.download_button("📥 Baixar Relatório Diocesano", st.session_state.pdf_diocesano, "Diocesano.pdf", use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗂️ Imprimir Fichas (Paróquia Inteira)", use_container_width=True, type="primary"):
            with st.spinner("Gerando fichas (Isso pode levar alguns segundos)..."):
                st.session_state.pdf_lote_f = gerar_fichas_paroquia_total(df_cat)
        if "pdf_lote_f" in st.session_state:
            st.download_button("📥 Baixar Fichas em Lote", st.session_state.pdf_lote_f, "Fichas_Lote.pdf", use_container_width=True)

elif menu == "🏫 Visão de Turmas e Equipe":
    st.title("🏫 Visão de Turmas e Equipe (Mapa da Catequese)")
    tab_turmas, tab_equipe = st.tabs(["🏫 Turmas e Catequizandos", "👥 Equipe de Catequistas"])
    
    with tab_turmas:
        st.markdown("#### Raio-X Administrativo das Turmas")
        if not df_turmas.empty:
            for _, t in df_turmas.iterrows():
                nome_t = str(t['nome_turma']).strip().upper()
                cats = str(t.get('catequista_responsavel', 'Não informado'))
                alunos_t = df_cat[(df_cat['etapa'].str.strip().str.upper() == nome_t) & (df_cat['status'] == 'ATIVO')] if not df_cat.empty else pd.DataFrame()
                
                qtd_alunos = len(alunos_t)
                idades =[calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()] if not alunos_t.empty else[]
                media_idade = round(sum(idades)/len(idades), 1) if idades else 0
                
                with st.expander(f"📚 {nome_t} - {qtd_alunos} inscritos ativos"):
                    st.markdown(f"**Catequistas:** {cats}")
                    st.markdown(f"**Média de Idade:** {media_idade} anos")
                    
                    if not alunos_t.empty:
                        st.dataframe(alunos_t[['nome_completo', 'data_nascimento', 'contato_principal']].rename(columns={'nome_completo': 'Catequizando', 'data_nascimento': 'Nascimento', 'contato_principal': 'Contato'}), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma turma cadastrada.")
            
    with tab_equipe:
        st.markdown("#### Acervo de Fichas dos Catequistas")
        if not equipe_tecnica.empty:
            busca_c = st.text_input("🔍 Pesquisar catequista:", key="busca_cat_sec").upper()
            df_c_filtrado = equipe_tecnica[equipe_tecnica['nome'].str.contains(busca_c, na=False)] if busca_c else equipe_tecnica
            
            for _, u in df_c_filtrado.iterrows():
                with st.expander(f"👤 {u['nome']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**E-mail:** {u['email']} | **Telefone:** {u.get('telefone', 'N/A')}")
                        st.write(f"**Nascimento:** {formatar_data_br(u.get('data_nascimento', ''))}")
                        st.write(f"**Turmas:** {u.get('turma_vinculada', 'Nenhuma')}")
                        st.write(f"**Sacramentos:** Batismo ({formatar_data_br(u.get('data_batismo', ''))}), Eucaristia ({formatar_data_br(u.get('data_eucaristia', ''))}), Crisma ({formatar_data_br(u.get('data_crisma', ''))})")
                    with c2:
                        if st.button(f"📄 Gerar Ficha PDF", key=f"btn_ficha_sec_{u['email']}", use_container_width=True):
                            st.session_state[f"pdf_cat_{u['email']}"] = gerar_ficha_catequista_pdf(u.to_dict(), pd.DataFrame())
                        if f"pdf_cat_{u['email']}" in st.session_state:
                            st.download_button("📥 Baixar Ficha", st.session_state[f"pdf_cat_{u['email']}"], f"Ficha_{u['nome']}.pdf", use_container_width=True)
        else:
            st.info("Nenhum catequista cadastrado.")

elif menu == "🕊️ Acervo de Sacramentos":
    st.title("🕊️ Cartório e Acervo Sacramental")
    st.markdown("Consulte o histórico de sacramentos ou registre lançamentos avulsos (ex: lembranças de outras paróquias).")
    
    tab_livro, tab_avulso = st.tabs(["📜 Livro de Registros (Cartório Oficial)", "➕ Lançamento Avulso"])
    
    with tab_livro:
        st.markdown("#### 📜 Livro de Registros (Cartório Oficial)")
        df_eventos = ler_aba("sacramentos_eventos")
        df_recebidos = ler_aba("sacramentos_recebidos")
        
        if not df_recebidos.empty and not df_eventos.empty:
            # Mescla as informações para a secretaria ver o NOME da pessoa
            df_eventos_min = df_eventos[['id_evento', 'turmas', 'catequista']]
            df_livro = pd.merge(df_recebidos, df_eventos_min, on='id_evento', how='left')
            
            df_livro['data_dt'] = pd.to_datetime(df_livro['data'], errors='coerce', dayfirst=True)
            df_livro = df_livro.sort_values(by='data_dt', ascending=False)
            
            # Renomeia as colunas para o padrão de Secretaria
            df_livro_exibicao = df_livro[['nome', 'tipo', 'data', 'turmas', 'catequista']].rename(columns={
                'nome': 'Catequizando', 'tipo': 'Sacramento', 'data': 'Data', 'turmas': 'Turma', 'catequista': 'Local / Celebrante'
            })
            
            c_busca, c_btn = st.columns([3, 1])
            busca_livro = c_busca.text_input("🔍 Buscar Certidão (Nome ou Sacramento):").upper()
            
            if busca_livro:
                df_livro_exibicao = df_livro_exibicao[
                    df_livro_exibicao['Catequizando'].str.contains(busca_livro, na=False) | 
                    df_livro_exibicao['Sacramento'].str.contains(busca_livro, na=False)
                ]
            
            if c_btn.button("🖨️ Gerar PDF do Livro", use_container_width=True):
                st.session_state.pdf_livro_sacramentos = gerar_livro_sacramentos_pdf(df_livro_exibicao)
                
            if "pdf_livro_sacramentos" in st.session_state:
                c_btn.download_button("📥 Baixar PDF", st.session_state.pdf_livro_sacramentos, "Livro_Sacramentos.pdf", "application/pdf", use_container_width=True)
            
            st.dataframe(df_livro_exibicao, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum sacramento registrado no histórico.")

    with tab_avulso:
        st.markdown("#### 🔍 Lançamento Avulso")
        st.markdown("Use para registrar um sacramento feito em outra cidade ou corrigir o acervo de um catequizando específico.")
        nome_busca = st.text_input("Digite o nome do catequizando:").upper()
        if nome_busca:
            sugestoes = df_cat[df_cat['nome_completo'].str.contains(nome_busca)] if not df_cat.empty else pd.DataFrame()
            if not sugestoes.empty:
                escolhido = st.selectbox("Selecione o catequizando:", sugestoes['nome_completo'].tolist())
                dados_c = sugestoes[sugestoes['nome_completo'] == escolhido].iloc[0]
                st.info(f"**Sacramentos Atuais:** {dados_c.get('sacramentos_ja_feitos', 'Nenhum')}")
                
                with st.form("form_sac_individual_sec"):
                    c1, c2 = st.columns(2)
                    tipo_s_ind = c1.selectbox("Sacramento",["BATISMO", "EUCARISTIA", "CRISMA"])
                    data_s_ind = c2.date_input("Data", date.today(), format="DD/MM/YYYY")
                    local_ind = st.text_input("Local (Ex: Paróquia São José - Ilhéus)").upper()
                    
                    if st.form_submit_button("💾 SALVAR REGISTRO AVULSO", use_container_width=True):
                        id_ev = f"IND-{int(time.time())}"
                        local_final = f"Avulso: {local_ind}" if local_ind else "Avulso"
                        if registrar_evento_sacramento_completo([id_ev, tipo_s_ind, data_s_ind.strftime('%d/%m/%Y'), dados_c['etapa'], f"{st.session_state.usuario['nome']} ({local_final})"], [[id_ev, dados_c['id_catequizando'], escolhido, tipo_s_ind, data_s_ind.strftime('%d/%m/%Y')]], tipo_s_ind):
                            st.success("Registrado no acervo!"); st.cache_data.clear(); time.sleep(1); st.rerun()
            else:
                st.warning("Catequizando não encontrado.")

elif menu == "📖 Consulta de Encontros":
    st.title("📖 Consulta de Encontros (Diário)")
    st.markdown("Consulte a linha do tempo das turmas para informar aos pais sobre os encontros realizados.")
    
    df_enc_local = ler_aba("encontros")
    turmas_permitidas = sorted(df_turmas['nome_turma'].unique().tolist()) if not df_turmas.empty else[]
    
    if turmas_permitidas:
        turma_focal = st.selectbox("🔍 Selecione a Turma para Consultar:", turmas_permitidas)
        st.divider()
        st.subheader(f"📜 Linha do Tempo: {turma_focal}")
        
        if not df_enc_local.empty:
            df_enc_local['turma_norm'] = df_enc_local['turma'].astype(str).str.strip().str.upper()
            df_enc_local['data_sort'] = pd.to_datetime(df_enc_local['data'], errors='coerce', dayfirst=True)
            hist_turma = df_enc_local[df_enc_local['turma_norm'] == turma_focal.strip().upper()].sort_values(by='data_sort', ascending=False)
            
            if not hist_turma.empty:
                for idx, row in hist_turma.iterrows():
                    data_d = str(row['data'])
                    tema_d = row.get('tema', 'Tema não registrado')
                    obs_d = row.get('observacoes', '')
                    cat_d = row.get('catequista', 'Não informado')
                    
                    with st.expander(f"📅 {formatar_data_br(data_d)} - {tema_d} | 👤 Resp: {cat_d}"):
                        st.markdown(f"**Observações Pastorais / Relato:**\n{obs_d}")
            else:
                st.info("Nenhum encontro registrado para esta turma.")
        else:
            st.info("O sistema ainda não possui registros de encontros.")
    else:
        st.warning("Nenhuma turma cadastrada.")







# ==============================================================================
# PÁGINA: ⚙️ MEU CADASTRO (AUTOATENDIMENTO DO CATEQUISTA)
# ==============================================================================
elif menu == "⚙️ Meu Cadastro":
    st.title("⚙️ Meu Cadastro e Perfil Ministerial")
    
    email_logado = st.session_state.usuario.get('email')
    
    if not df_usuarios.empty and email_logado:
        u_data = df_usuarios[df_usuarios['email'] == email_logado]
        if not u_data.empty:
            u = u_data.iloc[0]
            
            st.info("💡 **Dica:** Mantenha seus dados de contato e histórico sacramental sempre atualizados. Sua senha de acesso também pode ser alterada aqui.")
            
            hoje = date.today()
            d_min, d_max = date(1920, 1, 1), date(2050, 12, 31)

            def converter_ou_none(valor):
                if pd.isna(valor) or str(valor).strip() in["", "N/A", "None"]: return None
                try: return converter_para_data(valor)
                except: return None

            val_nasc = converter_ou_none(u.get('data_nascimento', '')) or hoje
            val_ini = converter_ou_none(u.get('data_inicio_catequese', '')) or hoje
            val_bat = converter_ou_none(u.get('data_batismo', ''))
            val_euc = converter_ou_none(u.get('data_eucaristia', ''))
            val_cri = converter_ou_none(u.get('data_crisma', ''))
            val_min = converter_ou_none(u.get('data_ministerio', ''))
            val_emerg = u.iloc[13] if len(u) > 13 else ""

            with st.form("form_meu_cadastro"):
                st.markdown("#### 📍 Dados Pessoais e Acesso")
                c1, c2 = st.columns(2)
                ed_nome = c1.text_input("Nome Completo", value=str(u.get('nome', ''))).upper()
                ed_senha = c2.text_input("Senha de Acesso", value=str(u.get('senha', '')), type="password")
                
                c3, c4 = st.columns(2)
                ed_tel = c3.text_input("Telefone / WhatsApp", value=str(u.get('telefone', '')))
                ed_emergencia = c4.text_input("🚨 Contato de Emergência (Nome e Tel)", value=val_emerg).upper()
                
                c5, c6 = st.columns(2)
                ed_nasc = c5.date_input("Data de Nascimento", value=val_nasc, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🔒 Informações Restritas (Apenas Leitura)")
                r1, r2 = st.columns(2)
                r1.text_input("E-mail (Login)", value=u['email'], disabled=True, help="Para mudar o e-mail de login, contate a coordenação.")
                r2.text_input("Turmas Vinculadas", value=str(u.get('turma_vinculada', '')), disabled=True, help="Apenas a coordenação pode alterar seus vínculos de turma.")
                
                st.divider()
                st.markdown("#### ⛪ Itinerário Sacramental (Marque apenas se possuir)")
                
                if "my_has_bat" not in st.session_state: st.session_state["my_has_bat"] = (val_bat is not None)
                if "my_has_euc" not in st.session_state: st.session_state["my_has_euc"] = (val_euc is not None)
                if "my_has_cri" not in st.session_state: st.session_state["my_has_cri"] = (val_cri is not None)
                if "my_has_min" not in st.session_state: st.session_state["my_has_min"] = (val_min is not None)

                col1, col2, col3 = st.columns(3)
                with col1:
                    has_ini = st.checkbox("Início na Catequese", value=True)
                    dt_ini = st.date_input("Data Início", value=val_ini, min_value=d_min, max_value=d_max, format="DD/MM/YYYY")
                with col2:
                    has_bat = st.checkbox("Possui Batismo?", key="my_has_bat")
                    dt_bat = st.date_input("Data Batismo", value=val_bat if val_bat else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_bat)
                with col3:
                    has_euc = st.checkbox("Possui 1ª Eucaristia?", key="my_has_euc")
                    dt_euc = st.date_input("Data Eucaristia", value=val_euc if val_euc else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_euc)

                col4, col5 = st.columns(2)
                with col4:
                    has_cri = st.checkbox("Possui Crisma?", key="my_has_cri")
                    dt_cri = st.date_input("Data Crisma", value=val_cri if val_cri else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_cri)
                with col5:
                    has_min = st.checkbox("É Ministro de Catequese?", key="my_has_min")
                    dt_min = st.date_input("Data Ministério", value=val_min if val_min else hoje, min_value=d_min, max_value=d_max, format="DD/MM/YYYY", disabled=not has_min)

                if st.form_submit_button("💾 SALVAR MEUS DADOS", use_container_width=True, type="primary"):
                    str_ini = dt_ini.strftime('%d/%m/%Y') if has_ini else ""
                    str_bat = dt_bat.strftime('%d/%m/%Y') if has_bat else ""
                    str_euc = dt_euc.strftime('%d/%m/%Y') if has_euc else ""
                    str_cri = dt_cri.strftime('%d/%m/%Y') if has_cri else ""
                    str_min = dt_min.strftime('%d/%m/%Y') if has_min else ""

                    # Preserva os dados restritos e de sessão
                    papel_atual = str(u.get('papel', 'CATEQUISTA'))
                    turmas_atuais = str(u.get('turma_vinculada', ''))
                    session_id_atual = str(u.iloc[12]) if len(u) > 12 else ""

                    dados_up =[
                        ed_nome, u['email'], ed_senha, papel_atual, turmas_atuais, 
                        ed_tel, ed_nasc.strftime('%d/%m/%Y'), str_ini, str_bat, str_euc, str_cri, str_min, 
                        session_id_atual, ed_emergencia
                    ]
                    
                    nome_cat_original = str(u.get('nome', ''))
                    
                    if atualizar_usuario(u['email'], dados_up):
                        with st.spinner("Atualizando seu perfil e sincronizando histórico..."):
                            if ed_nome != nome_cat_original:
                                from database import sincronizar_renomeacao_catequista
                                sincronizar_renomeacao_catequista(nome_cat_original, ed_nome)
                                # Atualiza o nome na sessão atual para refletir na barra lateral imediatamente
                                st.session_state.usuario['nome'] = ed_nome
                                
                        st.success("✅ Seus dados foram atualizados com sucesso!"); st.cache_data.clear(); time.sleep(1); st.rerun()

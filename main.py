import streamlit as st
import pandas as pd
import gspread
from datetime import date, datetime, timedelta, timezone
import database as db
import ai_engine as ai
import utils as util
import time
import os
import plotly.express as px
import exporter
import re

# --- CONFIGURAÇÃO DE ALTA PERFORMANCE (BRANDING EXCLUSIVO) ---
st.set_page_config(
    page_title="Ronaldo Gomes", 
    layout="wide", 
    page_icon="💻", # Ícone da aba atualizado para 💻
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE BLINDAGEM E PERSISTÊNCIA (6 HORAS) ---
def check_password():
    """Gerencia o acesso com botão de entrada explícito e persistência de 6h."""
    
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if "login_timestamp" not in st.session_state:
        st.session_state["login_timestamp"] = None

    # Verifica se a sessão de 6h ainda é válida
    if st.session_state["password_correct"]:
        tempo_decorrido = time.time() - st.session_state["login_timestamp"]
        if tempo_decorrido < 21600: # 6 horas
            return True
        else:
            st.session_state["password_correct"] = False
            st.warning("Sessão expirada. Por favor, entre novamente.")

    # INTERFACE DE LOGIN (Design Responsivo e Limpo)
    _, col_login, _ = st.columns([1, 2, 1]) 
    
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: 
            st.image("logo.png", width=180) 
        except: 
            st.markdown("<h1 style='text-align: center;'>Ronaldo Gomes</h1>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>🔐 Portal de Soberania</h3>", unsafe_allow_html=True)
        
        # FORMULÁRIO DE LOGIN
        with st.form("login_portal"):
            input_password = st.text_input("Chave de Acesso:", type="password", placeholder="Digite sua chave...")
            st.checkbox("Manter conectado por 6 horas", value=True, disabled=True)
            
            btn_entrar = st.form_submit_button("ENTRAR NO PAINEL", use_container_width=True)
            
            if btn_entrar:
                if input_password == "2496":
                    st.session_state["password_correct"] = True
                    st.session_state["login_timestamp"] = time.time()
                    st.success("Acesso Autorizado!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Chave incorreta. Acesso negado.")
        
        st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>Sistema restrito ao Prof. Ronaldo Gomes (Itabuna/BA)</p>", unsafe_allow_html=True)
    
    return False

if not check_password():
    st.stop()

# --- LÓGICA DE AUTO-ATUALIZAÇÃO ---
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = time.time()

if time.time() - st.session_state.last_sync > 600:
    st.cache_data.clear()
    st.session_state.last_sync = time.time()

# --- ESTILIZAÇÃO DE LUXO (CSS V40) ---
BRAND_BLUE = "#2962FF"
BRAND_NAVY = "#000B1A"

with st.sidebar:
    tema_selecionado = st.radio("Visual do Sistema:", ["🌙 Dark Mode", "🌞 Light Mode"], horizontal=True)

if tema_selecionado == "🌙 Dark Mode":
    cor_fundo, cor_texto, cor_sidebar, cor_card = BRAND_NAVY, "#FFFFFF", "#001226", "#001E3C"
    cor_borda = "#003366"
else:
    cor_fundo, cor_texto, cor_sidebar, cor_card = "#F8FAFC", "#1A202C", "#FFFFFF", "#FFFFFF"
    cor_borda = "#E2E8F0"

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
        * {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
        .stApp {{ background-color: {cor_fundo} !important; color: {cor_texto} !important; }}
        [data-testid="stSidebar"] {{ background-color: {cor_sidebar} !important; border-right: 1px solid {cor_borda}; }}
        div[data-testid="stMetric"] {{ background: {cor_card} !important; border: 1px solid {cor_borda} !important; border-radius: 20px !important; }}
        .stButton button {{ background: linear-gradient(135deg, {BRAND_BLUE}, #0039CB) !important; color: white !important; border-radius: 12px !important; font-weight: 700 !important; width: 100%; }}
        .clock-container {{ background: {BRAND_BLUE}15; color: {BRAND_BLUE}; padding: 8px 15px; border-radius: 30px; font-weight: 800; font-size: 14px; text-align: center; margin: 10px 0; border: 1px solid {BRAND_BLUE}33; }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: IDENTIDADE E NAVEGAÇÃO ---
with st.sidebar:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        try: st.image("logo.png", width=120)
        except: pass
    
    st.markdown(f"<h2 style='text-align: center; font-size: 22px; margin-top: 10px;'>Ronaldo Gomes</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 12px; color: {BRAND_BLUE}; font-weight: 800; margin-top: -15px; letter-spacing: 1px;'>SOBERANIA PEDAGÓGICA</p>", unsafe_allow_html=True)

    # Relógio Automático (Brasília)
    fuso_br = timezone(timedelta(hours=-3))
    hora_atual = datetime.now(fuso_br).strftime("%H:%M:%S")
    data_atual = datetime.now(fuso_br).strftime("%d/%m/%Y")
    
    st.markdown(f"""<div class="clock-container">🕒 {hora_atual} | 📅 {data_atual}</div>""", unsafe_allow_html=True)
    st.markdown("---")

    menu = st.radio("Navegação Estratégica:", [
        "📅 Planejamento (Ponto ID)",
        "🧪 Criador de Aulas",
        "📝 Central de Avaliações",
        "📸 Scanner de Gabaritos",
        "📝 Diário de Bordo Rápido",
        "👤 Biografia do Estudante",
        "📊 Painel de Notas & Vistos",
        "📈 Boletim Anual & Conselho",
        "👥 Gestão da Turma",
        "📚 Base de Conhecimento",
        "♿ Relatórios PEI / Perfil IA"
    ])

    st.markdown("<br>" * 2, unsafe_allow_html=True)
    st.markdown("---")
    
    # BOTÕES DE RODAPÉ (SYNC E SAIR)
    col_sync, col_exit = st.columns(2)
    with col_sync:
        if st.button("🔄 Sync"):
            st.cache_data.clear()
            st.rerun()
    with col_exit:
        if st.button("🚪 Sair"):
            st.session_state["password_correct"] = False
            st.session_state["login_timestamp"] = None
            st.rerun()

    # Rodapé atualizado conforme ordem soberana
    st.caption("Ronaldo Gomes | © 2026")

# --- CARREGAMENTO DE DADOS ---
wb, (df_alunos, df_curriculo, df_materiais, df_planos, df_aulas, df_notas, df_diario, df_turmas, df_relatorios, df_horarios, df_registro_aulas, df_diagnosticos) = db.carregar_tudo()



# --- FUNÇÕES AUXILIARES ---
def prensa_hidraulica_texto(texto, label):
    limpo = texto.replace(label, "").replace(label.upper(), "").replace(label.lower(), "")
    if limpo.startswith(":") or limpo.startswith(" :"):
        limpo = limpo.split(":", 1)[-1]
    return limpo.strip()

# ==============================================================================
# FUNÇÃO AUXILIAR DE VISUALIZAÇÃO HÍBRIDA (VERSÃO V25.11 - CONTEXTUAL)
# ==============================================================================
# --- FUNÇÃO DE VISUALIZAÇÃO V25.85 ---
def exibir_material_estruturado(texto_raw, key_prefix, dados_plano=None, info_aula=None):
    """
    Versão V25.90: Híbrida e Blindada. 
    Detecta automaticamente se é PLANEJAMENTO ou AULA.
    """
    if info_aula is None: info_aula = {}
    
    # Extração de Metadados
    f_aula = info_aula.get("aula", "Aula Geral")
    f_ano = info_aula.get("ano", "6")
    f_semana = info_aula.get("semana", "Semana Geral")
    f_trimestre = info_aula.get("trimestre", "I Trimestre")
    f_categoria = f"{f_ano}ano" # Formato esperado pelo Apps Script

    # --- LÓGICA DE DETECÇÃO DE CONTEÚDO ---
    if dados_plano:
        # MODO PLANEJAMENTO: Usa as tags MARKER_
        ed_met = ai.extrair_tag(texto_raw, "METODOLOGIA")
        ed_obj = ai.extrair_tag(texto_raw, "OBJETIVOS_ENSINO")
        ed_ava = ai.extrair_tag(texto_raw, "AVALIACAO")
        ed_pei_plan = ai.extrair_tag(texto_raw, "ADAPTACAO_PEI")
        
        t1, t2, t3, t4, t_exp = st.tabs(["🏫 Metodologia", "🎯 Objetivos", "📝 Avaliação", "♿ PEI", "📥 EXPORTAR/SYNC"])
        
        with t1: st.text_area("Roteiro das Aulas:", ed_met, height=400, key=f"{key_prefix}_met")
        with t2: st.text_area("Objetivos Curriculares:", ed_obj, height=400, key=f"{key_prefix}_obj")
        with t3: st.text_area("Critérios de Avaliação:", ed_ava, height=200, key=f"{key_prefix}_ava")
        with t4: st.text_area("Adaptação PEI (Plano):", ed_pei_plan, height=300, key=f"{key_prefix}_pei_plan")
        
        modo_sync = "PLANEJAMENTO"
        nome_base = f"PLANO_{f_ano}ANO_{f_semana.replace(' ', '')}"
        # No planejamento, o 'ed_prof' para o banco será o próprio texto do plano
        ed_prof_para_banco = texto_raw 

    else:
        # MODO CRIADOR DE AULAS: Usa as tags [PROFESSOR] e [ALUNO]
        ed_prof = ai.extrair_tag(texto_raw, "PROFESSOR")
        ed_alu = ai.extrair_tag(texto_raw, "ALUNO")
        
        t1, t2, t3, t4, t5, t_exp = st.tabs(["✍️ Lousa", "📄 Folha", "✅ Gabarito", "🎨 Imagens", "♿ PEI", "📥 EXPORTAR/SYNC"])
        
        with t1: st.text_area("Esquema de Lousa:", ed_prof, height=400, key=f"{key_prefix}_lousa")
        with t2: st.text_area("Folha do Aluno:", ed_alu, height=400, key=f"{key_prefix}_folha")
        with t3: st.text_area("Gabarito:", ai.extrair_tag(texto_raw, "GABARITO"), height=200, key=f"{key_prefix}_gab")
        with t4: st.text_area("Prompts de Imagem:", ai.extrair_tag(texto_raw, "IMAGENS"), height=150, key=f"{key_prefix}_img")
        
        with t5:
            st.subheader("♿ Adaptação PEI (Material)")
            if "lab_pei" not in st.session_state:
                if st.button("♿ GERAR ADAPTAÇÃO PEI", use_container_width=True, key=f"{key_prefix}_gen_pei"):
                    st.session_state.lab_pei = ai.gerar_ia("ARQUITETO_PEI_V24", f"ADAPTE: {ed_alu}")
                    st.rerun()
            else:
                st.session_state.lab_pei = st.text_area("PEI:", st.session_state.lab_pei, height=400, key=f"{key_prefix}_pei_area")
        
        modo_sync = "AULA"
        nome_base = f"AULA_{f_aula.replace(' ','')}_{f_ano}ANO_{datetime.now().strftime('%d%m')}"
        ed_prof_para_banco = ed_prof

# --- ABA DE EXPORTAÇÃO E SINCRONIA (UNIFICADA V25.96) ---
    with t_exp:
        st.subheader("🚀 Sincronia de Elite SOSA")
        
        # Definição do nome base para os arquivos
        if modo_sync == "PLANEJAMENTO":
            nome_base = f"PLANO_{f_ano}ANO_{f_semana.replace(' ', '')}"
        else:
            nome_base = f"AULA_{f_aula.replace(' ','')}_{f_ano}ANO_{datetime.now().strftime('%d%m')}"

        if st.button("☁️ SINCRONIZAR TUDO NO DRIVE E BANCO", use_container_width=True, type="primary", key=f"{key_prefix}_btn_sync"):
            with st.status("Iniciando Protocolo de Sincronia e Limpeza...", expanded=True) as status:
                
                # 1. LÓGICA ANTI-DUPLICIDADE (UPSERT)
                status.write("🧹 Verificando e removendo versões obsoletas...")
                if modo_sync == "PLANEJAMENTO":
                    filtro = df_planos[(df_planos['SEMANA'] == f_semana) & (df_planos['ANO'] == f"{f_ano}º")]
                    for _, row_antiga in filtro.iterrows():
                        db.excluir_registro_com_drive("DB_PLANOS", row_antiga['PLANO_TEXTO'])
                else:
                    filtro = df_aulas[(df_aulas['SEMANA_REF'] == f_semana) & (df_aulas['TIPO_MATERIAL'].str.contains(f_aula))]
                    for _, row_antiga in filtro.iterrows():
                        db.excluir_registro_com_drive("DB_AULAS_PRONTAS", row_antiga['CONTEUDO'])

                # 2. PROCESSAMENTO POR MODO
                if modo_sync == "PLANEJAMENTO":
                    # Geração do DOCX do Plano
                    doc_plano = exporter.gerar_docx_plano_pedagogico_ELITE(nome_base, dados_plano, {"ano": f"{f_ano}º", "semana": f_semana, "trimestre": f_trimestre})
                    
                    status.write("📤 Enviando Novo Plano para a Hierarquia Oficial...")
                    link = db.subir_e_converter_para_google_docs(doc_plano, nome_base, trimestre=f_trimestre, categoria=f"{f_ano}º Ano", semana=f_semana, modo="PLANEJAMENTO")
                    
                    if "https" in str(link):
                        final_txt = (
                            f"MARKER_CONTEUDO_GERAL {dados_plano['geral']} \n"
                            f"MARKER_CONTEUDOS_ESPECIFICOS {dados_plano['especificos']} \n"
                            f"MARKER_OBJETIVOS_ENSINO {dados_plano['objetivos']} \n"
                            f"MARKER_METODOLOGIA {dados_plano['metodologia']} \n"
                            f"MARKER_AVALIACAO {dados_plano['avaliacao']} \n"
                            f"MARKER_ADAPTACAO_PEI {dados_plano['pei']} \n"
                            f"MARKER_MODALIDADE {info_aula.get('modalidade', 'MANUAL')} \n"
                            f"--- LINK DRIVE --- {link}"
                        )
                        
                        sucesso = db.salvar_no_banco("DB_PLANOS", [datetime.now().strftime("%d/%m/%Y"), f_semana, f"{f_ano}º", f_trimestre, "PADRÃO", final_txt, link])
                        if sucesso:
                            status.update(label="✅ Plano Sincronizado!", state="complete")
                            st.balloons()
                    else:
                        status.update(label="❌ Falha na Ponte Google.", state="error")
                        st.error(link)

                else:
                    # MODO AULA (CRIADOR DE AULAS)
                    status.write("📄 Gerando Materiais (Fluxo Nativo)...")
                    doc_alu = exporter.gerar_docx_aluno_v24(nome_base, ed_alu, {"ano": f"{f_ano}º", "trimestre": f_trimestre})
                    doc_prof = exporter.gerar_docx_professor_v25(nome_base, ed_prof, {"ano": f"{f_ano}º", "semana": f_semana, "trimestre": f_trimestre})
                    
                    status.write("📤 Enviando Material do Aluno...")
                    link_alu = db.subir_e_converter_para_google_docs(doc_alu, f"{nome_base}_ALUNO", trimestre=f_trimestre, categoria=f_categoria, semana=f_semana, modo="AULA")
                    
                    status.write("📤 Enviando Guia do Professor...")
                    link_prof = db.subir_e_converter_para_google_docs(doc_prof, f"{nome_base}_PROF", trimestre=f_trimestre, categoria=f_categoria, semana=f_semana, modo="AULA")
                    
                    link_pei = "N/A"
                    if "lab_pei" in st.session_state:
                        status.write("♿ Enviando Material PEI Adaptado...")
                        doc_pei = exporter.gerar_docx_pei_v25(f"{nome_base}_PEI", st.session_state.lab_pei, {"ano": f"{f_ano}º", "trimestre": f_trimestre})
                        link_pei = db.subir_e_converter_para_google_docs(doc_pei, f"{nome_base}_PEI", trimestre=f_trimestre, categoria=f_categoria, semana=f_semana, modo="AULA")

                    if "https" in str(link_alu) and "https" in str(link_prof):
                        # CONTEÚDO ESTRUTURADO PARA AULAS (Sem variáveis de prova)
                        conteudo_banco = f"[PROFESSOR]\n{ed_prof}\n\n[ALUNO]\n{ed_alu}\n\n--- LINKS ---\nAluno({link_alu}) Prof({link_prof}) PEI({link_pei})"
                        
                        db.salvar_no_banco("DB_AULAS_PRONTAS", [
                            datetime.now().strftime("%d/%m/%Y"), f_semana, f"{f_aula}", conteudo_banco, f"{f_ano}º", link_alu
                        ])
                        status.update(label="✅ Aula Sincronizada!", state="complete")
                        st.balloons()
                    else:
                        status.update(label="❌ Erro no Upload da Aula.", state="error")
                        st.error(f"Falha no envio dos arquivos.")
                       

# ==============================================================================
# MÓDULO: PLANEJAMENTO ESTRATÉGICO (PONTO ID) - VERSÃO V100 (CLEAN & UX)
# ==============================================================================
if menu == "📅 Planejamento (Ponto ID)":
    st.title("📅 Ponto ID: Engenharia de Planejamento")
    st.markdown("---")
    st.caption("💡 **Guia de Comando:** Este é o cérebro do ecossistema. O planejamento gerado aqui define a rota da semana e alimenta automaticamente o *Criador de Aulas* e o *Diário de Bordo*.")

    def reset_planejamento():
        keys_to_clear =["p_temp", "refino_ativo", "p_meta", "chat_history_ponto_id"]
        for k in keys_to_clear:
            if k in st.session_state: del st.session_state[k]
        st.session_state.v_plano = int(time.time())
        st.rerun()

    if "v_plano" not in st.session_state: 
        st.session_state.v_plano = int(time.time())
    v = st.session_state.v_plano 

    tab_gerar, tab_producao, tab_acervo, tab_matriz, tab_auditoria = st.tabs([
        "🚀 1. Criar Novo Plano", "🏗️ 2. Hub de Produção", "📂 3. Acervo (PIP)", "📖 4. Matriz Curricular", "📈 5. Auditoria"
    ])
    
    with tab_gerar:
        # --- 🛡️ 1. STATUS E NATUREZA ---
        with st.container(border=True):
            st.markdown("### 🛡️ Passo 1: Natureza Pedagógica da Semana")
            st.info("Defina o objetivo principal desta semana. Isso mudará completamente a forma como a IA escreve o roteiro.")
            
            cg1, cg2, cg3 = st.columns([1.5, 1, 1])
            tipo_semana = cg1.selectbox("DNA da Semana:",[
                "📗 Aula de Safra (Regular)", "📝 Aplicação de Exame", 
                "🔥 Revisão & Recomposição", "📋 Trabalho Investigativo", "🔍 Sonda de Proficiência",
                "💡 Aula Aberta (Dinâmicas e Eventos)"
            ], help="Safra: Conteúdo novo. Exame: Foco em logística de prova. Revisão: Foco em correção de lacunas.", key=f"gate_tipo_{v}")
            
            tem_sabado = cg2.toggle("Sábado Letivo?", help="Ative se houver reposição no sábado. A IA gerará uma atividade extra.", key=f"gate_sab_{v}")
            carga_horaria = cg3.select_slider("Aulas Úteis na Semana:", options=["1 Aula", "2 Aulas", "3 Aulas"], value="2 Aulas", help="Quantos encontros você terá com a turma nesta semana?", key=f"gate_carga_{v}")

        # --- ⚙️ 2. PARÂMETROS E SMART MATCH ---
        with st.container(border=True):
            st.markdown("### ⚙️ Passo 2: Parâmetros de Regência e Vínculo")
            
            ctx_ia = ""
            strat = ""
            ctx_ativo_vinculado = ""
            uri_livro_drive = None
            base_didatica_info = "Matriz Curricular de Itabuna"
            
            c1, c2, c3 = st.columns([1, 2, 1.5])
            ano_p = c1.selectbox("Série/Ano Alvo:",[6, 7, 8, 9], index=0, key=f"ano_sel_{v}")
            ano_str_busca = f"{ano_p}º"
            ano_matriz_busca = ano_p # Por padrão, busca a matriz da própria série

            # LÓGICA BLINDADA: FILTRO DE SEMANAS PENDENTES
            todas_semanas = util.gerar_semanas()
            semanas_planejadas = df_planos[df_planos['ANO'] == ano_str_busca]['SEMANA'].tolist()
            semanas_disponiveis =[s for s in todas_semanas if s.split(" (")[0] not in semanas_planejadas]

            if not semanas_disponiveis:
                st.success(f"🏆 **Soberania Total!** Todas as semanas do ano letivo para o {ano_p}º Ano já foram planejadas.")
                if st.button("🔄 REVER ACERVO"): st.rerun()
                st.stop()

            sem_p = c2.selectbox("📅 Semana de Referência (Apenas Pendentes):", semanas_disponiveis, help="O sistema oculta automaticamente as semanas já planejadas.", key=f"sem_sel_{v}")
            sem_limpa = sem_p.split(" (")[0]
            trim_atual = sem_p.split(" - ")[1] if " - " in sem_p else "I Trimestre"

            # ==============================================================================
            # 🚨 MÁQUINA DO TEMPO CURRICULAR E SMART MATCH
            # ==============================================================================
            if tipo_semana == "🔥 Revisão & Recomposição":
                st.markdown("---")
                foco_rr = st.radio("Estratégia de Intervenção:",["🔄 Revisão Guiada (Vincular Material)", "🛠️ Recomposição de Base (Máquina do Tempo)"], horizontal=True, key=f"foco_rr_{v}")
                
                if "Revisão" in foco_rr:
                    df_ativos_ano = df_aulas[df_aulas['ANO'] == ano_str_busca]
                    opcoes_ativos = df_ativos_ano[df_ativos_ano['SEMANA_REF'].isin(["REVISÃO", "AVALIAÇÃO"])]['TIPO_MATERIAL'].tolist()
                    if opcoes_ativos:
                        ativo_sel = st.selectbox("🔗 Vincular Material Base (Prova ou Lista):", [""] + opcoes_ativos, key=f"ativo_match_{v}")
                        if ativo_sel:
                            dados_ativo = df_ativos_ano[df_ativos_ano['TIPO_MATERIAL'] == ativo_sel].iloc[0]
                            ctx_ativo_vinculado = f"--- ATIVO VINCULADO: {ativo_sel} ---\nCONTEÚDO: {dados_ativo['CONTEUDO']}"
                            
                            # Radar de Diagnóstico Ativo
                            with st.expander(f"📡 Radar de Diagnóstico Ativo (Série: {ano_p}º Ano)", expanded=True):
                                st.markdown(f"**Analisando dados de todas as turmas do {ano_p}º Ano para {ativo_sel}...**")
                                
                                alunos_rad = df_alunos[df_alunos['TURMA'].str.contains(str(ano_p))].copy()
                                perfil_txt = ""
                                if not alunos_rad.empty:
                                    def categorizar_aluno(nec):
                                        n = str(nec).upper().strip()
                                        if "PENDENTE" in n or "SUSPEITA" in n: return "Radar"
                                        if "DEFASAGEM LEITURA" in n: return "Barreira de Leitura"
                                        if "DEFASAGEM MATEMÁTICA" in n or "DEFASAGEM MATEMATICA" in n: return "Defasagem Matemática"
                                        if "ALTA PERFORMANCE" in n: return "Alta Performance"
                                        if n in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]: return "Típico"
                                        return "PEI" 
                                    
                                    alunos_rad['PERFIL'] = alunos_rad['NECESSIDADES'].apply(categorizar_aluno)
                                    contagem = alunos_rad['PERFIL'].value_counts(normalize=True) * 100
                                    
                                    perfis_relevantes =[]
                                    if "Barreira de Leitura" in contagem: perfis_relevantes.append(f"{contagem['Barreira de Leitura']:.0f}% com Barreira de Leitura 🧱")
                                    if "Defasagem Matemática" in contagem: perfis_relevantes.append(f"{contagem['Defasagem Matemática']:.0f}% com Defasagem Matemática 🧮")
                                    if "PEI" in contagem: perfis_relevantes.append(f"{contagem['PEI']:.0f}% de Inclusão Oficial ♿")
                                    
                                    if perfis_relevantes:
                                        perfil_txt = " | ".join(perfis_relevantes)
                                        st.warning(f"**Perfil Cognitivo da Série:** {perfil_txt}")
                                    else:
                                        st.success("**Perfil Cognitivo da Série:** Maioria Típica/Padrão.")
                                
                                lacunas_txt = ""
                                nome_curto_av = ativo_sel.split("-")[0].strip().replace(" (2ª CHAMADA)", "")
                                diag_t = df_diagnosticos[(df_diagnosticos['TURMA'].str.contains(str(ano_p))) & (df_diagnosticos['ID_AVALIACAO'].str.contains(nome_curto_av, case=False, na=False))]
                                
                                if not diag_t.empty:
                                    txt_prova = str(dados_ativo['CONTEUDO'])
                                    gab_raw = ai.extrair_tag(txt_prova, "GABARITO_TEXTO") or ai.extrair_tag(txt_prova, "GABARITO")
                                    grade_raw = ai.extrair_tag(txt_prova, "GRADE_DE_CORRECAO")
                                    
                                    if gab_raw and grade_raw:
                                        matches = re.findall(r"(\d+)[\s\.\)\-:]+([A-E])", gab_raw.upper())
                                        gab_oficial = {int(num): letra for num, letra in matches}
                                        if not gab_oficial:
                                            letras = re.findall(r"\b[A-E]\b", gab_raw.upper())
                                            # CORREÇÃO DO PYLANCE APLICADA AQUI
                                            gab_oficial = {i+1: letra for i, letra in enumerate(letras)}
                                            
                                        respostas_alunos = diag_t['RESPOSTAS_ALUNO'].astype(str).tolist()
                                        
                                        lacunas_stats =[]
                                        for q_num, letra_certa in gab_oficial.items():
                                            acertos = 0
                                            validos = 0
                                            for resp in respostas_alunos:
                                                if resp == "FALTOU": continue
                                                resp_lista = resp.split(";")
                                                if len(resp_lista) >= q_num:
                                                    validos += 1
                                                    if resp_lista[q_num-1] == letra_certa:
                                                        acertos += 1
                                            
                                            if validos > 0:
                                                taxa_acerto = acertos / validos
                                                if taxa_acerto < 0.6: 
                                                    padrao_h = rf"(?si)QUEST[AÃ]O\s*0?{q_num}\b.*?(?:\[)(.*?)(?:\])"
                                                    m_h = re.search(padrao_h, grade_raw)
                                                    habilidade = m_h.group(1).strip() if m_h else f"Revisar conceito da Questão {q_num}"
                                                    lacunas_stats.append({"q": q_num, "taxa": taxa_acerto, "hab": habilidade})
                                        
                                        if lacunas_stats:
                                            top_lacunas = sorted(lacunas_stats, key=lambda x: x['taxa'])[:3]
                                            st.error("🚨 **Top 3 Lacunas Críticas da Série:**")
                                            lacunas_str_list =[]
                                            for lac in top_lacunas:
                                                st.markdown(f"**Q{lac['q']} ({lac['taxa']*100:.0f}% de acerto):** {lac['hab']}")
                                                lacunas_str_list.append(f"Questão {lac['q']} ({lac['taxa']*100:.0f}% acerto) - Habilidade: {lac['hab']}")
                                            
                                            lacunas_txt = "\n".join(lacunas_str_list)
                                        else:
                                            st.success("✅ Nenhuma questão com menos de 60% de acerto na série.")
                                else:
                                    st.info("Nenhum gabarito escaneado para esta série nesta avaliação.")
                                
                                if lacunas_txt or perfil_txt:
                                    strat = f"--- DADOS DE DIAGNÓSTICO DA SÉRIE ({ano_p}º ANO) ---\n"
                                    if perfil_txt: strat += f"PERFIL COGNITIVO GERAL: {perfil_txt}\n"
                                    if lacunas_txt: strat += f"LACUNAS CRÍTICAS (Foque a revisão nestes pontos):\n{lacunas_txt}\n"
                                    strat += "🚨 DIRETRIZ DE RECOMPOSIÇÃO: Não revise a prova inteira. Foque EXCLUSIVAMENTE nas lacunas apontadas acima. Adapte a linguagem e as dinâmicas para o perfil cognitivo geral da série."
                else:
                    ano_origem_rec = st.selectbox("Série de Origem da Defasagem (Matriz Base):",[1, 2, 3, 4, 5, 6, 7, 8, 9], index=max(0, ano_p - 2), key=f"ano_rec_{v}")
                    ano_matriz_busca = ano_origem_rec
                    st.info(f"💡 **Máquina do Tempo Ativada:** A IA usará a Matriz Curricular do **{ano_origem_rec}º Ano** para planejar esta aula de resgate para a turma do **{ano_p}º Ano**.")

            elif tipo_semana not in["📗 Aula de Safra (Regular)", "💡 Aula Aberta (Dinâmicas e Eventos)"]:
                df_ativos_ano = df_aulas[df_aulas['ANO'] == ano_str_busca]
                opcoes_ativos =[]
                if "Exame" in tipo_semana: opcoes_ativos = df_ativos_ano[df_ativos_ano['SEMANA_REF'] == "AVALIAÇÃO"]['TIPO_MATERIAL'].tolist()
                elif "Trabalho" in tipo_semana: opcoes_ativos = df_ativos_ano[df_ativos_ano['TIPO_MATERIAL'].str.contains("PROJETO|TRABALHO", case=False, na=False)]['TIPO_MATERIAL'].tolist()
                else: opcoes_ativos = df_ativos_ano[df_ativos_ano['TIPO_MATERIAL'].str.contains("SONDA|DIAGNÓSTICA", case=False, na=False)]['TIPO_MATERIAL'].tolist()

                if opcoes_ativos:
                    ativo_sel = st.selectbox("🔗 Vincular Material Existente (Smart Match):", [""] + opcoes_ativos, key=f"ativo_match_{v}")
                    if ativo_sel:
                        dados_ativo = df_ativos_ano[df_ativos_ano['TIPO_MATERIAL'] == ativo_sel].iloc[0]
                        ctx_ativo_vinculado = f"--- ATIVO VINCULADO: {ativo_sel} ---\nCONTEÚDO: {dados_ativo['CONTEUDO']}"

            st.markdown("---")
            modo_p = c3.radio("📚 Método de Base Didática:",["📖 Livro Didático", "🎛️ Manual (Matriz)"], horizontal=True, help="Livro: A IA lê o PDF do seu cofre. Manual: A IA usa apenas a Matriz Curricular.", key=f"modo_p_{v}")
            
            # --- SEÇÃO DE PARÂMETROS (MODO MANUAL / BANCO) ---
            if modo_p == "🎛️ Manual (Matriz)":
                if tipo_semana == "💡 Aula Aberta (Dinâmicas e Eventos)":
                    st.markdown("#### 💡 Engenharia Reversa (Aula Aberta)")
                    st.info("Descreva o evento (ex: Palestra sobre Dengue). A IA varrerá a Matriz e fará o alinhamento curricular automaticamente para justificar a aula.")
                    desc_evento = st.text_area("Contexto do Evento:", placeholder="Ex: Palestra da prefeitura sobre a Dengue no pátio...", height=100, key=f"p_evento_{v}")
                    ctx_ia = f"MODO AULA ABERTA. EVENTO DESCRITO: {desc_evento}. MISSÃO: Faça engenharia reversa na matriz para justificar este evento."
                else:
                    st.markdown("#### 🎯 Curadoria da Matriz de Itabuna")
                    dist_manual = st.radio("Distribuição de Conteúdo:",["Integrar Aula 1 e 2", "Definir Trilhas Individuais (Aula 1 / Aula 2)"], 
                        horizontal=True, help="Integrar: A IA divide o conteúdo logicamente. Trilhas: Você escolhe o que entra em cada dia.", key=f"dist_m_{v}")

                    # 🚨 Usa a variável ano_matriz_busca (que pode ser do ano atual ou do ano de recomposição)
                    df_matriz_ano = df_curriculo[df_curriculo['ANO'].astype(str) == str(ano_matriz_busca)]
                    
                    if "Trilhas Individuais" in dist_manual:
                        with st.expander("📘 TRILHA 01: Foco da Aula 1", expanded=True):
                            c1a, c1b = st.columns(2)
                            eixo_1 = c1a.multiselect("1. Eixo (Aula 1):", sorted(df_matriz_ano['EIXO'].unique().tolist()), key=f"e1_{v}")
                            cont_1 = c1b.multiselect("2. Conteúdo (Aula 1):", sorted(df_matriz_ano[df_matriz_ano['EIXO'].isin(eixo_1)]['CONTEUDO_ESPECIFICO'].unique().tolist()) if eixo_1 else[], key=f"c1_{v}")
                            obj_1 = st.multiselect("3. Objetivos (Aula 1):", sorted(df_matriz_ano[df_matriz_ano['CONTEUDO_ESPECIFICO'].isin(cont_1)]['OBJETIVOS'].unique().tolist()) if cont_1 else[], key=f"o1_{v}")
                        
                        with st.expander("📗 TRILHA 02: Foco da Aula 2", expanded=(carga_horaria != "1 Aula")):
                            if carga_horaria == "1 Aula":
                                st.warning("Carga horária de 1 aula selecionada. Trilha 2 desativada.")
                                ctx_ia = f"AULA 1: Eixo {eixo_1}, Conteúdo {cont_1}, Objetivos {obj_1}."
                            else:
                                c2a, c2b = st.columns(2)
                                eixo_2 = c2a.multiselect("1. Eixo (Aula 2):", sorted(df_matriz_ano['EIXO'].unique().tolist()), key=f"e2_{v}")
                                cont_2 = c2b.multiselect("2. Conteúdo (Aula 2):", sorted(df_matriz_ano[df_matriz_ano['EIXO'].isin(eixo_2)]['CONTEUDO_ESPECIFICO'].unique().tolist()) if eixo_2 else[], key=f"c2_{v}")
                                obj_2 = st.multiselect("3. Objetivos (Aula 2):", sorted(df_matriz_ano[df_matriz_ano['CONTEUDO_ESPECIFICO'].isin(cont_2)]['OBJETIVOS'].unique().tolist()) if cont_2 else[], key=f"o2_{v}")
                                ctx_ia = f"TRILHA 1 (AULA 1): Eixo {eixo_1}, Conteúdo {cont_1}, Objetivos {obj_1}. \nTRILHA 2 (AULA 2): Eixo {eixo_2}, Conteúdo {cont_2}, Objetivos {obj_2}."
                    else:
                        sel_eixo = st.multiselect("1. Eixo (Semana):", sorted(df_matriz_ano['EIXO'].unique().tolist()), key=f"p_eixo_{v}")
                        sel_cont = st.multiselect("2. Conteúdo (Semana):", sorted(df_matriz_ano[df_matriz_ano['EIXO'].isin(sel_eixo)]['CONTEUDO_ESPECIFICO'].unique().tolist()) if sel_eixo else[], key=f"p_cont_{v}")
                        sel_obj = st.multiselect("3. Objetivos (Semana):", sorted(df_matriz_ano[df_matriz_ano['CONTEUDO_ESPECIFICO'].isin(sel_cont)]['OBJETIVOS'].unique().tolist()) if sel_cont else[], key=f"p_obj_{v}")
                        ctx_ia = f"MODO INTEGRADO: EIXO: {sel_eixo}, CONTEÚDO: {sel_cont}, OBJETIVOS: {sel_obj}."
            else:
                st.markdown("#### 📖 Extração Direta do Livro Didático")
                cx1, cx2 = st.columns([2, 1])
                livros_disponiveis = df_materiais[df_materiais['TIPO'].str.contains(str(ano_matriz_busca), na=False)]['NOME_ARQUIVO'].tolist()
                sel_mat = cx1.selectbox("Selecionar Livro do Cofre Digital:",[""] + livros_disponiveis, key=f"p_livro_{v}")
                
                pags = cx2.text_input("Páginas Alvo:", placeholder="Ex: 14-23 ; 45-50", help="Use ';' para separar capítulos. A IA usará a 1ª parte na Aula 1 e a 2ª parte na Aula 2.", key=f"p_pags_{v}")
                
                if sel_mat:
                    match_mat = df_materiais[df_materiais['NOME_ARQUIVO'] == sel_mat].iloc[0]
                    uri_livro_drive = match_mat['URI_ARQUIVO']
                    base_didatica_info = f"Livro: {sel_mat} | Páginas: {pags}"

        # ==============================================================================
        # 🚨 3. DIRETRIZ SOBERANA (NOVO)
        # ==============================================================================
        with st.container(border=True):
            st.markdown("### ✍️ Passo 3: Diretriz Soberana (Contexto de Regência)")
            st.caption("Dite as regras do jogo. Como você quer que a IA estruture a metodologia, os espaços e as dinâmicas desta semana?")
            diretriz_soberana = st.text_area("Suas ordens para o Maestro:", placeholder="Ex: Quero a Aula 1 no pátio com material dourado. A Aula 2 será em duplas focada em resolução de problemas...", height=100, key=f"dir_sob_{v}")

        # --- BOTÃO DE COMPILAÇÃO ---
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧠 INICIAR MOTOR DE IA: GERAR PLANEJAMENTO", use_container_width=True, type="primary", key=f"btn_compilar_{v}"):
            
            # Limpa o histórico do chat ao gerar um novo plano
            if "chat_history_ponto_id" in st.session_state:
                del st.session_state["chat_history_ponto_id"]
                
            v_ctx_ia = ctx_ia if 'ctx_ia' in locals() else ""
            v_strat = strat if 'strat' in locals() else ""
            v_ctx_ativo = ctx_ativo_vinculado if 'ctx_ativo_vinculado' in locals() else ""
            
            if modo_p == "📖 Livro Didático" and not uri_livro_drive:
                st.error("❌ Erro: O livro selecionado não possui um link válido no banco de materiais.")
            else:
                with st.spinner("Maestro SOSA analisando a Matriz e arquitetando o Plano de Ensino..."):
                    plano_anterior_txt = "Início de Safra. Não há plano anterior."
                    df_hist = df_planos[df_planos['ANO'] == ano_str_busca].sort_values(by='DATA', ascending=False)
                    if not df_hist.empty: 
                        plano_anterior_txt = df_hist.iloc[0]['PLANO_TEXTO']

                    status_sabado_cmd = "ATIVADO (Gere uma oficina/atividade extra)" if tem_sabado else "DESATIVADO (Escreva apenas N/A)"

                    if modo_p == "🎛️ Manual (Matriz)":
                        diretriz_base = "MÉTODO MANUAL: Baseie-se EXCLUSIVAMENTE na Matriz Curricular. É TERMINANTEMENTE PROIBIDO citar livros didáticos ou páginas."
                    else:
                        diretriz_base = f"MÉTODO LIVRO: Use EXCLUSIVAMENTE o PDF anexo como fonte. PÁGINAS ALVO: {base_didatica_info}."

                    prompt = (
                        f"NATUREZA DA SEMANA: {tipo_semana}\n"
                        f"{diretriz_base}\n"
                        f"SÉRIE ALVO: {ano_p}º Ano. SEMANA: {sem_limpa}. TRIMESTRE: {trim_atual}.\n"
                        f"CARGA HORÁRIA: {carga_horaria}.\n"
                        f"SÁBADO LETIVO: {status_sabado_cmd}.\n\n"
                        f"🚨 DIRETRIZ SOBERANA DO PROFESSOR (PRIORIDADE MÁXIMA):\n{diretriz_soberana if diretriz_soberana else 'Siga a estrutura padrão de excelência.'}\n\n"
                        f"🚨 MISSÃO DE DISTRIBUIÇÃO:\n"
                        f"1. Se houver múltiplos intervalos de páginas separados por ';', use o primeiro para a [AULA_1] e o segundo para a [AULA_2].\n"
                        f"2. Extraia os conceitos exatos de cada capítulo/intervalo citado (se for modo livro).\n"
                        f"3. Se a carga for '1 Aula', foque apenas no primeiro intervalo.\n"
                        f"4. Preencha todas as tags [TAG] com densidade acadêmica.\n\n"
                        f"--- PONTE PEDAGÓGICA (MEMÓRIA DA TURMA) ---\nAnalise o plano da semana anterior abaixo para criar o gancho de continuidade na AULA 1:\n{plano_anterior_txt}\n\n"
                        f"--- CONTEXTO DE APOIO E ATIVOS VINCULADOS ---\n{v_strat}\n{v_ctx_ia}\n{v_ctx_ativo}\n"
                        f"--- MATRIZ OFICIAL (ITABUNA) ---\n{df_curriculo[df_curriculo['ANO'].astype(str)==str(ano_matriz_busca)].to_string(index=False)}"
                    )
                    
                    resultado = ai.gerar_ia("PLANE_PEDAGOGICO", prompt, url_drive=uri_livro_drive)
                    
                    st.session_state.p_temp = resultado
                    st.session_state.p_meta = {
                        "semana": sem_limpa, "carga": carga_horaria, 
                        "trimestre": trim_atual, "ano": ano_str_busca,
                        "base": base_didatica_info
                    }
                    st.session_state.v_plano = int(time.time())
                    st.rerun()

        # --- EDITOR E VISUALIZAÇÃO ---
        if "p_temp" in st.session_state:
            txt_bruto = st.session_state.p_temp
            meta = st.session_state.get("p_meta", {})
            
            st.markdown("---")
            with st.container(border=True):
                st.markdown(f"### 📋 Conferência de Regência: **{meta.get('semana')}**")
                cm1, cm2, cm3, cm4 = st.columns([1, 1, 1, 2])
                cm1.metric("Série/Ano", meta.get('ano'))
                cm2.metric("Carga Horária", meta.get('carga'))
                cm3.metric("Trimestre", meta.get('trimestre'))
                cm4.metric("📖 Base Didática", meta.get('base'))

            t_ed, t_vis = st.tabs(["✏️ Editor Manual & Copilot", "👁️ Visão do Documento Final"])
            
            with t_ed:
                # ==============================================================================
                # 🤖 MAESTRO COPILOT (CHATBOT DE REFINO)
                # ==============================================================================
                with st.container(border=True):
                    st.subheader("🤖 Maestro Copilot (Coautoria em Tempo Real)")
                    st.caption("Converse com a IA para ajustar o plano. O editor abaixo será atualizado automaticamente.")
                    
                    if "chat_history_ponto_id" not in st.session_state:
                        st.session_state.chat_history_ponto_id =[{"role": "assistant", "avatar": "🤖", "content": "Saudações, Mestre! O plano base foi gerado. Como deseja refinar a nossa estratégia?"}]
                    
                    chat_container = st.container(height=300)
                    with chat_container:
                        for msg in st.session_state.chat_history_ponto_id:
                            with st.chat_message(msg["role"], avatar=msg["avatar"]):
                                st.markdown(msg["content"])
                    
                    if cmd_refine := st.chat_input("Ex: 'Deixe a Aula 1 mais lúdica' ou 'Foque mais na página 15'...", key=f"chat_refine_{v}"):
                        st.session_state.chat_history_ponto_id.append({"role": "user", "avatar": "💻", "content": cmd_refine})
                        
                        with chat_container:
                            with st.chat_message("user", avatar="💻"):
                                st.markdown(cmd_refine)
                            with st.chat_message("assistant", avatar="🤖"):
                                with st.spinner("Reengenharia em curso..."):
                                    hist_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history_ponto_id[-5:]])
                                    prompt_refino = (
                                        f"HISTÓRICO DA CONVERSA:\n{hist_text}\n\n"
                                        f"ORDEM ATUAL: {cmd_refine}\n\n"
                                        f"PLANO ATUAL PARA REFINAR:\n{st.session_state.p_temp}\n\n"
                                        f"MATRIZ DE REFERÊNCIA:\n{df_curriculo[df_curriculo['ANO'].astype(str)==str(ano_p)].to_string(index=False)}"
                                    )
                                    
                                    resultado_refino = ai.gerar_ia("REFINADOR_PEDAGOGICO", prompt_refino, url_drive=uri_livro_drive)
                                    
                                    msg_chat = ai.extrair_tag(resultado_refino, "MENSAGEM_CHAT")
                                    novo_conteudo = ai.extrair_tag(resultado_refino, "CONTEUDO_ATUALIZADO")
                                    
                                    if not novo_conteudo: 
                                        novo_conteudo = resultado_refino
                                        msg_chat = "Plano atualizado conforme solicitado, Mestre."
                                        
                                    st.markdown(msg_chat)
                                    st.session_state.chat_history_ponto_id.append({"role": "assistant", "avatar": "🤖", "content": msg_chat})
                                    st.session_state.p_temp = novo_conteudo
                                    st.session_state.v_plano = int(time.time())
                                    st.rerun()

                    if st.button("🗑️ DESCARTAR E RECOMEÇAR", use_container_width=True): reset_planejamento()

                st.markdown("#### 🛡️ Filtros de Curadoria (O que vai para o DOCX?)")
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                keep_objeto = col_f1.checkbox("Objeto de Conhecimento", value=True, key=f"k_obj_{v}")
                keep_conteudo = col_f2.checkbox("Conteúdos Específicos", value=True, key=f"k_cont_{v}")
                keep_objetivos = col_f3.checkbox("Objetivos de Ensino", value=True, key=f"k_objt_{v}")
                keep_justificativa = col_f4.checkbox("Justificativa PHC", value=True, key=f"k_just_{v}")

                st.divider()

                ed_hab = st.text_input("Habilidade/Competência:", ai.extrair_tag(txt_bruto, "HABILIDADE_BNCC") or ai.extrair_tag(txt_bruto, "COMPETENCIA_GERAL"), key=f"ed_h_{v}")
                ed_comp = st.text_input("Competências Foco:", ai.extrair_tag(txt_bruto, "COMPETENCIAS_FOCO"), key=f"ed_c_{v}")
                
                ed_geral = st.text_input("Objeto de Conhecimento:", ai.extrair_tag(txt_bruto, "OBJETO_CONHECIMENTO") or ai.extrair_tag(txt_bruto, "CONTEUDO_GERAL"), key=f"ed_g_{v}") if keep_objeto else "N/A"
                ed_espec = st.text_area("Conteúdos Específicos:", ai.extrair_tag(txt_bruto, "CONTEUDOS_ESPECIFICOS"), key=f"ed_e_{v}") if keep_conteudo else "N/A"
                ed_objs = st.text_area("Objetivos de Aprendizagem:", ai.extrair_tag(txt_bruto, "OBJETIVOS_ENSINO"), key=f"ed_o_{v}") if keep_objetivos else "N/A"
                
                ed_base = st.text_input("📖 Referência de Base (Livro/Páginas):", ai.extrair_tag(txt_bruto, "BASE_DIDATICA") or meta.get('base'), key=f"ed_base_{v}")
                ed_just = st.text_area("Justificativa Pedagógica:", ai.extrair_tag(txt_bruto, "JUSTIFICATIVA_PEDAGOGICA"), key=f"ed_j_{v}") if keep_justificativa else "N/A"
                
                st.markdown("#### 🏫 Roteiro de Aulas")
                ed_a1 = st.text_area("AULA 1:", ai.extrair_tag(txt_bruto, "AULA_1"), height=200, key=f"a1_{v}")
                if "1 Aula" not in meta.get('carga', ''):
                    ed_a2 = st.text_area("AULA 2:", ai.extrair_tag(txt_bruto, "AULA_2"), height=200, key=f"a2_{v}")
                else: ed_a2 = "N/A"
                
                ed_a3 = st.text_area("SÁBADO LETIVO:", ai.extrair_tag(txt_bruto, "SABADO_LETIVO") or "N/A", key=f"ed_a3_{v}")
                ed_ava = st.text_area("Avaliação/Logística:", ai.extrair_tag(txt_bruto, "AVALIACAO_DE_MERITO") or ai.extrair_tag(txt_bruto, "AVALIACAO"), key=f"ed_ava_{v}")
                ed_dua = st.text_area("Estratégia DUA/PEI:", ai.extrair_tag(txt_bruto, "ESTRATEGIA_DUA_PEI") or ai.extrair_tag(txt_bruto, "ADAPTACAO_PEI"), key=f"ed_dua_{v}")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 HOMOLOGAR PLANO E ENVIAR PARA O HUB DE PRODUÇÃO", use_container_width=True, type="primary"):
                    with st.status("Gerando DOCX e Sincronizando com o Google Drive...") as status:
                        final_ano_str = meta.get('ano')
                        nome_arquivo = f"PLANO_{final_ano_str.replace('º','')}_{meta.get('semana').replace(' ', '')}"
                        
                        db.excluir_plano_completo(meta.get('semana'), final_ano_str)
                        
                        dados_docx = {
                            "geral": ed_geral, "especificos": ed_espec, "objetivos": ed_objs, 
                            "recursos": ed_base, 
                            "metodologia": f"JUSTIFICATIVA: {ed_just}\n\nCOMPETÊNCIAS: {ed_comp}\n\nAULA 01:\n{ed_a1}\n\nAULA 02:\n{ed_a2}",
                            "avaliacao": ed_ava, "pei": ed_dua
                        }
                        
                        doc_io = exporter.gerar_docx_plano_pedagogico_ELITE(nome_arquivo, dados_docx, {"ano": final_ano_str, "semana": meta.get('semana'), "trimestre": meta.get('trimestre')})
                        link_drive = db.subir_e_converter_para_google_docs(doc_io, nome_arquivo, trimestre=meta.get('trimestre'), categoria=final_ano_str, semana=meta.get('semana'), modo="PLANEJAMENTO")
                        
                        if "https" in str(link_drive):
                            final_txt = (
                                f"[HABILIDADE_BNCC] {ed_hab} \n[COMPETENCIAS_FOCO] {ed_comp} \n"
                                f"[OBJETO_CONHECIMENTO] {ed_geral} \n[CONTEUDOS_ESPECIFICOS] {ed_espec} \n"
                                f"[OBJETIVOS_ENSINO] {ed_objs} \n[BASE_DIDATICA] {ed_base} \n"
                                f"[JUSTIFICATIVA_PEDAGOGICA] {ed_just} \n"
                                f"[AULA_1] {ed_a1} \n[AULA_2] {ed_a2} \n"
                                f"[SABADO_LETIVO] {ed_a3} \n[AVALIACAO_DE_MERITO] {ed_ava} \n"
                                f"[ESTRATEGIA_DUA_PEI] {ed_dua} \n--- LINK DRIVE --- {link_drive}"
                            )
                            db.salvar_no_banco("DB_PLANOS",[datetime.now().strftime("%d/%m/%Y"), meta.get('semana'), final_ano_str, meta.get('trimestre'), "HUB_ATIVO", final_txt, link_drive])
                            status.update(label="✅ Plano Sincronizado com Sucesso!", state="complete")
                            st.balloons(); reset_planejamento()

            with t_vis:
                st.subheader("👁️ Visão do Documento Final")
                st.caption(f"📅 {meta.get('semana')} | 🎓 {meta.get('ano')} Ano | 📅 {meta.get('trimestre')}")
                
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    if keep_objeto: st.info(f"**🎯 Objeto de Conhecimento:**\n{ed_geral}")
                    st.markdown(f"**🆔 Habilidade:** `{ed_hab}`")
                    st.markdown(f"**🌟 Competências Foco:**\n{ed_comp}")
                    st.success(f"**📖 Base Didática (DNA):**\n{ed_base}")
                
                with c_v2:
                    st.markdown("##### 🏫 Roteiro de Execução")
                    with st.container(border=True):
                        st.write(f"**📘 AULA 1:**\n{ed_a1}")
                    if "1 Aula" not in meta.get('carga', ''):
                        with st.container(border=True):
                            st.write(f"**📗 AULA 2:**\n{ed_a2}")
                
                st.divider()
                c_v3, c_v4 = st.columns(2)
                with c_v3: st.warning(f"**♿ Estratégia DUA/PEI (Equidade):**\n{ed_dua}")
                with c_v4: st.error(f"**📝 Avaliação de Mérito:**\n{ed_ava}")
                
                if ed_a3 and "N/A" not in ed_a3.upper() and "Atividade desativada" not in ed_a3:
                    st.info(f"**🗓️ Sábado Letivo:**\n{ed_a3}")

    # --- ABA 2: DASHBOARD DE PRODUÇÃO ---
    with tab_producao:
        st.subheader("🏗️ Hub de Produção de Materiais")
        st.info("💡 Aqui ficam os planos aprovados que estão aguardando a geração dos materiais físicos (Folha do Aluno, Guia do Professor, etc).")
        
        if not df_planos.empty:
            planos_ativos = df_planos[df_planos["EIXO"].astype(str).str.contains("HUB_ATIVO", case=False, na=False)].iloc[::-1]
            
            if not planos_ativos.empty:
                for _, row in planos_ativos.iterrows():
                    with st.container(border=True):
                        c_p1, c_p2, c_p3, c_p4 = st.columns([1.5, 1.5, 1, 1])
                        
                        sem_ref = row['SEMANA']
                        ano_ref = row['ANO']
                        plano_txt = str(row["PLANO_TEXTO"])
                        
                        c_p1.markdown(f"**{sem_ref}**\n`Série: {ano_ref}`")
                        
                        aulas_que_devem_existir = ["Aula 1"] 
                        conteudo_a2 = ai.extrair_tag(plano_txt, "AULA_2")
                        
                        if conteudo_a2 and "não previsto" not in conteudo_a2.lower() and "n/a" not in conteudo_a2.lower() and len(conteudo_a2) > 30:
                            aulas_que_devem_existir.append("Aula 2")
                        
                        aulas_no_banco = df_aulas[(df_aulas['SEMANA_REF'] == sem_ref) & (df_aulas['ANO'] == ano_ref)]
                        lista_materiais_prontos = aulas_no_banco['TIPO_MATERIAL'].astype(str).tolist()
                        
                        icones_progresso =[]
                        for aula_alvo in aulas_que_devem_existir:
                            foi_feita = any(aula_alvo in mat for mat in lista_materiais_prontos)
                            status_icon = "✅" if foi_feita else "⏳"
                            icones_progresso.append(f"{status_icon} {aula_alvo}")
                        
                        c_p2.markdown(f"**Status de Geração:**\n{' | '.join(icones_progresso)}")
                        
                        if c_p3.button("🧪 GERAR MATERIAL", key=f"gen_hub_{row.name}", use_container_width=True):
                            st.session_state.lab_temp = plano_txt
                            st.session_state.sosa_id_atual = util.gerar_sosa_id("AULA", ano_ref, row["TURMA"])
                            st.session_state.lab_meta = {
                                "ano": str(ano_ref).replace("º",""), 
                                "trimestre": row["TURMA"], 
                                "tipo": "PRODUÇÃO_HUB",
                                "semana_ref": sem_ref
                            }
                            st.success("Conteúdo enviado! Vá para a aba 'Criador de Aulas'.")

                        if c_p4.button("✅ MARCAR CONCLUÍDO", help="Remove este plano da fila de pendências.", key=f"fin_hub_{row.name}", use_container_width=True):
                            if db.arquivar_plano_produzido(sem_ref, ano_ref):
                                st.success("Safra Concluída!"); time.sleep(1); st.rerun()
            else:
                st.success("🎉 Tudo em dia! Nenhum plano pendente de produção no momento.")

    # --- ABA 3: GESTÃO DE ACERVO ---
    with tab_acervo:
        st.subheader("📂 Acervo de Planos Estratégicos")
        st.info("💡 Histórico completo de todos os planos já gerados e salvos no Google Drive.")
        
        if not df_planos.empty:
            c_h1, c_h2 = st.columns([1, 2])
            f_ano_h = c_h1.selectbox("Filtrar por Série:",["Todos", "1º", "2º", "3º", "4º", "5º", "6º", "7º", "8º", "9º"], key="hist_ano_v40")
            
            df_h = df_planos.copy()
            if f_ano_h != "Todos": 
                df_h = df_h[df_h["ANO"] == f"{f_ano_h}º"]
            
            if not df_h.empty:
                lista_semanas = df_h["SEMANA"].tolist()[::-1]
                sel_h = st.selectbox("Selecionar Plano para Visualização:", lista_semanas, key="hist_sem_v40")
                
                dados_h = df_h[df_h["SEMANA"] == sel_h].iloc[0]
                raw_h = str(dados_h["PLANO_TEXTO"])
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("🔄 REABRIR NO EDITOR", use_container_width=True, key=f"btn_reopen_{sel_h}"):
                        st.session_state.p_temp = raw_h
                        st.session_state.p_meta = {
                            "semana": sel_h, "ano": dados_h["ANO"], 
                            "trimestre": dados_h["TURMA"],
                            "carga": "2 Aulas",
                            "base": ai.extrair_tag(raw_h, "BASE_DIDATICA")
                        }
                        st.success("✅ Plano carregado no Editor!"); st.rerun()
                with col_btn2:
                    if st.button("🚀 DEVOLVER PARA PRODUÇÃO", help="Manda o plano de volta para a aba Hub de Produção.", use_container_width=True, type="primary", key=f"btn_hub_act_{sel_h}"):
                        if db.ativar_plano_no_hub(sel_h, dados_h["ANO"]):
                            st.success("✅ Plano enviado ao Dashboard!"); time.sleep(1); st.rerun()
                with col_btn3:
                    link_d = dados_h.get("LINK_DRIVE", "#")
                    st.link_button("📂 ABRIR DOCX NO DRIVE", str(link_d), use_container_width=True)

                with st.container(border=True):
                    val_objeto = ai.extrair_tag(raw_h, "OBJETO_CONHECIMENTO") or ai.extrair_tag(raw_h, "CONTEUDO_GERAL")
                    val_hab = ai.extrair_tag(raw_h, "HABILIDADE_BNCC")
                    val_comp = ai.extrair_tag(raw_h, "COMPETENCIAS_FOCO")
                    val_base = ai.extrair_tag(raw_h, "BASE_DIDATICA") or "Matriz Curricular"
                    
                    st.markdown(f"### 🎯 {val_objeto}")
                    st.caption(f"📅 {sel_h} | 🎓 {dados_h['ANO']} | 📅 {dados_h['TURMA']}")
                    
                    c_meta1, c_meta2 = st.columns([1, 1])
                    with c_meta1:
                        st.markdown(f"**🆔 Habilidade:** `{val_hab}`")
                        st.markdown(f"**🌟 Competências:** {val_comp}")
                    with c_meta2:
                        st.success(f"**📖 Base Didática (DNA):**\n{val_base}")
                    
                    st.divider()
                    c_info1, c_info2 = st.columns(2)
                    with c_info1:
                        st.markdown("##### 📖 Conteúdos Específicos")
                        st.info(ai.extrair_tag(raw_h, 'CONTEUDOS_ESPECIFICOS'))
                    with c_info2:
                        st.markdown("##### ✅ Objetivos de Aprendizagem")
                        st.info(ai.extrair_tag(raw_h, 'OBJETIVOS_ENSINO'))
                    
                    st.divider()
                    st.markdown("##### 🏫 Roteiro de Execução")
                    c_v1, c_v2 = st.columns(2)
                    with c_v1: 
                        with st.container(border=True):
                            st.write(f"**📘 AULA 1:**\n{ai.extrair_tag(raw_h, 'AULA_1')}")
                    with c_v2: 
                        val_a2 = ai.extrair_tag(raw_h, 'AULA_2')
                        if val_a2 and "N/A" not in val_a2.upper() and "não previsto" not in val_a2:
                            with st.container(border=True):
                                st.write(f"**📗 AULA 2:**\n{val_a2}")
                        else:
                            st.caption("Sem Aula 2 planejada para esta semana.")
                    
                    st.divider()
                    c_v3, c_v4 = st.columns(2)
                    with c_v3: st.warning(f"**♿ Estratégia DUA/PEI:**\n{ai.extrair_tag(raw_h, 'ESTRATEGIA_DUA_PEI')}")
                    with c_v4: st.error(f"**📝 Avaliação de Mérito:**\n{ai.extrair_tag(raw_h, 'AVALIACAO_DE_MERITO')}")
                    
                    val_sab = ai.extrair_tag(raw_h, "SABADO_LETIVO")
                    if val_sab and "N/A" not in val_sab.upper() and "não programada" not in val_sab:
                        st.info(f"**🗓️ Sábado Letivo:**\n{val_sab}")
                
                if st.button("🗑️ EXCLUIR PLANO DO ACERVO", use_container_width=True, key=f"btn_del_plan_{sel_h}"):
                    if db.excluir_plano_completo(sel_h, dados_h["ANO"]): 
                        st.rerun()
            else: 
                st.info("📭 Nenhum plano encontrado para esta série.")
        else: 
            st.info("📭 Acervo vazio.")

    # --- ABA 4: MATRIZ CURRICULAR ATIVA ---
    with tab_matriz:
        st.subheader("📖 Matriz de Competências e Status de Execução")
        if not df_curriculo.empty:
            ano_c = st.selectbox("Série para Consulta:",[1, 2, 3, 4, 5, 6, 7, 8, 9], index=5, key="matriz_ano_v35")
            df_c = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_c))].copy()
            planos_feitos = df_planos[df_planos["ANO"].astype(str).str.contains(str(ano_c))]
            lista_conteudos_oficiais =[ai.extrair_tag(p, "CONTEUDOS_ESPECIFICOS").upper() for p in planos_feitos["PLANO_TEXTO"]]
            texto_soberano_planos = " | ".join(lista_conteudos_oficiais)

            def checar_conclusao_cirurgica(conteudo_db):
                if not texto_soberano_planos: return "⏳ PENDENTE"
                def limpar(t): return re.sub(r'[^A-Z0-9]', '', str(t).upper())
                target_limpo = limpar(conteudo_db)
                soberano_limpo = limpar(texto_soberano_planos)
                if target_limpo in soberano_limpo: return "✅ CONCLUÍDO"
                palavras =[p for p in str(conteudo_db).upper().replace(";", "").replace(",", "").split() if len(p) > 4]
                if not palavras: return "⏳ PENDENTE"
                matches = sum(1 for p in palavras if limpar(p) in soberano_limpo)
                return "✅ CONCLUÍDO" if matches >= 2 else "⏳ PENDENTE"

            df_c["STATUS"] = df_c["CONTEUDO_ESPECIFICO"].apply(checar_conclusao_cirurgica)
            st.dataframe(df_c[["TRIMESTRE", "EIXO", "CONTEUDO_ESPECIFICO", "STATUS"]], use_container_width=True, hide_index=True)

    # --- ABA 5: ANALYTICS DE COBERTURA ---
    with tab_auditoria:
        st.subheader("📈 Analytics de Cobertura Curricular")
        if not df_curriculo.empty:
            ano_m = st.selectbox("Analisar Série:",[1, 2, 3, 4, 5, 6, 7, 8, 9], index=5, key="auditoria_ano_v35")
            df_m = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_m))].copy()
            planos_m = df_planos[df_planos["ANO"].astype(str).str.contains(str(ano_m))]
            lista_cont_m =[ai.extrair_tag(t, "CONTEUDOS_ESPECIFICOS").upper() for t in planos_m["PLANO_TEXTO"]]
            texto_m_soberano = " | ".join(lista_cont_m)
            
            def concluido_num_cirurgico(x):
                def limpar(t): return re.sub(r'[^A-Z0-9]', '', str(t).upper())
                txt = limpar(x)
                if txt in limpar(texto_m_soberano): return 1
                palavras =[p for p in str(x).upper().split() if len(p) > 4]
                return 1 if (palavras and sum(1 for p in palavras if limpar(p) in limpar(texto_m_soberano)) >= 2) else 0

            df_m["CONCLUIDO"] = df_m["CONTEUDO_ESPECIFICO"].apply(concluido_num_cirurgico)
            progresso_trim = df_m.groupby("TRIMESTRE")["CONCLUIDO"].agg(["sum", "count"]).reset_index()
            
            if not progresso_trim.empty:
                progresso_trim["sum"] = pd.to_numeric(progresso_trim["sum"], errors='coerce').fillna(0)
                progresso_trim["count"] = pd.to_numeric(progresso_trim["count"], errors='coerce').fillna(1)
                
                progresso_trim["%"] = (progresso_trim["sum"] / progresso_trim["count"] * 100)
                progresso_trim["%"] = pd.to_numeric(progresso_trim["%"]).round(1)
                
                c1, c2, c3 = st.columns(3)
                total_geral = (progresso_trim["sum"].sum() / progresso_trim["count"].sum() * 100) if progresso_trim["count"].sum() > 0 else 0
                c1.metric("Cobertura Anual", f"{total_geral:.1f}%")
                p_i = progresso_trim[progresso_trim["TRIMESTRE"] == "I"]["%"].values[0] if "I" in progresso_trim["TRIMESTRE"].values else 0
                c2.metric("Progresso I Trimestre", f"{p_i}%")
                p_ii = progresso_trim[progresso_trim["TRIMESTRE"] == "II"]["%"].values[0] if "II" in progresso_trim["TRIMESTRE"].values else 0
                c3.metric("Progresso II Trimestre", f"{p_ii}%")

                st.plotly_chart(px.bar(progresso_trim, x="TRIMESTRE", y="%", text="%", title=f"Evolução da Cobertura Real - {ano_m}º Ano", color="%", color_continuous_scale="RdYlGn", range_y=[0, 110]), use_container_width=True)



# ==============================================================================
# MÓDULO: LABORATÓRIO DE PRODUÇÃO (CRIADOR DE AULAS) - CLEAN & UX
# ==============================================================================
elif menu == "🧪 Criador de Aulas":
    st.title("🧪 Laboratório de Produção Semiótica")
    st.markdown("---")
    st.caption("💡 **Guia de Comando:** Transforme seus planejamentos (Ponto ID) em materiais físicos de alta densidade (Folha do Aluno, Guia do Professor e Adaptação PEI) com um clique.")
    
    def reset_laboratorio():
        keys_to_del =["lab_temp", "lab_pei", "lab_gab_pei", "refino_lab_ativo", "sosa_id_atual", "lab_meta", "hub_origem", "chat_history_lab"]
        for k in keys_to_del:
            if k in st.session_state: del st.session_state[k]
        st.cache_data.clear() 
        st.session_state.v_lab = int(time.time())
        st.rerun()

    if "v_lab" not in st.session_state: 
        st.session_state.v_lab = int(time.time())
    v = st.session_state.v_lab

    meta = st.session_state.get("lab_meta", {})
    is_hub = meta.get("tipo") == "PRODUÇÃO_HUB"
    
    # --- ÁREA DE EXIBIÇÃO E REFINO ---
    if "lab_temp" in st.session_state:
        txt_base = st.session_state.lab_temp
        s_id = st.session_state.get("sosa_id_atual", "SEM-ID")
        st.success(f"💎 Material em Edição: **{s_id}**")

        # ==============================================================================
        # 🤖 MAESTRO COPILOT (CHATBOT DE REFINO)
        # ==============================================================================
        with st.container(border=True):
            st.subheader("🤖 Maestro Copilot (Coautoria em Tempo Real)")
            st.caption("Converse com a IA para ajustar o material. O editor abaixo será atualizado automaticamente.")
            
            if "chat_history_lab" not in st.session_state:
                st.session_state.chat_history_lab =[{"role": "assistant", "avatar": "🤖", "content": "Saudações, Mestre! O material base foi gerado. Como deseja refinar a nossa estratégia?"}]
            
            chat_container_lab = st.container(height=300)
            with chat_container_lab:
                for msg in st.session_state.chat_history_lab:
                    with st.chat_message(msg["role"], avatar=msg["avatar"]):
                        st.markdown(msg["content"])
            
            if cmd_refine_lab := st.chat_input("Ex: 'Deixe o texto do aluno mais simples' ou 'Adicione mais uma questão'...", key=f"chat_lab_ref_{v}"):
                st.session_state.chat_history_lab.append({"role": "user", "avatar": "💻", "content": cmd_refine_lab})
                
                with chat_container_lab:
                    with st.chat_message("user", avatar="💻"):
                        st.markdown(cmd_refine_lab)
                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner("Reengenharia em curso..."):
                            hist_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history_lab[-5:]])
                            prompt_refino = (
                                f"HISTÓRICO DA CONVERSA:\n{hist_text}\n\n"
                                f"ORDEM ATUAL: {cmd_refine_lab}\n\n"
                                f"MATERIAL ATUAL PARA REFINAR:\n{txt_base}"
                            )
                            
                            resultado_refino = ai.gerar_ia("REFINADOR_MATERIAIS", prompt_refino)
                            
                            msg_chat = ai.extrair_tag(resultado_refino, "MENSAGEM_CHAT")
                            novo_conteudo = ai.extrair_tag(resultado_refino, "CONTEUDO_ATUALIZADO")
                            
                            if not novo_conteudo:
                                novo_conteudo = resultado_refino
                                msg_chat = "Material atualizado conforme solicitado, Mestre."
                                
                            st.markdown(msg_chat)
                            st.session_state.chat_history_lab.append({"role": "assistant", "avatar": "🤖", "content": msg_chat})
                            st.session_state.lab_temp = novo_conteudo
                            st.session_state.v_lab = int(time.time())
                            st.rerun()

            if st.button("🗑️ DESCARTAR EDIÇÃO E VOLTAR"): reset_laboratorio()
        
        t_prof, t_alu, t_gab, t_pei, t_img, t_sync = st.tabs(["👨‍🏫 Professor", "📝 Aluno", "✅ Gabarito", "♿ PEI", "🎨 Imagens", "☁️ SINCRONIA"])
        with t_prof: st.text_area("Lousa/Mediação:", ai.extrair_tag(txt_base, "PROFESSOR"), height=450, key=f"ed_prof_reg_{v}")
        with t_alu: st.text_area("Folha/Roteiro:", ai.extrair_tag(txt_base, "ALUNO"), height=450, key=f"ed_alu_reg_{v}")
        with t_gab: st.text_area("Gabarito:", ai.extrair_tag(txt_base, "GABARITO"), height=200, key=f"ed_res_reg_{v}")
        with t_pei: st.text_area("PEI (Obrigatório):", ai.extrair_tag(txt_base, "PEI"), height=400, key=f"ed_pei_reg_{v}")
        with t_img: st.text_area("Prompts de Imagem:", ai.extrair_tag(txt_base, "IMAGENS"), height=200, key=f"ed_img_reg_{v}")

        # --- ☁️ ABA DE SINCRONIA (TRIPLE-SYNC) ---
        with t_sync:
            st.subheader("🚀 Sincronia e Custódia Digital")
            st.info("Este comando irá gerar os documentos oficiais (DOCX) e salvar os links permanentes no seu banco de dados.")
            
            if st.button("💾 SALVAR MATERIAL E SINCRONIZAR NO DRIVE", use_container_width=True, type="primary", key=f"btn_triple_{v}"):
                with st.status("Sincronizando Ativos de Elite...") as status:
                    db.excluir_registro_com_drive("DB_AULAS_PRONTAS", s_id)
                    
                    ano_str = f"{meta.get('ano', '6')}º"
                    sem_ref = meta.get('semana_ref', 'Geral')
                    info_doc = {"ano": ano_str, "trimestre": "I Trimestre", "semana": sem_ref}

                    status.write("📝 Gerando Material do Aluno/Roteiro...")
                    doc_alu = exporter.gerar_docx_aluno_v24(s_id, ai.extrair_tag(txt_base, "ALUNO"), info_doc)
                    link_alu = db.subir_e_converter_para_google_docs(doc_alu, f"{s_id}_ALUNO", modo="AULA")
                    
                    status.write("♿ Gerando Atividade Adaptada PEI...")
                    doc_pei = exporter.gerar_docx_pei_v25(f"{s_id}_PEI", ai.extrair_tag(txt_base, "PEI"), info_doc)
                    link_pei = db.subir_e_converter_para_google_docs(doc_pei, f"{s_id}_PEI", modo="AULA")
                    
                    status.write("👨‍🏫 Gerando Guia de Mediação do Professor...")
                    doc_prof = exporter.gerar_docx_professor_v25(s_id, ai.extrair_tag(txt_base, "PROFESSOR"), info_doc)
                    link_prof = db.subir_e_converter_para_google_docs(doc_prof, f"{s_id}_PROF", modo="AULA")
                    
                    links_f = f"--- LINKS ---\nRegular({link_alu})\nPEI({link_pei})\nProf({link_prof})"
                    conteudo_final = txt_base + f"\n\n{links_f}"
                    
                    db.salvar_no_banco("DB_AULAS_PRONTAS",[
                        datetime.now().strftime("%d/%m/%Y"), 
                        sem_ref, 
                        s_id, 
                        conteudo_final, 
                        ano_str, 
                        link_alu
                    ])
                    
                    status.update(label="✅ Sincronizado com Sucesso!", state="complete")
                    st.balloons()
                    time.sleep(1)
                    reset_laboratorio()

    # --- SEÇÃO DE ENTRADA (CONFIGURAÇÃO COM INTELIGÊNCIA DE TRILHAS) ---
    else:
        tab_producao, tab_trabalhos, tab_complementar, tab_acervo_lab = st.tabs([
            "🚀 1. Produção de Aulas", "📋 2. Projetos e Trabalhos", "📚 3. Listas e Recomposição", "📂 4. Acervo de Materiais"
        ])

        with tab_producao:
            st.markdown("### ⚙️ Passo 1: Herança Didática (Ponto ID)")
            
            mostrar_tudo_lab = st.toggle("🔄 Mostrar semanas e aulas já concluídas (Modo Sobrescrita)", help="Ative se precisar refazer uma aula que já foi gerada e salva no acervo.", key=f"tog_lab_{v}")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                ano_lab = c1.selectbox("Série/Ano Alvo:",[6, 7, 8, 9], key=f"prod_ano_{v}")
                planos_ano = df_planos[df_planos["ANO"].astype(str).str.contains(str(ano_lab))]
                
                if planos_ano.empty: 
                    st.error("❌ Nenhum planejamento encontrado para esta série. Vá ao Ponto ID primeiro.")
                else:
                    # Lógica de filtragem de semanas concluídas
                    semanas_pendentes = []
                    for sem in planos_ano["SEMANA"].unique().tolist():
                        p_row = planos_ano[planos_ano["SEMANA"] == sem].iloc[0]
                        p_txt = str(p_row['PLANO_TEXTO'])
                        
                        pede_a2 = len(ai.extrair_tag(p_txt, "AULA_2")) > 30 and "N/A" not in ai.extrair_tag(p_txt, "AULA_2").upper()
                        t_sab = ai.extrair_tag(p_txt, "SABADO_LETIVO")
                        pede_sab = len(t_sab) > 10 and "N/A" not in t_sab.upper() and "NÃO PROGRAMADA" not in t_sab.upper()
                        
                        a_geradas = df_aulas[(df_aulas['ANO'].str.contains(str(ano_lab))) & (df_aulas['SEMANA_REF'] == sem)]['TIPO_MATERIAL'].astype(str).tolist()
                        t_a1 = any("Aula 1" in mat for mat in a_geradas)
                        t_a2 = any("Aula 2" in mat for mat in a_geradas)
                        t_sab_gen = any("Sábado" in mat or "Sabado" in mat for mat in a_geradas)
                        
                        if (not t_a1) or (pede_a2 and not t_a2) or (pede_sab and not t_sab_gen):
                            semanas_pendentes.append(sem)
                    
                    semanas_opcoes = planos_ano["SEMANA"].unique().tolist() if mostrar_tudo_lab else semanas_pendentes
                    
                    if not semanas_opcoes:
                        st.success("✅ Todas as semanas planejadas para esta série já tiveram seus materiais produzidos! O acervo está completo.")
                    else:
                        sem_lab = c2.selectbox("Semana Base (Herdada do Ponto ID):", semanas_opcoes, key=f"prod_sem_{v}")
                        plano_row = planos_ano[planos_ano["SEMANA"] == sem_lab].iloc[0]
                        plano_txt = str(plano_row['PLANO_TEXTO'])

                        with st.expander("📡 Radar de Regência (Memória das Turmas)", expanded=True):
                            st.caption("O sistema verifica onde você parou na última aula para garantir a continuidade.")
                            contexto_turmas_ia = ""
                            reg_ano = df_registro_aulas[df_registro_aulas['TURMA'].str.contains(str(ano_lab))]
                            if not reg_ano.empty:
                                for t_nome in sorted(reg_ano['TURMA'].unique()):
                                    dados_t = reg_ano[reg_ano['TURMA'] == t_nome].iloc[-1]
                                    est = dados_t.get('STATUS_EXECUCAO', 'Não Iniciado')
                                    pnt = dados_t.get('PONTE_PEDAGOGICA', 'Sem pendências.')
                                    emoji = "🟢" if "Concluído" in est else "🟡" if "Parcial" in est else "🔴"
                                    st.write(f"{emoji} **{t_nome}:** {est}")
                                    contexto_turmas_ia += f"- Turma {t_nome}: Status {est}. Pendência: {pnt}\n"
                            else: st.info("ℹ️ Nenhuma regência anterior registrada.")

                        base_herdada = ai.extrair_tag(plano_txt, "BASE_DIDATICA")
                        
                        metodo_entrega = st.radio("🎯 Método de Entrega:",[
                            "🚀 Geração Integral (SOSA AI)", 
                            "📖 Livro Didático + PEI (Híbrido)",
                            "🎟️ Registro de Evento / Dinâmica (Sem Material Físico)"
                        ], horizontal=True, help="Integral: A IA cria o texto e as questões. Livro: A IA cria o roteiro baseado nas páginas do livro. Evento: Apenas registra a aula no sistema.", key=f"metodo_{v}")
                        
                        aulas_ja_geradas = df_aulas[(df_aulas['ANO'].str.contains(str(ano_lab))) & (df_aulas['SEMANA_REF'] == sem_lab)]['TIPO_MATERIAL'].astype(str).tolist()
                        
                        tem_aula1 = any("Aula 1" in mat for mat in aulas_ja_geradas)
                        tem_aula2 = any("Aula 2" in mat for mat in aulas_ja_geradas)
                        tem_sabado = any("Sábado" in mat or "Sabado" in mat for mat in aulas_ja_geradas)

                        plano_pede_a2 = len(ai.extrair_tag(plano_txt, "AULA_2")) > 30 and "N/A" not in ai.extrair_tag(plano_txt, "AULA_2").upper()
                        txt_sabado = ai.extrair_tag(plano_txt, "SABADO_LETIVO")
                        plano_pede_sab = len(txt_sabado) > 10 and "N/A" not in txt_sabado.upper() and "NÃO PROGRAMADA" not in txt_sabado.upper()

                        opcoes_disponiveis =[]
                        if not tem_aula1: opcoes_disponiveis.append("Aula 1")
                        if plano_pede_a2 and not tem_aula2: opcoes_disponiveis.append("Aula 2")
                        if plano_pede_sab and not tem_sabado: opcoes_disponiveis.append("Sábado Letivo")

                        if mostrar_tudo_lab:
                            opcoes_disponiveis = ["Aula 1"]
                            if plano_pede_a2: opcoes_disponiveis.append("Aula 2")
                            if plano_pede_sab: opcoes_disponiveis.append("Sábado Letivo")

                        obj_geral = ai.extrair_tag(plano_txt, "OBJETO_CONHECIMENTO") or ai.extrair_tag(plano_txt, "CONTEUDO_GERAL")
                        
                        with st.container(border=True):
                            st.markdown(f"#### 🎯 Alvo Curricular: {obj_geral}")
                            
                            if not opcoes_disponiveis:
                                st.success("✅ Todas as aulas previstas para esta semana já foram produzidas! O acervo está completo.")
                                aula_alvo_prod = None
                            else:
                                col_config1, col_config2 = st.columns([1, 1])
                                with col_config1:
                                    aula_alvo_prod = st.radio("🚀 Material a Gerar:", opcoes_disponiveis, horizontal=True, key=f"prod_alvo_{v}")
                                with col_config2:
                                    if "Evento" not in metodo_entrega:
                                        qtd_q_prod = st.slider("Nº de Questões (PEI/Regular):", 1, 20, 10, key=f"prod_q_{v}")
                                    else:
                                        nome_evento = st.text_input("Nome do Evento/Dinâmica:", placeholder="Ex: Palestra sobre a Dengue", key=f"nome_ev_{v}")

                                if "1" in aula_alvo_prod: tag_roteiro = "AULA_1"
                                elif "2" in aula_alvo_prod: tag_roteiro = "AULA_2"
                                else: tag_roteiro = "SABADO_LETIVO"
                                
                                roteiro_especifico = ai.extrair_tag(plano_txt, tag_roteiro)
                                
                                roteiro_upper = roteiro_especifico.upper()
                                termos_av =["LOGÍSTICA DE APLICAÇÃO", "APLICAÇÃO DE AVALIAÇÃO", "APLICAÇÃO DE PROVA", "APLICAÇÃO DE TESTE", "APLICAÇÃO DA SONDA", "APLICAÇÃO DO EXAME"]
                                termos_cor =["CORREÇÃO COMENTADA", "CLÍNICA PEDAGÓGICA", "CORREÇÃO DE AVALIAÇÃO", "CORREÇÃO DA PROVA", "CORREÇÃO DO TESTE", "CORREÇÃO DA SONDA", "MAPEAMENTO DE DISTRATORES"]
                                
                                is_avaliacao = any(t in roteiro_upper for t in termos_av)
                                is_correcao = any(t in roteiro_upper for t in termos_cor)
                                
                                paginas_aula = base_herdada
                                if ";" in base_herdada:
                                    partes_pag = base_herdada.split(";")
                                    if "1" in aula_alvo_prod: paginas_aula = partes_pag[0].strip()
                                    elif "2" in aula_alvo_prod and len(partes_pag) > 1: paginas_aula = partes_pag[1].strip()
                                    else: paginas_aula = partes_pag[-1].strip()

                                with st.expander(f"👁️ Roteiro Herdado para {aula_alvo_prod}", expanded=False):
                                    st.info(f"📍 **Páginas Alvo:** {paginas_aula}\n\n{roteiro_especifico}")

                                conteudo_prova_vinculada = ""
                                if is_correcao or is_avaliacao:
                                    st.markdown("---")
                                    st.warning("🔍 **Modo de Avaliação/Correção Detectado:** Selecione a prova correspondente para que a IA possa ler as questões e gerar o guia.")
                                    
                                    mask_provas = df_aulas['TIPO_MATERIAL'].str.upper().str.contains("PROVA|TESTE|SONDA|AVALIAÇÃO|EXAME")
                                    provas_disponiveis = df_aulas[(df_aulas['ANO'].str.contains(str(ano_lab))) & mask_provas]
                                    
                                    if not provas_disponiveis.empty:
                                        prova_sel = st.selectbox("Vincular Avaliação do Acervo:",[""] + provas_disponiveis['TIPO_MATERIAL'].tolist(), key=f"vinc_prova_{v}")
                                        if prova_sel:
                                            conteudo_prova_vinculada = provas_disponiveis[provas_disponiveis['TIPO_MATERIAL'] == prova_sel].iloc[0]['CONTEUDO']
                                            st.success("✅ Avaliação vinculada! A IA usará as questões reais para montar a aula.")
                                    else:
                                        st.info("Nenhuma avaliação encontrada no acervo para esta série.")

                        if opcoes_disponiveis:
                            if "Evento" in metodo_entrega:
                                if st.button("💾 OFICIALIZAR EVENTO NO ACERVO", use_container_width=True, type="primary"):
                                    if not nome_evento:
                                        st.error("⚠️ Digite o nome do evento para registrar.")
                                    else:
                                        with st.spinner("Registrando evento com rastreabilidade curricular..."):
                                            hab_herdada = ai.extrair_tag(plano_txt, "HABILIDADE_BNCC")
                                            cont_herdado = ai.extrair_tag(plano_txt, "CONTEUDOS_ESPECIFICOS")
                                            obj_herdado = ai.extrair_tag(plano_txt, "OBJETIVOS_ENSINO")
                                            
                                            conteudo_fantasma = (
                                                f"[PROFESSOR]\n"
                                                f"🎟️ **REGISTRO DE EVENTO / DINÂMICA**\n"
                                                f"**Tema:** {nome_evento}\n"
                                                f"**Habilidade:** {hab_herdada}\n"
                                                f"**Conteúdos:** {cont_herdado}\n"
                                                f"**Objetivos:** {obj_herdado}\n\n"
                                                f"**Roteiro Executado:**\n{roteiro_especifico}\n\n"
                                                f"[ALUNO]\nAtividade prática/evento. Sem material físico gerado.\n\n"
                                                f"[GABARITO]\nN/A\n\n"
                                                f"[PEI]\nParticipação inclusiva no evento garantida via mediação direta.\n\n"
                                                f"--- LINKS ---\nRegular(N/A)\nPEI(N/A)\nProf(N/A)"
                                            )
                                            
                                            nome_elite = util.gerar_nome_material_elite(ano_lab, aula_alvo_prod, nome_evento)
                                            
                                            db.salvar_no_banco("DB_AULAS_PRONTAS",[
                                                datetime.now().strftime("%d/%m/%Y"), 
                                                sem_lab, 
                                                nome_elite, 
                                                conteudo_fantasma, 
                                                f"{ano_lab}º", 
                                                "N/A"
                                            ])
                                            st.success("✅ Evento oficializado no Acervo! Já disponível no Cockpit.")
                                            time.sleep(1.5)
                                            st.rerun()
                            else:
                                uri_referencia_aula = None
                                if "Livro" in metodo_entrega:
                                    nome_livro_limpo = base_herdada.split('|')[0].replace("Livro:", "").strip()
                                    match_biblioteca = df_materiais[df_materiais['NOME_ARQUIVO'].str.contains(nome_livro_limpo[:10], case=False, na=False)]
                                    if not match_biblioteca.empty:
                                        uri_referencia_aula = match_biblioteca.iloc[0]['URI_ARQUIVO']
                                        st.success(f"📚 **Fonte Vinculada:** {match_biblioteca.iloc[0]['NOME_ARQUIVO']} (Páginas: {paginas_aula})")

                                alunos_foco = df_alunos[(df_alunos['TURMA'].str.contains(str(ano_lab))) & (~df_alunos['NECESSIDADES'].isin(["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"]))]
                                texto_clinico = ", ".join(alunos_foco['NECESSIDADES'].unique().tolist()) if not alunos_foco.empty else "PADRÃO"
                                if not alunos_foco.empty: st.warning(f"♿ **Sensor PEI Ativo:** {texto_clinico}")
                                
                                instr_extra_prod = st.text_area("📝 Contexto Extra / Ajustes Específicos:", placeholder="Ex: Focar mais em frações equivalentes...", key=f"prod_extra_{v}")

                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🧠 INICIAR MOTOR DE IA: GERAR AULA", use_container_width=True, type="primary"):
                                    
                                    # Limpa o histórico do chat ao gerar um novo material
                                    if "chat_history_lab" in st.session_state:
                                        del st.session_state["chat_history_lab"]
                                        
                                    with st.spinner("Sosa estudando o roteiro e arquitetando material..."):
                                        
                                        nome_elite = util.gerar_nome_material_elite(ano_lab, aula_alvo_prod, sem_lab)
                                        st.session_state.sosa_id_atual = nome_elite
                                        st.session_state.lab_meta = {"ano": ano_lab, "semana_ref": sem_lab}
                                        
                                        if "Geração Integral" in metodo_entrega:
                                            regra_livro = "3. MODO MANUAL: Crie o conteúdo do zero com base na BNCC. É TERMINANTEMENTE PROIBIDO citar páginas de livros didáticos."
                                        else:
                                            regra_livro = "3. MODO LIVRO: O roteiro deve dizer exatamente: 'Inicie na página X explorando a imagem Y...' baseando-se no PDF."

                                        if is_avaliacao and not is_correcao:
                                            missao_especifica = (
                                                f"🚨 ATENÇÃO: Esta é uma aula de APLICAÇÃO DE AVALIAÇÃO.\n"
                                                f"1. Na tag[PROFESSOR]: Escreva apenas as instruções de logística, tempo, regras da prova e orientações de preenchimento de gabarito.\n"
                                                f"2. Nas tags [ALUNO] e [PEI]: Escreva APENAS 'Material de avaliação impresso separadamente. Não há atividade de caderno hoje.'\n"
                                                f"3. É TERMINANTEMENTE PROIBIDO gerar questões ou exercícios.\n"
                                                f"🚨 FORMATO OBRIGATÓRIO: Você DEVE separar o texto usando EXATAMENTE as tags entre colchetes:[PROFESSOR], [ALUNO], [PEI], [GABARITO], [IMAGENS]."
                                            )
                                        elif is_correcao:
                                            missao_especifica = (
                                                f"🚨 ATENÇÃO: Esta é uma aula de CORREÇÃO DE AVALIAÇÃO (Clínica Pedagógica).\n"
                                                f"1. Na tag [PROFESSOR]: Escreva um guia de como mediar a correção no quadro. USE AS QUESTÕES DA AVALIAÇÃO VINCULADA ABAIXO para dar exemplos reais de como explicar os erros (distratores).\n"
                                                f"2. Nas tags [ALUNO] e [PEI]: Escreva APENAS 'Acompanhamento da correção no quadro e anotações de feedback. Não há nova lista de exercícios hoje.'\n"
                                                f"3. É TERMINANTEMENTE PROIBIDO gerar novas questões.\n"
                                                f"🚨 FORMATO OBRIGATÓRIO: Você DEVE separar o texto usando EXATAMENTE as tags entre colchetes:[PROFESSOR], [ALUNO], [PEI], [GABARITO],[IMAGENS]."
                                            )
                                        else:
                                            missao_especifica = (
                                                f"🚨 MISSÃO DE ALTA DENSIDADE E RIGOR QUANTITATIVO:\n"
                                                f"1.[PROFESSOR]: Escreva um TRATADO DIDÁTICO denso. Explique o conceito de {obj_geral} com profundidade técnica antes de dar o roteiro de aula.\n"
                                                f"2. CONEXÃO ALPHA: Use o Google Search para trazer dados científicos reais de 2026 que validem a importância deste tema.\n"
                                                f"{regra_livro}\n"
                                                f"4.[ALUNO] (REGULAR): É OBRIGATÓRIO gerar EXATAMENTE {qtd_q_prod} questões inéditas e desafiadoras. Formato: **QUESTÃO X.** enunciado.\n"
                                                f"5.[PEI] (INCLUSÃO): É OBRIGATÓRIO gerar EXATAMENTE {qtd_q_prod} questões adaptadas, cada uma com [PARA LEMBRAR],[PASSO A PASSO] e [ PROMPT IMAGEM ].\n"
                                                f"6.[GABARITO]: Forneça as respostas detalhadas para as {qtd_q_prod} questões regulares e as {qtd_q_prod} questões PEI.\n"
                                                f"🚨 FORMATO OBRIGATÓRIO: Você DEVE separar o texto usando EXATAMENTE as tags entre colchetes: [PROFESSOR], [ALUNO], [PEI],[GABARITO], [IMAGENS]."
                                            )

                                        prompt_manual = (
                                            f"PERSONA: MAESTRO_SOSA_V28_ELITE. ID: {nome_elite}.\n"
                                            f"MÉTODO: {metodo_entrega}. REFERÊNCIA: {base_herdada}\n"
                                            f"SÉRIE: {ano_lab}º Ano. ALVO: {aula_alvo_prod}.\n\n"
                                            f"{missao_especifica}\n\n"
                                            f"--- HERANÇA DO PLANO ATUAL ---\n{roteiro_especifico}\n"
                                            f"--- MEMÓRIA DE REGÊNCIA (PONTE PEDAGÓGICA) ---\n{contexto_turmas_ia}\n"
                                            f"--- SENSOR DE INCLUSÃO ---\nA turma possui alunos com: {texto_clinico}."
                                        )
                                        
                                        if conteudo_prova_vinculada:
                                            prompt_manual += f"\n\n--- CONTEÚDO DA AVALIAÇÃO VINCULADA ---\n{conteudo_prova_vinculada}"
                                        
                                        resultado_ia = ai.gerar_ia(
                                            "MAESTRO_SOSA_V28_ELITE", 
                                            prompt_manual, 
                                            url_drive=uri_referencia_aula, 
                                            usar_busca=True
                                        )
                                        
                                        import re
                                        tags_para_limpar =["PROFESSOR", "ALUNO", "PEI", "GABARITO", "GABARITO_PEI", "IMAGENS"]
                                        for t in tags_para_limpar:
                                            resultado_ia = re.sub(rf"\*\*{t}\*\*", f"[{t}]", resultado_ia, flags=re.IGNORECASE)
                                            resultado_ia = re.sub(rf"\*\*{t}:\*\*", f"[{t}]", resultado_ia, flags=re.IGNORECASE)
                                            resultado_ia = re.sub(rf"^{t}$", f"[{t}]", resultado_ia, flags=re.IGNORECASE | re.MULTILINE)
                                            
                                        st.session_state.lab_temp = resultado_ia
                                        st.rerun()

        # --- ABA 2: ENGENHARIA DE TRABALHOS ---
        with tab_trabalhos:
            st.subheader("📋 Engenharia de Projetos e Semanários")
            st.caption("Crie roteiros de pesquisa, trabalhos em grupo e projetos interdisciplinares alinhados à BNCC.")
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.5, 1, 1])
                natureza_p = c1.selectbox("Natureza do Ativo:",["Semanário Temático", "Projeto de Identidade (Itabuna)", "Investigação Científica", "Projeto BNCC Livre"], 
                    key=f"t_nat_{v}")
                ano_t = c2.selectbox("Série Alvo:", [6, 7, 8, 9], key=f"t_ano_{v}")
                modo_t = c3.selectbox("Modo de Execução:",["Individual", "Em Grupo (Equipes)", "Interdisciplinar"], key=f"t_modo_{v}")

            with st.container(border=True):
                st.markdown("#### 🌟 Alinhamento de Competências Gerais (BNCC)")
                comps_proj = st.multiselect("Selecione as Competências Âncora do Projeto:",[
                    "1. Conhecimento", "2. Pensamento Crítico e Criativo", "3. Repertório Cultural",
                    "4. Comunicação", "5. Cultura Digital", "6. Trabalho e Projeto de Vida",
                    "7. Argumentação", "8. Autoconhecimento", "9. Empatia e Cooperação", "10. Responsabilidade e Cidadania"
                ], key=f"t_comp_bncc_{v}")

            with st.container(border=True):
                c_t1, c_t2, c_t3 = st.columns([2, 1, 1])
                tema_t = c_t1.text_input("Título do Projeto/Tema:", placeholder="Ex: A Matemática do Cacau...", key=f"t_tema_{v}")
                valor_t = c_t2.number_input("Valor (0-10):", 0.0, 10.0, 2.0, step=0.5, key=f"t_val_{v}")
                qtd_aulas_t = c_t3.slider("Duração (Aulas):", 1, 10, 2, key=f"t_q_aulas_{v}")
                
            df_cur_t = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_t))]
            if not df_cur_t.empty:
                lista_eixos_t = sorted(df_cur_t["EIXO"].unique().tolist())
                eixos_sel_t = st.multiselect("Eixos da Matriz para Integrar:", lista_eixos_t, key=f"t_eixos_multi_{v}")
                
                if eixos_sel_t:
                    df_hab_t = df_cur_t[df_cur_t["EIXO"].isin(eixos_sel_t)]
                    conts_t = st.multiselect("Conteúdos Específicos (Itabuna):", 
                                           sorted(df_hab_t["CONTEUDO_ESPECIFICO"].unique().tolist()), 
                                           key=f"t_cont_multi_{v}")
                    
                    instr_extra_p = st.text_area("📝 Instruções de Pesquisa / Contexto Adicional:", key=f"t_extra_proj_{v}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🧠 INICIAR MOTOR DE IA: GERAR PROJETO", use_container_width=True, type="primary"):
                        if not tema_t or not conts_t:
                            st.error("Defina o Título e selecione ao menos um Conteúdo da Matriz.")
                        else:
                            if "chat_history_lab" in st.session_state:
                                del st.session_state["chat_history_lab"]
                                
                            with st.spinner("Maestro Sosa arquitetando roteiro investigativo..."):
                                nome_legivel = util.gerar_nome_material_elite(ano_t, "Projeto", tema_t)
                                
                                st.session_state.sosa_id_atual = nome_legivel
                                st.session_state.lab_meta = {
                                    "ano": ano_t, "trimestre": "I Trimestre", 
                                    "tipo": "PROJETO", "aula_alvo": tema_t, "semana_ref": "PROJETO"
                                }
                                
                                prompt_t = (
                                    f"ID_FORNECIDO: {nome_legivel}.\n"
                                    f"TEMA: {tema_t}. NATUREZA: {natureza_p}.\n"
                                    f"SÉRIE: {ano_t}º Ano. MODO: {modo_t}.\n"
                                    f"COMPETÊNCIAS BNCC: {', '.join(comps_proj)}.\n"
                                    f"CONTEÚDOS ITABUNA: {', '.join(conts_t)}.\n"
                                    f"VALOR: {util.sosa_to_str(valor_t)} | DURAÇÃO: {qtd_aulas_t} aulas.\n"
                                    f"EXTRAS: {instr_extra_p}.\n\n"
                                    f"MISSÃO: Use o ID_FORNECIDO na tag [SOSA_ID]. Gere o material completo com as TAGS[SOSA_ID], [JUSTIFICATIVA_PHC],[CONTEXTO_INVESTIGATIVO],[MISSÃO_DE_PESQUISA], [PASSO_A_PASSO],[PRODUTO_ESPERADO],[ESTRATEGIA_DUA_PEI],[RUBRICA_DE_MERITO]."
                                )
                                st.session_state.lab_temp = ai.gerar_ia("ARQUITETO_CIENTIFICO_V33", prompt_t, usar_busca=True)
                                st.session_state.v_lab = int(time.time())
                                st.rerun()

        # --- ABA 3: ATIVIDADES COMPLEMENTARES ---
        with tab_complementar:
            st.subheader("📚 Listas Híbridas e Recomposição")
            st.caption("Crie listas de exercícios mesclando aulas anteriores ou gere material de reforço baseado em anos anteriores.")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                ano_alvo = c1.selectbox("Série Alvo (Sua Turma):",[6, 7, 8, 9], key=f"comp_ano_alvo_{v}")
                
                origem_tipo = c2.radio("Origem do Conteúdo (DNA Curricular):",["🟢 Série Atual (Lista de Consolidação Híbrida)", "🔴 Ano Anterior (Intervenção/Recomposição)"], 
                    horizontal=True, key=f"comp_origem_tipo_{v}")
            
            if "Série Atual" in origem_tipo:
                st.markdown("#### 📦 1. Herança de DNA (Aulas Base)")
                df_aulas_ano = df_aulas[df_aulas['ANO'].str.contains(str(ano_alvo))].copy()
                
                if df_aulas_ano.empty:
                    st.warning("⚠️ Nenhuma aula encontrada no acervo para esta série. Gere uma aula primeiro.")
                else:
                    aulas_puras = df_aulas_ano[df_aulas_ano['TIPO_MATERIAL'].str.contains("Aula", case=False, na=False)]
                    aulas_opcoes = aulas_puras['TIPO_MATERIAL'].tolist()[::-1]
                    
                    aulas_selecionadas = st.multiselect(
                        "Selecione 1 ou 2 aulas para basear a lista:", 
                        aulas_opcoes, 
                        max_selections=2, 
                        key=f"comp_aulas_sel_{v}"
                    )
                    
                    if aulas_selecionadas:
                        st.markdown("#### ⚙️ 2. Engenharia da Lista (Distribuição de Questões)")
                        with st.container(border=True):
                            cq1, cq2, cq3, cq4 = st.columns(4)
                            qtd_trad = cq1.number_input("📐 Tradicionais (Cálculo):", 0, 20, 4, key=f"qtd_trad_{v}")
                            qtd_cot = cq2.number_input("🛒 Cotidiano Real:", 0, 20, 3, key=f"qtd_cot_{v}")
                            qtd_tech = cq3.number_input("📱 Rotina Tecnológica:", 0, 20, 2, key=f"qtd_tech_{v}")
                            qtd_des = cq4.number_input("🔥 Desafio (Boss Fight):", 0, 5, 1, key=f"qtd_des_{v}")
                            
                            total_q = qtd_trad + qtd_cot + qtd_tech + qtd_des
                            st.info(f"**Total de Questões Regulares:** {total_q} | **Questões PEI (50%):** {max(1, total_q//2) if total_q > 0 else 0}")
                        
                        instr_extra_h = st.text_area("📝 Contexto Adicional / Foco Específico (Opcional):", placeholder="Ex: Focar mais em frações equivalentes...", key=f"comp_instr_h_{v}")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🧠 INICIAR MOTOR DE IA: GERAR LISTA HÍBRIDA", use_container_width=True, type="primary"):
                            if total_q == 0:
                                st.error("⚠️ A lista precisa ter pelo menos 1 questão configurada.")
                            else:
                                if "chat_history_lab" in st.session_state:
                                    del st.session_state["chat_history_lab"]
                                    
                                with st.spinner("Maestro Sosa varrendo a internet e arquitetando a lista híbrida..."):
                                    contexto_aulas = ""
                                    for aula_nome in aulas_selecionadas:
                                        cont_aula = df_aulas_ano[df_aulas_ano['TIPO_MATERIAL'] == aula_nome].iloc[0]['CONTEUDO']
                                        contexto_aulas += f"\n--- CONTEÚDO DA {aula_nome} ---\n{cont_aula}\n"
                                    
                                    sosa_id_hash = util.gerar_sosa_id("LISTA", ano_alvo, "I")
                                    nome_elite_c = f"{ano_alvo}º Ano - Lista Híbrida - {sosa_id_hash}"
                                    
                                    st.session_state.sosa_id_atual = nome_elite_c
                                    st.session_state.lab_meta = {
                                        "ano": ano_alvo, 
                                        "trimestre": "I Trimestre", 
                                        "tipo": "LISTA_HIBRIDA", 
                                        "semana_ref": "CONSOLIDAÇÃO"
                                    }
                                    
                                    prompt_h = (
                                        f"ID_FORNECIDO: {nome_elite_c}.\n"
                                        f"SÉRIE ALVO: {ano_alvo}º Ano.\n"
                                        f"DISTRIBUIÇÃO EXATA DE QUESTÕES (TOTAL: {total_q}):\n"
                                        f"- {qtd_trad} Questões Tradicionais (Mecânica/Cálculo).\n"
                                        f"- {qtd_cot} Questões de Cotidiano Real.\n"
                                        f"- {qtd_tech} Questões de Rotina Tecnológica (Use o Google Search para dados reais).\n"
                                        f"- {qtd_des} Questão Desafio (Boss Fight).\n"
                                        f"EXTRAS: {instr_extra_h}\n\n"
                                        f"BASE DE CONHECIMENTO (Use os conceitos ensinados nestas aulas para criar as questões):\n{contexto_aulas}\n\n"
                                        f"MISSÃO: Use o ID_FORNECIDO na tag [SOSA_ID]. Gere o material completo com as TAGS [SOSA_ID],[PROFESSOR], [ALUNO], [GABARITO],[PEI], [GABARITO_PEI],[IMAGENS]."
                                    )
                                    
                                    st.session_state.lab_temp = ai.gerar_ia("ARQUITETO_LISTAS_HIBRIDAS", prompt_h, usar_busca=True)
                                    st.session_state.v_lab = int(time.time())
                                    st.rerun()

            else:
                contexto_scanner = ""
                with st.container(border=True):
                    st.markdown("#### 🔍 1. Análise de Evidências (Scanner)")
                    c_t1, c_t2 = st.columns([1, 1])
                    turma_interv = c_t1.selectbox("Selecione a Turma para Diagnóstico:", sorted(df_alunos['TURMA'].unique()), key=f"comp_turma_{v}")
                    ano_origem = c_t2.selectbox("Buscar base em qual série?",[1, 2, 3, 4, 5, 6, 7, 8], index=ano_alvo-2, key=f"comp_ano_orig_{v}")
                    
                    if not df_diagnosticos.empty:
                        erros_turma = df_diagnosticos[df_diagnosticos['TURMA'] == turma_interv]
                        if not erros_turma.empty:
                            media_baixa = erros_turma[erros_turma['NOTA_CALCULADA'].apply(util.sosa_to_float) < 6.0]
                            if not media_baixa.empty:
                                lista_avs = media_baixa['ID_AVALIACAO'].unique()
                                st.error(f"🚨 **Lacunas Detectadas:** A turma teve baixo desempenho em: {', '.join(lista_avs[:2])}")
                                contexto_scanner = f"A Turma {turma_interv} apresentou dificuldades reais nas avaliações: {lista_avs}. Foque em resgatar a base do {ano_origem}º ano."
                            else:
                                st.success("✅ Turma com bom desempenho médio no Scanner.")

                df_cur_comp = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_origem))]
                
                if not df_cur_comp.empty:
                    with st.container(border=True):
                        c_f1, c_f2 = st.columns(2)
                        sel_eixo_c = c_f1.multiselect("2. Eixo da Matriz:", sorted(df_cur_comp["EIXO"].unique().tolist()), key=f"comp_eixo_{v}")
                        if sel_eixo_c:
                            sel_cont_c = c_f2.multiselect("3. Conteúdo Base:", sorted(df_cur_comp[df_cur_comp["EIXO"].isin(sel_eixo_c)]["CONTEUDO_ESPECIFICO"].unique().tolist()), key=f"comp_cont_{v}")
                            if sel_cont_c:
                                sel_obj_c = st.multiselect("4. Objetivos Oficiais:", sorted(df_cur_comp[df_cur_comp["CONTEUDO_ESPECIFICO"].isin(sel_cont_c)]["OBJETIVOS"].unique().tolist()), key=f"comp_obj_{v}")
                                
                                st.divider()
                                c_q1, c_q2, c_q3 = st.columns([1, 1, 2])
                                tipo_comp = c_q1.selectbox("Objetivo:",["Fixação", "Reforço", "Aprofundamento", "Recomposição"], key=f"comp_tipo_{v}")
                                qtd_q_comp = c_q2.slider("Nº Questões:", 3, 15, 10, key=f"comp_q_{v}")
                                instr_extra_c = c_q3.text_area("📝 Contexto Adicional:", key=f"comp_instr_{v}")

                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🧠 INICIAR MOTOR DE IA: GERAR RECOMPOSIÇÃO", use_container_width=True, type="primary"):
                                    if "chat_history_lab" in st.session_state:
                                        del st.session_state["chat_history_lab"]
                                        
                                    with st.spinner("Maestro Sosa arquitetando material com DNA único..."):
                                        sosa_id_hash = util.gerar_sosa_id(tipo_comp, ano_alvo, "I") 
                                        nome_elite_c = f"RECOMP - {turma_interv} - {sosa_id_hash}"
                                        
                                        st.session_state.sosa_id_atual = nome_elite_c
                                        st.session_state.lab_meta = {
                                            "ano": ano_alvo, 
                                            "trimestre": "I Trimestre", 
                                            "tipo": tipo_comp.upper(), 
                                            "semana_ref": "RECOMPOSIÇÃO"
                                        }
                                        
                                        prompt_c = (
                                            f"ID_FORNECIDO: {nome_elite_c}.\n"
                                            f"SÉRIE ALVO: {ano_alvo}º Ano | SÉRIE ORIGEM: {ano_origem}º Ano.\n"
                                            f"OBJETIVO: {tipo_comp}. CONTEXTO SCANNER: {contexto_scanner}.\n"
                                            f"CONTEÚDOS: {', '.join(sel_cont_c)}.\n"
                                            f"OBJETIVOS: {', '.join(sel_obj_c)}.\n"
                                            f"QUANTIDADE: {qtd_q_comp} questões. EXTRAS: {instr_extra_c}.\n\n"
                                            f"MISSÃO: Use o ID_FORNECIDO na tag[SOSA_ID]. Gere com as TAGS [VALOR: 0.0],[SOSA_ID],[MAPA_DE_RECOMPOSICAO], [PROFESSOR], [ALUNO],[RESPOSTAS_PEDAGOGICAS], [GRADE_DE_CORRECAO], [PEI]."
                                        )
                                        
                                        st.session_state.lab_temp = ai.gerar_ia("ARQUITETO_RECOMPOSICAO_V68_ELITE", prompt_c, usar_busca=True)
                                        st.session_state.v_lab = int(time.time())
                                        st.rerun()

        # --- ABA 4: ACERVO DE MATERIAIS ---
        with tab_acervo_lab:
            st.subheader("📂 Gestão de Acervo de Materiais")
            st.caption("Histórico de todas as aulas, projetos e listas geradas.")
            
            c_m1, c_m2, c_m3 = st.columns([1, 1, 1])
            f_trim_m = c_m1.selectbox("📅 Filtrar Trimestre:",["Todos", "I Trimestre", "II Trimestre", "III Trimestre"], key="m_trim_filter")
            f_ano_m = c_m2.selectbox("🎓 Filtrar Série:",["Todos", "6º", "7º", "8º", "9º"], key="m_ano_filter")
            f_tipo_m = c_m3.selectbox("🧪 Tipo de Ativo:",["Todos", "Aula", "PROJETO", "Fixação", "Reforço", "Recomposição", "Lista"], key="m_tipo_filter")

            df_m = df_aulas[~df_aulas['SEMANA_REF'].isin(["AVALIAÇÃO", "REVISÃO"])].copy()
            termos_proibidos =["TESTE", "PROVA", "SONDA", "RECUPERAÇÃO", "2ª CHAMADA"]
            df_m = df_m[~df_m['TIPO_MATERIAL'].str.upper().str.contains('|'.join(termos_proibidos), na=False)]

            if f_trim_m != "Todos":
                df_m = df_m[df_m['CONTEUDO'].str.contains(f_trim_m, na=False)]
            if f_ano_m != "Todos":
                df_m = df_m[df_m['ANO'] == f_ano_m]
            if f_tipo_m != "Todos":
                df_m = df_m[df_m['TIPO_MATERIAL'].str.upper().str.contains(f_tipo_m.upper())]

            df_m = df_m.iloc[::-1] 

            if not df_m.empty:
                st.write(f"📚 **Materiais Didáticos Localizados:** {len(df_m)}")
                for _, row in df_m.iterrows():
                    with st.container(border=True):
                        txt_f = str(row['CONTEUDO'])
                        identificador = row['TIPO_MATERIAL']
                        
                        st.markdown(f"#### 📘 {identificador}")
                        
                        def buscar_link_soberano(texto, rotulo, link_reserva):
                            padrao = rf"{rotulo}\s*\(?\s*(https?://[^\s\)]+)\)?"
                            match = re.search(padrao, texto, re.IGNORECASE)
                            if match:
                                return match.group(1).strip()
                            if rotulo.lower() in["regular", "aluno"]:
                                return link_reserva
                            return None

                        l_alu = buscar_link_soberano(txt_f, "Regular", row.get('LINK_DRIVE'))
                        l_pei = buscar_link_soberano(txt_f, "PEI", None)
                        l_prof = buscar_link_soberano(txt_f, "Prof", None)

                        c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)

                        if l_alu and "http" in str(l_alu):
                            c_b1.link_button("📝 ALUNO", str(l_alu), use_container_width=True, type="primary")
                        else:
                            c_b1.button("⚪ SEM LINK", disabled=True, use_container_width=True)

                        if l_pei and "http" in str(l_pei) and "N/A" not in str(l_pei):
                            c_b2.link_button("♿ PEI", str(l_pei), use_container_width=True)
                        else:
                            c_b2.button("⚪ SEM PEI", disabled=True, use_container_width=True)

                        if l_prof and "http" in str(l_prof) and "N/A" not in str(l_prof):
                            c_b3.link_button("👨‍🏫 PROF", str(l_prof), use_container_width=True)
                        else:
                            c_b3.button("⚪ SEM GUIA", disabled=True, use_container_width=True)
                        
                        if c_b4.button("🔄 REFINAR", key=f"ref_mat_h_{row.name}", use_container_width=True):
                            st.session_state.lab_temp = txt_f
                            st.session_state.sosa_id_atual = identificador
                            st.session_state.lab_meta = {"ano": str(row["ANO"]).replace("º",""), "semana_ref": row['SEMANA_REF']}
                            if "chat_history_lab" in st.session_state: del st.session_state["chat_history_lab"]
                            st.rerun()
                            
                        if c_b5.button("🗑️ APAGAR", key=f"del_mat_h_{row.name}", use_container_width=True):
                            if db.excluir_registro_com_drive("DB_AULAS_PRONTAS", identificador):
                                st.rerun()

                        with st.expander("👁️ ANALISAR ESTRUTURA PEDAGÓGICA E ITENS"):
                            t_prof, t_alu, t_gab, t_pei_tab, t_img = st.tabs([
                                "👨‍🏫 Guia do Professor", "📝 Material do Aluno", "✅ Gabarito", "♿ Inclusão PEI", "🎨 Imagens"
                            ])
                            
                            with t_prof:
                                val_prof = ai.extrair_tag(txt_f, "PROFESSOR")
                                st.info(val_prof if val_prof else "Conteúdo não localizado.")

                            with t_alu:
                                val_alu = ai.extrair_tag(txt_f, "ALUNO")
                                if val_alu:
                                    st.write(val_alu)
                                else: st.write("Roteiro não localizado.")

                            with t_gab:
                                val_gab = ai.extrair_tag(txt_f, "GABARITO")
                                st.success(val_gab if val_gab else "Gabarito não disponível.")

                            with t_pei_tab:
                                val_pei = ai.extrair_tag(txt_f, "PEI")
                                st.warning(val_pei if val_pei else "Nenhuma adaptação registrada.")
                                
                            with t_img:
                                val_img = ai.extrair_tag(txt_f, "IMAGENS")
                                if val_img:
                                    st.info(val_img)
                                else:
                                    st.caption("Nenhum prompt de imagem gerado para este material.")
            else:
                st.info("📭 Nenhum material didático encontrado.")


# ==============================================================================
# MÓDULO: LABORATÓRIO DE PRODUÇÃO (CRIADOR DE AULAS) - CLEAN & UX
# ==============================================================================
elif menu == "🧪 Criador de Aulas":
    st.title("🧪 Laboratório de Produção Semiótica")
    st.markdown("---")
    st.caption("💡 **Guia de Comando:** Transforme seus planejamentos (Ponto ID) em materiais físicos de alta densidade (Folha do Aluno, Guia do Professor e Adaptação PEI) com um clique.")
    
    def reset_laboratorio():
        keys_to_del =["lab_temp", "lab_pei", "lab_gab_pei", "refino_lab_ativo", "sosa_id_atual", "lab_meta", "hub_origem"]
        for k in keys_to_del:
            if k in st.session_state: del st.session_state[k]
        st.cache_data.clear() 
        st.session_state.v_lab = int(time.time())
        st.rerun()

    if "v_lab" not in st.session_state: 
        st.session_state.v_lab = int(time.time())
    v = st.session_state.v_lab

    meta = st.session_state.get("lab_meta", {})
    is_hub = meta.get("tipo") == "PRODUÇÃO_HUB"
    
    # --- ÁREA DE EXIBIÇÃO E REFINO ---
    if "lab_temp" in st.session_state:
        txt_base = st.session_state.lab_temp
        s_id = st.session_state.get("sosa_id_atual", "SEM-ID")
        st.success(f"💎 Material em Edição: **{s_id}**")

        with st.container(border=True):
            st.subheader("🤖 Refinador Maestro (Ajuste Rápido)")
            st.caption("Peça para a IA reescrever partes específicas antes de salvar o documento final.")
            cmd_refine_lab = st.chat_input("Ex: 'Deixe o texto do aluno mais simples' ou 'Adicione mais uma questão'...", key=f"chat_lab_ref_{v}")
            if cmd_refine_lab:
                with st.spinner("Reengenharia em curso..."):
                    st.session_state.lab_temp = ai.gerar_ia("REFINADOR_MATERIAIS", f"ORDEM: {cmd_refine_lab}\n\nATUAL:\n{txt_base}")
                    st.rerun()
            if st.button("🗑️ DESCARTAR EDIÇÃO E VOLTAR"): reset_laboratorio()
        
        t_prof, t_alu, t_gab, t_pei, t_img, t_sync = st.tabs(["👨‍🏫 Professor", "📝 Aluno", "✅ Gabarito", "♿ PEI", "🎨 Imagens", "☁️ SINCRONIA"])
        with t_prof: st.text_area("Lousa/Mediação:", ai.extrair_tag(txt_base, "PROFESSOR"), height=450, key=f"ed_prof_reg_{v}")
        with t_alu: st.text_area("Folha/Roteiro:", ai.extrair_tag(txt_base, "ALUNO"), height=450, key=f"ed_alu_reg_{v}")
        with t_gab: st.text_area("Gabarito:", ai.extrair_tag(txt_base, "GABARITO"), height=200, key=f"ed_res_reg_{v}")
        with t_pei: st.text_area("PEI (Obrigatório):", ai.extrair_tag(txt_base, "PEI"), height=400, key=f"ed_pei_reg_{v}")
        with t_img: st.text_area("Prompts de Imagem:", ai.extrair_tag(txt_base, "IMAGENS"), height=200, key=f"ed_img_reg_{v}")

        # --- ☁️ ABA DE SINCRONIA (TRIPLE-SYNC) ---
        with t_sync:
            st.subheader("🚀 Sincronia e Custódia Digital")
            st.info("Este comando irá gerar os documentos oficiais (DOCX) e salvar os links permanentes no seu banco de dados.")
            
            if st.button("💾 SALVAR MATERIAL E SINCRONIZAR NO DRIVE", use_container_width=True, type="primary", key=f"btn_triple_{v}"):
                with st.status("Sincronizando Ativos de Elite...") as status:
                    db.excluir_registro_com_drive("DB_AULAS_PRONTAS", s_id)
                    
                    ano_str = f"{meta.get('ano', '6')}º"
                    sem_ref = meta.get('semana_ref', 'Geral')
                    info_doc = {"ano": ano_str, "trimestre": "I Trimestre", "semana": sem_ref}

                    status.write("📝 Gerando Material do Aluno/Roteiro...")
                    doc_alu = exporter.gerar_docx_aluno_v24(s_id, ai.extrair_tag(txt_base, "ALUNO"), info_doc)
                    link_alu = db.subir_e_converter_para_google_docs(doc_alu, f"{s_id}_ALUNO", modo="AULA")
                    
                    status.write("♿ Gerando Atividade Adaptada PEI...")
                    doc_pei = exporter.gerar_docx_pei_v25(f"{s_id}_PEI", ai.extrair_tag(txt_base, "PEI"), info_doc)
                    link_pei = db.subir_e_converter_para_google_docs(doc_pei, f"{s_id}_PEI", modo="AULA")
                    
                    status.write("👨‍🏫 Gerando Guia de Mediação do Professor...")
                    doc_prof = exporter.gerar_docx_professor_v25(s_id, ai.extrair_tag(txt_base, "PROFESSOR"), info_doc)
                    link_prof = db.subir_e_converter_para_google_docs(doc_prof, f"{s_id}_PROF", modo="AULA")
                    
                    links_f = f"--- LINKS ---\nRegular({link_alu})\nPEI({link_pei})\nProf({link_prof})"
                    conteudo_final = txt_base + f"\n\n{links_f}"
                    
                    db.salvar_no_banco("DB_AULAS_PRONTAS",[
                        datetime.now().strftime("%d/%m/%Y"), 
                        sem_ref, 
                        s_id, 
                        conteudo_final, 
                        ano_str, 
                        link_alu
                    ])
                    
                    status.update(label="✅ Sincronizado com Sucesso!", state="complete")
                    st.balloons()
                    time.sleep(1)
                    reset_laboratorio()

    # --- SEÇÃO DE ENTRADA (CONFIGURAÇÃO COM INTELIGÊNCIA DE TRILHAS) ---
    else:
        tab_producao, tab_trabalhos, tab_complementar, tab_acervo_lab = st.tabs([
            "🚀 1. Produção de Aulas", "📋 2. Projetos e Trabalhos", "📚 3. Listas e Recomposição", "📂 4. Acervo de Materiais"
        ])

        with tab_producao:
            st.markdown("### ⚙️ Passo 1: Herança Didática (Ponto ID)")
            
            mostrar_tudo_lab = st.toggle("🔄 Mostrar semanas e aulas já concluídas (Modo Sobrescrita)", help="Ative se precisar refazer uma aula que já foi gerada e salva no acervo.", key=f"tog_lab_{v}")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                ano_lab = c1.selectbox("Série/Ano Alvo:", [6, 7, 8, 9], key=f"prod_ano_{v}")
                planos_ano = df_planos[df_planos["ANO"].astype(str).str.contains(str(ano_lab))]
                
                if planos_ano.empty: 
                    st.error("❌ Nenhum planejamento encontrado para esta série. Vá ao Ponto ID primeiro.")
                else:
                    # Lógica de filtragem de semanas concluídas
                    semanas_pendentes = []
                    for sem in planos_ano["SEMANA"].unique().tolist():
                        p_row = planos_ano[planos_ano["SEMANA"] == sem].iloc[0]
                        p_txt = str(p_row['PLANO_TEXTO'])
                        
                        pede_a2 = len(ai.extrair_tag(p_txt, "AULA_2")) > 30 and "N/A" not in ai.extrair_tag(p_txt, "AULA_2").upper()
                        t_sab = ai.extrair_tag(p_txt, "SABADO_LETIVO")
                        pede_sab = len(t_sab) > 10 and "N/A" not in t_sab.upper() and "NÃO PROGRAMADA" not in t_sab.upper()
                        
                        a_geradas = df_aulas[(df_aulas['ANO'].str.contains(str(ano_lab))) & (df_aulas['SEMANA_REF'] == sem)]['TIPO_MATERIAL'].astype(str).tolist()
                        t_a1 = any("Aula 1" in mat for mat in a_geradas)
                        t_a2 = any("Aula 2" in mat for mat in a_geradas)
                        t_sab_gen = any("Sábado" in mat or "Sabado" in mat for mat in a_geradas)
                        
                        if (not t_a1) or (pede_a2 and not t_a2) or (pede_sab and not t_sab_gen):
                            semanas_pendentes.append(sem)
                    
                    semanas_opcoes = planos_ano["SEMANA"].unique().tolist() if mostrar_tudo_lab else semanas_pendentes
                    
                    if not semanas_opcoes:
                        st.success("✅ Todas as semanas planejadas para esta série já tiveram seus materiais produzidos! O acervo está completo.")
                    else:
                        sem_lab = c2.selectbox("Semana Base (Herdada do Ponto ID):", semanas_opcoes, key=f"prod_sem_{v}")
                        plano_row = planos_ano[planos_ano["SEMANA"] == sem_lab].iloc[0]
                        plano_txt = str(plano_row['PLANO_TEXTO'])

                        with st.expander("📡 Radar de Regência (Memória das Turmas)", expanded=True):
                            st.caption("O sistema verifica onde você parou na última aula para garantir a continuidade.")
                            contexto_turmas_ia = ""
                            reg_ano = df_registro_aulas[df_registro_aulas['TURMA'].str.contains(str(ano_lab))]
                            if not reg_ano.empty:
                                for t_nome in sorted(reg_ano['TURMA'].unique()):
                                    dados_t = reg_ano[reg_ano['TURMA'] == t_nome].iloc[-1]
                                    est = dados_t.get('STATUS_EXECUCAO', 'Não Iniciado')
                                    pnt = dados_t.get('PONTE_PEDAGOGICA', 'Sem pendências.')
                                    emoji = "🟢" if "Concluído" in est else "🟡" if "Parcial" in est else "🔴"
                                    st.write(f"{emoji} **{t_nome}:** {est}")
                                    contexto_turmas_ia += f"- Turma {t_nome}: Status {est}. Pendência: {pnt}\n"
                            else: st.info("ℹ️ Nenhuma regência anterior registrada.")

                        base_herdada = ai.extrair_tag(plano_txt, "BASE_DIDATICA")
                        
                        metodo_entrega = st.radio("🎯 Método de Entrega:",[
                            "🚀 Geração Integral (SOSA AI)", 
                            "📖 Livro Didático + PEI (Híbrido)",
                            "🎟️ Registro de Evento / Dinâmica (Sem Material Físico)"
                        ], horizontal=True, help="Integral: A IA cria o texto e as questões. Livro: A IA cria o roteiro baseado nas páginas do livro. Evento: Apenas registra a aula no sistema.", key=f"metodo_{v}")
                        
                        aulas_ja_geradas = df_aulas[(df_aulas['ANO'].str.contains(str(ano_lab))) & (df_aulas['SEMANA_REF'] == sem_lab)]['TIPO_MATERIAL'].astype(str).tolist()
                        
                        tem_aula1 = any("Aula 1" in mat for mat in aulas_ja_geradas)
                        tem_aula2 = any("Aula 2" in mat for mat in aulas_ja_geradas)
                        tem_sabado = any("Sábado" in mat or "Sabado" in mat for mat in aulas_ja_geradas)

                        plano_pede_a2 = len(ai.extrair_tag(plano_txt, "AULA_2")) > 30 and "N/A" not in ai.extrair_tag(plano_txt, "AULA_2").upper()
                        txt_sabado = ai.extrair_tag(plano_txt, "SABADO_LETIVO")
                        plano_pede_sab = len(txt_sabado) > 10 and "N/A" not in txt_sabado.upper() and "NÃO PROGRAMADA" not in txt_sabado.upper()

                        opcoes_disponiveis =[]
                        if not tem_aula1: opcoes_disponiveis.append("Aula 1")
                        if plano_pede_a2 and not tem_aula2: opcoes_disponiveis.append("Aula 2")
                        if plano_pede_sab and not tem_sabado: opcoes_disponiveis.append("Sábado Letivo")

                        if mostrar_tudo_lab:
                            opcoes_disponiveis = ["Aula 1"]
                            if plano_pede_a2: opcoes_disponiveis.append("Aula 2")
                            if plano_pede_sab: opcoes_disponiveis.append("Sábado Letivo")

                        obj_geral = ai.extrair_tag(plano_txt, "OBJETO_CONHECIMENTO") or ai.extrair_tag(plano_txt, "CONTEUDO_GERAL")
                        
                        with st.container(border=True):
                            st.markdown(f"#### 🎯 Alvo Curricular: {obj_geral}")
                            
                            if not opcoes_disponiveis:
                                st.success("✅ Todas as aulas previstas para esta semana já foram produzidas! O acervo está completo.")
                                aula_alvo_prod = None
                            else:
                                col_config1, col_config2 = st.columns([1, 1])
                                with col_config1:
                                    aula_alvo_prod = st.radio("🚀 Material a Gerar:", opcoes_disponiveis, horizontal=True, key=f"prod_alvo_{v}")
                                with col_config2:
                                    if "Evento" not in metodo_entrega:
                                        qtd_q_prod = st.slider("Nº de Questões (PEI/Regular):", 1, 20, 10, key=f"prod_q_{v}")
                                    else:
                                        nome_evento = st.text_input("Nome do Evento/Dinâmica:", placeholder="Ex: Palestra sobre a Dengue", key=f"nome_ev_{v}")

                                if "1" in aula_alvo_prod: tag_roteiro = "AULA_1"
                                elif "2" in aula_alvo_prod: tag_roteiro = "AULA_2"
                                else: tag_roteiro = "SABADO_LETIVO"
                                
                                roteiro_especifico = ai.extrair_tag(plano_txt, tag_roteiro)
                                
                                roteiro_upper = roteiro_especifico.upper()
                                termos_av =["LOGÍSTICA DE APLICAÇÃO", "APLICAÇÃO DE AVALIAÇÃO", "APLICAÇÃO DE PROVA", "APLICAÇÃO DE TESTE", "APLICAÇÃO DA SONDA", "APLICAÇÃO DO EXAME"]
                                termos_cor =["CORREÇÃO COMENTADA", "CLÍNICA PEDAGÓGICA", "CORREÇÃO DE AVALIAÇÃO", "CORREÇÃO DA PROVA", "CORREÇÃO DO TESTE", "CORREÇÃO DA SONDA", "MAPEAMENTO DE DISTRATORES"]
                                
                                is_avaliacao = any(t in roteiro_upper for t in termos_av)
                                is_correcao = any(t in roteiro_upper for t in termos_cor)
                                
                                paginas_aula = base_herdada
                                if ";" in base_herdada:
                                    partes_pag = base_herdada.split(";")
                                    if "1" in aula_alvo_prod: paginas_aula = partes_pag[0].strip()
                                    elif "2" in aula_alvo_prod and len(partes_pag) > 1: paginas_aula = partes_pag[1].strip()
                                    else: paginas_aula = partes_pag[-1].strip()

                                with st.expander(f"👁️ Roteiro Herdado para {aula_alvo_prod}", expanded=False):
                                    st.info(f"📍 **Páginas Alvo:** {paginas_aula}\n\n{roteiro_especifico}")

                                conteudo_prova_vinculada = ""
                                if is_correcao or is_avaliacao:
                                    st.markdown("---")
                                    st.warning("🔍 **Modo de Avaliação/Correção Detectado:** Selecione a prova correspondente para que a IA possa ler as questões e gerar o guia.")
                                    
                                    mask_provas = df_aulas['TIPO_MATERIAL'].str.upper().str.contains("PROVA|TESTE|SONDA|AVALIAÇÃO|EXAME")
                                    provas_disponiveis = df_aulas[(df_aulas['ANO'].str.contains(str(ano_lab))) & mask_provas]
                                    
                                    if not provas_disponiveis.empty:
                                        prova_sel = st.selectbox("Vincular Avaliação do Acervo:",[""] + provas_disponiveis['TIPO_MATERIAL'].tolist(), key=f"vinc_prova_{v}")
                                        if prova_sel:
                                            conteudo_prova_vinculada = provas_disponiveis[provas_disponiveis['TIPO_MATERIAL'] == prova_sel].iloc[0]['CONTEUDO']
                                            st.success("✅ Avaliação vinculada! A IA usará as questões reais para montar a aula.")
                                    else:
                                        st.info("Nenhuma avaliação encontrada no acervo para esta série.")

                        if opcoes_disponiveis:
                            if "Evento" in metodo_entrega:
                                if st.button("💾 OFICIALIZAR EVENTO NO ACERVO", use_container_width=True, type="primary"):
                                    if not nome_evento:
                                        st.error("⚠️ Digite o nome do evento para registrar.")
                                    else:
                                        with st.spinner("Registrando evento com rastreabilidade curricular..."):
                                            hab_herdada = ai.extrair_tag(plano_txt, "HABILIDADE_BNCC")
                                            cont_herdado = ai.extrair_tag(plano_txt, "CONTEUDOS_ESPECIFICOS")
                                            obj_herdado = ai.extrair_tag(plano_txt, "OBJETIVOS_ENSINO")
                                            
                                            conteudo_fantasma = (
                                                f"[PROFESSOR]\n"
                                                f"🎟️ **REGISTRO DE EVENTO / DINÂMICA**\n"
                                                f"**Tema:** {nome_evento}\n"
                                                f"**Habilidade:** {hab_herdada}\n"
                                                f"**Conteúdos:** {cont_herdado}\n"
                                                f"**Objetivos:** {obj_herdado}\n\n"
                                                f"**Roteiro Executado:**\n{roteiro_especifico}\n\n"
                                                f"[ALUNO]\nAtividade prática/evento. Sem material físico gerado.\n\n"
                                                f"[GABARITO]\nN/A\n\n"
                                                f"[PEI]\nParticipação inclusiva no evento garantida via mediação direta.\n\n"
                                                f"--- LINKS ---\nRegular(N/A)\nPEI(N/A)\nProf(N/A)"
                                            )
                                            
                                            nome_elite = util.gerar_nome_material_elite(ano_lab, aula_alvo_prod, nome_evento)
                                            
                                            db.salvar_no_banco("DB_AULAS_PRONTAS",[
                                                datetime.now().strftime("%d/%m/%Y"), 
                                                sem_lab, 
                                                nome_elite, 
                                                conteudo_fantasma, 
                                                f"{ano_lab}º", 
                                                "N/A"
                                            ])
                                            st.success("✅ Evento oficializado no Acervo! Já disponível no Cockpit.")
                                            time.sleep(1.5)
                                            st.rerun()
                            else:
                                uri_referencia_aula = None
                                if "Livro" in metodo_entrega:
                                    nome_livro_limpo = base_herdada.split('|')[0].replace("Livro:", "").strip()
                                    match_biblioteca = df_materiais[df_materiais['NOME_ARQUIVO'].str.contains(nome_livro_limpo[:10], case=False, na=False)]
                                    if not match_biblioteca.empty:
                                        uri_referencia_aula = match_biblioteca.iloc[0]['URI_ARQUIVO']
                                        st.success(f"📚 **Fonte Vinculada:** {match_biblioteca.iloc[0]['NOME_ARQUIVO']} (Páginas: {paginas_aula})")

                                alunos_foco = df_alunos[(df_alunos['TURMA'].str.contains(str(ano_lab))) & (~df_alunos['NECESSIDADES'].isin(["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"]))]
                                texto_clinico = ", ".join(alunos_foco['NECESSIDADES'].unique().tolist()) if not alunos_foco.empty else "PADRÃO"
                                if not alunos_foco.empty: st.warning(f"♿ **Sensor PEI Ativo:** {texto_clinico}")
                                
                                instr_extra_prod = st.text_area("📝 Contexto Extra / Ajustes Específicos:", placeholder="Ex: Focar mais em frações equivalentes...", key=f"prod_extra_{v}")

                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🧠 INICIAR MOTOR DE IA: GERAR AULA", use_container_width=True, type="primary"):
                                    with st.spinner("Sosa estudando o roteiro e arquitetando material..."):
                                        
                                        nome_elite = util.gerar_nome_material_elite(ano_lab, aula_alvo_prod, sem_lab)
                                        st.session_state.sosa_id_atual = nome_elite
                                        st.session_state.lab_meta = {"ano": ano_lab, "semana_ref": sem_lab}
                                        
                                        if "Geração Integral" in metodo_entrega:
                                            regra_livro = "3. MODO MANUAL: Crie o conteúdo do zero com base na BNCC. É TERMINANTEMENTE PROIBIDO citar páginas de livros didáticos."
                                        else:
                                            regra_livro = "3. MODO LIVRO: O roteiro deve dizer exatamente: 'Inicie na página X explorando a imagem Y...' baseando-se no PDF."

                                        if is_avaliacao and not is_correcao:
                                            missao_especifica = (
                                                f"🚨 ATENÇÃO: Esta é uma aula de APLICAÇÃO DE AVALIAÇÃO.\n"
                                                f"1. Na tag [PROFESSOR]: Escreva apenas as instruções de logística, tempo, regras da prova e orientações de preenchimento de gabarito.\n"
                                                f"2. Nas tags [ALUNO] e [PEI]: Escreva APENAS 'Material de avaliação impresso separadamente. Não há atividade de caderno hoje.'\n"
                                                f"3. É TERMINANTEMENTE PROIBIDO gerar questões ou exercícios.\n"
                                                f"🚨 FORMATO OBRIGATÓRIO: Você DEVE separar o texto usando EXATAMENTE as tags entre colchetes: [PROFESSOR], [ALUNO], [PEI], [GABARITO], [IMAGENS]."
                                            )
                                        elif is_correcao:
                                            missao_especifica = (
                                                f"🚨 ATENÇÃO: Esta é uma aula de CORREÇÃO DE AVALIAÇÃO (Clínica Pedagógica).\n"
                                                f"1. Na tag [PROFESSOR]: Escreva um guia de como mediar a correção no quadro. USE AS QUESTÕES DA AVALIAÇÃO VINCULADA ABAIXO para dar exemplos reais de como explicar os erros (distratores).\n"
                                                f"2. Nas tags [ALUNO] e [PEI]: Escreva APENAS 'Acompanhamento da correção no quadro e anotações de feedback. Não há nova lista de exercícios hoje.'\n"
                                                f"3. É TERMINANTEMENTE PROIBIDO gerar novas questões.\n"
                                                f"🚨 FORMATO OBRIGATÓRIO: Você DEVE separar o texto usando EXATAMENTE as tags entre colchetes: [PROFESSOR], [ALUNO], [PEI], [GABARITO],[IMAGENS]."
                                            )
                                        else:
                                            missao_especifica = (
                                                f"🚨 MISSÃO DE ALTA DENSIDADE E RIGOR QUANTITATIVO:\n"
                                                f"1. [PROFESSOR]: Escreva um TRATADO DIDÁTICO denso. Explique o conceito de {obj_geral} com profundidade técnica antes de dar o roteiro de aula.\n"
                                                f"2. CONEXÃO ALPHA: Use o Google Search para trazer dados científicos reais de 2026 que validem a importância deste tema.\n"
                                                f"{regra_livro}\n"
                                                f"4. [ALUNO] (REGULAR): É OBRIGATÓRIO gerar EXATAMENTE {qtd_q_prod} questões inéditas e desafiadoras. Formato: **QUESTÃO X.** enunciado.\n"
                                                f"5. [PEI] (INCLUSÃO): É OBRIGATÓRIO gerar EXATAMENTE {qtd_q_prod} questões adaptadas, cada uma com [PARA LEMBRAR],[PASSO A PASSO] e [ PROMPT IMAGEM ].\n"
                                                f"6.[GABARITO]: Forneça as respostas detalhadas para as {qtd_q_prod} questões regulares e as {qtd_q_prod} questões PEI.\n"
                                                f"🚨 FORMATO OBRIGATÓRIO: Você DEVE separar o texto usando EXATAMENTE as tags entre colchetes: [PROFESSOR], [ALUNO], [PEI], [GABARITO], [IMAGENS]."
                                            )

                                        prompt_manual = (
                                            f"PERSONA: MAESTRO_SOSA_V28_ELITE. ID: {nome_elite}.\n"
                                            f"MÉTODO: {metodo_entrega}. REFERÊNCIA: {base_herdada}\n"
                                            f"SÉRIE: {ano_lab}º Ano. ALVO: {aula_alvo_prod}.\n\n"
                                            f"{missao_especifica}\n\n"
                                            f"--- HERANÇA DO PLANO ATUAL ---\n{roteiro_especifico}\n"
                                            f"--- MEMÓRIA DE REGÊNCIA (PONTE PEDAGÓGICA) ---\n{contexto_turmas_ia}\n"
                                            f"--- SENSOR DE INCLUSÃO ---\nA turma possui alunos com: {texto_clinico}."
                                        )
                                        
                                        if conteudo_prova_vinculada:
                                            prompt_manual += f"\n\n--- CONTEÚDO DA AVALIAÇÃO VINCULADA ---\n{conteudo_prova_vinculada}"
                                        
                                        resultado_ia = ai.gerar_ia(
                                            "MAESTRO_SOSA_V28_ELITE", 
                                            prompt_manual, 
                                            url_drive=uri_referencia_aula, 
                                            usar_busca=True
                                        )
                                        
                                        import re
                                        tags_para_limpar =["PROFESSOR", "ALUNO", "PEI", "GABARITO", "GABARITO_PEI", "IMAGENS"]
                                        for t in tags_para_limpar:
                                            resultado_ia = re.sub(rf"\*\*{t}\*\*", f"[{t}]", resultado_ia, flags=re.IGNORECASE)
                                            resultado_ia = re.sub(rf"\*\*{t}:\*\*", f"[{t}]", resultado_ia, flags=re.IGNORECASE)
                                            resultado_ia = re.sub(rf"^{t}$", f"[{t}]", resultado_ia, flags=re.IGNORECASE | re.MULTILINE)
                                            
                                        st.session_state.lab_temp = resultado_ia
                                        st.rerun()

        # --- ABA 2: ENGENHARIA DE TRABALHOS ---
        with tab_trabalhos:
            st.subheader("📋 Engenharia de Projetos e Semanários")
            st.caption("Crie roteiros de pesquisa, trabalhos em grupo e projetos interdisciplinares alinhados à BNCC.")
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.5, 1, 1])
                natureza_p = c1.selectbox("Natureza do Ativo:",["Semanário Temático", "Projeto de Identidade (Itabuna)", "Investigação Científica", "Projeto BNCC Livre"], 
                    key=f"t_nat_{v}")
                ano_t = c2.selectbox("Série Alvo:", [6, 7, 8, 9], key=f"t_ano_{v}")
                modo_t = c3.selectbox("Modo de Execução:",["Individual", "Em Grupo (Equipes)", "Interdisciplinar"], key=f"t_modo_{v}")

            with st.container(border=True):
                st.markdown("#### 🌟 Alinhamento de Competências Gerais (BNCC)")
                comps_proj = st.multiselect("Selecione as Competências Âncora do Projeto:",[
                    "1. Conhecimento", "2. Pensamento Crítico e Criativo", "3. Repertório Cultural",
                    "4. Comunicação", "5. Cultura Digital", "6. Trabalho e Projeto de Vida",
                    "7. Argumentação", "8. Autoconhecimento", "9. Empatia e Cooperação", "10. Responsabilidade e Cidadania"
                ], key=f"t_comp_bncc_{v}")

            with st.container(border=True):
                c_t1, c_t2, c_t3 = st.columns([2, 1, 1])
                tema_t = c_t1.text_input("Título do Projeto/Tema:", placeholder="Ex: A Matemática do Cacau...", key=f"t_tema_{v}")
                valor_t = c_t2.number_input("Valor (0-10):", 0.0, 10.0, 2.0, step=0.5, key=f"t_val_{v}")
                qtd_aulas_t = c_t3.slider("Duração (Aulas):", 1, 10, 2, key=f"t_q_aulas_{v}")
                
            df_cur_t = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_t))]
            if not df_cur_t.empty:
                lista_eixos_t = sorted(df_cur_t["EIXO"].unique().tolist())
                eixos_sel_t = st.multiselect("Eixos da Matriz para Integrar:", lista_eixos_t, key=f"t_eixos_multi_{v}")
                
                if eixos_sel_t:
                    df_hab_t = df_cur_t[df_cur_t["EIXO"].isin(eixos_sel_t)]
                    conts_t = st.multiselect("Conteúdos Específicos (Itabuna):", 
                                           sorted(df_hab_t["CONTEUDO_ESPECIFICO"].unique().tolist()), 
                                           key=f"t_cont_multi_{v}")
                    
                    instr_extra_p = st.text_area("📝 Instruções de Pesquisa / Contexto Adicional:", key=f"t_extra_proj_{v}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🧠 INICIAR MOTOR DE IA: GERAR PROJETO", use_container_width=True, type="primary"):
                        if not tema_t or not conts_t:
                            st.error("Defina o Título e selecione ao menos um Conteúdo da Matriz.")
                        else:
                            with st.spinner("Maestro Sosa arquitetando roteiro investigativo..."):
                                nome_legivel = util.gerar_nome_material_elite(ano_t, "Projeto", tema_t)
                                
                                st.session_state.sosa_id_atual = nome_legivel
                                st.session_state.lab_meta = {
                                    "ano": ano_t, "trimestre": "I Trimestre", 
                                    "tipo": "PROJETO", "aula_alvo": tema_t, "semana_ref": "PROJETO"
                                }
                                
                                prompt_t = (
                                    f"ID_FORNECIDO: {nome_legivel}.\n"
                                    f"TEMA: {tema_t}. NATUREZA: {natureza_p}.\n"
                                    f"SÉRIE: {ano_t}º Ano. MODO: {modo_t}.\n"
                                    f"COMPETÊNCIAS BNCC: {', '.join(comps_proj)}.\n"
                                    f"CONTEÚDOS ITABUNA: {', '.join(conts_t)}.\n"
                                    f"VALOR: {util.sosa_to_str(valor_t)} | DURAÇÃO: {qtd_aulas_t} aulas.\n"
                                    f"EXTRAS: {instr_extra_p}.\n\n"
                                    f"MISSÃO: Use o ID_FORNECIDO na tag [SOSA_ID]. Gere o material completo com as TAGS [SOSA_ID], [JUSTIFICATIVA_PHC],[CONTEXTO_INVESTIGATIVO], [MISSÃO_DE_PESQUISA], [PASSO_A_PASSO],[PRODUTO_ESPERADO], [ESTRATEGIA_DUA_PEI],[RUBRICA_DE_MERITO]."
                                )
                                st.session_state.lab_temp = ai.gerar_ia("ARQUITETO_CIENTIFICO_V33", prompt_t, usar_busca=True)
                                st.session_state.v_lab = int(time.time())
                                st.rerun()

        # --- ABA 3: ATIVIDADES COMPLEMENTARES ---
        with tab_complementar:
            st.subheader("📚 Listas Híbridas e Recomposição")
            st.caption("Crie listas de exercícios mesclando aulas anteriores ou gere material de reforço baseado em anos anteriores.")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                ano_alvo = c1.selectbox("Série Alvo (Sua Turma):", [6, 7, 8, 9], key=f"comp_ano_alvo_{v}")
                
                origem_tipo = c2.radio("Origem do Conteúdo (DNA Curricular):",["🟢 Série Atual (Lista de Consolidação Híbrida)", "🔴 Ano Anterior (Intervenção/Recomposição)"], 
                    horizontal=True, key=f"comp_origem_tipo_{v}")
            
            if "Série Atual" in origem_tipo:
                st.markdown("#### 📦 1. Herança de DNA (Aulas Base)")
                df_aulas_ano = df_aulas[df_aulas['ANO'].str.contains(str(ano_alvo))].copy()
                
                if df_aulas_ano.empty:
                    st.warning("⚠️ Nenhuma aula encontrada no acervo para esta série. Gere uma aula primeiro.")
                else:
                    aulas_puras = df_aulas_ano[df_aulas_ano['TIPO_MATERIAL'].str.contains("Aula", case=False, na=False)]
                    aulas_opcoes = aulas_puras['TIPO_MATERIAL'].tolist()[::-1]
                    
                    aulas_selecionadas = st.multiselect(
                        "Selecione 1 ou 2 aulas para basear a lista:", 
                        aulas_opcoes, 
                        max_selections=2, 
                        key=f"comp_aulas_sel_{v}"
                    )
                    
                    if aulas_selecionadas:
                        st.markdown("#### ⚙️ 2. Engenharia da Lista (Distribuição de Questões)")
                        with st.container(border=True):
                            cq1, cq2, cq3, cq4 = st.columns(4)
                            qtd_trad = cq1.number_input("📐 Tradicionais (Cálculo):", 0, 20, 4, key=f"qtd_trad_{v}")
                            qtd_cot = cq2.number_input("🛒 Cotidiano Real:", 0, 20, 3, key=f"qtd_cot_{v}")
                            qtd_tech = cq3.number_input("📱 Rotina Tecnológica:", 0, 20, 2, key=f"qtd_tech_{v}")
                            qtd_des = cq4.number_input("🔥 Desafio (Boss Fight):", 0, 5, 1, key=f"qtd_des_{v}")
                            
                            total_q = qtd_trad + qtd_cot + qtd_tech + qtd_des
                            st.info(f"**Total de Questões Regulares:** {total_q} | **Questões PEI (50%):** {max(1, total_q//2) if total_q > 0 else 0}")
                        
                        instr_extra_h = st.text_area("📝 Contexto Adicional / Foco Específico (Opcional):", placeholder="Ex: Focar mais em frações equivalentes...", key=f"comp_instr_h_{v}")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🧠 INICIAR MOTOR DE IA: GERAR LISTA HÍBRIDA", use_container_width=True, type="primary"):
                            if total_q == 0:
                                st.error("⚠️ A lista precisa ter pelo menos 1 questão configurada.")
                            else:
                                with st.spinner("Maestro Sosa varrendo a internet e arquitetando a lista híbrida..."):
                                    contexto_aulas = ""
                                    for aula_nome in aulas_selecionadas:
                                        cont_aula = df_aulas_ano[df_aulas_ano['TIPO_MATERIAL'] == aula_nome].iloc[0]['CONTEUDO']
                                        contexto_aulas += f"\n--- CONTEÚDO DA {aula_nome} ---\n{cont_aula}\n"
                                    
                                    sosa_id_hash = util.gerar_sosa_id("LISTA", ano_alvo, "I")
                                    nome_elite_c = f"{ano_alvo}º Ano - Lista Híbrida - {sosa_id_hash}"
                                    
                                    st.session_state.sosa_id_atual = nome_elite_c
                                    st.session_state.lab_meta = {
                                        "ano": ano_alvo, 
                                        "trimestre": "I Trimestre", 
                                        "tipo": "LISTA_HIBRIDA", 
                                        "semana_ref": "CONSOLIDAÇÃO"
                                    }
                                    
                                    prompt_h = (
                                        f"ID_FORNECIDO: {nome_elite_c}.\n"
                                        f"SÉRIE ALVO: {ano_alvo}º Ano.\n"
                                        f"DISTRIBUIÇÃO EXATA DE QUESTÕES (TOTAL: {total_q}):\n"
                                        f"- {qtd_trad} Questões Tradicionais (Mecânica/Cálculo).\n"
                                        f"- {qtd_cot} Questões de Cotidiano Real.\n"
                                        f"- {qtd_tech} Questões de Rotina Tecnológica (Use o Google Search para dados reais).\n"
                                        f"- {qtd_des} Questão Desafio (Boss Fight).\n"
                                        f"EXTRAS: {instr_extra_h}\n\n"
                                        f"BASE DE CONHECIMENTO (Use os conceitos ensinados nestas aulas para criar as questões):\n{contexto_aulas}\n\n"
                                        f"MISSÃO: Use o ID_FORNECIDO na tag [SOSA_ID]. Gere o material completo com as TAGS [SOSA_ID], [PROFESSOR], [ALUNO], [GABARITO],[PEI], [GABARITO_PEI], [IMAGENS]."
                                    )
                                    
                                    st.session_state.lab_temp = ai.gerar_ia("ARQUITETO_LISTAS_HIBRIDAS", prompt_h, usar_busca=True)
                                    st.session_state.v_lab = int(time.time())
                                    st.rerun()

            else:
                contexto_scanner = ""
                with st.container(border=True):
                    st.markdown("#### 🔍 1. Análise de Evidências (Scanner)")
                    c_t1, c_t2 = st.columns([1, 1])
                    turma_interv = c_t1.selectbox("Selecione a Turma para Diagnóstico:", sorted(df_alunos['TURMA'].unique()), key=f"comp_turma_{v}")
                    ano_origem = c_t2.selectbox("Buscar base em qual série?",[1, 2, 3, 4, 5, 6, 7, 8], index=ano_alvo-2, key=f"comp_ano_orig_{v}")
                    
                    if not df_diagnosticos.empty:
                        erros_turma = df_diagnosticos[df_diagnosticos['TURMA'] == turma_interv]
                        if not erros_turma.empty:
                            media_baixa = erros_turma[erros_turma['NOTA_CALCULADA'].apply(util.sosa_to_float) < 6.0]
                            if not media_baixa.empty:
                                lista_avs = media_baixa['ID_AVALIACAO'].unique()
                                st.error(f"🚨 **Lacunas Detectadas:** A turma teve baixo desempenho em: {', '.join(lista_avs[:2])}")
                                contexto_scanner = f"A Turma {turma_interv} apresentou dificuldades reais nas avaliações: {lista_avs}. Foque em resgatar a base do {ano_origem}º ano."
                            else:
                                st.success("✅ Turma com bom desempenho médio no Scanner.")

                df_cur_comp = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_origem))]
                
                if not df_cur_comp.empty:
                    with st.container(border=True):
                        c_f1, c_f2 = st.columns(2)
                        sel_eixo_c = c_f1.multiselect("2. Eixo da Matriz:", sorted(df_cur_comp["EIXO"].unique().tolist()), key=f"comp_eixo_{v}")
                        if sel_eixo_c:
                            sel_cont_c = c_f2.multiselect("3. Conteúdo Base:", sorted(df_cur_comp[df_cur_comp["EIXO"].isin(sel_eixo_c)]["CONTEUDO_ESPECIFICO"].unique().tolist()), key=f"comp_cont_{v}")
                            if sel_cont_c:
                                sel_obj_c = st.multiselect("4. Objetivos Oficiais:", sorted(df_cur_comp[df_cur_comp["CONTEUDO_ESPECIFICO"].isin(sel_cont_c)]["OBJETIVOS"].unique().tolist()), key=f"comp_obj_{v}")
                                
                                st.divider()
                                c_q1, c_q2, c_q3 = st.columns([1, 1, 2])
                                tipo_comp = c_q1.selectbox("Objetivo:", ["Fixação", "Reforço", "Aprofundamento", "Recomposição"], key=f"comp_tipo_{v}")
                                qtd_q_comp = c_q2.slider("Nº Questões:", 3, 15, 10, key=f"comp_q_{v}")
                                instr_extra_c = c_q3.text_area("📝 Contexto Adicional:", key=f"comp_instr_{v}")

                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("🧠 INICIAR MOTOR DE IA: GERAR RECOMPOSIÇÃO", use_container_width=True, type="primary"):
                                    with st.spinner("Maestro Sosa arquitetando material com DNA único..."):
                                        sosa_id_hash = util.gerar_sosa_id(tipo_comp, ano_alvo, "I") 
                                        nome_elite_c = f"RECOMP - {turma_interv} - {sosa_id_hash}"
                                        
                                        st.session_state.sosa_id_atual = nome_elite_c
                                        st.session_state.lab_meta = {
                                            "ano": ano_alvo, 
                                            "trimestre": "I Trimestre", 
                                            "tipo": tipo_comp.upper(), 
                                            "semana_ref": "RECOMPOSIÇÃO"
                                        }
                                        
                                        prompt_c = (
                                            f"ID_FORNECIDO: {nome_elite_c}.\n"
                                            f"SÉRIE ALVO: {ano_alvo}º Ano | SÉRIE ORIGEM: {ano_origem}º Ano.\n"
                                            f"OBJETIVO: {tipo_comp}. CONTEXTO SCANNER: {contexto_scanner}.\n"
                                            f"CONTEÚDOS: {', '.join(sel_cont_c)}.\n"
                                            f"OBJETIVOS: {', '.join(sel_obj_c)}.\n"
                                            f"QUANTIDADE: {qtd_q_comp} questões. EXTRAS: {instr_extra_c}.\n\n"
                                            f"MISSÃO: Use o ID_FORNECIDO na tag [SOSA_ID]. Gere com as TAGS [VALOR: 0.0],[SOSA_ID], [MAPA_DE_RECOMPOSICAO], [PROFESSOR], [ALUNO],[RESPOSTAS_PEDAGOGICAS], [GRADE_DE_CORRECAO], [PEI]."
                                        )
                                        
                                        st.session_state.lab_temp = ai.gerar_ia("ARQUITETO_RECOMPOSICAO_V68_ELITE", prompt_c, usar_busca=True)
                                        st.session_state.v_lab = int(time.time())
                                        st.rerun()

        # --- ABA 4: ACERVO DE MATERIAIS ---
        with tab_acervo_lab:
            st.subheader("📂 Gestão de Acervo de Materiais")
            st.caption("Histórico de todas as aulas, projetos e listas geradas.")
            
            c_m1, c_m2, c_m3 = st.columns([1, 1, 1])
            f_trim_m = c_m1.selectbox("📅 Filtrar Trimestre:", ["Todos", "I Trimestre", "II Trimestre", "III Trimestre"], key="m_trim_filter")
            f_ano_m = c_m2.selectbox("🎓 Filtrar Série:",["Todos", "6º", "7º", "8º", "9º"], key="m_ano_filter")
            f_tipo_m = c_m3.selectbox("🧪 Tipo de Ativo:",["Todos", "Aula", "PROJETO", "Fixação", "Reforço", "Recomposição", "Lista"], key="m_tipo_filter")

            df_m = df_aulas[~df_aulas['SEMANA_REF'].isin(["AVALIAÇÃO", "REVISÃO"])].copy()
            termos_proibidos =["TESTE", "PROVA", "SONDA", "RECUPERAÇÃO", "2ª CHAMADA"]
            df_m = df_m[~df_m['TIPO_MATERIAL'].str.upper().str.contains('|'.join(termos_proibidos), na=False)]

            if f_trim_m != "Todos":
                df_m = df_m[df_m['CONTEUDO'].str.contains(f_trim_m, na=False)]
            if f_ano_m != "Todos":
                df_m = df_m[df_m['ANO'] == f_ano_m]
            if f_tipo_m != "Todos":
                df_m = df_m[df_m['TIPO_MATERIAL'].str.upper().str.contains(f_tipo_m.upper())]

            df_m = df_m.iloc[::-1] 

            if not df_m.empty:
                st.write(f"📚 **Materiais Didáticos Localizados:** {len(df_m)}")
                for _, row in df_m.iterrows():
                    with st.container(border=True):
                        txt_f = str(row['CONTEUDO'])
                        identificador = row['TIPO_MATERIAL']
                        
                        st.markdown(f"#### 📘 {identificador}")
                        
                        def buscar_link_soberano(texto, rotulo, link_reserva):
                            padrao = rf"{rotulo}\s*\(?\s*(https?://[^\s\)]+)\)?"
                            match = re.search(padrao, texto, re.IGNORECASE)
                            if match:
                                return match.group(1).strip()
                            if rotulo.lower() in["regular", "aluno"]:
                                return link_reserva
                            return None

                        l_alu = buscar_link_soberano(txt_f, "Regular", row.get('LINK_DRIVE'))
                        l_pei = buscar_link_soberano(txt_f, "PEI", None)
                        l_prof = buscar_link_soberano(txt_f, "Prof", None)

                        c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)

                        if l_alu and "http" in str(l_alu):
                            c_b1.link_button("📝 ALUNO", str(l_alu), use_container_width=True, type="primary")
                        else:
                            c_b1.button("⚪ SEM LINK", disabled=True, use_container_width=True)

                        if l_pei and "http" in str(l_pei) and "N/A" not in str(l_pei):
                            c_b2.link_button("♿ PEI", str(l_pei), use_container_width=True)
                        else:
                            c_b2.button("⚪ SEM PEI", disabled=True, use_container_width=True)

                        if l_prof and "http" in str(l_prof) and "N/A" not in str(l_prof):
                            c_b3.link_button("👨‍🏫 PROF", str(l_prof), use_container_width=True)
                        else:
                            c_b3.button("⚪ SEM GUIA", disabled=True, use_container_width=True)
                        
                        if c_b4.button("🔄 REFINAR", key=f"ref_mat_h_{row.name}", use_container_width=True):
                            st.session_state.lab_temp = txt_f
                            st.session_state.sosa_id_atual = identificador
                            st.session_state.lab_meta = {"ano": str(row["ANO"]).replace("º",""), "semana_ref": row['SEMANA_REF']}
                            st.rerun()
                            
                        if c_b5.button("🗑️ APAGAR", key=f"del_mat_h_{row.name}", use_container_width=True):
                            if db.excluir_registro_com_drive("DB_AULAS_PRONTAS", identificador):
                                st.rerun()

                        with st.expander("👁️ ANALISAR ESTRUTURA PEDAGÓGICA E ITENS"):
                            t_prof, t_alu, t_gab, t_pei_tab, t_img = st.tabs([
                                "👨‍🏫 Guia do Professor", "📝 Material do Aluno", "✅ Gabarito", "♿ Inclusão PEI", "🎨 Imagens"
                            ])
                            
                            with t_prof:
                                val_prof = ai.extrair_tag(txt_f, "PROFESSOR")
                                st.info(val_prof if val_prof else "Conteúdo não localizado.")

                            with t_alu:
                                val_alu = ai.extrair_tag(txt_f, "ALUNO")
                                if val_alu:
                                    st.write(val_alu)
                                else: st.write("Roteiro não localizado.")

                            with t_gab:
                                val_gab = ai.extrair_tag(txt_f, "GABARITO")
                                st.success(val_gab if val_gab else "Gabarito não disponível.")

                            with t_pei_tab:
                                val_pei = ai.extrair_tag(txt_f, "PEI")
                                st.warning(val_pei if val_pei else "Nenhuma adaptação registrada.")
                                
                            with t_img:
                                val_img = ai.extrair_tag(txt_f, "IMAGENS")
                                if val_img:
                                    st.info(val_img)
                                else:
                                    st.caption("Nenhum prompt de imagem gerado para este material.")
            else:
                st.info("📭 Nenhum material didático encontrado.")


# ==============================================================================
# MÓDULO: CENTRAL DE AVALIAÇÕES - CLEAN & UX
# ==============================================================================
elif menu == "📝 Central de Avaliações":
    st.title("📝 Central de Avaliações: Arquiteto de Exames")
    st.markdown("---")
    st.caption("💡 **Guia de Comando:** Crie provas, testes e sondas diagnósticas com alto rigor psicométrico. O sistema gera automaticamente a versão Regular, a versão PEI e a Grade de Perícia para o Raio-X.")
    
    is_refinando_av = "refino_av_ativo" in st.session_state

    def reset_avaliacoes():
        keys_to_del =["temp_prova", "temp_revisao", "av_pei", "refino_av_ativo", "av_valor_total", "av_gab_pei", "av_res_pei_ia", "av_nome_fixo"]
        for k in keys_to_del:
            if k in st.session_state: del st.session_state[k]
        st.cache_data.clear()
        st.session_state.v_av = int(time.time())
        st.rerun()

    if "v_av" not in st.session_state: st.session_state.v_av = 1
    v = st.session_state.v_av

    tab_arquiteto_av, tab_refino, tab_vis, tab_recomposicao, tab_finalizar, tab_acervo_av = st.tabs([
        "🚀 1. Arquiteto de Exames", "🤖 2. Refinador", "👁️ 3. Visão 360°", "🔥 4. Recomposição", "💾 5. Finalizar Ativo", "🗂️ 6. Acervo"
    ])

    # --- ABA 1: ARQUITETO DE EXAMES ---
    with tab_arquiteto_av:
        if is_refinando_av:
            st.warning(f"🛠️ **MODO REFINO:** Editando {st.session_state.refino_av_ativo.get('tipo')}")
            if st.button("❌ CANCELAR E VOLTAR AO NOVO"): reset_avaliacoes()

        # --- 1. CONFIGURAÇÃO BÁSICA ---
        with st.container(border=True):
            st.markdown("### ⚙️ Passo 1: Configuração do Exame")
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
            
            tipo_av = c1.selectbox("Tipo de Ativo:",["Teste", "Prova", "Sonda de Proficiência", "Recuperação Paralela", "Recuperação Final", "2ª Chamada"], 
                help="Sonda: Foca em lacunas do ano anterior. 2ª Chamada: Gera questões gêmeas de uma prova existente.",
                key=f"av_t_{v}")
            
            val_sugerido = 3.0 if "Teste" in tipo_av else 10.0 if "Sonda" in tipo_av else 4.0
            v_total = c2.number_input("Valor Total:", 0.0, 10.0, val_sugerido, step=0.5, key=f"av_v_{v}")
            ano_av = c3.selectbox("Série Atual:", [6, 7, 8, 9], index=0, key=f"av_a_{v}")
            qtd_q = c4.number_input("Nº de Questões:", 1, 20, 10, help="A versão PEI terá automaticamente a mesma quantidade ou metade, dependendo da configuração da IA.", key=f"av_q_{v}")

        is_sonda = "Sonda" in tipo_av
        is_segunda = "2ª Chamada" in tipo_av

        if is_sonda:
            # --- MODO 2: ENGENHARIA DE SONDAGEM ---
            with st.container(border=True):
                st.markdown("#### 🔍 Passo 2: Parâmetros de Sondagem Diagnóstica")
                st.caption("A Sonda busca identificar defasagens. O sistema buscará automaticamente os conteúdos da série anterior se for o I Trimestre.")
                
                instr_extra = "" 
                
                trim_filtro = st.selectbox("Trimestre de Referência:",["I Trimestre", "II Trimestre", "III Trimestre"], key=f"s_trim_{v}")
                
                ano_busca = int(ano_av) - 1 if trim_filtro == "I Trimestre" else int(ano_av)
                st.info(f"💡 **Foco Diagnóstico:** Buscando conteúdos do **{ano_busca}º Ano** na Matriz Curricular para mapear lacunas.")

                df_matriz = df_curriculo[df_curriculo["ANO"].astype(str).str.contains(str(ano_busca))].copy()
                
                c_s1, c_s2 = st.columns(2)
                lista_eixos = sorted(df_matriz["EIXO"].unique().tolist()) if not df_matriz.empty else[]
                sel_eixos = c_s1.multiselect("Selecione o(s) Eixo(s):", lista_eixos, key=f"s_e_m_{v}")
                
                sel_conts = []
                sel_objs =[]
                
                if sel_eixos:
                    df_c_f = df_matriz[df_matriz["EIXO"].isin(sel_eixos)].copy()
                    lista_conts = sorted(df_c_f["CONTEUDO_ESPECIFICO"].unique().tolist()) if not df_c_f.empty else[]
                    sel_conts = c_s2.multiselect("Conteúdo(s) Base:", lista_conts, key=f"s_c_m_{v}")
                    
                    if sel_conts:
                        df_o_f = df_c_f[df_c_f["CONTEUDO_ESPECIFICO"].isin(sel_conts)].copy()
                        lista_objs = sorted(df_o_f["OBJETIVOS"].unique().tolist()) if not df_o_f.empty else[]
                        sel_objs = st.multiselect("Refine pelos Objetivos (Descritores):", lista_objs, key=f"s_o_m_{v}")
                
                instr_extra = st.text_area("📝 Instruções de Sondagem (Ex: Focar em itens do SAEB):", key=f"s_instr_{v}")

        else:
            # --- MODO 1: ENGENHARIA DE SAFRA (TESTE/PROVA/2ª CHAMADA) ---
            with st.container(border=True):
                st.markdown("### 📊 Passo 2: Distribuição de Dificuldade (Taxonomia)")
                st.caption("A soma das questões fáceis, médias e difíceis deve ser exatamente igual ao número total de questões.")
                cd1, cd2, cd3 = st.columns(3)
                q_facil = cd1.number_input("Fáceis (Relembrar):", 0, qtd_q, int(qtd_q*0.3), key=f"q_f_{v}")
                q_medio = cd2.number_input("Médias (Aplicar):", 0, qtd_q, int(qtd_q*0.5), key=f"q_m_{v}")
                q_dificil = cd3.number_input("Difíceis (Analisar):", 0, qtd_q, max(0, qtd_q-(q_facil+q_medio)), key=f"q_d_{v}")
                soma_q = q_facil + q_medio + q_dificil

            with st.container(border=True):
                st.markdown("### 🎯 Passo 3: Matriz de Mérito e Vínculo de Safra")
                st.caption("Selecione as aulas que você já ministrou. A IA usará o conteúdo exato dessas aulas para gerar a prova, evitando cobrar o que não foi ensinado.")
                trim_filtro = st.selectbox("Filtrar Ativos por Trimestre:", ["I Trimestre", "II Trimestre", "III Trimestre"], key=f"av_trim_filter_{v}")
                
                df_ref = df_aulas[df_aulas['ANO'].str.contains(str(ano_av))].copy()
                
                def validar_pertenca_trimestre(row):
                    if trim_filtro.upper() in str(row['CONTEUDO']).upper():
                        return True
                    try:
                        data_str = str(row['DATA'])
                        d, m, y = map(int, data_str.split('/'))
                        dt_aula = date(y, m, d)
                        trim_nome, _ = util.obter_info_trimestre(dt_aula)
                        return trim_nome == trim_filtro
                    except:
                        return False

                if not df_ref.empty:
                    mask = df_ref.apply(validar_pertenca_trimestre, axis=1)
                    df_ref = df_ref[mask]

                if is_segunda:
                    df_ref_2a = df_ref[df_ref['SEMANA_REF'] == "AVALIAÇÃO"]
                    mats_selecionados = st.selectbox(f"📦 Selecione a Prova Original ({len(df_ref_2a)} detectadas):", [""] + df_ref_2a['TIPO_MATERIAL'].tolist(), help="A IA lerá esta prova e criará questões com a mesma estrutura matemática, mas com valores e contextos diferentes.", key=f"av_ref_{v}")
                else:
                    mats_selecionados = st.multiselect(f"📦 Ativos de Safra ({len(df_ref)} detectados):", options=df_ref["TIPO_MATERIAL"].tolist(), key=f"av_ref_{v}")
                
                instr_extra = st.text_area("📝 Instruções Extras de Composição:", placeholder="Ex: Focar mais em frações do que em decimais...", key=f"av_extra_{v}")

        # --- 4. DIAGNÓSTICO DE CONFIGURAÇÃO ---
        with st.container(border=True):
            col_diag1, col_diag2 = st.columns(2)
            with col_diag1:
                if is_sonda:
                    if sel_conts: st.success(f"✅ Sonda configurada: {len(sel_conts)} conteúdos.")
                    else: st.warning("⚠️ Selecione os conteúdos da matriz.")
                else:
                    if soma_q == qtd_q: st.success(f"✅ Taxonomia: {soma_q}/{qtd_q} questões.")
                    else: st.error(f"🚨 Erro: Soma ({soma_q}) ≠ Total ({qtd_q}). Ajuste a distribuição.")
            with col_diag2:
                peso_q = v_total / qtd_q if qtd_q > 0 else 0
                st.metric("Peso por Questão", f"{peso_q:.2f} pts")

        # --- 5. BOTÃO DE COMPILAÇÃO UNIFICADO ---
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🧠 INICIAR MOTOR DE IA: GERAR AVALIAÇÃO", use_container_width=True, type="primary"):
            if not is_sonda and not is_segunda and soma_q != qtd_q:
                st.error("⚠️ Ajuste a distribuição de dificuldade antes de gerar.")
            else:
                with st.spinner("Maestro Sosa arquitetando Tratado Pedagógico e Grade de Perícia..."):
                    peso_str = util.sosa_to_str(peso_q)
                    nome_tecnico = f"{tipo_av.upper().replace(' ', '_')}_{ano_av}ANO_{trim_filtro.replace(' ', '')}"
                    
                    if is_sonda:
                        prompt = (
                            f"ORDEM DE PERÍCIA V70 - PSICOMETRIA DIAGNÓSTICA\n"
                            f"SÉRIE ATUAL: {ano_av}º. SÉRIE BASE: {ano_busca}º. VALOR: 10.0. QTD: {qtd_q}.\n"
                            f"CONTEÚDOS MATRIZ: {sel_conts}. OBJETIVOS: {sel_objs}.\n"
                            f"EXTRAS: {instr_extra}.\n\n"
                            f"🚨 MISSÃO: Use o Google Search para encontrar itens de avaliação diagnóstica oficiais (SAEB, Prova Brasil, AAP). "
                            f"Gere questões de múltipla escolha com erros planejados para mapear lacunas. "
                            f"Formatação INLINE: **QUESTÃO XX ({peso_str} ponto) -** Texto."
                        )
                        persona_alvo = "ARQUITETO_SONDA_DIAGNOSTICA"
                    else:
                        contexto_base = ""
                        for m_nome in (mats_selecionados if isinstance(mats_selecionados, list) else [mats_selecionados]):
                            m_row = df_aulas[df_aulas["TIPO_MATERIAL"] == m_nome].iloc[0]
                            contexto_base += f"MATERIAL: {m_nome}\n{m_row['CONTEUDO']}\n"
                        
                        diretriz = f"DISTRIBUIÇÃO: {q_facil} Fáceis, {q_medio} Médias, {q_dificil} Difíceis." if not is_segunda else "MODO 2ª CHAMADA (QUESTÕES GÊMEAS)."
                        
                        prompt = (
                            f"TIPO: {tipo_av}. SÉRIE: {ano_av}º. VALOR: {v_total}. QTD: {qtd_q}.\n"
                            f"DIRETRIZ: {diretriz}. EXTRAS: {instr_extra}.\n\n"
                            f"--- CONTEÚDO HERDADO DAS AULAS ---\n{contexto_base}"
                        )
                        persona_alvo = "ARQUITETO_EXAMES_V30_ELITE"

                    st.session_state.temp_prova = ai.gerar_ia(persona_alvo, prompt, usar_busca=True)
                    st.session_state.av_valor_total = v_total
                    st.session_state.av_nome_fixo = nome_tecnico
                    st.rerun()

    # --- ABA 2: REFINADOR ---
    with tab_refino:
        if "temp_prova" in st.session_state:
            st.subheader("🤖 Refinador Maestro (Ajuste Rápido)")
            st.caption("Peça para a IA trocar uma questão específica, ajustar o nível de dificuldade ou alterar o gabarito.")
            cmd = st.chat_input("Ex: 'Troque a questão 3 por uma mais fácil' ou 'Mude o contexto da prova para Itabuna'...", key=f"chat_av_{v}")
            if cmd:
                with st.spinner("Reescrevendo avaliação..."):
                    st.session_state.temp_prova = ai.gerar_ia("REFINADOR_EXAMES", f"ORDEM: {cmd}\n\nATUAL:\n{st.session_state.temp_prova}")
                    st.session_state.v_av += 1; st.rerun()
            st.text_area("Editor de Exame (Texto Bruto):", st.session_state.temp_prova, height=500, key=f"ed_av_raw_{v}")
        else: st.info("Gere um exame na aba 'Arquiteto' para habilitar o Refinador.")

    # --- ABA 3: VISUALIZAÇÃO ---
    with tab_vis:
        if "temp_prova" in st.session_state:
            st.subheader("👁️ Visão 360° do Exame")
            txt_f = st.session_state.temp_prova
            
            t1, t2, t3, t4, t5 = st.tabs(["📝 Prova Regular", "🔍 Perícia Regular", "♿ Prova PEI", "🔬 Perícia PEI", "✅ Gabaritos"])
            
            with t1: st.text_area("Questões Regulares:", ai.extrair_tag(txt_f, "QUESTOES"), height=500, key=f"vis_reg_{v}")
            with t2: st.text_area("Grade de Perícia Regular:", ai.extrair_tag(txt_f, "GRADE_DE_CORRECAO"), height=500, key=f"vis_grade_reg_{v}")
            with t3: st.text_area("Questões PEI:", ai.extrair_tag(txt_f, "PEI"), height=500, key=f"vis_pei_q_{v}")
            
            with t4: 
                val_grade_pei = ai.extrair_tag(txt_f, "GRADE_DE_CORRECAO_PEI")
                if val_grade_pei:
                    st.text_area("Habilidades e Lacunas PEI:", val_grade_pei, height=500, key=f"vis_grade_pei_{v}")
                else:
                    st.info("Aguardando nova geração para povoar a Perícia PEI.")
                    
            with t5: 
                c_g1, c_g2 = st.columns(2)
                with c_g1:
                    st.markdown("### 📝 Gabarito Regular")
                    st.code(ai.extrair_tag(txt_f, "GABARITO_TEXTO"))
                with c_g2:
                    st.markdown("### ♿ Gabarito PEI")
                    st.code(ai.extrair_tag(txt_f, "GABARITO_PEI"))
        else: st.info("Gere um exame para carregar a Visualização 360°.")

    # --- ABA 4: RECOMPOSIÇÃO ---
    with tab_recomposicao:
        if "temp_prova" in st.session_state:
            st.subheader("🔥 Gerador de Revisão Sincronizada")
            st.caption("Transforme a prova que você acabou de criar em uma lista de revisão discursiva para aplicar antes do exame.")
            
            if st.button("🧠 INICIAR MOTOR DE IA: GERAR REVISÃO", use_container_width=True, type="primary"):
                with st.spinner("Convertendo prova em roteiro de recomposição..."):
                    prompt_rev = f"PROVA BASE:\n{st.session_state.temp_prova}\n\nID_EXAME: {st.session_state.av_nome_fixo}"
                    st.session_state.temp_revisao = ai.gerar_ia("ARQUITETO_REVISAO_V29", prompt_rev)
                    st.rerun()
            
            if "temp_revisao" in st.session_state:
                txt_rev = st.session_state.temp_revisao
                tr1, tr2, tr3, tr_sync = st.tabs(["👨‍🏫 Professor", "📝 Aluno", "♿ PEI", "☁️ SINCRONIA"])
                with tr1: st.text_area("Guia:", ai.extrair_tag(txt_rev, "PROFESSOR"), height=400, key=f"rev_prof_{v}")
                with tr2: st.text_area("Folha:", ai.extrair_tag(txt_rev, "ALUNO"), height=400, key=f"rev_alu_{v}")
                with tr3: st.text_area("PEI:", ai.extrair_tag(txt_rev, "PEI"), height=400, key=f"rev_pei_{v}")
                
                with tr_sync:
                    st.info("Gere os arquivos DOCX da revisão e salve no Drive.")
                    if st.button("💾 SALVAR REVISÃO E SINCRONIZAR NO DRIVE", use_container_width=True, type="primary"):
                        with st.status("Sincronizando...") as status:
                            nome_rev = f"REVISAO_{st.session_state.av_nome_fixo}"
                            db.excluir_registro_com_drive("DB_AULAS_PRONTAS", nome_rev)
                            
                            doc_alu = exporter.gerar_docx_aluno_v24(nome_rev, ai.extrair_tag(txt_rev, "ALUNO"), {"ano": f"{ano_av}º", "trimestre": trim_filtro})
                            link_alu = db.subir_e_converter_para_google_docs(doc_alu, f"{nome_rev}_ALUNO", modo="AULA")
                            
                            doc_pei = exporter.gerar_docx_pei_v25(f"{nome_rev}_PEI", ai.extrair_tag(txt_rev, "PEI"), {"ano": f"{ano_av}º", "trimestre": trim_filtro})
                            link_pei = db.subir_e_converter_para_google_docs(doc_pei, f"{nome_rev}_PEI", modo="AULA")
                            
                            doc_prof = exporter.gerar_docx_professor_v25(nome_rev, ai.extrair_tag(txt_rev, "PROFESSOR"), {"ano": f"{ano_av}º", "semana": "REVISÃO", "trimestre": trim_filtro})
                            link_prof = db.subir_e_converter_para_google_docs(doc_prof, f"{nome_rev}_PROF", modo="AULA")
                            
                            db.salvar_no_banco("DB_AULAS_PRONTAS",[
                                datetime.now().strftime("%d/%m/%Y"), "REVISÃO", nome_rev, 
                                txt_rev + f"\n--- LINKS ---\nRegular({link_alu}) PEI({link_pei}) Prof({link_prof})", f"{ano_av}º", link_alu
                            ])
                            status.update(label="✅ Revisão Sincronizada!", state="complete"); st.balloons()
        else: st.warning("⚠️ Gere a prova primeiro na aba 'Arquiteto'.")

    # --- ABA 5: FINALIZAR ATIVO ---
    with tab_finalizar:
        if "temp_prova" in st.session_state:
            st.subheader("💾 Consolidação do Ativo de Safra")
            st.caption("Gere os arquivos DOCX (Prova Regular, Prova PEI e Guia de Correção) e salve tudo no seu Google Drive.")
            
            v_tipo = st.session_state.get(f"av_t_{v}", "Prova")
            v_ano = st.session_state.get(f"av_a_{v}", 6)
            v_qtd = st.session_state.get(f"av_q_{v}", 10)
            v_total_num = st.session_state.get('av_valor_total', 10.0)
            
            c_s1, c_s2 = st.columns(2)
            trim_av = c_s1.selectbox("Confirmar Trimestre:", ["I Trimestre", "II Trimestre", "III Trimestre"], key=f"trim_fin_{v}")
            
            nome_tecnico_sugerido = st.session_state.get('av_nome_fixo', 'AVALIACAO_SEM_NOME')
            nome_arq = c_s2.text_input("ID Técnico do Material (Nome no Banco):", nome_tecnico_sugerido, help="Este é o nome que aparecerá no Scanner de Gabaritos.", key=f"name_av_in_{v}")

            st.info(f"🚀 O material será salvo como: **{nome_arq}**")

            if st.button("💾 SALVAR AVALIAÇÃO E SINCRONIZAR NO DRIVE", use_container_width=True, type="primary"):
                with st.status("Sincronizando Ativos e Gerando DOCX...") as status:
                    link_reg = "N/A"
                    link_pei = "N/A"
                    link_prof = "N/A"
                    identificador = nome_arq 
                    
                    db.excluir_avaliacao_completa(identificador, v_tipo)
                    
                    texto_puro_ia = ai.limpar_links_antigos(st.session_state.temp_prova)
                    
                    status.write("📝 Gerando Prova Regular...")
                    info_reg = {
                        "ano": f"{v_ano}º", "tipo_prova": v_tipo, 
                        "valor": util.sosa_to_str(v_total_num), 
                        "valor_questao": util.sosa_to_str(v_total_num/v_qtd), 
                        "qtd_questoes": v_qtd, "trimestre": trim_av
                    }
                    doc_reg = exporter.gerar_docx_prova_v25(nome_arq, texto_puro_ia, info_reg)
                    link_reg = db.subir_e_converter_para_google_docs(doc_reg, nome_arq, modo="AVALIACAO")
                    
                    status.write("♿ Gerando Versão PEI...")
                    txt_pei_raw = ai.extrair_tag(texto_puro_ia, "PEI")
                    if txt_pei_raw:
                        qtd_q_pei = len(re.findall(r'QUESTÃO', txt_pei_raw.upper()))
                        if qtd_q_pei == 0: qtd_q_pei = 5
                        info_pei = {
                            "ano": f"{v_ano}º", "tipo_prova": v_tipo, 
                            "valor": util.sosa_to_str(v_total_num), 
                            "valor_questao": util.sosa_to_str(v_total_num/qtd_q_pei), 
                            "qtd_questoes": qtd_q_pei, "trimestre": trim_av
                        }
                        doc_pei = exporter.gerar_docx_prova_v25(f"{nome_arq}_PEI", txt_pei_raw, info_pei)
                        link_pei = db.subir_e_converter_para_google_docs(doc_pei, f"{nome_arq}_PEI", modo="AVALIACAO")

                    status.write("🔍 Gerando Guia de Perícia Integral...")
                    txt_gab_reg = ai.extrair_tag(texto_puro_ia, "GABARITO_TEXTO")
                    txt_grade_reg = ai.extrair_tag(texto_puro_ia, "GRADE_DE_CORRECAO")
                    txt_gab_pei = ai.extrair_tag(texto_puro_ia, "GABARITO_PEI")
                    txt_grade_pei = ai.extrair_tag(texto_puro_ia, "GRADE_DE_CORRECAO_PEI")

                    txt_prof_completo = (
                        f"GABARITO OFICIAL (REGULAR):\n{txt_gab_reg}\n\n"
                        f"GABARITO OFICIAL (PEI):\n{txt_gab_pei}\n\n"
                        f"DETALHAMENTO POR ITEM (REGULAR):\n{txt_grade_reg}\n\n"
                        f"DETALHAMENTO POR ITEM (PEI):\n{txt_grade_pei}"
                    )

                    if txt_grade_reg:
                        doc_prof = exporter.gerar_docx_professor_v25(f"{nome_arq}_GRADE", txt_prof_completo, {"ano": f"{v_ano}º", "semana": "AVALIAÇÃO", "trimestre": trim_av})
                        link_prof = db.subir_e_converter_para_google_docs(doc_prof, f"{nome_arq}_GRADE", modo="AVALIACAO")

                    status.write("💾 Sincronizando com o Banco de Dados...")
                    links_footer = f"--- LINKS ---\nRegular({link_reg}) PEI({link_pei}) Prof({link_prof})"
                    conteudo_final_banco = f"[VALOR: {v_total_num}]\n" + texto_puro_ia + f"\n\n{links_footer}"
                    
                    db.salvar_no_banco("DB_AULAS_PRONTAS",[
                        datetime.now().strftime("%d/%m/%Y"), 
                        "AVALIAÇÃO", 
                        identificador, 
                        conteudo_final_banco, 
                        f"{v_ano}º", 
                        link_reg
                    ])
                    
                    status.update(label="✅ Ativo Salvo e Sincronizado!", state="complete")
                    st.balloons()
                    time.sleep(1.5)
                    reset_avaliacoes()
        else:
            st.warning("⚠️ Gere a prova no Arquiteto antes de finalizar.")

    # --- ABA 6: ACERVO DE SAFRA ---
    with tab_acervo_av:
        st.subheader("🗂️ Gestão de Acervo de Safra (Provas e Revisões)")
        st.caption("Acesse, edite ou apague avaliações já geradas.")
        
        with st.container(border=True):
            c_h1, c_h2, c_h3 = st.columns([1, 1, 1])
            f_trim_h = c_h1.selectbox("📅 Filtrar Trimestre:",["Todos", "I Trimestre", "II Trimestre", "III Trimestre"], key="h_trim_av")
            f_ano_h = c_h2.selectbox("🎓 Filtrar Série:", ["Todos", "6º", "7º", "8º", "9º"], key="h_ano_av")
            f_tipo_h = c_h3.selectbox("📝 Tipo de Ativo:", ["Todos", "AVALIAÇÃO", "REVISÃO"], key="h_tipo_av")

        df_exames = df_aulas[df_aulas['SEMANA_REF'].isin(["AVALIAÇÃO", "REVISÃO"])].copy()
        if f_trim_h != "Todos": df_exames = df_exames[df_exames['CONTEUDO'].str.contains(f_trim_h, na=False)]
        if f_ano_h != "Todos": df_exames = df_exames[df_exames['ANO'] == f_ano_h]
        if f_tipo_h != "Todos": df_exames = df_exames[df_exames['SEMANA_REF'] == f_tipo_h]

        df_exames = df_exames.iloc[::-1] 

        if not df_exames.empty:
            for _, row in df_exames.iterrows():
                with st.container(border=True):
                    txt_f = str(row['CONTEUDO'])
                    identificador = row['TIPO_MATERIAL']
                    
                    col_tit, col_meta = st.columns([2, 1])
                    with col_tit:
                        st.markdown(f"#### 📄 {identificador}")
                    with col_meta:
                        val_ex = re.sub(r'[*#]', '', ai.extrair_tag(txt_f, "VALOR")).strip()
                        st.markdown(f"**💰 Valor:** `{val_ex if val_ex else 'N/A'}` | **🎓 Série:** `{row['ANO']}`")

                    gab_simples = ai.extrair_tag(txt_f, "GABARITO_TEXTO") or ai.extrair_tag(txt_f, "RESPOSTAS_IA")
                    if gab_simples:
                        gab_limpo = re.sub(r'[*#]', '', gab_simples).replace('QUESTÃO', '').strip()
                        st.markdown(f"**✅ Gabarito Regular:** `{gab_limpo}`")

                    l_reg = (re.findall(r"Regular\((.*?)\)", txt_f) or[row.get('LINK_DRIVE')])[-1]
                    l_pei = (re.findall(r"PEI\((.*?)\)", txt_f) or [None])[-1]
                    l_prof = (re.findall(r"Prof\((.*?)\)", txt_f) or [None])[-1]

                    c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)
                    c_b1.link_button("📝 REGULAR", str(l_reg), use_container_width=True, type="primary")
                    if l_pei and "N/A" not in str(l_pei): c_b2.link_button("♿ PEI", str(l_pei), use_container_width=True)
                    else: c_b2.button("⚪ SEM PEI", disabled=True, use_container_width=True)
                    if l_prof and "N/A" not in str(l_prof): c_b3.link_button("🔍 PERÍCIA", str(l_prof), use_container_width=True)
                    else: c_b3.button("⚪ SEM GRADE", disabled=True, use_container_width=True)
                    
                    if c_b4.button("🔄 REFINAR", key=f"ref_av_h_{row.name}", use_container_width=True):
                        st.session_state.temp_prova = txt_f
                        st.session_state.av_nome_fixo = identificador
                        st.rerun()
                        
                    if c_b5.button("🗑️ APAGAR", key=f"del_av_h_{row.name}", use_container_width=True):
                        if db.excluir_avaliacao_completa(identificador, row['SEMANA_REF']): st.rerun()

                    with st.expander("👁️ ANALISAR ESTRUTURA PEDAGÓGICA E ITENS"):
                        t_gab, t_ques, t_pei_v, t_peri_pei = st.tabs([
                            "🎯 Perícia Regular", "📝 Prova Regular", "♿ Adaptação PEI", "🔬 Perícia PEI"
                        ])
                        
                        with t_gab:
                            st.markdown("##### 🔬 Grade de Perícia (Regular)")
                            grade_raw = ai.extrair_tag(txt_f, "GRADE_DE_CORRECAO")
                            if grade_raw:
                                questoes_grade = re.split(r"(?i)QUEST[AÃ]O\s*0?(\d+)", grade_raw)
                                if len(questoes_grade) > 1:
                                    for i in range(1, len(questoes_grade), 2):
                                        q_num, q_txt = questoes_grade[i], questoes_grade[i+1]
                                        with st.container(border=True):
                                            st.markdown(f"**📑 QUESTÃO {q_num}**")
                                            q_txt_limpo = re.sub(r'[*#]', '', q_txt).strip()
                                            
                                            m_hab = re.search(r"(?i)(?:HABILIDADE|BNCC|DESCRITOR).*?[:\-]\s*(.*?)(?=RESPOSTA|JUSTIFICATIVA|ALERTA|PERÍCIA|$)", q_txt_limpo, re.DOTALL)
                                            m_just = re.search(r"(?i)(?:RESPOSTA|JUSTIFICATIVA).*?[:\-]\s*(.*?)(?=ALERTA|PERÍCIA|DISTRATORES|$)", q_txt_limpo, re.DOTALL)
                                            m_peri = re.search(r"(?i)(?:ALERTA|PERÍCIA|DISTRATORES).*?[:\-]\s*(.*)", q_txt_limpo, re.DOTALL)
                                            
                                            if m_hab: st.caption(f"🆔 **Habilidade:** {m_hab.group(1).strip()}")
                                            if m_just: st.write(f"🎯 **Resposta:** {m_just.group(1).strip()}")
                                            if m_peri: st.info(f"🔍 **Análise de Erros:** {m_peri.group(1).strip()}")
                                else: st.write(re.sub(r'[*#]', '', grade_raw))
                            else: st.warning("Grade não localizada.")

                        with t_ques:
                            st.markdown("##### 📋 Conteúdo da Prova Regular")
                            questoes_reg = ai.extrair_tag(txt_f, "QUESTOES")
                            if questoes_reg:
                                txt_limpo_q = re.sub(r'\[\s*PROMPT IMAGEM:.*?\]', '🖼️ *(Imagem)*', questoes_reg, flags=re.IGNORECASE)
                                st.write(re.sub(r'[*#]', '', txt_limpo_q))

                        with t_pei_v:
                            st.markdown("##### ♿ Detalhes da Adaptação PEI")
                            pei_txt = ai.extrair_tag(txt_f, "PEI")
                            if pei_txt:
                                st.info(re.sub(r'[*#]', '', pei_txt))
                                st.divider()
                                gab_pei = ai.extrair_tag(txt_f, "GABARITO_PEI")
                                if gab_pei: st.code(re.sub(r'[*#]', '', gab_pei))

                        with t_peri_pei:
                            st.markdown("##### 🔬 Grade de Perícia PEI")
                            grade_pei_raw = ai.extrair_tag(txt_f, "GRADE_DE_CORRECAO_PEI")
                            if grade_pei_raw:
                                q_grade_pei = re.split(r"(?i)QUEST[AÃ]O\s*PEI\s*0?(\d+)", grade_pei_raw)
                                if len(q_grade_pei) > 1:
                                    for i in range(1, len(q_grade_pei), 2):
                                        q_n, q_t = q_grade_pei[i], q_grade_pei[i+1]
                                        with st.container(border=True):
                                            st.markdown(f"**♿ QUESTÃO PEI {q_n}**")
                                            q_t_limpo = re.sub(r'[*#]', '', q_t).strip()
                                            m_just_p = re.search(r"(?i)(?:JUSTIFICATIVA|RESPOSTA).*?[:\-]\s*(.*?)(?=ANÁLISE|LACUNA|ERRO|$)", q_t_limpo, re.DOTALL)
                                            m_lacu_p = re.search(r"(?i)(?:ANÁLISE|LACUNA|ERRO).*?[:\-]\s*(.*)", q_t_limpo, re.DOTALL)
                                            if m_just_p: st.write(f"🎯 **Resposta:** {m_just_p.group(1).strip()}")
                                            if m_lacu_p: st.warning(f"🧠 **Análise de Lacuna:** {m_lacu_p.group(1).strip()}")
                                else: st.write(re.sub(r'[*#]', '', grade_pei_raw))
                            else: st.info("Perícia PEI não disponível.")
        else:
            st.info("📭 Acervo vazio.")


# ==============================================================================
# MÓDULO: CENTRAL DE INTELIGÊNCIA DE RESULTADOS (CIR / SCANNER) - CLEAN & UX
# ==============================================================================
elif menu == "📸 Scanner de Gabaritos":
    st.title("📸 Central de Inteligência de Resultados (CIR)")
    st.markdown("---")
    st.caption("💡 **Guia de Comando:** Escaneie gabaritos com a câmera do celular, lance notas de trabalhos manuais, audite resultados e gere o Dossiê de Raio-X Pedagógico para o Conselho de Classe.")

    if "v_scan" not in st.session_state: st.session_state.v_scan = 1
    v = st.session_state.v_scan

    # --- FUNÇÃO AUXILIAR: FILTRO HIERÁRQUICO BLINDADO ---
    def filtrar_ativos_cir(turma, trimestre_nome, apenas_provas=True):
        """Motor de busca inteligente que entende a abrangência da Recuperação Final."""
        if not turma or not trimestre_nome: return[]
        try:
            serie_num = str(turma)[0] 
            df_f = df_aulas[df_aulas['ANO'].astype(str).str.contains(serie_num)].copy()
            
            def detectar_trimestre(x):
                try:
                    if str(x).replace('.','',1).isdigit():
                        dt = date(1899, 12, 30) + timedelta(days=int(float(x)))
                        return util.obter_info_trimestre(dt)[0]
                    if "/" in str(x):
                        partes = str(x).split("/")
                        dt = date(int(partes[2]), int(partes[1]), int(partes[0]))
                        return util.obter_info_trimestre(dt)[0]
                except: pass
                return "Outros"

            df_f['TRIM_DETECTADO'] = df_f['DATA'].apply(detectar_trimestre)
            
            if apenas_provas:
                permitidos =["TESTE", "PROVA", "SONDA", "DIAGNÓSTICA", "RECUPERAÇÃO", "AVALIAÇÃO"]
                df_f = df_f[df_f['TIPO_MATERIAL'].str.upper().str.contains('|'.join(permitidos))]
                
                mask_trim = (df_f['TRIM_DETECTADO'] == trimestre_nome) | \
                            (df_f['CONTEUDO'].str.contains(trimestre_nome, na=False)) | \
                            (df_f['TIPO_MATERIAL'].str.upper().str.contains("FINAL"))
                df_f = df_f[mask_trim]
            else:
                permitidos =["PROJETO", "FIXAÇÃO", "REFORÇO", "ATIVIDADE", "TRABALHO", "AULA"]
                df_f = df_f[df_f['TIPO_MATERIAL'].str.upper().str.contains('|'.join(permitidos))]
                df_f = df_f[df_f['TRIM_DETECTADO'] == trimestre_nome]
            
            return sorted(df_f['TIPO_MATERIAL'].unique().tolist())
        except Exception as e: 
            return[]

    # --- ABAS PERSISTENTES ---
    tab_pericia, tab_atividades, tab_soberania, tab_raiox, tab_acervo_cir = st.tabs([
        "📸 1. Scanner de Gabaritos", "✍️ 2. Atividades & Projetos", "🏛️ 3. Hub de Soberania", 
        "📊 4. Raio-X Pedagógico", "📂 5. Acervo de Dossiês"
    ])

    # --- ABA 1: PERÍCIA DE GABARITOS (SCANNER) ---
    with tab_pericia:
        st.subheader("📸 Scanner de Gabaritos (Visão Computacional)")
        st.caption("Selecione a turma e a avaliação. O sistema criará uma fila dinâmica apenas com os alunos que ainda não tiveram a prova corrigida.")
        
        turmas_reais_cir = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
        lista_turmas_cir = sorted(turmas_reais_cir['ID_TURMA'].unique()) if not turmas_reais_cir.empty else sorted(df_alunos['TURMA'].unique())
        
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1, 1.5])
            t_sel = c1.selectbox("👥 Turma:", [""] + lista_turmas_cir, key=f"t_p_{v}")
            tr_sel = c2.selectbox("📅 Trimestre:", ["I Trimestre", "II Trimestre", "III Trimestre"], key=f"tr_p_{v}")
            
            opcoes_p = filtrar_ativos_cir(t_sel, tr_sel, apenas_provas=True)
            opcoes_base =[opt for opt in opcoes_p if "2CHAMADA" not in opt.upper()]
            at_sel = c3.selectbox("📋 Selecione a Avaliação Base (Slot):", [""] + opcoes_base, help="Selecione a prova original. Se o aluno fez a 2ª chamada, você poderá indicar isso na hora de escanear.", key=f"at_p_{v}")

        if not t_sel or not at_sel:
            st.info("💡 Selecione a Turma e a Avaliação Base para abrir a Mesa de Triagem.")
        else:
            nome_filtro_pendente = at_sel.split("-")[0].strip()
            escaneados = df_diagnosticos[df_diagnosticos['ID_AVALIACAO'].str.contains(nome_filtro_pendente)]['ID_ALUNO'].astype(str).tolist()
            pendentes = df_alunos[(df_alunos['TURMA'] == t_sel) & (~df_alunos['ID'].astype(str).isin(escaneados))].sort_values(by="NOME_ALUNO")

            if pendentes.empty:
                st.success(f"🏆 **SOBERANIA TOTAL:** Todos os alunos da {t_sel} já possuem nota para {at_sel}!")
                if st.button("🔄 REVISAR HUB DE SOBERANIA"): st.rerun()
            else:
                st.markdown("### 🗂️ Mesa de Triagem e Fila Dinâmica")
                
                with st.expander("❌ Registrar Faltas em Lote", expanded=False):
                    st.caption("Selecione todos os alunos que não entregaram esta prova para retirá-los da fila de correção.")
                    faltosos = st.multiselect("Alunos Ausentes:", pendentes['NOME_ALUNO'].tolist(), key=f"faltas_{v}")
                    
                    if st.button("💾 CONFIRMAR FALTAS", type="primary"):
                        if faltosos:
                            with st.spinner("Registrando ausências no banco de dados..."):
                                linhas_faltas =[]
                                data_hoje = datetime.now().strftime("%d/%m/%Y")
                                for f_nome in faltosos:
                                    f_id = pendentes[pendentes['NOME_ALUNO'] == f_nome].iloc[0]['ID']
                                    linhas_faltas.append([data_hoje, f_id, f_nome, t_sel, at_sel, "FALTOU", "0,00", "N/A"])
                                
                                if db.salvar_lote("DB_GABARITOS_ALUNOS", linhas_faltas):
                                    st.success(f"✅ {len(faltosos)} faltas registradas com sucesso!"); time.sleep(1); st.rerun()
                        else:
                            st.warning("Selecione ao menos um aluno.")

                st.markdown("#### 📄 Qual prova está no topo da sua pilha agora?")
                al_sel = st.selectbox("Selecione o aluno para escanear:", [""] + pendentes['NOME_ALUNO'].tolist(), key=f"pilha_{v}")
                
                if al_sel:
                    al_info = pendentes[pendentes['NOME_ALUNO'] == al_sel].iloc[0]
                    id_aluno_atual = al_info['ID']
                    
                    is_pei_aluno = str(al_info['NECESSIDADES']).upper().strip() not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"]
                    
                    st.markdown("---")
                    st.markdown(f"### 📸 Corrigindo agora: **{al_sel}**")
                    
                    with st.container(border=True):
                        c_v1, c_v2 = st.columns([1, 1])
                        modo_2a = c_v1.toggle("🚀 Aplicar Segunda Chamada para este aluno?", help="Ative se o aluno fez a prova de 2ª chamada. O sistema buscará o gabarito correto.", key=f"toggle_2a_{id_aluno_atual}")
                        
                        if modo_2a:
                            tipo_base = at_sel.split("-")[0].strip().upper()
                            serie_num = "".join(filter(str.isdigit, t_sel))
                            df_2a_candidatos = df_aulas[
                                (df_aulas['TIPO_MATERIAL'].str.upper().str.contains("2CHAMADA")) & 
                                (df_aulas['TIPO_MATERIAL'].str.upper().str.contains(tipo_base)) &
                                (df_aulas['ANO'].str.contains(serie_num))
                            ]
                            opcoes_2a = df_2a_candidatos['TIPO_MATERIAL'].unique().tolist()
                            at_segunda = c_v2.selectbox("📋 Selecione o Ativo 2CHAMADA:", [""] + opcoes_2a, key=f"sel_2a_{id_aluno_atual}")
                            if at_segunda:
                                material_ref = df_aulas[df_aulas['TIPO_MATERIAL'] == at_segunda].iloc[0]
                            else:
                                st.error("Selecione o material de 2ª chamada.")
                                material_ref = None
                        else:
                            material_ref = df_aulas[df_aulas['TIPO_MATERIAL'] == at_sel].iloc[0]
                        
                        if material_ref is not None:
                            tipo_txt = "2ª CHAMADA" if modo_2a else "REGULAR"
                            perfil_txt = "♿ PEI" if is_pei_aluno else "📝 REGULAR"
                            st.info(f"⚖️ **Lente Ativa:** Prova {tipo_txt} | Perfil {perfil_txt}")

                    if material_ref is not None:
                        txt_ref = str(material_ref['CONTEUDO'])
                        val_tag = ai.extrair_tag(txt_ref, "VALOR")
                        v_total_at = util.sosa_to_float(val_tag) if val_tag else 10.0

                        def extrair_gab_blindado(texto, is_pei=False):
                            tag_alvo = "GABARITO_PEI" if is_pei else "GABARITO_TEXTO"
                            raw = ai.extrair_tag(texto, tag_alvo) or ai.extrair_tag(texto, "GABARITO")
                            if not raw: return []
                            matches = re.findall(r"(\d+)[\s\.\)\-:]+([A-E])", raw.upper())
                            mapa = {int(num): letra for num, letra in matches}
                            return [mapa[n] for n in sorted(mapa.keys())]

                        gab_alvo = extrair_gab_blindado(txt_ref, is_pei_aluno)

                        col_cam, col_falta = st.columns([2, 1])
                        
                        with col_cam:
                            st.info("📱 **Dica Mobile:** Clique abaixo para abrir a câmera nativa do seu celular (melhor foco e resolução).")
                            img_file = st.file_uploader(f"📸 Capturar Gabarito de {al_sel}", type=["jpg", "jpeg", "png"], key=f"up_{id_aluno_atual}")
                            
                            with st.expander("💻 Usar Webcam (Computador)"):
                                img_cam = st.camera_input("Webcam", key=f"cam_{id_aluno_atual}")
                                
                            img = img_file if img_file else img_cam
                        
                        with col_falta:
                            st.write("---")
                            if st.button("❌ REGISTRAR FALTA", use_container_width=True):
                                db.salvar_no_banco("DB_GABARITOS_ALUNOS",[datetime.now().strftime("%d/%m/%Y"), id_aluno_atual, al_sel, t_sel, at_sel, "FALTOU", "0,00", "N/A"])
                                st.rerun()

                        if img and "current_scan_res" not in st.session_state:
                            with st.spinner("Analisando marcações com Visão Computacional (Gemini 2.5 Pro)..."):
                                res_json = ai.analisar_gabarito_vision(img.getvalue())
                                qtd_q = len(gab_alvo)
                                st.session_state.current_scan_res =[res_json.get(f"{i+1:02d}", res_json.get(str(i+1), "?")) for i in range(qtd_q)]
                                st.session_state.current_scan_img = img.getvalue()
                                st.rerun()

                        if "current_scan_res" in st.session_state:
                            res_lidas = st.session_state.current_scan_res
                            st.markdown("---")
                            col_res1, col_res2 = st.columns([1.5, 1])
                            
                            with col_res1:
                                st.subheader("⚖️ Mesa de Perícia")
                                dados_pericia =[]
                                for i, lido in enumerate(res_lidas):
                                    if i < len(gab_alvo):
                                        certo = gab_alvo[i]
                                        status = "✅ ACERTO" if lido == certo else ("🚫 DUPLA" if lido == "X" else ("⚪ VAZIA" if lido == "?" else f"❌ (Era {certo})"))
                                        dados_pericia.append({"Q": f"{i+1:02d}", "Lido": lido, "Status": status})
                                
                                df_mesa = st.data_editor(pd.DataFrame(dados_pericia), hide_index=True, use_container_width=True,
                                    column_config={"Lido": st.column_config.SelectboxColumn("Ajustar", options=["A", "B", "C", "D", "E", "X", "?"], required=True)},
                                    key=f"ed_turbo_{id_aluno_atual}")
                            
                            with col_res2:
                                st.subheader("📊 Resultado")
                                novas_res = df_mesa["Lido"].tolist()
                                acertos = sum(1 for i, r in enumerate(novas_res) if i < len(gab_alvo) and r == gab_alvo[i])
                                nota_f = (acertos / len(gab_alvo)) * v_total_at if len(gab_alvo) > 0 else 0
                                st.metric("Nota Final", f"{nota_f:.2f}", delta=f"{acertos}/{len(gab_alvo)} acertos")
                                
                                if st.button("💾 SALVAR CORREÇÃO E CHAMAR PRÓXIMO ➔", type="primary", use_container_width=True):
                                    with st.spinner("Arquivando com Rastreabilidade no Drive..."):
                                        id_av_final = f"{at_sel} (2ª CHAMADA)" if modo_2a else at_sel
                                        link_pasta = db.subir_e_converter_para_google_docs(st.session_state.current_scan_img, al_sel.replace(" ","_"), trimestre=tr_sel, categoria=t_sel, semana=id_av_final, modo="SCANNER")
                                        
                                        db.salvar_no_banco("DB_GABARITOS_ALUNOS",[
                                            datetime.now().strftime("%d/%m/%Y"), 
                                            id_aluno_atual, al_sel, t_sel, 
                                            id_av_final, 
                                            ";".join(novas_res), 
                                            util.sosa_to_str(nota_f), 
                                            link_pasta
                                        ])
                                        del st.session_state.current_scan_res
                                        del st.session_state.current_scan_img
                                        st.success(f"✅ {al_sel} processado!"); time.sleep(0.5); st.rerun()

                            if st.button("🗑️ DESCARTAR LEITURA E REFAZER"):
                                del st.session_state.current_scan_res
                                del st.session_state.current_scan_img
                                st.rerun()

    # --- ABA 2: ATIVIDADES & PROJETOS ---
    with tab_atividades:
        st.subheader("✍️ Gestão de Notas de Projetos e Atividades")
        st.caption("Use esta mesa para lançar notas de Redações, Cartazes e Apresentações que não podem ser escaneadas.")
        
        with st.container(border=True):
            c_f1, c_f2 = st.columns(2)
            t_sel_a = c_f1.selectbox("👥 Selecione a Turma:", [""] + sorted(df_alunos['TURMA'].unique().tolist()), key=f"t_a_v68_{v}")
            tr_sel_a = c_f2.selectbox("📅 Selecione o Trimestre:",["I Trimestre", "II Trimestre", "III Trimestre"], key=f"tr_a_v68_{v}")

            opcoes_a = filtrar_ativos_cir(t_sel_a, tr_sel_a, apenas_provas=False)
            at_sel_a = st.selectbox("📋 Selecione o Trabalho ou Atividade:", [""] + opcoes_a, key=f"at_a_sel_v68_{v}")

        if not t_sel_a or not at_sel_a:
            st.info("💡 Selecione a Turma e o Material para abrir a Mesa de Lançamento.")
        else:
            dados_at = df_aulas[df_aulas['TIPO_MATERIAL'] == at_sel_a].iloc[0]
            txt_at = str(dados_at['CONTEUDO'])
            
            val_tag = ai.extrair_tag(txt_at, "VALOR")
            v_max_padrao = util.sosa_to_float(val_tag) if val_tag else 2.0

            with st.container(border=True):
                c_m1, c_m2 = st.columns([2, 1])
                c_m1.warning(f"📝 **ATIVIDADE EM FOCO:** {at_sel_a}")
                v_max_ativ = c_m2.number_input("💎 Valor Máximo deste Trabalho:", 0.0, 10.0, v_max_padrao, step=0.5, key=f"v_max_v68_{v}")

            st.divider()
            st.subheader(f"⭐ Mesa de Notas: {at_sel_a}")
            st.info("💡 **DICA:** Clique duas vezes na célula da coluna 'Nota' para digitar o valor.")
            
            alunos_a = df_alunos[df_alunos['TURMA'] == t_sel_a].sort_values(by="NOME_ALUNO")
            
            notas_atuais = {}
            if not df_diario.empty:
                mask_p = (df_diario['TURMA'] == t_sel_a) & (df_diario['OBSERVACOES'].str.contains(at_sel_a, na=False))
                df_p = df_diario[mask_p]
                for _, row_d in df_p.iterrows():
                    notas_atuais[db.limpar_id(row_d['ID_ALUNO'])] = util.sosa_to_float(row_d.get('BONUS', 0))

            dados_editor =[]
            for _, alu in alunos_a.iterrows():
                id_a = db.limpar_id(alu['ID'])
                nota_v = notas_atuais.get(id_a, 0.0)
                is_pei = str(alu['NECESSIDADES']).upper() not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"]
                
                dados_editor.append({
                    "ID": id_a, 
                    "Estudante": f"♿ {alu['NOME_ALUNO']}" if is_pei else alu['NOME_ALUNO'], 
                    "Nota": nota_v,
                    "Status": "✅ Lançado" if nota_v > 0 else "⏳ Pendente"
                })
            
            df_notas_ed = st.data_editor(
                pd.DataFrame(dados_editor),
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "ID": None,
                    "Estudante": st.column_config.TextColumn("Estudante", width="medium", disabled=True),
                    "Nota": st.column_config.NumberColumn(
                        "Nota", 
                        min_value=0.0, 
                        max_value=v_max_ativ, 
                        step=0.1, 
                        format="%.1f",
                        required=True 
                    ),
                    "Status": st.column_config.TextColumn("Status", width="small", disabled=True)
                },
                key=f"editor_atividades_v68_{at_sel_a.replace(' ','_')}"
            )

            if st.button("💾 CONSOLIDAR NOTAS NO BOLETIM", type="primary", use_container_width=True):
                with st.status("Sincronizando Notas de Mérito...") as status:
                    data_hoje = datetime.now().strftime("%d/%m/%Y")
                    lista_lote =[]
                    
                    for _, r in df_notas_ed.iterrows():
                        lista_lote.append([
                            data_hoje, 
                            r['ID'], 
                            r['Estudante'].replace("♿ ", ""), 
                            t_sel_a, 
                            "FALSE", 
                            "SISTEMA_NOTA", 
                            f"Nota de Trabalho: {at_sel_a}", 
                            util.sosa_to_str(r['Nota'])
                        ])
                    
                    if lista_lote:
                        db.excluir_registro("DB_DIARIO_BORDO", f"Nota de Trabalho: {at_sel_a}")
                        db.salvar_lote("DB_DIARIO_BORDO", lista_lote)
                        status.update(label=f"✅ Notas de {at_sel_a} consolidadas no Boletim!", state="complete")
                        st.balloons()
                        time.sleep(1); st.rerun()

    # --- ABA 3: HUB DE SOBERANIA ---
    with tab_soberania:
        st.subheader("🏛️ Hub de Soberania: Autoridade do Professor")
        st.caption("Audite notas, altere status de alunos e integre notas de avaliações externas (SAEB).")
        st.markdown("---")

        with st.container(border=True):
            c_h1, c_h2 = st.columns([1, 1])
            t_sel_h = c_h1.selectbox("👥 Selecione a Turma:",[""] + lista_turmas_cir, key=f"t_h_v74_{v}")
            tr_sel_h = c_h2.selectbox("📅 Trimestre de Referência:",["I Trimestre", "II Trimestre", "III Trimestre"], key=f"tr_h_v74_{v}")

        if not t_sel_h:
            st.info("💡 Selecione uma turma para abrir a Mesa de Soberania.")
        else:
            alunos_turma_h = df_alunos[df_alunos['TURMA'] == t_sel_h].sort_values(by="NOME_ALUNO")
            sub_auditoria, sub_externas = st.tabs(["⚖️ Auditoria e Lançamento Manual", "🌍 Notas Externas (SAEB/Governo)"])

            with sub_auditoria:
                st.markdown("#### 🔍 Consolidação de Notas e Resgate de Faltas")
                st.caption("Nesta mesa, o senhor tem soberania total. Alterar para '✍️ PENDENTE' faz o aluno voltar para a fila do Scanner.")
                
                serie_num = "".join(filter(str.isdigit, t_sel_h))
                df_oficiais = df_aulas[(df_aulas['SEMANA_REF'] == "AVALIAÇÃO") & (df_aulas['ANO'].str.contains(serie_num))]
                opcoes_base = [opt for opt in df_oficiais['TIPO_MATERIAL'].unique().tolist() if "2ª" not in opt.upper()]
                av_alvo_h = st.selectbox("📋 Selecione a Avaliação Base (Slot do Boletim):", [""] + opcoes_base, key=f"av_h_sel_{v}")

                if av_alvo_h:
                    is_sonda = "SONDA" in av_alvo_h.upper() or "DIAGNÓSTICA" in av_alvo_h.upper()
                    if is_sonda:
                        st.info("💡 **Modo Diagnóstico Ativo:** Esta é uma Sonda. Os gabaritos serão salvos para o Raio-X, mas as notas **NÃO** serão enviadas para o Boletim.")
                    
                    nome_curto_av = av_alvo_h.split("-")[0].strip()
                    gabaritos_lidos = df_diagnosticos[(df_diagnosticos['TURMA'] == t_sel_h) & (df_diagnosticos['ID_AVALIACAO'].str.contains(nome_curto_av))]
                    
                    dados_soberania =[]
                    for _, alu in alunos_turma_h.iterrows():
                        id_a = db.limpar_id(alu['ID'])
                        leitura = gabaritos_lidos[gabaritos_lidos['ID_ALUNO'].apply(db.limpar_id) == id_a]
                        
                        situacao_txt, versao_prova, nota_atual, link_ev = "✍️ PENDENTE", "PROVA ORIGINAL", 0.0, ""
                        respostas_salvas = "MANUAL"

                        if not leitura.empty:
                            reg = leitura.iloc[-1]
                            nota_atual = util.sosa_to_float(reg['NOTA_CALCULADA'])
                            link_ev = reg.get('LINK_FOTO_DRIVE', '')
                            respostas_salvas = reg.get('RESPOSTAS_ALUNO', 'MANUAL')
                            
                            if reg['RESPOSTAS_ALUNO'] == "FALTOU": situacao_txt, versao_prova = "❌ FALTOU", "N/A"
                            elif "2ª" in reg['ID_AVALIACAO'].upper(): situacao_txt, versao_prova = "✅ REALIZADA", "SEGUNDA CHAMADA"
                            else: situacao_txt = "✅ REALIZADA"

                        nec_str = str(alu['NECESSIDADES']).upper().strip()
                        is_pei_sob = nec_str not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"]

                        dados_soberania.append({
                            "ID": id_a, 
                            "Estudante": alu['NOME_ALUNO'],
                            "Perfil": "♿ PEI" if is_pei_sob else "📝 REGULAR",
                            "Situação": situacao_txt, 
                            "Versão": versao_prova,
                            "Nota Final (Soberana)": nota_atual, 
                            "Evidência": link_ev,
                            "_Respostas": respostas_salvas
                        })

                    df_soberano_ed = st.data_editor(
                        pd.DataFrame(dados_soberania), 
                        hide_index=True, 
                        use_container_width=True, 
                        key=f"ed_soberania_v74_{v}",
                        column_config={
                            "ID": None, 
                            "_Respostas": None,
                            "Estudante": st.column_config.TextColumn("Estudante", disabled=True),
                            "Perfil": st.column_config.TextColumn("Perfil", disabled=True),
                            "Situação": st.column_config.SelectboxColumn("Situação", options=["✅ REALIZADA", "❌ FALTOU", "✍️ PENDENTE"], required=True),
                            "Versão": st.column_config.SelectboxColumn("Versão", options=["PROVA ORIGINAL", "SEGUNDA CHAMADA", "N/A"]),
                            "Nota Final (Soberana)": st.column_config.NumberColumn("Nota", format="%.1f"), 
                            "Evidência": st.column_config.LinkColumn("🔗 Ver")
                        }
                    )

                    if st.button("⚖️ HOMOLOGAR E SALVAR ALTERAÇÕES", use_container_width=True, type="primary"):
                        with st.status("Executando Engenharia de Deleção Reversa e Sincronizando...") as status_h:
                            wb_s = db.conectar()
                            ws_g = wb_s.worksheet("DB_GABARITOS_ALUNOS")
                            d_g = ws_g.get_all_values()
                            
                            linhas_para_deletar = []
                            ids_na_tabela = df_soberano_ed['ID'].astype(str).tolist()
                            
                            for i, row_g in enumerate(d_g):
                                if i == 0: continue 
                                if len(row_g) > 4:
                                    id_banco = db.limpar_id(row_g[1])
                                    av_banco = row_g[4]
                                    if id_banco in ids_na_tabela and nome_curto_av in av_banco:
                                        linhas_para_deletar.append(i + 1) 
                            
                            for row_idx in sorted(linhas_para_deletar, reverse=True):
                                ws_g.delete_rows(row_idx)
                            
                            novos_registros_gabarito = []
                            lista_boletim =[]
                            notas_atuais = df_notas[(df_notas['TURMA'] == t_sel_h) & (df_notas['TRIMESTRE'] == tr_sel_h)]
                            
                            for _, r in df_soberano_ed.iterrows():
                                id_l = str(r['ID'])
                                nota_s = util.sosa_to_str(r['Nota Final (Soberana)'])
                                nome_limpo = r['Estudante'].replace("♿ ", "").replace("👤 ", "")
                                resp_originais = r['_Respostas']
                                
                                if r['Situação'] == "✅ REALIZADA":
                                    id_f = av_alvo_h if r['Versão'] == "PROVA ORIGINAL" else f"{av_alvo_h} (2ª CHAMADA)"
                                    resp_final = "MANUAL" if resp_originais == "FALTOU" else resp_originais
                                    novos_registros_gabarito.append([datetime.now().strftime("%d/%m/%Y"), id_l, nome_limpo, t_sel_h, id_f, resp_final, nota_s, r['Evidência'] if r['Evidência'] else "N/A"])
                                elif r['Situação'] == "❌ FALTOU":
                                    novos_registros_gabarito.append([datetime.now().strftime("%d/%m/%Y"), id_l, nome_limpo, t_sel_h, av_alvo_h, "FALTOU", "0,00", "N/A"])
                                
                                if not is_sonda and r['Situação'] != "✍️ PENDENTE":
                                    reg_atual = notas_atuais[notas_atuais['ID_ALUNO'].apply(db.limpar_id) == id_l]
                                    v_vistos = reg_atual.iloc[0]['NOTA_VISTOS'] if not reg_atual.empty else "0,0"
                                    v_teste = reg_atual.iloc[0]['NOTA_TESTE'] if not reg_atual.empty else "0,0"
                                    v_prova = reg_atual.iloc[0]['NOTA_PROVA'] if not reg_atual.empty else "0,0"
                                    v_rec = reg_atual.iloc[0]['NOTA_REC'] if not reg_atual.empty else "0,0"
                                    
                                    nota_boletim = nota_s if r['Situação'] == "✅ REALIZADA" else "0,00"
                                    
                                    if "TESTE" in av_alvo_h.upper():
                                        v_teste = nota_boletim
                                    else:
                                        v_prova = nota_boletim
                                        
                                    nova_media = util.sosa_to_str(util.sosa_to_float(v_vistos) + util.sosa_to_float(v_teste) + util.sosa_to_float(v_prova))
                                    lista_boletim.append([id_l, nome_limpo, t_sel_h, tr_sel_h, v_vistos, v_teste, v_prova, v_rec, nova_media])
                            
                            if novos_registros_gabarito:
                                ws_g.append_rows(novos_registros_gabarito, value_input_option="USER_ENTERED")
                            
                            if not is_sonda and lista_boletim:
                                db.limpar_notas_turma_trimestre(t_sel_h, tr_sel_h)
                                db.salvar_lote("DB_NOTAS", lista_boletim)
                                
                            status_h.update(label="✅ Sistema Atualizado com Sucesso!", state="complete")
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()

                    st.markdown("---")
                    with st.expander("🚑 Protocolo Lázaro: Restaurar Gabaritos Perdidos", expanded=True):
                        st.info("💡 **Como usar:** Clique no link para ver a foto da prova. Depois, digite as letras que o aluno marcou tudo junto (Ex: BCCXC) e clique em Salvar. O sistema fará o resto.")
                        
                        df_perdidos = pd.DataFrame([r for r in dados_soberania if r['_Respostas'] == "MANUAL" and r['Evidência'] != "N/A" and r['Situação'] == "✅ REALIZADA"])
                        
                        if not df_perdidos.empty:
                            dados_restauracao =[]
                            for _, row_p in df_perdidos.iterrows():
                                dados_restauracao.append({
                                    "ID": row_p['ID'],
                                    "Estudante": row_p['Estudante'],
                                    "Ver Foto": row_p['Evidência'],
                                    "Digite as Letras (Ex: ABCDE)": ""
                                })
                            
                            df_rest_ed = st.data_editor(
                                pd.DataFrame(dados_restauracao),
                                hide_index=True,
                                use_container_width=True,
                                column_config={
                                    "ID": None,
                                    "Estudante": st.column_config.TextColumn("Estudante", disabled=True),
                                    "Ver Foto": st.column_config.LinkColumn("📸 Abrir Foto no Drive"),
                                    "Digite as Letras (Ex: ABCDE)": st.column_config.TextColumn("Gabarito (Digite tudo junto)", required=True)
                                },
                                key=f"ed_lazaro_{v}"
                            )
                            
                            if st.button("💾 PROCESSAR RESTAURAÇÃO", type="primary", use_container_width=True):
                                with st.spinner("Restaurando gabaritos e recalculando notas..."):
                                    material_ref = df_aulas[df_aulas['TIPO_MATERIAL'] == av_alvo_h].iloc[0]
                                    txt_ref = str(material_ref['CONTEUDO'])
                                    val_tag = ai.extrair_tag(txt_ref, "VALOR")
                                    v_total_at = util.sosa_to_float(val_tag) if val_tag else 10.0
                                    
                                    def extrair_gab_blindado(texto, is_pei=False):
                                        tag_alvo = "GABARITO_PEI" if is_pei else "GABARITO_TEXTO"
                                        raw = ai.extrair_tag(texto, tag_alvo) or ai.extrair_tag(texto, "GABARITO")
                                        if not raw: return[]
                                        matches = re.findall(r"(\d+)[\s\.\)\-:]+([A-E])", raw.upper())
                                        mapa = {int(num): letra for num, letra in matches}
                                        return [mapa[n] for n in sorted(mapa.keys())]
                                    
                                    gab_reg = extrair_gab_blindado(txt_ref, False)
                                    gab_pei = extrair_gab_blindado(txt_ref, True)
                                    
                                    wb_s = db.conectar()
                                    ws_g = wb_s.worksheet("DB_GABARITOS_ALUNOS")
                                    d_g = ws_g.get_all_values()
                                    
                                    updates =[]
                                    for _, r in df_rest_ed.iterrows():
                                        letras_digitadas = str(r['Digite as Letras (Ex: ABCDE)']).upper().replace(" ", "").replace(";", "")
                                        if len(letras_digitadas) > 0:
                                            resp_formatada = ";".join(list(letras_digitadas))
                                            
                                            alu_info = df_alunos[df_alunos['ID'].apply(db.limpar_id) == str(r['ID'])].iloc[0]
                                            nec_str = str(alu_info['NECESSIDADES']).upper().strip()
                                            is_pei_aluno = nec_str not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"]
                                            
                                            gab_alvo = gab_pei if is_pei_aluno else gab_reg
                                            
                                            res_lista = list(letras_digitadas)
                                            acertos = sum(1 for i, lido in enumerate(res_lista) if i < len(gab_alvo) and lido == gab_alvo[i])
                                            nota_f = (acertos / len(gab_alvo)) * v_total_at if len(gab_alvo) > 0 else 0
                                            nota_str = util.sosa_to_str(nota_f)
                                            
                                            for i, row_g in enumerate(d_g):
                                                if i > 0 and db.limpar_id(row_g[1]) == str(r['ID']) and nome_curto_av in row_g[4]:
                                                    updates.append(gspread.Cell(row=i+1, col=6, value=resp_formatada)) 
                                                    updates.append(gspread.Cell(row=i+1, col=7, value=nota_str)) 
                                                    break
                                    
                                    if updates:
                                        ws_g.update_cells(updates)
                                        st.success("✅ Gabaritos restaurados com sucesso! O Raio-X voltou a enxergar esses alunos.")
                                        time.sleep(2)
                                        st.rerun()
                        else:
                            st.success("✅ Nenhum gabarito perdido detectado para esta avaliação.")

            with sub_externas:
                st.markdown("#### 🌍 Integração de Notas Externas (SAEB / Governo)")
                c_ext1, c_ext2 = st.columns([1, 1])
                alvo_sub = c_ext1.radio("Onde aplicar esta nota externa?",["Substituir Teste", "Substituir Prova"], horizontal=True, key=f"alvo_ext_{v}")
                origem_ext = c_ext2.text_input("Origem da Nota:", "SAEB 2026", key=f"orig_ext_{v}")

                dados_externos =[]
                for _, alu in alunos_turma_h.iterrows():
                    dados_externos.append({"ID": alu['ID'], "Estudante": alu['NOME_ALUNO'], "Nota Externa (0-10)": 0.0})
                
                df_ext_ed = st.data_editor(pd.DataFrame(dados_externos), hide_index=True, use_container_width=True, key=f"ed_ext_v74_{v}",
                    column_config={"ID": None, "Nota Externa (0-10)": st.column_config.NumberColumn("Nota", format="%.1f", min_value=0.0, max_value=10.0)})

                if st.button("🚀 INTEGRAR NOTAS EXTERNAS AO BOLETIM", use_container_width=True):
                    with st.status("Processando Substituição de Notas...") as status_ext:
                        lista_boletim_ext = []
                        notas_atuais = df_notas[(df_notas['TURMA'] == t_sel_h) & (df_notas['TRIMESTRE'] == tr_sel_h)]
                        
                        for _, r in df_ext_ed.iterrows():
                            id_l = db.limpar_id(r['ID'])
                            nota_ext_str = util.sosa_to_str(r['Nota Externa (0-10)'])
                            reg_atual = notas_atuais[notas_atuais['ID_ALUNO'].apply(db.limpar_id) == id_l]
                            
                            v_vistos = reg_atual.iloc[0]['NOTA_VISTOS'] if not reg_atual.empty else "0,0"
                            v_teste = reg_atual.iloc[0]['NOTA_TESTE'] if not reg_atual.empty else "0,0"
                            v_prova = reg_atual.iloc[0]['NOTA_PROVA'] if not reg_atual.empty else "0,0"
                            v_rec = reg_atual.iloc[0]['NOTA_REC'] if not reg_atual.empty else "0,0"

                            if r['Nota Externa (0-10)'] > 0:
                                if "Teste" in alvo_sub: v_teste = nota_ext_str
                                else: v_prova = nota_ext_str
                                db.salvar_no_banco("DB_RELATORIOS",[datetime.now().strftime("%d/%m/%Y"), id_l, r['Estudante'], "NOTA_EXTERNA", f"Substituição via {origem_ext} no {alvo_sub}"])

                            nova_media = (util.sosa_to_float(v_vistos) + util.sosa_to_float(v_teste) + util.sosa_to_float(v_prova))
                            lista_boletim_ext.append([id_l, r['Estudante'], t_sel_h, tr_sel_h, v_vistos, v_teste, v_prova, v_rec, util.sosa_to_str(nova_media)])

                        db.limpar_notas_turma_trimestre(t_sel_h, tr_sel_h)
                        if db.salvar_lote("DB_NOTAS", lista_boletim_ext):
                            status_ext.update(label=f"✅ Notas do {origem_ext} integradas com sucesso!", state="complete"); st.balloons(); time.sleep(1); st.rerun()

    # --- ABA 4: RAIO-X PEDAGÓGICO ---
    with tab_raiox:
        st.subheader("📊 Raio-X Pedagógico: Diagnóstico Individual de Lacunas")
        st.caption("Analise o desempenho da turma por questão e gere um Dossiê Impresso para o Conselho de Classe.")
        st.markdown("---")

        def is_regular_student(nec_val):
            val = str(nec_val).upper()
            if "TIPICO" in val or "TÍPICO" in val or "TÃPICO" in val: return True
            if val.strip() in["", "NAN", "NONE", "NENHUMA", "PENDENTE"]: return True
            return False

        def extrair_gab_blindado(texto, is_pei=False):
            if not texto: return {}
            txt_limpo = re.sub(r'[*#]', '', texto).upper()
            tag_alvo = "GABARITO_PEI" if is_pei else "GABARITO_TEXTO"
            bloco = ai.extrair_tag(txt_limpo, tag_alvo) or ai.extrair_tag(txt_limpo, "GABARITO")
            matches = re.findall(r"(?:QUEST[AÃ]O\s*)?0?(\d+)\s*[\s\.\-\:\)]+\s*([A-E])", bloco)
            if matches: return {int(num): letra for num, letra in matches}
            letras = re.findall(r"\b[A-E]\b", bloco)
            return {i+1: letra for i, letra in enumerate(letras)}

        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1, 1.5])
            t_sel_r = c1.selectbox("👥 Selecione a Turma:", [""] + lista_turmas_cir, key=f"t_r_v90_{v}")
            tr_sel_r = c2.selectbox("📅 Selecione o Trimestre:",["I Trimestre", "II Trimestre", "III Trimestre"], key=f"tr_r_v90_{v}")
            
            opcoes_r = filtrar_ativos_cir(t_sel_r, tr_sel_r, apenas_provas=True)
            opcoes_base_r =[opt for opt in opcoes_r if not re.search(r"2[ªA]|CHAMADA", opt, re.IGNORECASE)]
            at_sel_r = c3.selectbox("📋 Selecione a Avaliação Base (Slot):", [""] + opcoes_base_r, key=f"at_r_v90_{v}")

        if not t_sel_r or not at_sel_r:
            st.info("💡 Selecione a Turma e a Avaliação para carregar a Perícia Pedagógica.")
        else:
            nome_curto_av = at_sel_r.split("-")[0].strip()
            ano_num_r = "".join(filter(str.isdigit, t_sel_r))
            
            respostas_brutas = df_diagnosticos[
                (df_diagnosticos['TURMA'].str.strip() == t_sel_r.strip()) & 
                (df_diagnosticos['ID_AVALIACAO'].str.contains(nome_curto_av, case=False))
            ].copy()

            if respostas_brutas.empty:
                st.warning("⚠️ Nenhuma resposta de aluno encontrada para esta avaliação.")
            else:
                df_alunos_min = df_alunos[['ID', 'NECESSIDADES']].copy()
                df_alunos_min['ID'] = df_alunos_min['ID'].apply(db.limpar_id)
                respostas_brutas['ID_ALUNO_L'] = respostas_brutas['ID_ALUNO'].apply(db.limpar_id)
                
                df_analise = pd.merge(respostas_brutas, df_alunos_min, left_on='ID_ALUNO_L', right_on='ID', how='left')
                df_analise['IS_PEI'] = ~df_analise['NECESSIDADES'].apply(is_regular_student)
                df_analise['IS_2A_CHAMADA'] = df_analise['ID_AVALIACAO'].str.contains(r"2[ªA]|CHAMADA", case=False, regex=True)

                st.markdown("### 🎯 1. Análise de Performance por Item")
                col_l1, col_l2 = st.columns(2)
                perfil_visao = col_l1.radio("1. Perfil do Aluno:",["📝 Alunos Regulares", "♿ Alunos PEI"], horizontal=True, key=f"perf_v90_{v}")
                versao_visao = col_l2.radio("2. Versão da Prova:",["📄 Prova Original", "🔄 2ª Chamada"], horizontal=True, key=f"vers_v90_{v}")
                
                is_pei_view = "PEI" in perfil_visao
                is_2a_view = "2ª" in versao_visao
                df_filtrado = df_analise[(df_analise['IS_PEI'] == is_pei_view) & (df_analise['IS_2A_CHAMADA'] == is_2a_view)]

                if is_2a_view:
                    query_mat = df_aulas[(df_aulas['TIPO_MATERIAL'].str.upper().str.contains("2CHAMADA")) & (df_aulas['TIPO_MATERIAL'].str.upper().str.contains(nome_curto_av.upper()))]
                else:
                    query_mat = df_aulas[df_aulas['TIPO_MATERIAL'] == at_sel_r]

                txt_prova_global = ""
                grade_pericia_global = ""
                df_stats_global = pd.DataFrame()
                fig_global = None 

                if query_mat.empty:
                    st.error(f"❌ Gabarito da {versao_visao} não localizado.")
                elif df_filtrado.empty:
                    st.info(f"📭 Não há dados de {perfil_visao} para a {versao_visao}.")
                else:
                    dados_prova = query_mat.iloc[0]
                    txt_prova_global = str(dados_prova['CONTEUDO'])
                    grade_pericia_global = re.sub(r'[*#]', '', ai.extrair_tag(txt_prova_global, "GRADE_DE_CORRECAO"))
                    gab_ativo = extrair_gab_blindado(txt_prova_global, is_pei_view)

                    num_q_total = len(gab_ativo)
                    stats_list =[]
                    matriz_respostas = [str(r).split(';') for r in df_filtrado['RESPOSTAS_ALUNO']]

                    for i in range(1, num_q_total + 1):
                        correta = gab_ativo.get(i, "?")
                        votos = [res[i-1] if len(res) >= i else "?" for res in matriz_respostas]
                        acertos = votos.count(correta)
                        perc = (acertos / len(votos)) * 100 if len(votos) > 0 else 0
                        stats_list.append({"Questão": f"Q{i:02d}", "Acerto %": perc, "Gabarito": correta})

                    df_stats_global = pd.DataFrame(stats_list)
                    col_graf, col_item = st.columns([1.2, 1])
                    with col_graf:
                        fig_global = px.bar(df_stats_global, x="Questão", y="Acerto %", text_auto='.0f', color="Acerto %", color_continuous_scale="RdYlGn")
                        fig_global.update_layout(yaxis_range=[0, 110], height=350)
                        st.plotly_chart(fig_global, use_container_width=True)
                    with col_item:
                        with st.container(border=True):
                            st.markdown("**🔬 Perícia do Item**")
                            q_sel = st.selectbox("Analisar questão:", df_stats_global["Questão"].tolist(), key=f"q_sel_v90_{is_pei_view}_{is_2a_view}")
                            info_q = df_stats_global[df_stats_global["Questão"] == q_sel].iloc[0]
                            idx_num = int(q_sel[1:])
                            st.write(f"**Gabarito:** :green[{info_q['Gabarito']}] | **Média:** {info_q['Acerto %']:.1f}%")
                            padrao = rf"(?si)QUEST[AÃ]O\s*(?:PEI\s*)?0?{idx_num}\b.*?(?=QUEST[AÃ]O\s*(?:PEI\s*)?0?{idx_num+1}\b|GABARITO|RESPOSTAS|$)"
                            match = re.search(padrao, grade_pericia_global)
                            if match: st.info(match.group(0).strip())

                st.markdown("---")
                st.markdown("#### 👤 2. Perícia Individual: Lacunas e Diagnóstico de Erros")
                
                alunos_turma = df_alunos[df_alunos['TURMA'] == t_sel_r].sort_values(by="NOME_ALUNO")
                dados_indiv =[]

                for _, alu in alunos_turma.iterrows():
                    id_a = db.limpar_id(alu['ID'])
                    is_pei_alu = not is_regular_student(alu['NECESSIDADES'])
                    reg_aluno = df_analise[df_analise['ID_ALUNO_L'] == id_a]
                    
                    if reg_aluno.empty:
                        dados_indiv.append({"Estudante": alu['NOME_ALUNO'], "Perfil": "🔴 Ausente", "Nota": 0.00, "Diagnóstico Técnico de Erros": "Aguardando Realização"})
                    else:
                        reg = reg_aluno.iloc[-1]
                        nota_alu = util.sosa_to_float(reg['NOTA_CALCULADA'])
                        material_aluno = reg['ID_AVALIACAO']
                        
                        if str(reg['RESPOSTAS_ALUNO']).upper() == "FALTOU":
                            dados_indiv.append({"Estudante": alu['NOME_ALUNO'], "Perfil": "♿ PEI" if is_pei_alu else "📝 Regular", "Nota": 0.00, "Diagnóstico Técnico de Erros": "🔴 Aluno Ausente no dia da aplicação."})
                            continue

                        m_ref_query = df_aulas[df_aulas['TIPO_MATERIAL'] == material_aluno]
                        
                        if not m_ref_query.empty:
                            m_ref = m_ref_query.iloc[0]
                            txt_cont = str(m_ref['CONTEUDO'])
                            tag_grade = "GRADE_DE_CORRECAO_PEI" if is_pei_alu else "GRADE_DE_CORRECAO"
                            grade_texto = re.sub(r'[*#]', '', ai.extrair_tag(txt_cont, tag_grade) or ai.extrair_tag(txt_cont, "GRADE_DE_CORRECAO"))
                            
                            gab_ref_alu = extrair_gab_blindado(txt_cont, is_pei_alu)
                            resp_aluno_lista = str(reg['RESPOSTAS_ALUNO']).split(';')
                            
                            analise_de_erros =[]
                            for i, letra_marcada in enumerate(resp_aluno_lista):
                                q_n = i + 1
                                letra_correta = gab_ref_alu.get(q_n)
                                
                                if letra_marcada == "?":
                                    analise_de_erros.append(f"Q{q_n}: ⚪ Deixou em branco.")
                                    continue
                                elif letra_marcada == "X":
                                    analise_de_erros.append(f"Q{q_n}: 🚫 Dupla marcação / Rasura.")
                                    continue
                                
                                if letra_marcada != letra_correta:
                                    if letra_marcada not in ["A", "B", "C", "D", "E"]:
                                        analise_de_erros.append(f"Q{q_n}: Marcação inválida ({letra_marcada}).")
                                        continue
                                        
                                    padrao_bloco = rf"(?si)QUEST[AÃ]O\s*(?:PEI\s*)?0?{q_n}\b.*?(?=QUEST[AÃ]O|$)"
                                    bloco_q = re.search(padrao_bloco, grade_texto)
                                    
                                    if bloco_q:
                                        texto_bloco = bloco_q.group(0)
                                        match_hab = re.search(r"\[?(EF\d{2}MA\d{2})", texto_bloco)
                                        cod_h = match_hab.group(1) if match_hab else "BNCC"

                                        if is_pei_alu:
                                            m_lacuna = re.search(r"(?i)(?:ANÁLISE DE LACUNA PEI|LACUNA|ERRO)[\s\:]*(.*)", texto_bloco, re.DOTALL)
                                            if m_lacuna:
                                                txt_erro = m_lacuna.group(1).replace('\n', ' ').strip()
                                            else:
                                                m_just = re.search(r"(?i)JUSTIFICATIVA[\s\:]*(.*?)(?=ANÁLISE|$)", texto_bloco, re.DOTALL)
                                                txt_erro = m_just.group(1).replace('\n', ' ').strip() if m_just else "Falha na compreensão do conceito."
                                            analise_de_erros.append(f"[{cod_h}] Q{q_n}({letra_marcada}): {txt_erro}")
                                        else:
                                            padrao_distrator = rf"\({letra_marcada}\)\s*(.*?)(?=\([A-E]\)|$)"
                                            match_d = re.search(padrao_distrator, texto_bloco, re.DOTALL)
                                            if match_d:
                                                txt_erro = match_d.group(1).replace('\n', ' ').strip()
                                            else:
                                                m_peri = re.search(r"(?i)(?:PERÍCIA DE DISTRATORES|PERÍCIA|ANÁLISE)[\s\:]*(.*)", texto_bloco, re.DOTALL)
                                                txt_erro = m_peri.group(1).replace('\n', ' ').strip() if m_peri else "Erro de interpretação."
                                            analise_de_erros.append(f"[{cod_h}] Q{q_n}({letra_marcada}): {txt_erro}")
                            
                            if nota_alu < 10.0 and not analise_de_erros:
                                lacunas_txt = "⚠️ Erro na leitura da grade de correção. Verifique se a IA gerou a seção 'PERÍCIA DE DISTRATORES'."
                            else:
                                lacunas_txt = " | ".join(analise_de_erros) if analise_de_erros else "✅ Domínio Total das Habilidades"
                        else:
                            lacunas_txt = "⚠️ Material não localizado no Acervo."

                        dados_indiv.append({"Estudante": alu['NOME_ALUNO'], "Perfil": "♿ PEI" if is_pei_alu else "📝 Regular", "Nota": nota_alu, "Diagnóstico Técnico de Erros": lacunas_txt})

                df_f = pd.DataFrame(dados_indiv)
                st.data_editor(df_f, column_config={"Estudante": st.column_config.TextColumn("Estudante", width="medium"), "Diagnóstico Técnico de Erros": st.column_config.TextColumn("Diagnóstico (Raciocínio do Erro)", width="large")},
                    hide_index=True, use_container_width=True, disabled=True, key=f"raiox_final_v90_{v}")

                st.markdown("---")
                st.markdown("### 🖨️ Materialização do Dossiê (Para Impressão)")
                st.info("Gere um documento formatado com a autópsia completa da prova para levar para a sala dos professores ou Conselho de Classe.")
                
                if st.button("🖨️ GERAR DOSSIÊ DE RAIO-X (DOCX PARA IMPRESSÃO)", type="primary", use_container_width=True):
                    if df_stats_global.empty or not txt_prova_global:
                        st.error("⚠️ Dados insuficientes para gerar o dossiê. Certifique-se de que a prova foi carregada corretamente.")
                    else:
                        with st.spinner("Compilando Dossiê Analítico e renderizando gráficos..."):
                            
                            grafico_bytes = None
                            if fig_global is not None:
                                try:
                                    grafico_bytes = fig_global.to_image(format="png", width=800, height=350)
                                except Exception as e:
                                    st.warning("⚠️ O gráfico não pôde ser exportado. Certifique-se de que 'kaleido' está no requirements.txt.")
                            
                            media_turma = df_f['Nota'].mean()
                            top_3 = df_stats_global.sort_values(by="Acerto %").head(3)
                            top_3_str = ", ".join([f"{r['Questão']} ({r['Acerto %']:.1f}%)" for _, r in top_3.iterrows()])
                            
                            stats_gerais = {
                                "total_alunos": len(df_f),
                                "media_turma": f"{media_turma:.1f}",
                                "top_3": top_3_str
                            }
                            
                            questoes_detalhes =[]
                            questoes_raw = ai.extrair_tag(txt_prova_global, "QUESTOES")
                            
                            for _, r_stat in df_stats_global.iterrows():
                                q_str = r_stat['Questão']
                                q_num = int(q_str.replace("Q", ""))
                                
                                padrao_q = rf"(?si)(QUEST[AÃ]O\s*0?{q_num}\b.*?)(?=QUEST[AÃ]O\s*0?{q_num+1}\b|GABARITO|$)"
                                m_q = re.search(padrao_q, questoes_raw)
                                enunciado = re.sub(r'\[\s*PROMPT IMAGEM:.*?\]', '[IMAGEM DE APOIO]', m_q.group(1)).strip() if m_q else "Enunciado não localizado."
                                enunciado = re.sub(r'[*#]', '', enunciado)
                                
                                padrao_p = rf"(?si)(QUEST[AÃ]O\s*0?{q_num}\b.*?)(?=QUEST[AÃ]O\s*0?{q_num+1}\b|$)"
                                m_p = re.search(padrao_p, grade_pericia_global)
                                pericia_txt = m_p.group(1).strip() if m_p else "Perícia não localizada."
                                pericia_txt = re.sub(r'[*#]', '', pericia_txt)
                                
                                questoes_detalhes.append({
                                    "titulo": q_str,
                                    "enunciado": enunciado,
                                    "acerto": f"{r_stat['Acerto %']:.1f}%",
                                    "gabarito": r_stat['Gabarito'],
                                    "pericia": pericia_txt
                                })
                            
                            criticos = df_f[df_f['Nota'] < 6.0]['Estudante'].tolist()
                            
                            info_doc = {
                                "ano": t_sel_r, 
                                "trimestre": tr_sel_r,
                                "avaliacao": at_sel_r,
                                "data": datetime.now().strftime("%d/%m/%Y")
                            }
                            
                            nome_arquivo_dossie = f"RAIOX_{t_sel_r}_{nome_curto_av}"
                            doc_stream = exporter.gerar_docx_raiox_v90(nome_arquivo_dossie, info_doc, stats_gerais, questoes_detalhes, criticos, grafico_bytes)
                            link_doc = db.subir_e_converter_para_google_docs(doc_stream, nome_arquivo_dossie, trimestre=tr_sel_r, categoria=t_sel_r, modo="PLANEJAMENTO")
                            
                            if "https" in link_doc:
                                db.salvar_no_banco("DB_RELATORIOS",[
                                    datetime.now().strftime("%d/%m/%Y"), 
                                    "TURMA", 
                                    t_sel_r, 
                                    "DOSSIE_RAIO_X", 
                                    f"Avaliação: {at_sel_r}\nLink: {link_doc}"
                                ])
                                st.success("✅ Dossiê gerado e salvo no Acervo!")
                                st.balloons()
                            else:
                                st.error(f"Erro ao salvar no Drive: {link_doc}")

    # --- ABA 5: ACERVO DE DOSSIÊS ---
    with tab_acervo_cir:
        st.subheader("🗂️ Acervo de Dossiês Analíticos")
        st.caption("Acesse os relatórios de Raio-X gerados anteriormente para impressão.")
        st.markdown("---")
        
        if not df_relatorios.empty and 'TIPO' in df_relatorios.columns:
            df_dossies = df_relatorios[df_relatorios['TIPO'] == 'DOSSIE_RAIO_X'].copy()
        else:
            df_dossies = pd.DataFrame()
        
        if df_dossies.empty:
            st.info("📭 Nenhum Dossiê de Raio-X gerado ainda. Vá na aba 'Raio-X Pedagógico' para gerar o primeiro.")
        else:
            df_dossies = df_dossies.iloc[::-1]
            
            for idx, row in df_dossies.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    
                    data_d = row.get('DATA', 'S/D')
                    turma_d = row.get('NOME_ALUNO', 'Desconhecida') 
                    conteudo_d = str(row.get('CONTEUDO', ''))
                    
                    linhas_cont = conteudo_d.split("\n")
                    av_nome = linhas_cont[0].replace("Avaliação: ", "") if len(linhas_cont) > 0 else "Avaliação Desconhecida"
                    link_d = linhas_cont[1].replace("Link: ", "") if len(linhas_cont) > 1 else "#"
                    
                    c1.markdown(f"#### 📄 {av_nome}")
                    c1.caption(f"📅 Gerado em: {data_d} | 👥 Turma: {turma_d}")
                    
                    if "http" in link_d:
                        c2.link_button("🖨️ ABRIR PARA IMPRIMIR", link_d, use_container_width=True, type="primary")
                    else:
                        c2.button("⚪ SEM LINK", disabled=True, use_container_width=True)
                    
                    if c3.button("🗑️ APAGAR", key=f"del_dossie_{idx}", use_container_width=True):
                        with st.spinner("Apagando arquivo do Drive e limpando banco..."):
                            termo_busca = link_d if "http" in link_d else conteudo_d
                            db.excluir_registro_com_drive("DB_RELATORIOS", termo_busca)
                            st.rerun()


# ==============================================================================
# MÓDULO: DIÁRIO DE BORDO RÁPIDO - MOBILE FIRST (CLEAN & UX)
# ==============================================================================
elif menu == "📝 Diário de Bordo Rápido":
    st.title("📝 Diário de Bordo")
    st.caption("📱 **Modo Mobile:** Interface otimizada para toques rápidos. Os ícones ao lado dos nomes indicam o perfil cognitivo do aluno para facilitar a mediação em sala.")
    
    if "v_diario" not in st.session_state: st.session_state.v_diario = int(time.time())
    v = st.session_state.v_diario

    if df_alunos.empty:
        st.warning("⚠️ Base de alunos vazia. Por favor, cadastre as turmas e os alunos na aba 'Gestão da Turma'.")
    else:
        turmas_reais_db = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
        
        if turmas_reais_db.empty:
            st.warning("⚠️ Nenhuma turma regular cadastrada para o Diário.")
        else:
            # --- 1. FILTROS RÁPIDOS (TOPO DA TELA) ---
            with st.container(border=True):
                c1, c2 = st.columns(2)
                turma_sel = c1.selectbox("👥 Turma:", sorted(turmas_reais_db['ID_TURMA'].unique()), key=f"db_t_{v}")
                data_sel = c2.date_input("📅 Data:", date.today(), format="DD/MM/YYYY", key=f"db_d_{v}")
                data_str = data_sel.strftime("%d/%m/%Y")
                ano_num = "".join(filter(str.isdigit, str(turma_sel)))

            # --- 2. DETECÇÃO DO COCKPIT E DNA DO PLANO ---
            aula_ativa = df_registro_aulas[(df_registro_aulas['TURMA'] == turma_sel) & (df_registro_aulas['DATA'] == data_str)]
            
            if not aula_ativa.empty:
                row_ativa = aula_ativa.iloc[0]
                material_hoje = row_ativa['CONTEUDO_MINISTRADO']
                semana_ref = row_ativa['SEMANA']
                
                st.info(f"🚀 **Aula Ativa:** {material_hoje}")

                plano_vinculado = df_planos[(df_planos['SEMANA'] == semana_ref) & (df_planos['ANO'].str.contains(ano_num))]
                if not plano_vinculado.empty:
                    plano_txt = str(plano_vinculado.iloc[0]['PLANO_TEXTO'])
                    base_didatica = ai.extrair_tag(plano_txt, "BASE_DIDATICA")
                    if base_didatica: st.success(f"📍 **Páginas Alvo:** {base_didatica}")
                    else: st.warning("📍 **Páginas Alvo:** Método Manual (Sem livro vinculado)")

                match_material = df_aulas[df_aulas['TIPO_MATERIAL'].str.contains(material_hoje.split('+')[0].strip(), na=False)]
                if not match_material.empty:
                    with st.expander("📦 Ver Ativos de Safra (Links)", expanded=False):
                        txt_m = str(match_material.iloc[0]['CONTEUDO'])
                        def extrair_link(t, k):
                            m = re.search(rf"{k}.*?\(?(https?://[^\s\)]+)\)?", t, re.IGNORECASE)
                            return m.group(1).strip() if m else None
                        
                        l_alu = match_material.iloc[0].get('LINK_DRIVE')
                        l_pei = extrair_link(txt_m, "PEI")
                        l_prof = extrair_link(txt_m, "Prof")
                        
                        c_at1, c_at2, c_at3 = st.columns(3)
                        if l_alu and "N/A" not in l_alu: c_at1.link_button("📄 ALUNO", l_alu, use_container_width=True, type="primary")
                        if l_pei and "N/A" not in l_pei: c_at2.link_button("♿ PEI", l_pei, use_container_width=True)
                        if l_prof and "N/A" not in l_prof: c_at3.link_button("👨‍🏫 PROF", l_prof, use_container_width=True)
                
                reg_anterior = df_registro_aulas[(df_registro_aulas['TURMA'] == turma_sel) & (df_registro_aulas['DATA'] != data_str)].sort_values(by='DATA', ascending=False)
                if not reg_anterior.empty:
                    ultima_ponte = reg_anterior.iloc[0].get('PONTE_PEDAGOGICA', 'Sem registro.')
                    if ultima_ponte and str(ultima_ponte).strip() != "":
                        st.warning(f"🔙 **Na aula anterior paramos em:** {ultima_ponte}")
            else:
                st.warning("⚠️ Nenhuma aula aberta no Cockpit para esta data. O registro será salvo como 'Instrução Avulsa'.")
                material_hoje = "Instrução Avulsa"
            
            # --- 3. PAINEL DE REGÊNCIA (FECHADO POR PADRÃO) ---
            with st.expander("🚦 Fechamento de Aula (Regência)", expanded=False):
                st.caption("Preencha ao final da aula para alimentar a memória do sistema.")
                c_reg1, c_reg2, c_reg3 = st.columns([1, 2, 1])
                status_aula = c_reg1.selectbox("Status da Execução:",["🟢 Concluído (100%)", "🟡 Parcial (Pendência)", "🔴 Bloqueado (Crítico)"], key=f"status_reg_{v}")
                ponte_pedagogica = c_reg2.text_area("🔗 Ponte Pedagógica (Onde paramos?):", placeholder="Ex: Parei no slide 5...", height=68, key=f"ponte_reg_{v}")
                clima_turma = c_reg3.select_slider("🌡️ Clima da Turma:", options=["😴 Apática", "😐 Dispersa", "🧠 Focada", "⚡ Agitada", "🤯 Dificuldade Alta"], value="🧠 Focada", key=f"clima_reg_{v}")

            st.markdown("---")
            
            # --- 4. NATUREZA E AÇÕES EM LOTE ---
            c_nat, c_lote1, c_lote2 = st.columns([2, 1, 1])
            
            with c_nat:
                natureza_registro = st.radio(
                    "Modo de Aula:",["📝 Com Visto (Padrão)", "🗣️ Sem Visto (Evento)"],
                    horizontal=True,
                    help="Se 'Sem Visto', a coluna de vistos será ignorada no cálculo de notas.",
                    key=f"nat_reg_{v}"
                )
            
            with c_lote1:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ VISTO EM TODOS", use_container_width=True):
                    st.session_state[f"visto_lote_{turma_sel}"] = True
                    st.rerun()
            with c_lote2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🧹 LIMPAR TUDO", use_container_width=True):
                    st.session_state[f"visto_lote_{turma_sel}"] = False
                    st.rerun()

            # --- 5. BUSCA DE REGISTROS E MONTAGEM DA MESA ---
            registros_atuais = df_diario[(df_diario['DATA'] == data_str) & (df_diario['TURMA'] == turma_sel) & (df_diario['TAGS'] != "SISTEMA_NOTA")]
            alunos_turma = df_alunos[df_alunos['TURMA'] == turma_sel].sort_values(by="NOME_ALUNO")
            
            # 🚨 MOTOR DE ÍCONES MULTIPERFIL
            def definir_icone_status(nec):
                n = str(nec).upper().strip()
                if "PENDENTE" in n or "SUSPEITA" in n: return "🟠"
                if "DEFASAGEM LEITURA" in n: return "🧱"
                if "DEFASAGEM MATEMÁTICA" in n or "DEFASAGEM MATEMATICA" in n: return "🧮"
                if "ALTA PERFORMANCE" in n: return "🚀"
                if n in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]: return "👤"
                return "♿"

            dados_diario =[]
            for _, alu in alunos_turma.iterrows():
                id_a = db.limpar_id(alu['ID'])
                icone_perfil = definir_icone_status(alu['NECESSIDADES'])
                
                reg_existente = registros_atuais[registros_atuais['ID_ALUNO'].apply(db.limpar_id) == id_a]
                
                if not reg_existente.empty:
                    visto_val = str(reg_existente.iloc[0]['VISTO_ATIVIDADE']).upper() == "TRUE"
                    falta_val = reg_existente.iloc[0]['TAGS'] == "AUSÊNCIA"
                    bonus_val = util.sosa_to_float(reg_existente.iloc[0].get('BONUS', 0))
                    tag_val = reg_existente.iloc[0]['TAGS'] if not falta_val else ""
                    obs_val = reg_existente.iloc[0]['OBSERVACOES']
                else:
                    visto_val = st.session_state.get(f"visto_lote_{turma_sel}", True)
                    falta_val = False
                    bonus_val = 0.0
                    tag_val = ""
                    obs_val = ""

                dados_diario.append({
                    "ID": id_a,
                    "Estudante": f"{icone_perfil} {alu['NOME_ALUNO']}",
                    "F": falta_val,
                    "V": visto_val,
                    "⭐": bonus_val,
                    "Vetor": tag_val,
                    "Obs (🎙️)": obs_val
                })

            # 🚨 CÁLCULO DINÂMICO DE ALTURA (TABELA INFINITA MOBILE-FIRST)
            altura_dinamica = (len(dados_diario) * 35) + 40

            df_editado = st.data_editor(
                pd.DataFrame(dados_diario),
                height=altura_dinamica, 
                column_config={
                    "ID": None,
                    "Estudante": st.column_config.TextColumn("Estudante", width="medium", disabled=True),
                    "F": st.column_config.CheckboxColumn("F", help="Faltou"),
                    "V": st.column_config.CheckboxColumn("V", help="Visto", disabled=("Sem Visto" in natureza_registro)),
                    "⭐": st.column_config.SelectboxColumn("⭐", options=[0.0, 0.1, 0.2, 0.3, 0.5, 1.0], width="small"),
                    "Vetor": st.column_config.SelectboxColumn(
                        "Vetor", 
                        options=["", "Fardamento", "Postura", "Atraso", "Celular", "Indisciplina", "Comunicação", "Elogio", "Destaque", "Dormiu", "PEI CONCLUÍDO"],
                        width="small"
                    ),
                    "Obs (🎙️)": st.column_config.TextColumn("Obs (🎙️)", width="large")
                },
                hide_index=True, use_container_width=True, key=f"editor_diario_{v}"
            )

            # --- 6. SALVAMENTO E SINCRONIA ---
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 SALVAR DIÁRIO E CONSOLIDAR", type="primary", use_container_width=True):
                with st.status("Sincronizando Práxis...") as status:
                    db.limpar_diario_data_turma(data_str, turma_sel)
                    
                    linhas_diario =[]
                    for _, r in df_editado.iterrows():
                        # Lógica de PEI Concluído (Apenas para Laudos e Suspeitas)
                        aluno_eh_pei = "♿" in r['Estudante'] or "🟠" in r['Estudante']
                        tag_f = "AUSÊNCIA" if r['F'] else r['Vetor']
                        
                        visto_f = False if r['F'] else r['V']
                        visto_db = "ISENTO" if "Sem Visto" in natureza_registro else str(visto_f)
                        
                        if aluno_eh_pei and visto_f and not tag_f and "Sem Visto" not in natureza_registro:
                            tag_f = "PEI CONCLUÍDO"
                        
                        obs_final = r['Obs (🎙️)']
                        if r['Vetor'] == "Comunicação":
                            obs_final = f"🚨 COMUNICAÇÃO: {obs_final}"

                        # Limpeza blindada do nome para salvar no banco
                        nome_limpo = r['Estudante'].replace("♿ ", "").replace("👤 ", "").replace("🟠 ", "").replace("🧱 ", "").replace("🧮 ", "").replace("🚀 ", "")

                        linhas_diario.append([
                            data_str, r['ID'], nome_limpo, turma_sel,
                            visto_db, tag_f, obs_final, util.sosa_to_str(r['⭐'])
                        ])
                                
                    if db.salvar_lote("DB_DIARIO_BORDO", linhas_diario):
                        db.atualizar_fechamento_aula(data_str, turma_sel, status_aula, ponte_pedagogica, clima_turma)
                        status.update(label="✅ Diário e Regência Atualizados!", state="complete")
                        st.balloons()
                        if f"visto_lote_{turma_sel}" in st.session_state: del st.session_state[f"visto_lote_{turma_sel}"]
                        time.sleep(1); st.rerun()


# ==============================================================================
# MÓDULO: BIOGRAFIA DO ESTUDANTE - DOSSIÊ DE EVOLUÇÃO (CLEAN & UX)
# ==============================================================================
elif menu == "👤 Biografia do Estudante":
    st.title("👤 Biografia do Estudante: Dossiê de Evolução")
    st.caption("💡 **Guia de Comando:** Visão analítica da jornada do aluno. Use este painel em reuniões de pais para justificar médias mostrando a composição exata das notas, a evolução nas provas e o engajamento em sala.")
    st.markdown("---")

    if df_alunos.empty:
        st.warning("⚠️ Base de alunos vazia. Cadastre as turmas primeiro.")
    else:
        # --- 1. FILTROS DE ACESSO RÁPIDO ---
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 1.5, 1])
            
            turmas_reais_bio = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
            lista_turmas_bio = sorted(turmas_reais_bio['ID_TURMA'].unique()) if not turmas_reais_bio.empty else sorted(df_alunos['TURMA'].unique())
            
            turma_b = c1.selectbox("👥 Turma:", lista_turmas_bio, key="bio_t")
            lista_alunos = df_alunos[df_alunos['TURMA'] == turma_b].sort_values(by="NOME_ALUNO").copy()
            
            if lista_alunos.empty:
                st.warning("Nenhum aluno cadastrado nesta turma.")
                st.stop()
            
            # 🚨 MOTOR DE ÍCONES MULTIPERFIL
            def definir_icone_status(nec):
                n = str(nec).upper().strip()
                if "PENDENTE" in n or "SUSPEITA" in n: return "🟠"
                if "DEFASAGEM LEITURA" in n: return "🧱"
                if "DEFASAGEM MATEMÁTICA" in n or "DEFASAGEM MATEMATICA" in n: return "🧮"
                if "ALTA PERFORMANCE" in n: return "🚀"
                if n in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]: return "👤"
                return "♿"

            lista_alunos['STATUS_ICON'] = lista_alunos['NECESSIDADES'].apply(definir_icone_status)
            lista_alunos['LABEL'] = lista_alunos.apply(lambda x: f"{x['STATUS_ICON']} {x['NOME_ALUNO']}", axis=1)
                
            aluno_b_label = c2.selectbox("🎓 Estudante:", lista_alunos['LABEL'].tolist(), key="bio_a")
            trim_b = c3.selectbox("📅 Período de Análise:",["Todos", "I Trimestre", "II Trimestre", "III Trimestre"], help="Filtre para ver o desempenho em um trimestre específico ou o consolidado do ano.", key="bio_trim")

        # --- LÓGICA DE DATAS DO TRIMESTRE (Sincronia Itabuna 2026) ---
        if trim_b == "I Trimestre": dt_ini, dt_fim = date(2026, 2, 9), date(2026, 5, 22)
        elif trim_b == "II Trimestre": dt_ini, dt_fim = date(2026, 5, 25), date(2026, 9, 4)
        elif trim_b == "III Trimestre": dt_ini, dt_fim = date(2026, 9, 8), date(2026, 12, 17)
        else: dt_ini, dt_fim = date(2026, 1, 1), date(2026, 12, 31)

        # Captura dados básicos do aluno
        nome_limpo = aluno_b_label.split(" ", 1)[1].strip() # Remove o ícone para buscar no banco
        info_alu = lista_alunos[lista_alunos['NOME_ALUNO'] == nome_limpo].iloc[0]
        id_alu = db.limpar_id(info_alu['ID'])
        perfil_atual = str(info_alu['NECESSIDADES']).upper().strip()
        
        # --- FILTRAGEM DE BASES POR ALUNO E TEMPO ---
        n_alu = df_notas[df_notas['ID_ALUNO'].apply(db.limpar_id) == id_alu]
        n_alu_f = n_alu[n_alu['TRIMESTRE'] == trim_b] if trim_b != "Todos" else n_alu.copy()

        d_alu_f = pd.DataFrame()
        if not df_diario.empty:
            d_alu = df_diario[df_diario['ID_ALUNO'].apply(db.limpar_id) == id_alu].copy()
            if not d_alu.empty:
                d_alu['DATA_DT'] = pd.to_datetime(d_alu['DATA'], format="%d/%m/%Y", errors='coerce').dt.date
                d_alu_f = d_alu[(d_alu['DATA_DT'] >= dt_ini) & (d_alu['DATA_DT'] <= dt_fim)]

        diag_alu_f = pd.DataFrame()
        if not df_diagnosticos.empty:
            diag_alu = df_diagnosticos[df_diagnosticos['ID_ALUNO'].apply(db.limpar_id) == id_alu]
            if trim_b != "Todos":
                diag_alu_f = diag_alu[diag_alu['ID_AVALIACAO'].str.replace(" ","").str.upper().str.contains(trim_b.replace(" ","").upper(), na=False)]
            else:
                diag_alu_f = diag_alu.copy()

        # --- CABEÇALHO DE STATUS (IDENTIDADE DO ALUNO) ---
        c_h1, c_h2 = st.columns([2, 1])
        with c_h1:
            st.subheader(f"🎓 {nome_limpo}")
            st.caption(f"**ID do Sistema:** {id_alu}")
        with c_h2:
            if not n_alu.empty:
                soma_anual = n_alu[n_alu['TRIMESTRE'].isin(["I Trimestre", "II Trimestre", "III Trimestre"])]['MEDIA_FINAL'].apply(util.sosa_to_float).sum()
                st.metric("Soma Anual (Meta 18.0)", f"{soma_anual:.1f}", delta=f"{soma_anual - 18.0:.1f}")

        # 🚨 BANNERS DINÂMICOS DE PERFIL COGNITIVO
        if "PENDENTE" in perfil_atual or "SUSPEITA" in perfil_atual:
            st.warning(f"🟠 **Radar de Investigação:** {perfil_atual}")
        elif "DEFASAGEM" in perfil_atual:
            st.error(f"🧱 **Barreira de Aprendizagem:** {perfil_atual}")
        elif "ALTA PERFORMANCE" in perfil_atual:
            st.info(f"🚀 **Destaque Cognitivo:** {perfil_atual}")
        elif perfil_atual not in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]:
            st.warning(f"♿ **Condição Clínica (PEI):** {perfil_atual}")
        else:
            st.success(f"👤 **Perfil Cognitivo:** Típico / Padrão")

        # --- BLOCO 1: EXTRATO ANALÍTICO DE NOTAS ---
        st.markdown(f"### 🧾 1. Extrato Analítico de Notas ({trim_b})")
        st.caption("Composição exata da média final. Mostra o peso do engajamento (Vistos) no resultado do aluno.")
        with st.container(border=True):
            if not n_alu_f.empty:
                dados_notas =[]
                trims_para_exibir = ["I Trimestre", "II Trimestre", "III Trimestre"] if trim_b == "Todos" else [trim_b]
                for t in trims_para_exibir:
                    reg = n_alu[n_alu['TRIMESTRE'] == t]
                    if not reg.empty:
                        dados_notas.append({
                            "Trimestre": t,
                            "Vistos (Caderno)": util.sosa_to_float(reg.iloc[0]['NOTA_VISTOS']),
                            "Teste/Trabalho": util.sosa_to_float(reg.iloc[0]['NOTA_TESTE']),
                            "Prova Oficial": util.sosa_to_float(reg.iloc[0]['NOTA_PROVA']),
                            "Rec. Paralela": util.sosa_to_float(reg.iloc[0]['NOTA_REC']),
                            "Média Final": util.sosa_to_float(reg.iloc[0]['MEDIA_FINAL']),
                            "Status": "✅ OK" if util.sosa_to_float(reg.iloc[0]['MEDIA_FINAL']) >= 6.0 else "⚠️ ABAIXO"
                        })
                if dados_notas:
                    st.dataframe(pd.DataFrame(dados_notas), use_container_width=True, hide_index=True)
                else: 
                    st.info(f"📭 Sem notas lançadas para o {trim_b}.")
            else: 
                st.info(f"📭 Aguardando lançamento de notas no Boletim.")

        # --- BLOCO 2: LINHA DO TEMPO DE EVOLUÇÃO (AVALIAÇÕES) ---
        st.markdown(f"### 📈 2. Linha do Tempo de Avaliações ({trim_b})")
        st.caption("Trajetória de aprendizagem extraída diretamente do Scanner de Gabaritos.")
        with st.container(border=True):
            if not diag_alu_f.empty:
                # Ordena pela data para mostrar a evolução cronológica
                diag_alu_f['DATA_DT'] = pd.to_datetime(diag_alu_f['DATA'], format="%d/%m/%Y", errors='coerce')
                diag_ordenado = diag_alu_f.sort_values(by='DATA_DT')
                
                qtd_avs = len(diag_ordenado)
                cols_av = st.columns(qtd_avs if qtd_avs > 0 else 1)
                
                for i, (_, row_av) in enumerate(diag_ordenado.iterrows()):
                    with cols_av[i % len(cols_av)]:
                        nome_av_curto = row_av['ID_AVALIACAO'].split('-')[0].strip()
                        nota_av = util.sosa_to_float(row_av['NOTA_CALCULADA'])
                        
                        # Define a cor baseada na nota
                        if nota_av >= 7.0:
                            cor = "normal" # Verde no Streamlit
                        elif nota_av >= 5.0:
                            cor = "off" # Cinza
                        else:
                            cor = "inverse" # Vermelho
                            
                        st.metric(label=nome_av_curto, value=f"{nota_av:.1f}", delta="Avaliação Escaneada", delta_color=cor)
            else:
                st.info("📭 Nenhuma avaliação escaneada para este aluno no período selecionado.")

        # --- BLOCO 3: ENGAJAMENTO E COMPORTAMENTO ---
        st.markdown(f"### 📊 3. Perfil de Engajamento e Comportamento ({trim_b})")
        with st.container(border=True):
            col_v1, col_v2 = st.columns([1.2, 1.8])
            with col_v1:
                if not d_alu_f.empty:
                    # Lógica de Assiduidade (Conta todas as aulas)
                    total_aulas_presenca = len(d_alu_f)
                    faltas = len(d_alu_f[d_alu_f['TAGS'] == "AUSÊNCIA"])
                    presencas = total_aulas_presenca - faltas
                    perc_presenca = (presencas / total_aulas_presenca) * 100 if total_aulas_presenca > 0 else 0
                    
                    # Lógica de Vistos (Ignora aulas ISENTAS)
                    d_alu_vistos = d_alu_f[d_alu_f['VISTO_ATIVIDADE'].astype(str).str.upper() != "ISENTO"]
                    total_aulas_visto = len(d_alu_vistos)
                    vistos = len(d_alu_vistos[d_alu_vistos['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"])
                    perc_visto = (vistos / total_aulas_visto) * 100 if total_aulas_visto > 0 else 0
                    
                    st.metric("Assiduidade (Presença)", f"{perc_presenca:.0f}%", f"{faltas} faltas registradas", delta_color="inverse" if faltas > 0 else "normal")
                    st.progress(perc_presenca / 100)
                    
                    st.metric("Vistos no Caderno", f"{perc_visto:.0f}%", f"{vistos}/{total_aulas_visto} aulas válidas")
                else: 
                    st.info(f"📭 Sem registros de diário para o período.")

            with col_v2:
                st.markdown("**🚩 Ocorrências, Trabalhos e Observações:**")
                if not d_alu_f.empty:
                    tags_obs = d_alu_f[(d_alu_f['TAGS'] != "") | (d_alu_f['OBSERVACOES'] != "")]
                    if not tags_obs.empty:
                        for _, row in tags_obs.tail(8).iterrows():
                            tag_str = str(row['TAGS']).upper()
                            obs_str = str(row['OBSERVACOES'])
                            
                            # Define o ícone baseado na natureza do registro
                            if "SISTEMA_NOTA" in tag_str or "PROJETO" in obs_str.upper():
                                emoji = "📘"
                            elif any(x in tag_str for x in["DORMIU", "CONVERSA", "MATERIAL", "FALTOU", "AUSÊNCIA", "ATRASO", "CELULAR", "INDISCIPLINA"]):
                                emoji = "🔴"
                            else:
                                emoji = "🟢"
                                
                            # Formata a exibição
                            display_tag = tag_str if tag_str != "SISTEMA_NOTA" else "TRABALHO"
                            st.caption(f"{emoji} **{row['DATA']}**: {display_tag} - *{obs_str}*")
                    else: 
                        st.success("✅ Nenhuma ocorrência ou trabalho registrado.")

        # --- BLOCO 4: MAPA DE LACUNAS (RAIO-X) ---
        st.markdown(f"### 🧠 4. Mapa de Lacunas e Dificuldades ({trim_b})")
        st.caption("Habilidades da BNCC que o aluno errou nas avaliações e que precisam de reforço.")
        with st.container(border=True):
            if not diag_alu_f.empty:
                todas_as_lacunas =[]
                
                for _, reg_av in diag_alu_f.iterrows():
                    nome_av_real = reg_av['ID_AVALIACAO']
                    m_ref_query = df_aulas[df_aulas['TIPO_MATERIAL'] == nome_av_real.replace(" (2ª CHAMADA)", "")]
                    
                    if not m_ref_query.empty:
                        m_ref = m_ref_query.iloc[0]
                        txt_p = str(m_ref['CONTEUDO'])
                        
                        # Verifica se o aluno é PEI para buscar a grade correta
                        is_pei_alu = perfil_atual not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"] and "TIPICO" not in perfil_atual
                        
                        tag_grade = "GRADE_DE_CORRECAO_PEI" if is_pei_alu else "GRADE_DE_CORRECAO"
                        grade = ai.extrair_tag(txt_p, tag_grade) or ai.extrair_tag(txt_p, "GRADE_DE_CORRECAO")
                        
                        tag_g = "GABARITO_PEI" if is_pei_alu else "GABARITO_TEXTO"
                        gab_raw = ai.extrair_tag(txt_p, tag_g) or ai.extrair_tag(txt_p, "GABARITO")
                        gab_oficial = re.findall(r"\b[A-E]\b", gab_raw.upper())
                        
                        respostas_aluno = str(reg_av['RESPOSTAS_ALUNO']).split(';')
                        
                        for i, r in enumerate(respostas_aluno):
                            if i < len(gab_oficial) and r != gab_oficial[i] and r not in["FALTOU", "?", "X"]:
                                q_n = i + 1
                                padrao_h = rf"(?si)QUEST[AÃ]O\s*(?:PEI\s*)?0?{q_n}\b.*?(?:[:\-])\s*(.*?)(?=\.?\s*(?:JUSTIFICATIVA|PERÍCIA|ANÁLISE|DISTRATORES|$))"
                                m_h = re.search(padrao_h, grade)
                                
                                if m_h:
                                    txt_limpo = re.sub(r'[*#\[\]]', '', m_h.group(1)).strip()
                                    todas_as_lacunas.append(txt_limpo)
                
                if todas_as_lacunas:
                    for l in list(dict.fromkeys(todas_as_lacunas)): 
                        st.error(f"❌ {l}")
                else:
                    st.success("✅ Domínio total nas habilidades das avaliações realizadas.")
            else:
                st.info("📭 Aguardando avaliações escaneadas para gerar o mapa de lacunas.")

        st.caption(f"Dossiê atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ==============================================================================
# MÓDULO: PAINEL DE NOTAS & VISTOS - CLEAN & UX (MULTIPERFIL)
# ==============================================================================
elif menu == "📊 Painel de Notas & Vistos":
    st.title("📊 Torre de Comando: Gestão de Notas")
    st.caption("💡 **Guia de Comando:** Defina os pesos do trimestre. O sistema calculará automaticamente a nota de caderno (Vistos) e aplicará o algoritmo de transbordamento de Bônus (preenchendo Vistos, depois Teste, depois Prova).")
    st.markdown("---")

    if "v_notas" not in st.session_state: 
        st.session_state.v_notas = int(time.time())
    v = st.session_state.v_notas

    if df_alunos.empty:
        st.warning("⚠️ Cadastre alunos primeiro na aba 'Gestão da Turma'.")
    else:
        turmas_reais_notas = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
        lista_turmas_notas = sorted(turmas_reais_notas['ID_TURMA'].unique()) if not turmas_reais_notas.empty else sorted(df_alunos['TURMA'].unique())

        if not lista_turmas_notas:
            st.warning("⚠️ Nenhuma turma regular cadastrada.")
            st.stop()

        # --- 1. CONFIGURADOR DE PESOS ---
        with st.container(border=True):
            st.markdown("### ⚙️ Passo 1: Critérios de Avaliação do Trimestre")
            c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns([1.5, 1, 0.8, 0.8, 0.8])
            turma_sel = c_f1.selectbox("👥 Selecione a Turma:", lista_turmas_notas, key=f"n_turma_{v}")
            trimestre_sel = c_f2.selectbox("📅 Trimestre Atual:", ["I Trimestre", "II Trimestre", "III Trimestre"], key=f"n_trim_{v}")
            
            p_visto = c_f3.number_input("Peso Vistos:", 0.0, 10.0, 3.0, step=0.5, help="Pontuação máxima que o aluno pode atingir com os vistos de caderno.", key=f"p_v_{v}")
            p_teste = c_f4.number_input("Peso Teste:", 0.0, 10.0, 3.0, step=0.5, help="Pontuação máxima do Teste/Trabalho.", key=f"p_t_{v}")
            p_prova = c_f5.number_input("Peso Prova:", 0.0, 10.0, 4.0, step=0.5, help="Pontuação máxima da Prova Oficial.", key=f"p_p_{v}")
            
            if (p_visto + p_teste + p_prova) != 10.0:
                st.warning(f"⚠️ A soma dos pesos ({p_visto + p_teste + p_prova}) deve ser exatamente 10.0 para o sistema oficial.")

        # 🚨 VACINA ANTI-VAZIO
        alunos_turma = df_alunos[df_alunos['TURMA'] == turma_sel].sort_values(by="NOME_ALUNO")
        
        if alunos_turma.empty:
            st.warning(f"⚠️ Nenhum aluno cadastrado na turma {turma_sel} ainda. Vá em 'Gestão da Turma' para povoar.")
            st.stop()

        # --- 2. MOTOR DE CÁLCULO AUTOMÁTICO (DIÁRIO DE BORDO) ---
        vistos_auto_map = {}
        bonus_total_map = {}
        
        calendario = {
            "I Trimestre": (date(2026, 2, 9), date(2026, 5, 22)),
            "II Trimestre": (date(2026, 5, 25), date(2026, 9, 4)),
            "III Trimestre": (date(2026, 9, 8), date(2026, 12, 17))
        }
        dt_ini, dt_fim = calendario.get(trimestre_sel)

        if not df_diario.empty:
            df_d_t = df_diario[df_diario['TURMA'] == turma_sel].copy()
            df_d_t['DATA_DT'] = pd.to_datetime(df_d_t['DATA'], format="%d/%m/%Y", errors='coerce').dt.date
            df_d_trim = df_d_t[(df_d_t['DATA_DT'] >= dt_ini) & (df_d_t['DATA_DT'] <= dt_fim)]
            
            for id_aluno in alunos_turma['ID']:
                id_l = db.limpar_id(id_aluno)
                d_alu = df_d_trim[df_d_trim['ID_ALUNO'].apply(db.limpar_id) == id_l]
                
                if not d_alu.empty:
                    # Ignora as aulas ISENTAS no cálculo do total de vistos
                    d_alu_validas = d_alu[d_alu['VISTO_ATIVIDADE'].astype(str).str.upper() != "ISENTO"]
                    
                    vistos_validos = d_alu_validas[d_alu_validas['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"]
                    aulas_com_visto = len(vistos_validos)
                    total_aulas_periodo = len(d_alu_validas)
                    
                    vistos_auto_map[id_l] = round((aulas_com_visto / total_aulas_periodo * p_visto), 2) if total_aulas_periodo > 0 else 0.0
                    
                    # O Bônus continua somando de TODAS as aulas
                    bonus_total_map[id_l] = d_alu['BONUS'].apply(util.sosa_to_float).sum()
                else:
                    vistos_auto_map[id_l], bonus_total_map[id_l] = 0.0, 0.0

        # --- 3. CONSOLIDAÇÃO DA MESA DE LANÇAMENTO ---
        notas_banco = df_notas[(df_notas['TURMA'] == turma_sel) & (df_notas['TRIMESTRE'] == trimestre_sel)]
        
        # 🚨 MOTOR DE ÍCONES MULTIPERFIL
        def definir_icone_status(nec):
            n = str(nec).upper().strip()
            if "PENDENTE" in n or "SUSPEITA" in n: return "🟠"
            if "DEFASAGEM LEITURA" in n: return "🧱"
            if "DEFASAGEM MATEMÁTICA" in n or "DEFASAGEM MATEMATICA" in n: return "🧮"
            if "ALTA PERFORMANCE" in n: return "🚀"
            if n in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]: return "👤"
            return "♿"

        dados_editor =[]
        for _, alu in alunos_turma.iterrows():
            id_a = db.limpar_id(alu['ID'])
            reg_b = notas_banco[notas_banco['ID_ALUNO'].apply(db.limpar_id) == id_a]
            
            n_teste = util.sosa_to_float(reg_b.iloc[0]['NOTA_TESTE']) if not reg_b.empty else 0.0
            n_prova = util.sosa_to_float(reg_b.iloc[0]['NOTA_PROVA']) if not reg_b.empty else 0.0
            n_rec = util.sosa_to_float(reg_b.iloc[0]['NOTA_REC']) if not reg_b.empty else 0.0
            
            icone_perfil = definir_icone_status(alu['NECESSIDADES'])

            dados_editor.append({
                "ID": id_a,
                "ESTUDANTE": f"{icone_perfil} {alu['NOME_ALUNO']}",
                "VISTOS (AUTO)": vistos_auto_map.get(id_a, 0.0),
                "BÔNUS (TOTAL)": bonus_total_map.get(id_a, 0.0),
                "TESTE (LANÇAR)": n_teste,
                "PROVA (LANÇAR)": n_prova,
                "REC. PARALELA": n_rec
            })

        # --- 4. TABELA 1: CONSOLIDAÇÃO E ENTRADA ---
        st.subheader("📝 Passo 2: Lançamento e Consolidação")
        st.info("💡 **Dica:** Digite as notas do Teste, Prova e Recuperação. O sistema somará os Vistos e o Bônus automaticamente.")
        
        df_input = st.data_editor(
            pd.DataFrame(dados_editor),
            column_config={
                "ID": None,
                "ESTUDANTE": st.column_config.TextColumn("Estudante", width="medium", disabled=True),
                "VISTOS (AUTO)": st.column_config.NumberColumn("Vistos (Sistema)", format="%.1f", disabled=True),
                "BÔNUS (TOTAL)": st.column_config.NumberColumn("⭐ Bônus", format="%.1f", disabled=True),
                "TESTE (LANÇAR)": st.column_config.NumberColumn("Nota Teste", min_value=0.0, max_value=p_teste, format="%.1f"),
                "PROVA (LANÇAR)": st.column_config.NumberColumn("Nota Prova", min_value=0.0, max_value=p_prova, format="%.1f"),
                "REC. PARALELA": st.column_config.NumberColumn("🔄 Rec. Paralela", min_value=0.0, max_value=10.0, format="%.1f"),
            },
            hide_index=True, use_container_width=True, key=f"editor_notas_{v}"
        )

        # --- 5. ALGORITMO DE TRANSBORDAMENTO E SUBSTITUIÇÃO ---
        def aplicar_transbordamento(row):
            bonus_restante = row['BÔNUS (TOTAL)']
            v_base = row['VISTOS (AUTO)']
            t_base = row['TESTE (LANÇAR)']
            p_base = row['PROVA (LANÇAR)']
            rec_paralela = row['REC. PARALELA']
            
            # Passo 1: Completar Vistos
            v_final = min(p_visto, v_base + bonus_restante)
            bonus_restante -= (v_final - v_base)
            
            # Passo 2: Completar Teste
            t_final = min(p_teste, t_base + max(0, bonus_restante))
            bonus_restante -= (t_final - t_base)
            
            # Passo 3: Completar Prova
            p_final = min(p_prova, p_base + max(0, bonus_restante))
            
            # Média Final: Soma das notas ou a Recuperação (o que for maior)
            soma_notas = v_final + t_final + p_final
            media_final = min(10.0, max(soma_notas, rec_paralela))
            
            return pd.Series([v_final, t_final, p_final, rec_paralela, media_final])

        df_input[['V_PREF', 'T_PREF', 'P_PREF', 'REC_PREF', 'MEDIA_FINAL']] = df_input.apply(aplicar_transbordamento, axis=1)

        # --- 6. TABELA 2: GABARITO DE LANÇAMENTO ---
        st.markdown("---")
        st.subheader("🏛️ Passo 3: Gabarito Final (Sistema Prefeitura)")
        st.caption("Estas são as notas finais processadas. O Bônus já foi distribuído e a Recuperação Paralela já substituiu a média (se for maior). Copie estes valores para o sistema da escola.")
        
        def style_situacao(v):
            color = '#2ECC71' if v >= 6.0 else '#FF4B4B'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_input[['ESTUDANTE', 'V_PREF', 'T_PREF', 'P_PREF', 'REC_PREF', 'MEDIA_FINAL']].style.applymap(
                style_situacao, subset=['MEDIA_FINAL']
            ).format({
                "V_PREF": "{:.1f}", "T_PREF": "{:.1f}", "P_PREF": "{:.1f}", "REC_PREF": "{:.1f}", "MEDIA_FINAL": "{:.2f}"
            }),
            use_container_width=True, hide_index=True,
            column_config={
                "V_PREF": "Atividades",
                "T_PREF": "Teste",
                "P_PREF": "Prova",
                "REC_PREF": "🔄 Rec. Paralela",
                "MEDIA_FINAL": "Média Final"
            }
        )

        # --- 7. SALVAMENTO ---
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 SALVAR NOTAS E SINCRONIZAR BOLETIM", type="primary", use_container_width=True):
            with st.status("Sincronizando registros no Banco de Dados...") as status:
                db.limpar_notas_turma_trimestre(turma_sel, trimestre_sel)
                linhas_save =[]
                for _, r in df_input.iterrows():
                    # 🚨 LIMPEZA BLINDADA DO NOME ANTES DE SALVAR
                    nome_limpo = r['ESTUDANTE'].replace("♿ ", "").replace("👤 ", "").replace("🟠 ", "").replace("🧱 ", "").replace("🧮 ", "").replace("🚀 ", "")
                    
                    linhas_save.append([
                        r['ID'], nome_limpo, turma_sel, trimestre_sel,
                        util.sosa_to_str(r["V_PREF"]), util.sosa_to_str(r["T_PREF"]),
                        util.sosa_to_str(r["P_PREF"]), util.sosa_to_str(r["REC_PREF"]),
                        util.sosa_to_str(r['MEDIA_FINAL'])
                    ])
                if db.salvar_lote("DB_NOTAS", linhas_save):
                    status.update(label="✅ Boletim Sincronizado com Sucesso!", state="complete")
                    st.balloons(); time.sleep(1); st.rerun()


# ==============================================================================
# MÓDULO: BOLETIM ANUAL & CONSELHO - CLEAN & UX
# ==============================================================================
elif menu == "📈 Boletim Anual & Conselho":
    st.title("📈 Inteligência de Conselho e Resultados")
    st.caption("💡 **Guia de Comando:** Visão panorâmica do ano letivo. O sistema cruza notas, recuperações e faltas para calcular automaticamente a situação final de cada estudante.")
    st.markdown("---")

    if df_notas.empty:
        st.warning("⚠️ Sem notas lançadas no sistema. O Boletim Anual será gerado assim que houver dados.")
    else:
        # --- 1. FILTRO DE TURMA ---
        turmas_reais_bol = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
        lista_turmas_bol = sorted(turmas_reais_bol['ID_TURMA'].unique()) if not turmas_reais_bol.empty else sorted(df_alunos['TURMA'].unique())
        
        if not lista_turmas_bol:
            st.warning("Nenhuma turma cadastrada.")
            st.stop()
            
        with st.container(border=True):
            turma_sel = st.selectbox("🎯 Selecione a Turma para Análise:", lista_turmas_bol, key="bol_turma_clean")
        
        # --- 2. PROCESSAMENTO DE DADOS (DATA FUSION) ---
        df_t = df_notas[df_notas['TURMA'] == turma_sel].copy()
        
        if df_t.empty:
            st.info(f"📭 Nenhuma nota lançada para a turma {turma_sel} ainda.")
            st.stop()

        pivot = df_t.pivot_table(
            index=["ID_ALUNO", "NOME_ALUNO"], 
            columns="TRIMESTRE", 
            values=["MEDIA_FINAL", "NOTA_REC"], 
            aggfunc='first'
        ).reset_index()

        pivot.columns = [f"{col[0]}_{col[1]}".strip('_') for col in pivot.columns.values]

        trims = ["I Trimestre", "II Trimestre", "III Trimestre"]
        for t in trims:
            if f"MEDIA_FINAL_{t}" not in pivot.columns: pivot[f"MEDIA_FINAL_{t}"] = 0.0
            if f"NOTA_REC_{t}" not in pivot.columns: pivot[f"NOTA_REC_{t}"] = 0.0

        rec_f_data = df_t[df_t['TRIMESTRE'].str.contains("REC_FINAL|FINAL", na=False, case=False)]
        if not rec_f_data.empty:
            rec_f_min = rec_f_data[['ID_ALUNO', 'MEDIA_FINAL']].rename(columns={'MEDIA_FINAL': 'RF'})
            pivot = pd.merge(pivot, rec_f_min, on='ID_ALUNO', how='left')
        else:
            pivot['RF'] = 0.0
        
        # CÁLCULO DE FALTAS TOTAIS DO ANO
        faltas_df = df_diario[(df_diario['TURMA'] == turma_sel) & (df_diario['TAGS'] == "AUSÊNCIA")]
        
        if not faltas_df.empty:
            faltas_count = faltas_df.groupby('ID_ALUNO').size().reset_index(name='FALTAS')
            faltas_count['ID_ALUNO'] = faltas_count['ID_ALUNO'].apply(db.limpar_id)
            
            pivot['ID_ALUNO_CLEAN'] = pivot['ID_ALUNO'].apply(db.limpar_id)
            pivot = pd.merge(pivot, faltas_count, left_on='ID_ALUNO_CLEAN', right_on='ID_ALUNO', how='left')
            
            if 'ID_ALUNO_y' in pivot.columns: pivot = pivot.drop(columns=['ID_ALUNO_y'])
            if 'ID_ALUNO_CLEAN' in pivot.columns: pivot = pivot.drop(columns=['ID_ALUNO_CLEAN'])
            if 'ID_ALUNO_x' in pivot.columns: pivot = pivot.rename(columns={'ID_ALUNO_x': 'ID_ALUNO'})
                
            pivot['FALTAS'] = pivot['FALTAS'].fillna(0).astype(int)
        else:
            pivot['FALTAS'] = 0

        pivot = pivot.fillna(0.0)

        # Total de dias letivos registrados para a turma (para calcular o limite de 25%)
        total_dias_letivos = df_diario[df_diario['TURMA'] == turma_sel]['DATA'].nunique()
        limite_faltas = total_dias_letivos * 0.25 

        # --- 3. LÓGICA DE STATUS (COM PESO DE FALTAS) ---
        def calcular_situacao_anual(row):
            t1 = util.sosa_to_float(row.get("MEDIA_FINAL_I Trimestre", 0))
            t2 = util.sosa_to_float(row.get("MEDIA_FINAL_II Trimestre", 0))
            t3 = util.sosa_to_float(row.get("MEDIA_FINAL_III Trimestre", 0))
            rf = util.sosa_to_float(row.get("RF", 0))
            faltas_aluno = row.get("FALTAS", 0)
            
            soma = t1 + t2 + t3
            falta_pts = max(0.0, 18.0 - soma)
            
            aluno_match = df_alunos[df_alunos['ID'].apply(db.limpar_id) == db.limpar_id(row['ID_ALUNO'])]
            if not aluno_match.empty:
                aluno_info = aluno_match.iloc[0]
                pei = "♿" if str(aluno_info['NECESSIDADES']).upper().strip() not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"] else "👤"
            else:
                pei = "👤"
            
            # INTELIGÊNCIA DE STATUS: Faltas pesam mais que nota
            if faltas_aluno > limite_faltas and total_dias_letivos > 20: 
                status = "🚨 RISCO (FALTAS)"
            elif soma >= 18.0: status = "✅ APROV"
            elif rf >= 6.0: status = "🔄 APROV.REC"
            elif soma > 0 and falta_pts <= 10.0: status = "⚠️ REC.FINAL"
            elif soma > 0 and falta_pts > 10.0: status = "🚨 RISCO (NOTA)"
            else: status = "⏳ AGUARD"
            
            return pd.Series([pei, soma, falta_pts, status])

        pivot[['P', 'Σ', 'FALTA_PTS', 'SITUAÇÃO']] = pivot.apply(calcular_situacao_anual, axis=1)

        # --- 4. KPIs DE TOPO (TERMÔMETRO DA TURMA) ---
        st.markdown("### 📊 Termômetro da Turma")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Média Geral da Turma", f"{pivot['Σ'].mean()/3:.1f}")
        
        aprov = len(pivot[pivot['SITUAÇÃO'].str.contains("APROV")])
        c2.metric("Taxa de Aprovação", f"{(aprov/len(pivot)*100):.0f}%" if len(pivot) > 0 else "0%")
        
        c3.metric("Em Rec. Final", len(pivot[pivot['SITUAÇÃO'] == "⚠️ REC.FINAL"]))
        
        risco_total = len(pivot[pivot['SITUAÇÃO'].str.contains("🚨 RISCO")])
        c4.metric("Risco Crítico (Nota/Falta)", risco_total, delta_color="inverse", help="Alunos que já estouraram o limite de faltas ou que precisam de mais de 10 pontos para passar.")

        # --- 5. TABELA MOBILE-FIRST ---
        st.markdown("---")
        st.markdown("### 📋 Mapa de Desempenho Anual e Assiduidade")
        
        def style_status_anual(v):
            if "APROV" in str(v): return 'color: #2ECC71; font-weight: bold;'
            if "RISCO" in str(v): return 'color: #E74C3C; font-weight: bold;'
            if "REC.FINAL" in str(v): return 'color: #F1C40F; font-weight: bold;'
            return ''

        st.dataframe(
            pivot[['P', 'NOME_ALUNO', 
                   'MEDIA_FINAL_I Trimestre', 'NOTA_REC_I Trimestre',
                   'MEDIA_FINAL_II Trimestre', 'NOTA_REC_II Trimestre',
                   'MEDIA_FINAL_III Trimestre', 'NOTA_REC_III Trimestre',
                   'Σ', 'RF', 'FALTAS', 'SITUAÇÃO']]
            .style.applymap(style_status_anual, subset=['SITUAÇÃO'])
            .format("{:.1f}", subset=['MEDIA_FINAL_I Trimestre', 'NOTA_REC_I Trimestre', 
                                      'MEDIA_FINAL_II Trimestre', 'NOTA_REC_II Trimestre', 
                                      'MEDIA_FINAL_III Trimestre', 'NOTA_REC_III Trimestre', 
                                      'Σ', 'RF']),
            use_container_width=True, hide_index=True,
            column_config={
                "P": st.column_config.TextColumn("P", width="small", help="Perfil: ♿ PEI ou 👤 Regular"),
                "NOME_ALUNO": st.column_config.TextColumn("Estudante", width="medium"),
                "MEDIA_FINAL_I Trimestre": st.column_config.NumberColumn("I", width="small"),
                "NOTA_REC_I Trimestre": st.column_config.NumberColumn("R1", width="small"),
                "MEDIA_FINAL_II Trimestre": st.column_config.NumberColumn("II", width="small"),
                "NOTA_REC_II Trimestre": st.column_config.NumberColumn("R2", width="small"),
                "MEDIA_FINAL_III Trimestre": st.column_config.NumberColumn("III", width="small"),
                "NOTA_REC_III Trimestre": st.column_config.NumberColumn("R3", width="small"),
                "Σ": st.column_config.NumberColumn("Σ", width="small", help="Soma Anual (Meta: 18.0)"),
                "RF": st.column_config.NumberColumn("RF", width="small", help="Recuperação Final"),
                "FALTAS": st.column_config.NumberColumn("F", width="small", help=f"Total de Faltas no Ano. Limite atual: {int(limite_faltas)}"),
                "SITUAÇÃO": st.column_config.TextColumn("Status", width="small")
            }
        )
        
        st.caption(f"📌 **Legenda:** I, II, III (Médias Trimestrais) | R1, R2, R3 (Recuperações Paralelas) | Σ (Soma Anual) | RF (Recuperação Final) | F (Faltas). Limite de faltas atual: **{int(limite_faltas)}**.")


# ==============================================================================
# MÓDULO: BOLETIM ANUAL & CONSELHO - CLEAN & UX
# ==============================================================================
elif menu == "📈 Boletim Anual & Conselho":
    st.title("📈 Inteligência de Conselho e Resultados")
    st.caption("💡 **Guia de Comando:** Visão panorâmica do ano letivo. O sistema cruza notas, recuperações e faltas para calcular automaticamente a situação final de cada estudante.")
    st.markdown("---")

    if df_notas.empty:
        st.warning("⚠️ Sem notas lançadas no sistema. O Boletim Anual será gerado assim que houver dados.")
    else:
        # --- 1. FILTRO DE TURMA ---
        turmas_reais_bol = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
        lista_turmas_bol = sorted(turmas_reais_bol['ID_TURMA'].unique()) if not turmas_reais_bol.empty else sorted(df_alunos['TURMA'].unique())
        
        if not lista_turmas_bol:
            st.warning("Nenhuma turma cadastrada.")
            st.stop()
            
        with st.container(border=True):
            turma_sel = st.selectbox("🎯 Selecione a Turma para Análise:", lista_turmas_bol, key="bol_turma_clean")
        
        # --- 2. PROCESSAMENTO DE DADOS (DATA FUSION) ---
        df_t = df_notas[df_notas['TURMA'] == turma_sel].copy()
        
        if df_t.empty:
            st.info(f"📭 Nenhuma nota lançada para a turma {turma_sel} ainda.")
            st.stop()

        pivot = df_t.pivot_table(
            index=["ID_ALUNO", "NOME_ALUNO"], 
            columns="TRIMESTRE", 
            values=["MEDIA_FINAL", "NOTA_REC"], 
            aggfunc='first'
        ).reset_index()

        pivot.columns = [f"{col[0]}_{col[1]}".strip('_') for col in pivot.columns.values]

        trims = ["I Trimestre", "II Trimestre", "III Trimestre"]
        for t in trims:
            if f"MEDIA_FINAL_{t}" not in pivot.columns: pivot[f"MEDIA_FINAL_{t}"] = 0.0
            if f"NOTA_REC_{t}" not in pivot.columns: pivot[f"NOTA_REC_{t}"] = 0.0

        rec_f_data = df_t[df_t['TRIMESTRE'].str.contains("REC_FINAL|FINAL", na=False, case=False)]
        if not rec_f_data.empty:
            rec_f_min = rec_f_data[['ID_ALUNO', 'MEDIA_FINAL']].rename(columns={'MEDIA_FINAL': 'RF'})
            pivot = pd.merge(pivot, rec_f_min, on='ID_ALUNO', how='left')
        else:
            pivot['RF'] = 0.0
        
        # CÁLCULO DE FALTAS TOTAIS DO ANO
        faltas_df = df_diario[(df_diario['TURMA'] == turma_sel) & (df_diario['TAGS'] == "AUSÊNCIA")]
        
        if not faltas_df.empty:
            faltas_count = faltas_df.groupby('ID_ALUNO').size().reset_index(name='FALTAS')
            faltas_count['ID_ALUNO'] = faltas_count['ID_ALUNO'].apply(db.limpar_id)
            
            pivot['ID_ALUNO_CLEAN'] = pivot['ID_ALUNO'].apply(db.limpar_id)
            pivot = pd.merge(pivot, faltas_count, left_on='ID_ALUNO_CLEAN', right_on='ID_ALUNO', how='left')
            
            if 'ID_ALUNO_y' in pivot.columns: pivot = pivot.drop(columns=['ID_ALUNO_y'])
            if 'ID_ALUNO_CLEAN' in pivot.columns: pivot = pivot.drop(columns=['ID_ALUNO_CLEAN'])
            if 'ID_ALUNO_x' in pivot.columns: pivot = pivot.rename(columns={'ID_ALUNO_x': 'ID_ALUNO'})
                
            pivot['FALTAS'] = pivot['FALTAS'].fillna(0).astype(int)
        else:
            pivot['FALTAS'] = 0

        pivot = pivot.fillna(0.0)

        # Total de dias letivos registrados para a turma (para calcular o limite de 25%)
        total_dias_letivos = df_diario[df_diario['TURMA'] == turma_sel]['DATA'].nunique()
        limite_faltas = total_dias_letivos * 0.25 

        # --- 3. LÓGICA DE STATUS (COM PESO DE FALTAS) ---
        def calcular_situacao_anual(row):
            t1 = util.sosa_to_float(row.get("MEDIA_FINAL_I Trimestre", 0))
            t2 = util.sosa_to_float(row.get("MEDIA_FINAL_II Trimestre", 0))
            t3 = util.sosa_to_float(row.get("MEDIA_FINAL_III Trimestre", 0))
            rf = util.sosa_to_float(row.get("RF", 0))
            faltas_aluno = row.get("FALTAS", 0)
            
            soma = t1 + t2 + t3
            falta_pts = max(0.0, 18.0 - soma)
            
            aluno_match = df_alunos[df_alunos['ID'].apply(db.limpar_id) == db.limpar_id(row['ID_ALUNO'])]
            if not aluno_match.empty:
                aluno_info = aluno_match.iloc[0]
                pei = "♿" if str(aluno_info['NECESSIDADES']).upper().strip() not in["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"] else "👤"
            else:
                pei = "👤"
            
            # INTELIGÊNCIA DE STATUS: Faltas pesam mais que nota
            if faltas_aluno > limite_faltas and total_dias_letivos > 20: 
                status = "🚨 RISCO (FALTAS)"
            elif soma >= 18.0: status = "✅ APROV"
            elif rf >= 6.0: status = "🔄 APROV.REC"
            elif soma > 0 and falta_pts <= 10.0: status = "⚠️ REC.FINAL"
            elif soma > 0 and falta_pts > 10.0: status = "🚨 RISCO (NOTA)"
            else: status = "⏳ AGUARD"
            
            return pd.Series([pei, soma, falta_pts, status])

        pivot[['P', 'Σ', 'FALTA_PTS', 'SITUAÇÃO']] = pivot.apply(calcular_situacao_anual, axis=1)

        # --- 4. KPIs DE TOPO (TERMÔMETRO DA TURMA) ---
        st.markdown("### 📊 Termômetro da Turma")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Média Geral da Turma", f"{pivot['Σ'].mean()/3:.1f}")
        
        aprov = len(pivot[pivot['SITUAÇÃO'].str.contains("APROV")])
        c2.metric("Taxa de Aprovação", f"{(aprov/len(pivot)*100):.0f}%" if len(pivot) > 0 else "0%")
        
        c3.metric("Em Rec. Final", len(pivot[pivot['SITUAÇÃO'] == "⚠️ REC.FINAL"]))
        
        risco_total = len(pivot[pivot['SITUAÇÃO'].str.contains("🚨 RISCO")])
        c4.metric("Risco Crítico (Nota/Falta)", risco_total, delta_color="inverse", help="Alunos que já estouraram o limite de faltas ou que precisam de mais de 10 pontos para passar.")

        # --- 5. TABELA MOBILE-FIRST ---
        st.markdown("---")
        st.markdown("### 📋 Mapa de Desempenho Anual e Assiduidade")
        
        def style_status_anual(v):
            if "APROV" in str(v): return 'color: #2ECC71; font-weight: bold;'
            if "RISCO" in str(v): return 'color: #E74C3C; font-weight: bold;'
            if "REC.FINAL" in str(v): return 'color: #F1C40F; font-weight: bold;'
            return ''

        st.dataframe(
            pivot[['P', 'NOME_ALUNO', 
                   'MEDIA_FINAL_I Trimestre', 'NOTA_REC_I Trimestre',
                   'MEDIA_FINAL_II Trimestre', 'NOTA_REC_II Trimestre',
                   'MEDIA_FINAL_III Trimestre', 'NOTA_REC_III Trimestre',
                   'Σ', 'RF', 'FALTAS', 'SITUAÇÃO']]
            .style.applymap(style_status_anual, subset=['SITUAÇÃO'])
            .format("{:.1f}", subset=['MEDIA_FINAL_I Trimestre', 'NOTA_REC_I Trimestre', 
                                      'MEDIA_FINAL_II Trimestre', 'NOTA_REC_II Trimestre', 
                                      'MEDIA_FINAL_III Trimestre', 'NOTA_REC_III Trimestre', 
                                      'Σ', 'RF']),
            use_container_width=True, hide_index=True,
            column_config={
                "P": st.column_config.TextColumn("P", width="small", help="Perfil: ♿ PEI ou 👤 Regular"),
                "NOME_ALUNO": st.column_config.TextColumn("Estudante", width="medium"),
                "MEDIA_FINAL_I Trimestre": st.column_config.NumberColumn("I", width="small"),
                "NOTA_REC_I Trimestre": st.column_config.NumberColumn("R1", width="small"),
                "MEDIA_FINAL_II Trimestre": st.column_config.NumberColumn("II", width="small"),
                "NOTA_REC_II Trimestre": st.column_config.NumberColumn("R2", width="small"),
                "MEDIA_FINAL_III Trimestre": st.column_config.NumberColumn("III", width="small"),
                "NOTA_REC_III Trimestre": st.column_config.NumberColumn("R3", width="small"),
                "Σ": st.column_config.NumberColumn("Σ", width="small", help="Soma Anual (Meta: 18.0)"),
                "RF": st.column_config.NumberColumn("RF", width="small", help="Recuperação Final"),
                "FALTAS": st.column_config.NumberColumn("F", width="small", help=f"Total de Faltas no Ano. Limite atual: {int(limite_faltas)}"),
                "SITUAÇÃO": st.column_config.TextColumn("Status", width="small")
            }
        )
        
        st.caption(f"📌 **Legenda:** I, II, III (Médias Trimestrais) | R1, R2, R3 (Recuperações Paralelas) | Σ (Soma Anual) | RF (Recuperação Final) | F (Faltas). Limite de faltas atual: **{int(limite_faltas)}**.")


# ==============================================================================
# MÓDULO: GESTÃO DA TURMA (COCKPIT DE REGÊNCIA) - CLEAN & UX
# ==============================================================================
elif menu == "👥 Gestão da Turma":
    st.title("👥 Cockpit de Regência: Gestão 360°")
    st.caption("💡 **Guia de Comando:** Central de controle da sua rotina. Aqui você abre a aula do dia, monitora o clima da turma, detecta risco de evasão e mapeia o perfil cognitivo dos alunos.")
    st.markdown("---")

    if "v_gestao" not in st.session_state: 
        st.session_state.v_gestao = int(time.time())
    v = st.session_state.v_gestao

    # 🚨 VACINA ANTI-KEYERROR (BLINDAGEM GLOBAL DE TURMAS)
    lista_turmas_segura =[]
    if not df_turmas.empty and 'ID_TURMA' in df_turmas.columns:
        turmas_reais = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
        lista_turmas_segura = sorted(turmas_reais['ID_TURMA'].unique())
    elif not df_alunos.empty and 'TURMA' in df_alunos.columns:
        lista_turmas_segura = sorted(df_alunos['TURMA'].unique())

    tab_cockpit, tab_criar, tab_povoar, tab_editar, tab_radiografia = st.tabs([
        "📊 1. Cockpit de Prontidão", "🏗️ 2. Arquitetura de Turmas", "➕ 3. Povoar Alunos", "✏️ 4. Edição & Transferência", "🧠 5. Radiografia Cognitiva"
    ])

    # --- ABA 1: COCKPIT DA TURMA ---
    with tab_cockpit:
        if df_turmas.empty or 'ID_TURMA' not in df_turmas.columns:
            st.info("📭 Nenhuma turma cadastrada. Vá na aba '2. Arquitetura de Turmas' para iniciar.")
        else:
            st.markdown("### 📅 Grade Oficial de Regência")
            
            dias_semana =["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
            tempos = ["1º Tempo", "2º Tempo"]
            grade_map = {t: {d: "---" for d in dias_semana} for t in tempos}

            for _, row in df_turmas.iterrows():
                # Uso do .get() para evitar KeyError se a coluna sumir
                sigla = str(row.get('ID_TURMA', ''))
                nome_turma = str(row.iloc[1]) if len(row) > 1 else ""
                horarios_str = str(row.iloc[3]) if len(row) > 3 else ""
                
                display_name = sigla
                if "ª" in sigla: display_name = nome_turma.replace("Ano ", "ANO ").upper()
                
                if horarios_str and horarios_str != "N/A":
                    for h in[x.strip() for x in horarios_str.split("/")]:
                        for dia in dias_semana:
                            for tempo in tempos:
                                if dia in h and tempo in h:
                                    grade_map[tempo][dia] = display_name

            df_grade = pd.DataFrame(grade_map).T
            
            def colorir_grade(val):
                if val in ["PI", "PC", "AC", "HTPC"]: return 'background-color: #2962FF; color: white; font-weight: bold; text-align: center;'
                if val != "---": return 'background-color: #001E3C; color: #2ECC71; font-weight: bold; text-align: center;'
                return 'color: gray; text-align: center;'

            st.dataframe(df_grade.style.applymap(colorir_grade), use_container_width=True)
            st.markdown("---")

            if not lista_turmas_segura:
                st.warning("⚠️ Apenas horários de planejamento cadastrados. Cadastre turmas regulares para liberar o comando acadêmico.")
            else:
                c_f1, c_f2 = st.columns([1, 1])
                turma_foco = c_f1.selectbox("🎯 Selecione a Turma para Comando:", lista_turmas_segura, key=f"foco_t_{v}")
                trim_foco = c_f2.selectbox("📅 Trimestre de Safra:", ["I Trimestre", "II Trimestre", "III Trimestre", "Todos"], key=f"foco_trim_{v}")
                
                alunos_t = df_alunos[df_alunos['TURMA'] == turma_foco].sort_values(by="NOME_ALUNO")
                id_alunos_turma = set(alunos_t['ID'].apply(db.limpar_id).tolist())
                ano_num = "".join(filter(str.isdigit, turma_foco))
                ano_str_ref = f"{ano_num}º"

                # 🚨 MÉTRICAS DE TOPO
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("👥 Total Alunos", len(alunos_t))
                
                mask_pei = ~alunos_t['NECESSIDADES'].astype(str).str.upper().str.strip().isin(["NENHUMA", "PENDENTE", "", "NAN", "TÍPICO", "TIPICO"])
                df_pei_turma = alunos_t[mask_pei]
                m2.metric("♿ Estudantes PEI", len(df_pei_turma))
                
                planos_totais = len(df_planos[df_planos['ANO'] == ano_str_ref])
                aulas_feitas = len(df_registro_aulas[df_registro_aulas['TURMA'] == turma_foco])
                saude_val = (aulas_feitas / (planos_totais * 2) * 100) if planos_totais > 0 else 0
                m3.metric("🎯 Saúde de Execução", f"{min(100, int(saude_val))}%", help="Percentual de aulas ministradas em relação ao total planejado.")

                clima_predominante = "Sem Dados"
                if not df_registro_aulas.empty and len(df_registro_aulas.columns) >= 9:
                    try:
                        climas_turma = df_registro_aulas[df_registro_aulas['TURMA'] == turma_foco].iloc[:, 8].dropna().astype(str).tolist()
                        climas_validos =[c for c in climas_turma if c.strip() and c.lower() not in["nan", "none", "n/a"]]
                        if climas_validos:
                            recentes = climas_validos[-5:]
                            clima_predominante = max(set(recentes), key=recentes.count)
                    except: pass
                
                clima_curto = clima_predominante.split(" ")[0] + " " + clima_predominante.split(" ")[1] if " " in clima_predominante else clima_predominante
                m4.metric("🌡️ Clima Recente", clima_curto, help=f"Clima predominante nas últimas aulas: {clima_predominante}")

                # ==============================================================================
                # 🚨 FUNIL DE PERFORMANCE E ENGAJAMENTO 360°
                # ==============================================================================
                with st.expander("🎯 Funil de Performance e Engajamento 360°", expanded=True):
                    if trim_foco == "Todos":
                        st.warning("⚠️ Selecione um trimestre específico (I, II ou III) no topo da tela para habilitar o Funil de Performance.")
                    else:
                        calendario = {
                            "I Trimestre": (date(2026, 2, 9), date(2026, 5, 22)),
                            "II Trimestre": (date(2026, 5, 25), date(2026, 9, 4)),
                            "III Trimestre": (date(2026, 9, 8), date(2026, 12, 17))
                        }
                        dt_ini, dt_fim = calendario.get(trim_foco, (date(2026, 1, 1), date(2026, 12, 31)))

                        # --- BLOCO 1: ENGAJAMENTO (VISTOS) ---
                        st.markdown("#### 📝 1. Engajamento Contínuo (Vistos e Caderno)")
                        df_d_t = df_diario[df_diario['TURMA'] == turma_foco].copy()
                        
                        if not df_d_t.empty:
                            df_d_t['DATA_DT'] = pd.to_datetime(df_d_t['DATA'], format="%d/%m/%Y", errors='coerce').dt.date
                            df_d_trim = df_d_t[(df_d_t['DATA_DT'] >= dt_ini) & (df_d_t['DATA_DT'] <= dt_fim)]
                            
                            df_validas = df_d_trim[df_d_trim['VISTO_ATIVIDADE'].astype(str).str.upper() != "ISENTO"]
                            total_vistos_possiveis = len(df_validas)
                            vistos_dados = len(df_validas[df_validas['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"])
                            taxa_geral = (vistos_dados / total_vistos_possiveis * 100) if total_vistos_possiveis > 0 else 0
                            
                            st.progress(taxa_geral / 100)
                            st.caption(f"**Taxa de Entrega da Turma:** {taxa_geral:.1f}% das atividades foram vistadas.")
                            
                            alunos_stats =[]
                            for id_aluno in id_alunos_turma:
                                d_alu = df_validas[df_validas['ID_ALUNO'].apply(db.limpar_id) == id_aluno]
                                if not d_alu.empty:
                                    v_alu = len(d_alu[d_alu['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"])
                                    b_alu = d_alu['BONUS'].apply(util.sosa_to_float).sum()
                                    nome_alu = d_alu.iloc[0]['NOME_ALUNO']
                                    alunos_stats.append({"nome": nome_alu, "vistos": v_alu, "total": len(d_alu), "bonus": b_alu})
                            
                            fantasmas = [a['nome'] for a in alunos_stats if a['total'] > 0 and (a['vistos']/a['total']) <= 0.2]
                            top_alunos = sorted([a for a in alunos_stats if a['total'] > 0 and (a['vistos']/a['total']) >= 0.8], key=lambda x: x['bonus'], reverse=True)[:3]
                            
                            c_e1, c_e2 = st.columns(2)
                            with c_e1:
                                if fantasmas:
                                    st.error(f"👻 **Alerta Fantasma (Baixa Entrega):** {', '.join(fantasmas)}")
                                else:
                                    st.success("✅ Nenhum aluno com entrega crítica.")
                            with c_e2:
                                if top_alunos:
                                    st.success(f"🌟 **Top Engajamento:** {', '.join([a['nome'] for a in top_alunos])}")
                        else:
                            st.info("Sem registros de diário neste trimestre.")

                        st.divider()

                        # --- BLOCO 2: TERMÔMETRO DE AVALIAÇÕES ---
                        st.markdown("#### 📊 2. Termômetro de Avaliações (Notas)")
                        df_n_trim = df_notas[(df_notas['TURMA'] == turma_foco) & (df_notas['TRIMESTRE'] == trim_foco)]
                        if not df_n_trim.empty:
                            media_teste = df_n_trim['NOTA_TESTE'].apply(util.sosa_to_float).mean()
                            media_prova = df_n_trim['NOTA_PROVA'].apply(util.sosa_to_float).mean()
                            
                            c_n1, c_n2, c_n3 = st.columns(3)
                            c_n1.metric("Média nos Testes", f"{media_teste:.1f}")
                            c_n2.metric("Média nas Provas", f"{media_prova:.1f}")
                            
                            medias_finais = df_n_trim['MEDIA_FINAL'].apply(util.sosa_to_float)
                            azul = len(medias_finais[medias_finais >= 7.0])
                            amarelo = len(medias_finais[(medias_finais >= 5.0) & (medias_finais < 7.0)])
                            vermelho = len(medias_finais[medias_finais < 5.0])
                            
                            c_n3.markdown(f"🟢 **Azul:** {azul} | 🟡 **Média:** {amarelo} | 🔴 **Risco:** {vermelho}")
                            
                            alunos_vermelho = df_n_trim[df_n_trim['MEDIA_FINAL'].apply(util.sosa_to_float) < 5.0]['NOME_ALUNO'].tolist()
                            if alunos_vermelho:
                                with st.expander("🚨 Ver alunos na Zona de Risco (Abaixo de 5.0)"):
                                    st.error(", ".join(alunos_vermelho))
                        else:
                            st.info("Notas ainda não consolidadas no Boletim para este trimestre.")

                        st.divider()

                        # --- BLOCO 3: ALERTA DE FALTOSOS NAS AVALIAÇÕES ---
                        st.markdown("#### ❌ 3. Radar de Faltosos em Avaliações")
                        st.caption("Alunos que não realizaram as provas ou que ainda estão pendentes de escaneamento.")
                        diag_t = df_diagnosticos[df_diagnosticos['TURMA'] == turma_foco].copy()
                        
                        if not diag_t.empty:
                            diag_trim = diag_t[diag_t['ID_AVALIACAO'].str.contains(trim_foco.replace(" ", ""), case=False, na=False)]
                            if not diag_trim.empty:
                                avaliacoes_aplicadas = diag_trim['ID_AVALIACAO'].unique()
                                houve_falta = False
                                
                                cols_faltas = st.columns(len(avaliacoes_aplicadas) if len(avaliacoes_aplicadas) > 0 else 1)
                                
                                for idx, av in enumerate(avaliacoes_aplicadas):
                                    faltosos_av = diag_trim[(diag_trim['ID_AVALIACAO'] == av) & (diag_trim['RESPOSTAS_ALUNO'] == "FALTOU")]['NOME_ALUNO'].tolist()
                                    alunos_com_registro = diag_trim[diag_trim['ID_AVALIACAO'] == av]['ID_ALUNO'].apply(db.limpar_id).tolist()
                                    pendentes_av = [alu['NOME_ALUNO'] for _, alu in alunos_t.iterrows() if db.limpar_id(alu['ID']) not in alunos_com_registro]
                                    
                                    todos_ausentes = list(set(faltosos_av + pendentes_av))
                                    
                                    with cols_faltas[idx % len(cols_faltas)]:
                                        nome_curto = av.split("-")[0].strip()
                                        if todos_ausentes:
                                            houve_falta = True
                                            st.warning(f"**{nome_curto}**\n" + "\n".join([f"• {a}" for a in todos_ausentes]))
                                        else:
                                            st.success(f"**{nome_curto}**\n100% de participação!")
                                            
                                if not houve_falta:
                                    st.success("✅ Nenhum aluno faltou às avaliações deste trimestre!")
                            else:
                                st.info("Nenhuma avaliação escaneada neste trimestre ainda.")
                        else:
                            st.info("Nenhuma avaliação escaneada para esta turma.")

                        st.divider()

                        # --- BLOCO 4: RAIO-X CIRÚRGICO (TOP 3 LACUNAS) ---
                        st.markdown("#### 🧠 4. Raio-X Cirúrgico (Última Avaliação)")
                        if not diag_t.empty and 'diag_trim' in locals() and not diag_trim.empty:
                            ultima_av = diag_trim['ID_AVALIACAO'].unique()[-1]
                            st.caption(f"Analisando a prova mais recente: **{ultima_av}**")
                            
                            nome_curto = ultima_av.split("-")[0].strip().replace(" (2ª CHAMADA)", "")
                            df_ref = df_aulas[df_aulas['TIPO_MATERIAL'].str.contains(nome_curto, regex=False, na=False)]
                            
                            if not df_ref.empty:
                                txt_prova = str(df_ref.iloc[0]['CONTEUDO'])
                                gab_raw = ai.extrair_tag(txt_prova, "GABARITO_TEXTO") or ai.extrair_tag(txt_prova, "GABARITO")
                                grade_raw = ai.extrair_tag(txt_prova, "GRADE_DE_CORRECAO")
                                
                                if gab_raw and grade_raw:
                                    matches = re.findall(r"(\d+)[\s\.\)\-:]+([A-E])", gab_raw.upper())
                                    gab_oficial = {int(num): letra for num, letra in matches}
                                    if not gab_oficial:
                                        letras = re.findall(r"\b[A-E]\b", gab_raw.upper())
                                        gab_oficial = {i+1: letra for i, letra in enumerate(letras)}
                                        
                                    respostas_alunos = diag_trim[diag_trim['ID_AVALIACAO'] == ultima_av]['RESPOSTAS_ALUNO'].astype(str).tolist()
                                    
                                    lacunas_stats =[]
                                    for q_num, letra_certa in gab_oficial.items():
                                        acertos = 0
                                        validos = 0
                                        for resp in respostas_alunos:
                                            if resp == "FALTOU": continue
                                            resp_lista = resp.split(";")
                                            if len(resp_lista) >= q_num:
                                                validos += 1
                                                if resp_lista[q_num-1] == letra_certa:
                                                    acertos += 1
                                        
                                        if validos > 0:
                                            taxa_acerto = acertos / validos
                                            if taxa_acerto < 0.6: 
                                                padrao_h = rf"(?si)QUEST[AÃ]O\s*0?{q_num}\b.*?(?:\[)(.*?)(?:\])"
                                                m_h = re.search(padrao_h, grade_raw)
                                                habilidade = m_h.group(1).strip() if m_h else f"Revisar conceito da Questão {q_num}"
                                                lacunas_stats.append({"q": q_num, "taxa": taxa_acerto, "hab": habilidade})
                                    
                                    if lacunas_stats:
                                        top_lacunas = sorted(lacunas_stats, key=lambda x: x['taxa'])[:3]
                                        st.error("🚨 **Professor, revise estes conceitos na próxima aula:**")
                                        for lac in top_lacunas:
                                            st.markdown(f"**Q{lac['q']} ({lac['taxa']*100:.0f}% de acerto):** {lac['hab']}")
                                    else:
                                        st.success("✅ Turma com excelente desempenho! Nenhuma questão com menos de 60% de acerto.")
                            else:
                                st.caption("Gabarito oficial não encontrado no acervo.")
                        else:
                            st.info("Aguardando dados da primeira avaliação para gerar o Raio-X.")

                st.markdown("---")
                
                # 🚨 FILTRAGEM EM CASCATA (TRIMESTRE -> PLANOS -> MATERIAIS)
                df_p_atual = df_planos[df_planos['ANO'] == ano_str_ref].sort_values(by='DATA', ascending=False)
                df_mats_ano = df_aulas[df_aulas['ANO'].str.contains(ano_num)].iloc[::-1]

                if trim_foco != "Todos":
                    df_p_atual = df_p_atual[df_p_atual['TURMA'] == trim_foco]
                    semanas_validas = df_p_atual['SEMANA'].tolist()
                    df_mats_ano = df_mats_ano[df_mats_ano['SEMANA_REF'].isin(semanas_validas)]

                col_esq, col_dir = st.columns([1.6, 1.4])

                with col_esq:
                    st.subheader("🕒 Abertura de Aula")
                    mostrar_historico = st.toggle("🔄 Mostrar histórico completo (Modo Revisão / Continuidade)", help="Ative para ver aulas que já foram dadas ou planos já concluídos.", key=f"tog_hist_{v}")
                    
                    historico_turma = df_registro_aulas[df_registro_aulas['TURMA'] == turma_foco]
                    planos_usados = historico_turma['SEMANA'].unique().tolist()
                    
                    materiais_usados_raw = historico_turma['CONTEUDO_MINISTRADO'].dropna().tolist()
                    materiais_usados =[]
                    for raw in materiais_usados_raw:
                        materiais_usados.extend([m.strip() for m in str(raw).split('+')])
                    
                    plano_sugerido = "Nenhum"
                    base_didatica_sugerida = "Matriz Curricular"
                    ponte_sugerida = "Início de novo ciclo pedagógico."
                    
                    df_p_sugestao = df_p_atual.copy()
                    if not mostrar_historico: 
                        df_p_sugestao = df_p_sugestao[~df_p_sugestao['SEMANA'].isin(planos_usados)]
                        df_p_sugestao = df_p_sugestao[df_p_sugestao['EIXO'] == 'HUB_ATIVO']
                        
                    if not df_p_sugestao.empty:
                        row_p = df_p_sugestao.iloc[0]
                        plano_sugerido = row_p['SEMANA']
                        txt_p = row_p['PLANO_TEXTO']
                        base_didatica_sugerida = ai.extrair_tag(txt_p, "BASE_DIDATICA") or "Matriz de Itabuna"
                        ponte_match = re.search(r"Ponte Pedagógica:(.*?)(?=Início|Meio|Fim|$)", ai.extrair_tag(txt_p, "AULA_1"), re.DOTALL)
                        if ponte_match: ponte_sugerida = ponte_match.group(1).strip()

                    with st.container(border=True):
                        st.markdown("#### 🚀 MISSÃO PLANEJADA PARA HOJE")
                        if plano_sugerido != "Nenhum":
                            st.success(f"**Próxima Semana Inédita:** {plano_sugerido}")
                            st.info(f"**📖 Base Didática (DNA):**\n{base_didatica_sugerida}")
                        else:
                            st.success("✅ Todos os planos ativos já foram aplicados nesta turma!")
                        
                        with st.expander("🔗 Ver Ponte de Continuidade (Onde paramos?)"):
                            st.caption(ponte_sugerida)
                        
                        st.divider()
                        
                        data_aula = st.date_input("Data da Aula:", date.today(), format="DD/MM/YYYY", key=f"dt_reg_{v}")
                        
                        mats_disp_bruto = df_mats_ano['TIPO_MATERIAL'].tolist()
                        if not mostrar_historico: 
                            semanas_concluidas = df_planos[df_planos['EIXO'] == 'PRODUZIDO']['SEMANA'].tolist()
                            mats_disp =[]
                            for m in mats_disp_bruto:
                                if m not in materiais_usados:
                                    sem_ref_mat = df_mats_ano[df_mats_ano['TIPO_MATERIAL'] == m].iloc[0]['SEMANA_REF']
                                    if sem_ref_mat not in semanas_concluidas:
                                        mats_disp.append(m)
                        else: 
                            mats_disp = mats_disp_bruto
                            
                        label_mats = "📦 Selecione o Material (Máx 2):" if not mostrar_historico else "📦 Selecione o Material (Todos):"
                        
                        mats_sel = st.multiselect(label_mats, options=mats_disp, max_selections=2, key=f"mats_reg_{v}")

                        if st.button("💾 CONFIRMAR ABERTURA DE AULA", use_container_width=True, type="primary"):
                            if not mats_sel:
                                st.error("⚠️ Selecione ao menos um material para abrir a aula.")
                            else:
                                mat_ref = df_aulas[df_aulas['TIPO_MATERIAL'] == mats_sel[0]].iloc[0]
                                plano_inferido = mat_ref['SEMANA_REF']
                                
                                db.salvar_no_banco("DB_REGISTRO_AULAS",[
                                    data_aula.strftime("%d/%m/%Y"), plano_inferido, turma_foco, 
                                    " + ".join(mats_sel), "PENDENTE", "ABERTA"
                                ])
                                st.success("✅ Aula aberta com sucesso! Vá para o Diário de Bordo.")
                                time.sleep(1); st.rerun()

                    st.markdown("---")
                    with st.expander("🗑️ Gerenciar Aulas Abertas (Borracha Temporal)"):
                        st.caption("⚠️ **Atenção:** Apagar uma aula aqui também removerá todos os vistos e faltas lançados no Diário de Bordo para aquele dia específico.")
                        aulas_abertas = df_registro_aulas[df_registro_aulas['TURMA'] == turma_foco].sort_values(by='DATA', ascending=False).head(5)
                        if aulas_abertas.empty: st.info("Nenhuma aula registrada para esta turma.")
                        else:
                            for _, row_aula in aulas_abertas.iterrows():
                                c_del1, c_del2 = st.columns([3, 1])
                                c_del1.markdown(f"📅 **{row_aula['DATA']}** - {row_aula['CONTEUDO_MINISTRADO']}")
                                if c_del2.button("❌ APAGAR", key=f"del_aula_{row_aula['DATA']}_{turma_foco}"):
                                    with st.spinner("Apagando registros e limpando o diário..."):
                                        if db.excluir_aula_aberta(row_aula['DATA'], turma_foco):
                                            st.success("Aula e diário apagados com sucesso!")
                                            time.sleep(1); st.rerun()

                with col_dir:
                    st.subheader("📂 Inventário de Ativos")
                    with st.container(border=True):
                        titulo_inv = f"**Próximos Ativos Inéditos ({ano_str_ref} Ano)**" if not mostrar_historico else f"**Todos os Ativos ({ano_str_ref} Ano)**"
                        st.markdown(titulo_inv)
                        
                        df_mats_exibir = df_mats_ano.copy()
                        if not mostrar_historico and not df_mats_exibir.empty: 
                            df_mats_exibir = df_mats_exibir[~df_mats_exibir['TIPO_MATERIAL'].isin(materiais_usados)]
                            semanas_concluidas = df_planos[df_planos['EIXO'] == 'PRODUZIDO']['SEMANA'].tolist()
                            df_mats_exibir = df_mats_exibir[~df_mats_exibir['SEMANA_REF'].isin(semanas_concluidas)]
                        
                        if df_mats_exibir.empty: st.caption("Nenhum material pendente para esta turma neste trimestre. Tudo em dia!")
                        else:
                            for _, m_row in df_mats_exibir.head(5).iterrows():
                                with st.container():
                                    c_m_txt, c_m_links = st.columns([1.8, 1.2])
                                    c_m_txt.markdown(f"📘 {m_row['TIPO_MATERIAL']}")
                                    txt_m = str(m_row['CONTEUDO'])
                                    def extrair_url(t, k):
                                        match = re.search(rf"{k}.*?\(?(https?://[^\s\)]+)\)?", t, re.IGNORECASE)
                                        return match.group(1).strip() if match else None
                                    l_alu = m_row.get('LINK_DRIVE')
                                    l_pei = extrair_url(txt_m, "PEI")
                                    l_prof = extrair_url(txt_m, "Prof")
                                    btn_html = ""
                                    if l_alu: btn_html += f"[📄]({l_alu}) "
                                    if l_pei: btn_html += f"[♿]({l_pei}) "
                                    if l_prof: btn_html += f"[👨‍🏫]({l_prof})"
                                    c_m_links.markdown(btn_html)
                                    st.divider()

                    with st.container(border=True):
                        st.markdown("**👥 Foco em Inclusão (Alunos PEI)**")
                        if not df_pei_turma.empty:
                            for _, alu in df_pei_turma.iterrows(): st.warning(f"♿ **{alu['NOME_ALUNO']}**\n↳ {alu['NECESSIDADES']}")
                        else: st.success("✅ Nenhum aluno PEI nesta turma.")

    # --- ABA 2: ARQUITETURA DE TURMAS E HORÁRIOS ---
    with tab_criar:
        st.subheader("🏗️ Configurar Grade: Turmas e Planejamento")
        
        tipo_cadastro = st.radio(
            "O que o senhor deseja alocar na grade?",["📚 Turma Regular (Alunos)", "⚙️ Planejamento (PI / PC)"], 
            horizontal=True, 
            key=f"tipo_cad_{v}"
        )
        
        with st.container(border=True):
            if tipo_cadastro == "📚 Turma Regular (Alunos)":
                c1, c2, c3 = st.columns(3)
                ano_t = c1.selectbox("Série/Ano:",[1, 2, 3, 4, 5, 6, 7, 8, 9], index=5, key=f"ano_cad_{v}")
                letra_t = c2.selectbox("Letra:",["A", "B", "C", "D", "E", "F", "G"], key=f"letra_cad_{v}")
                turno_t = c3.selectbox("Turno:",["Matutino", "Vespertino", "Noturno"], key=f"turno_cad_{v}")
                
                sigla_final = f"{ano_t}ª {turno_t[0].upper()}{letra_t}"
                nome_final = f"{ano_t}º Ano {letra_t}"
            else:
                c1, c2, c3 = st.columns([1, 2, 1])
                sigla_plan = c1.selectbox("Sigla:",["PI", "PC", "AC", "HTPC", "OUTRO"], key=f"sigla_plan_{v}")
                desc_plan = c2.text_input("Descrição:", placeholder="Ex: Planejamento Individual", key=f"desc_plan_{v}")
                turno_t = c3.selectbox("Turno:",["Matutino", "Vespertino", "Noturno"], key=f"turno_plan_{v}")
                
                sigla_final = sigla_plan
                nome_final = desc_plan if desc_plan else "Planejamento"

        st.markdown("#### 📅 Alocação de Horário (Dias e Tempos)")
        st.info("💡 Selecione os dias e os tempos exatos para esta alocação.")
        
        opcoes_horarios =[
            "Segunda (1º Tempo)", "Segunda (2º Tempo)", 
            "Terça (1º Tempo)", "Terça (2º Tempo)", 
            "Quarta (1º Tempo)", "Quarta (2º Tempo)", 
            "Quinta (1º Tempo)", "Quinta (2º Tempo)", 
            "Sexta (1º Tempo)", "Sexta (2º Tempo)"
        ]
        
        dias_aula = st.multiselect("Selecione a grade:", opcoes_horarios, key=f"dias_cad_{v}")
        
        if st.button("💾 ALOCAR NA GRADE OFICIAL", use_container_width=True, type="primary"):
            if not dias_aula:
                st.error("⚠️ Ordem negada: Selecione pelo menos um horário.")
            else:
                if db.salvar_no_banco("DB_TURMAS",[sigla_final, nome_final, turno_t, " / ".join(dias_aula), "N/A", "ATIVO"]):
                    st.success(f"✅ {sigla_final} alocado com sucesso na grade oficial!"); time.sleep(1.5); st.rerun()

    # --- ABA 3: POVOAR ALUNOS ---
    with tab_povoar:
        st.subheader("➕ Inclusão de Estudantes (Manual e Lote)")
        
        if not lista_turmas_segura:
            st.warning("Cadastre uma turma primeiro.")
        else:
            t_dest = st.selectbox("Turma de Destino:", lista_turmas_segura, key=f"dest_pov_{v}")
            
            if t_dest:
                t1_man, t2_lote = st.tabs(["✍️ Cadastro Manual", "📄 Importação em Lote (CSV)"])
                
                with t1_man:
                    with st.form("f_manual_povoar"):
                        nome_a = st.text_input("Nome Completo:").upper()
                        
                        opcoes_nec =["TÍPICO", "TEA", "TDAH", "DISLEXIA", "DEF. INTELECTUAL", "TOD", "BAIXA VISÃO", "SURDEZ", "PEI - PENDENTE", "OUTRO"]
                        perfil_base = st.multiselect("Perfil / Necessidades (Pode selecionar vários):", opcoes_nec, default=["TÍPICO"])
                        
                        if st.form_submit_button("💾 SALVAR ALUNO"):
                            if not nome_a:
                                st.error("⚠️ Digite o nome do aluno.")
                            else:
                                if "TÍPICO" in perfil_base and len(perfil_base) > 1:
                                    perfil_base.remove("TÍPICO")
                                
                                perfil_str = " + ".join(perfil_base) if perfil_base else "TÍPICO"
                                
                                id_n = db.gerar_proximo_id(df_alunos)
                                if db.salvar_no_banco("DB_ALUNOS",[id_n, nome_a, t_dest, "ATIVO", perfil_str, "MANUAL"]):
                                    st.success(f"✅ {nome_a} cadastrado com perfil: {perfil_str}!"); st.rerun()
                
                with t2_lote:
                    st.info("💡 **Dica de Soberania:** Cole a lista de alunos abaixo. Se o aluno tiver um asterisco (*) no final do nome, o sistema detectará automaticamente como PEI.")
                    texto_lote = st.text_area("Cole os dados CSV aqui (NOME, PERFIL):", height=300, placeholder="ADRIEL VINICIUS ALVES MARTINS,TÍPICO\nJOSE LEVI BRONZE SANTOS*,PEI - PENDENTE")
                    
                    if st.button("🚀 PROCESSAR IMPORTAÇÃO EM LOTE", type="primary", use_container_width=True):
                        if texto_lote.strip():
                            linhas = texto_lote.strip().split('\n')
                            novos_alunos =[]
                            id_atual = db.gerar_proximo_id(df_alunos)
                            
                            with st.status("Importando alunos para o Banco de Dados...") as status:
                                for linha in linhas:
                                    if not linha.strip(): continue
                                    
                                    partes = linha.split(',')
                                    nome_bruto = partes[0].strip().upper()
                                    
                                    if "*" in nome_bruto:
                                        nome_limpo = nome_bruto.replace("*", "").strip()
                                        perfil = "PEI - PENDENTE"
                                    else:
                                        nome_limpo = nome_bruto
                                        perfil = partes[1].strip().upper() if len(partes) > 1 else "TÍPICO"
                                    
                                    novos_alunos.append([id_atual, nome_limpo, t_dest, "ATIVO", perfil, "LOTE"])
                                    id_atual += 1 
                                
                                if db.salvar_lote("DB_ALUNOS", novos_alunos):
                                    status.update(label=f"✅ {len(novos_alunos)} alunos importados com sucesso para a turma {t_dest}!", state="complete")
                                    st.balloons()
                                    time.sleep(1.5)
                                    st.rerun()
                        else:
                            st.error("⚠️ Cole os dados na caixa de texto antes de processar.")

    # --- ABA 4: EDIÇÃO & TRANSFERÊNCIA (COM DIAGNÓSTICO RÁPIDO) ---
    with tab_editar:
        st.subheader("✏️ Gestão de Cadastro e Transferência")
        st.caption("Altere o nome, a turma ou o laudo de um aluno. O sistema atualizará todo o histórico dele (notas, faltas, provas) automaticamente.")
        
        t_origem = st.selectbox("Selecione a Turma Atual:", [""] + sorted(df_alunos['TURMA'].unique().tolist()), key=f"orig_ed_{v}")
        
        if t_origem:
            alunos_opcoes = df_alunos[df_alunos['TURMA'] == t_origem].sort_values(by="NOME_ALUNO")
            aluno_sel_nome = st.selectbox("Selecione o Aluno:", alunos_opcoes['NOME_ALUNO'].tolist(), key=f"alu_ed_{v}")
            dados_atuais = alunos_opcoes[alunos_opcoes['NOME_ALUNO'] == aluno_sel_nome].iloc[0]
            
            # ==============================================================================
            # 🚨 BOTÕES DE DIAGNÓSTICO RÁPIDO (1-CLICK)
            # ==============================================================================
            st.markdown("#### ⚡ Diagnóstico Rápido (1-Click)")
            st.caption("Clique para classificar o aluno instantaneamente na Radiografia Cognitiva.")
            c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
            
            if c_btn1.button("📚 Defasagem Leitura", use_container_width=True):
                with st.spinner("Atualizando perfil..."):
                    db.atualizar_aluno_cascata(dados_atuais['ID'], dados_atuais['NOME_ALUNO'], t_origem, "DEFASAGEM LEITURA")
                    st.success("Perfil atualizado!"); time.sleep(0.5); st.rerun()
            if c_btn2.button("🧮 Defasagem Matemática", use_container_width=True):
                with st.spinner("Atualizando perfil..."):
                    db.atualizar_aluno_cascata(dados_atuais['ID'], dados_atuais['NOME_ALUNO'], t_origem, "DEFASAGEM MATEMÁTICA")
                    st.success("Perfil atualizado!"); time.sleep(0.5); st.rerun()
            if c_btn3.button("🚀 Alta Performance", use_container_width=True):
                with st.spinner("Atualizando perfil..."):
                    db.atualizar_aluno_cascata(dados_atuais['ID'], dados_atuais['NOME_ALUNO'], t_origem, "ALTA PERFORMANCE")
                    st.success("Perfil atualizado!"); time.sleep(0.5); st.rerun()
            if c_btn4.button("👤 Típico (Limpar)", use_container_width=True):
                with st.spinner("Limpando perfil..."):
                    db.atualizar_aluno_cascata(dados_atuais['ID'], dados_atuais['NOME_ALUNO'], t_origem, "TÍPICO")
                    st.success("Perfil limpo!"); time.sleep(0.5); st.rerun()
            
            st.markdown("---")
            
            with st.form("form_edicao"):
                novo_nome = st.text_input("Nome Completo:", value=dados_atuais['NOME_ALUNO']).upper()
                
                idx_turma = lista_turmas_segura.index(t_origem) if t_origem in lista_turmas_segura else 0
                nova_turma = st.selectbox("Turma de Destino (Para Transferência):", lista_turmas_segura, index=idx_turma)
                
                st.info("💡 **Dica:** Para alunos PEI com múltiplas condições, digite separando por '+' ou vírgula. O sistema aceita códigos CID exatos (Ex: TEA + TDAH + F84.0).")
                nova_nec = st.text_input("Necessidades / CIDs:", value=dados_atuais['NECESSIDADES']).upper()
                
                if st.form_submit_button("💾 SALVAR E ATUALIZAR HISTÓRICO EM CASCATA"):
                    with st.spinner("Viajando no tempo e atualizando todo o histórico do aluno..."):
                        if db.atualizar_aluno_cascata(dados_atuais['ID'], novo_nome, nova_turma, nova_nec):
                            st.success("✅ Cadastro, laudos e histórico atualizados em cascata com sucesso!")
                            time.sleep(1.5)
                            st.rerun()

    # ==============================================================================
    # 🚨 NOVA ABA 5: RADIOGRAFIA COGNITIVA DA TURMA (VISÃO GLOBAL 360°)
    # ==============================================================================
    with tab_radiografia:
        st.subheader("🧠 Radiografia Cognitiva e Desempenho Global")
        st.caption("Mapeamento tático de perfis, engajamento, assiduidade e resultados em avaliações para geração de dossiês futuros.")
        
        t_rad = st.selectbox("🎯 Selecione a Turma para Mapeamento Global:", lista_turmas_segura, key=f"rad_t_{v}")
        
        if t_rad:
            alunos_rad = df_alunos[df_alunos['TURMA'] == t_rad].copy()
            if alunos_rad.empty:
                st.info("Nenhum aluno cadastrado nesta turma.")
            else:
                # --- 1. KPIs GLOBAIS DA TURMA ---
                st.markdown("#### 📊 1. Termômetro Global da Turma")
                df_d_rad = df_diario[df_diario['TURMA'] == t_rad]
                df_diag_rad = df_diagnosticos[df_diagnosticos['TURMA'] == t_rad]
                
                taxa_assiduidade = 0.0
                taxa_engajamento = 0.0
                media_geral_av = 0.0
                
                if not df_d_rad.empty:
                    total_registros = len(df_d_rad)
                    faltas = len(df_d_rad[df_d_rad['TAGS'] == "AUSÊNCIA"])
                    taxa_assiduidade = ((total_registros - faltas) / total_registros) * 100 if total_registros > 0 else 0
                    
                    df_vistos = df_d_rad[df_d_rad['VISTO_ATIVIDADE'].astype(str).str.upper() != "ISENTO"]
                    vistos_possiveis = len(df_vistos)
                    vistos_dados = len(df_vistos[df_vistos['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"])
                    taxa_engajamento = (vistos_dados / vistos_possiveis) * 100 if vistos_possiveis > 0 else 0
                
                if not df_diag_rad.empty:
                    media_geral_av = df_diag_rad['NOTA_CALCULADA'].apply(util.sosa_to_float).mean()
                
                c_k1, c_k2, c_k3 = st.columns(3)
                c_k1.metric("Assiduidade Média", f"{taxa_assiduidade:.1f}%")
                c_k2.metric("Engajamento (Vistos)", f"{taxa_engajamento:.1f}%")
                c_k3.metric("Média em Avaliações", f"{media_geral_av:.1f}")
                
                st.divider()

                # --- 2. DESEMPENHO EM AVALIAÇÕES ---
                st.markdown("#### 📈 2. Evolução nas Avaliações")
                if not df_diag_rad.empty:
                    df_diag_rad['NOTA_NUM'] = df_diag_rad['NOTA_CALCULADA'].apply(util.sosa_to_float)
                    evolucao_av = df_diag_rad.groupby('ID_AVALIACAO')['NOTA_NUM'].mean().reset_index()
                    evolucao_av['AVALIACAO_CURTA'] = evolucao_av['ID_AVALIACAO'].apply(lambda x: str(x).split('-')[0].strip()[:20])
                    
                    fig_av = px.bar(evolucao_av, x='AVALIACAO_CURTA', y='NOTA_NUM', text_auto='.1f', 
                                    title="Média da Turma por Avaliação",
                                    color='NOTA_NUM', color_continuous_scale="RdYlGn", range_y=[0, 10])
                    fig_av.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig_av, use_container_width=True)
                else:
                    st.info("Nenhuma avaliação escaneada para esta turma ainda.")

                st.divider()

                # --- 3. MAPA COGNITIVO (GRÁFICO DE ROSCA) ---
                st.markdown("#### 🧠 3. Mapa de Perfis Cognitivos")
                def categorizar_aluno(nec):
                    n = str(nec).upper().strip()
                    if "PENDENTE" in n or "SUSPEITA" in n: return "🟠 Radar (Suspeita/Pendente)"
                    if "DEFASAGEM LEITURA" in n: return "🧱 Barreira de Leitura"
                    if "DEFASAGEM MATEMÁTICA" in n or "DEFASAGEM MATEMATICA" in n: return "🧮 Desafio Lógico (Matemática)"
                    if "ALTA PERFORMANCE" in n: return "🚀 Alta Performance"
                    if n in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]: return "👤 Típico / Padrão"
                    return "♿ Inclusão Oficial (PEI)" 
                
                alunos_rad['PERFIL_COG'] = alunos_rad['NECESSIDADES'].apply(categorizar_aluno)
                
                contagem = alunos_rad['PERFIL_COG'].value_counts().reset_index()
                contagem.columns = ['Perfil', 'Quantidade']
                
                color_map = {
                    "👤 Típico / Padrão": "#A0AEC0",
                    "♿ Inclusão Oficial (PEI)": "#9F7AEA",
                    "🟠 Radar (Suspeita/Pendente)": "#ED8936",
                    "🧱 Barreira de Leitura": "#E53E3E",
                    "🧮 Desafio Lógico (Matemática)": "#D69E2E",
                    "🚀 Alta Performance": "#38B2AC"
                }
                
                col_graf, col_listas = st.columns([1, 1.5])
                with col_graf:
                    fig = px.pie(contagem, values='Quantidade', names='Perfil', hole=0.4, color='Perfil', color_discrete_map=color_map)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_listas:
                    def listar_alunos(perfil, emoji):
                        lista = alunos_rad[alunos_rad['PERFIL_COG'] == perfil]['NOME_ALUNO'].tolist()
                        if lista:
                            with st.expander(f"{emoji} {perfil.split(' ', 1)[1] if ' ' in perfil else perfil} ({len(lista)})", expanded=False):
                                for a in lista: st.caption(f"• {a}")
                    
                    listar_alunos("♿ Inclusão Oficial (PEI)", "♿")
                    listar_alunos("🟠 Radar (Suspeita/Pendente)", "🟠")
                    listar_alunos("🧱 Barreira de Leitura", "🧱")
                    listar_alunos("🧮 Desafio Lógico (Matemática)", "🧮")
                    listar_alunos("🚀 Alta Performance", "🚀")
                    listar_alunos("👤 Típico / Padrão", "👤")

                st.divider()

                # --- 4. SENSOR SEMÂNTICO DO DIÁRIO ---
                st.markdown("#### 🚨 4. Sensor Semântico do Diário (Ação Rápida)")
                st.caption("O sistema leu suas anotações recentes no Diário de Bordo. Classifique os alunos com 1 clique. Ao classificar ou clicar em 'Ciente', o aviso sumirá da tela.")
                
                def ocultar_aviso_diario(data_obs, id_alu, texto_obs):
                    try:
                        wb = db.conectar()
                        ws = wb.worksheet("DB_DIARIO_BORDO")
                        dados = ws.get_all_values()
                        for i, row in enumerate(dados):
                            if i > 0 and row[0] == data_obs and db.limpar_id(row[1]) == db.limpar_id(id_alu) and row[6] == texto_obs:
                                ws.update_cell(i + 1, 7, texto_obs + " [LIDO]")
                                st.cache_data.clear()
                                return True
                    except: pass
                    return False

                if not df_d_rad.empty:
                    obs_reais = df_d_rad[
                        (df_d_rad['OBSERVACOES'] != "") & 
                        (~df_d_rad['OBSERVACOES'].str.contains("Nota de Trabalho", na=False, case=False)) &
                        (~df_d_rad['OBSERVACOES'].str.contains(r"\[LIDO\]", na=False, case=False))
                    ]
                    
                    if not obs_reais.empty:
                        ultimas_obs = obs_reais.tail(5).iloc[::-1]
                        
                        for _, row_obs in ultimas_obs.iterrows():
                            with st.container(border=True):
                                st.markdown(f"🗣️ **{row_obs['NOME_ALUNO']}** ({row_obs['DATA']})")
                                st.info(f"*{row_obs['OBSERVACOES']}*")
                                
                                c_b1, c_b2, c_b3, c_b4 = st.columns(4)
                                id_aluno_obs = row_obs['ID_ALUNO']
                                nome_aluno_obs = row_obs['NOME_ALUNO']
                                data_obs = row_obs['DATA']
                                texto_obs = row_obs['OBSERVACOES']
                                
                                if c_b1.button("🧱 Barreira Leitura", key=f"btn_leit_{id_aluno_obs}_{row_obs.name}", use_container_width=True):
                                    with st.spinner("Atualizando e ocultando aviso..."):
                                        db.atualizar_aluno_cascata(id_aluno_obs, nome_aluno_obs, t_rad, "DEFASAGEM LEITURA")
                                        ocultar_aviso_diario(data_obs, id_aluno_obs, texto_obs)
                                        st.success("Classificado!"); time.sleep(0.5); st.rerun()
                                        
                                if c_b2.button("🧮 Defasagem Mat.", key=f"btn_mat_{id_aluno_obs}_{row_obs.name}", use_container_width=True):
                                    with st.spinner("Atualizando e ocultando aviso..."):
                                        db.atualizar_aluno_cascata(id_aluno_obs, nome_aluno_obs, t_rad, "DEFASAGEM MATEMÁTICA")
                                        ocultar_aviso_diario(data_obs, id_aluno_obs, texto_obs)
                                        st.success("Classificado!"); time.sleep(0.5); st.rerun()
                                        
                                if c_b3.button("🟠 Suspeita PEI", key=f"btn_pei_{id_aluno_obs}_{row_obs.name}", use_container_width=True):
                                    with st.spinner("Atualizando e ocultando aviso..."):
                                        db.atualizar_aluno_cascata(id_aluno_obs, nome_aluno_obs, t_rad, "PEI - PENDENTE")
                                        ocultar_aviso_diario(data_obs, id_aluno_obs, texto_obs)
                                        st.success("Classificado!"); time.sleep(0.5); st.rerun()
                                        
                                if c_b4.button("✅ Ciente (Ocultar)", key=f"btn_ok_{id_aluno_obs}_{row_obs.name}", use_container_width=True):
                                    with st.spinner("Ocultando aviso..."):
                                        ocultar_aviso_diario(data_obs, id_aluno_obs, texto_obs)
                                        st.rerun()
                    else:
                        st.success("✅ Nenhuma observação pendente de análise no Diário de Bordo.")
                else:
                    st.info("Sem registros no Diário de Bordo para esta turma.")


# ==============================================================================
# MÓDULO: BASE DE CONHECIMENTO (V45 - COFRE DIGITAL NO GOOGLE DRIVE)
# ==============================================================================
elif menu == "📚 Base de Conhecimento":
    st.title("📚 Biblioteca Digital de Soberania")
    st.markdown("---")
    
    tab_upload, tab_acervo_lib = st.tabs(["📤 Novo Upload (Drive)", "📖 Acervo Permanente"])
    
    with tab_upload:
        with st.form("form_upload_drive", clear_on_submit=True):
            st.markdown("#### 📤 Armazenar Material no Cofre")
            c1, c2 = st.columns(2)
            tipo_doc = c1.selectbox("Categoria:", ["Livro Didático", "Referencial Curricular", "Documento PEI", "Outros"])
            ano_doc = c2.selectbox("Série Alvo:", ["6º Ano", "7º Ano", "8º Ano", "9º Ano", "Geral"])
            
            nome_arq = st.text_input("Nome de Exibição do Material:", placeholder="Ex: Livro do 6 ano Flavio Simoes")
            uploaded_file = st.file_uploader("Selecione o arquivo PDF:", type=["pdf"])
            
            if st.form_submit_button("🚀 SALVAR NO GOOGLE DRIVE"):
                if uploaded_file and nome_arq:
                    with st.spinner("Enviando para o seu Cofre Digital..."):
                        # Usa a sua ponte para salvar no Drive
                        link_drive = db.subir_e_converter_para_google_docs(
                            uploaded_file, 
                            nome_arq, 
                            categoria=ano_doc, 
                            modo="BIBLIOTECA"
                        )
                        
                        if "drive.google.com" in link_drive:
                            # Salva no CSV do Banco de Dados
                            db.salvar_no_banco("DB_MATERIAIS", [
                                datetime.now().strftime("%d/%m/%Y"), 
                                nome_arq, 
                                link_drive, 
                                f"{tipo_doc} - {ano_doc}"
                            ])
                            st.success(f"✅ '{nome_arq}' guardado com segurança no Drive!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Erro no upload: {link_drive}")

    with tab_acervo_lib:
        if not df_materiais.empty:
            st.markdown(f"**📚 Materiais no Cofre:** {len(df_materiais)}")
            for _, row in df_materiais.iterrows():
                with st.container(border=True):
                    col_icon, col_txt, col_btn = st.columns([0.5, 3, 1])
                    col_icon.markdown("# 📕")
                    col_txt.markdown(f"**{row['NOME_ARQUIVO']}**")
                    col_txt.caption(f"📅 Upload: {row['DATA_UPLOAD']} | 🏷️ {row['TIPO']}")
                    col_btn.link_button("👁️ Ver no Drive", row['URI_ARQUIVO'], use_container_width=True)
        else:
            st.info("📭 Sua biblioteca está vazia.")


# ==============================================================================
# MÓDULO: RELATÓRIOS PEI / PERFIL IA - CLEAN & UX (V100 - MULTIPERFIL)
# ==============================================================================
elif menu == "♿ Relatórios PEI / Perfil IA":
    st.title("🧠 Analista de Perfis e Dossiê PEI")
    st.caption("💡 **Guia de Comando:** O sistema cruza dados de engajamento e notas para redigir relatórios evolutivos. A IA adapta o texto automaticamente se o aluno for PEI, tiver defasagem de base ou for de alta performance.")
    st.markdown("---")

    if df_alunos.empty:
        st.warning("⚠️ Base de alunos vazia. Cadastre alunos na Gestão da Turma.")
    else:
        # --- 1. SELEÇÃO DE ESTUDANTE ---
        with st.container(border=True):
            c_t, c_a = st.columns([1, 2])
            
            turmas_reais_pei = df_turmas[~df_turmas['ID_TURMA'].isin(["PI", "PC", "AC", "HTPC", "OUTRO"])]
            lista_turmas = sorted(turmas_reais_pei['ID_TURMA'].unique()) if not turmas_reais_pei.empty else sorted(df_alunos['TURMA'].unique())
            
            turma_pei = c_t.selectbox("🎯 Filtrar Turma:", lista_turmas, key="pei_t_clean")
            df_turma_foco = df_alunos[df_alunos['TURMA'] == turma_pei].copy()
            
            # 🚨 VACINA ANTI-VAZIO
            if df_turma_foco.empty:
                st.warning(f"⚠️ Nenhum aluno cadastrado na turma {turma_pei} ainda. Vá em 'Gestão da Turma' para povoar.")
                st.stop()
            
            # 🚨 NOVO MOTOR DE ÍCONES (MULTIPERFIL)
            def definir_icone_status(nec):
                n = str(nec).upper().strip()
                if "PENDENTE" in n or "SUSPEITA" in n: return "🟠"
                if "DEFASAGEM LEITURA" in n: return "🧱"
                if "DEFASAGEM MATEMÁTICA" in n or "DEFASAGEM MATEMATICA" in n: return "🧮"
                if "ALTA PERFORMANCE" in n: return "🚀"
                if n in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]: return "👤"
                return "♿"

            df_turma_foco['STATUS_ICON'] = df_turma_foco['NECESSIDADES'].apply(definir_icone_status)
            df_turma_foco['LABEL'] = df_turma_foco.apply(lambda x: f"{x['STATUS_ICON']} {x['NOME_ALUNO']} | {x['NECESSIDADES']}", axis=1)
            
            aluno_sel_label = c_a.selectbox("🔍 Selecionar Estudante:", df_turma_foco['LABEL'].tolist(), key="pei_a_clean")
            
            # Limpeza blindada do nome
            nome_limpo = aluno_sel_label.split(" | ")[0].replace("♿ ", "").replace("👤 ", "").replace("🟠 ", "").replace("🧱 ", "").replace("🧮 ", "").replace("🚀 ", "").strip()
            
            dados_a = df_turma_foco[df_turma_foco['NOME_ALUNO'] == nome_limpo].iloc[0]
            id_a = db.limpar_id(dados_a['ID'])
            perfil_atual = str(dados_a['NECESSIDADES']).upper().strip()

        # --- 2. MOTOR DE FUSÃO E MEMÓRIA ---
        with st.status("🔍 Maestro Sosa interconectando safras e evidências...", expanded=False) as status:
            hist_aluno = df_relatorios[df_relatorios['ID_ALUNO'].apply(db.limpar_id) == id_a]
            tem_passado = not hist_aluno.empty
            ultimo_relatorio = hist_aluno.iloc[-1]['CONTEUDO'] if tem_passado else "Primeiro Relatório (Linha de Base)."
            
            vistos = 0
            bonus = 0.0
            if not df_diario.empty:
                d_aluno = df_diario[df_diario['ID_ALUNO'].apply(db.limpar_id) == id_a]
                if not d_aluno.empty and 'VISTO_ATIVIDADE' in d_aluno.columns:
                    vistos = len(d_aluno[d_aluno['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"])
                    bonus = d_aluno['BONUS'].apply(util.sosa_to_float).sum()
            
            media_scan = 0.0
            if not df_diagnosticos.empty:
                s_aluno = df_diagnosticos[df_diagnosticos['ID_ALUNO'].apply(db.limpar_id) == id_a]
                if not s_aluno.empty:
                    media_scan = s_aluno['NOTA_CALCULADA'].apply(util.sosa_to_float).mean()
            
            nota_safra = min(10.0, media_scan + bonus)
            status.update(label="✅ Dados Sincronizados com Sucesso!", state="complete")

        # --- 3. DASHBOARD DE MÉTRICAS E ALERTA DE PERFIL ---
        # 🚨 BANNERS DINÂMICOS DE PERFIL
        if "PENDENTE" in perfil_atual or "SUSPEITA" in perfil_atual:
            st.warning(f"🟠 **Radar de Investigação:** {perfil_atual}")
        elif "DEFASAGEM" in perfil_atual:
            st.error(f"🧱 **Barreira de Aprendizagem:** {perfil_atual}")
        elif "ALTA PERFORMANCE" in perfil_atual:
            st.info(f"🚀 **Destaque Cognitivo:** {perfil_atual}")
        elif perfil_atual not in["NENHUMA", "", "NAN", "TÍPICO", "TIPICO"]:
            st.warning(f"♿ **Condição Clínica (PEI):** {perfil_atual}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Engajamento (Vistos)", vistos)
        c2.metric("Mérito Acumulado ⭐", f"{bonus:.1f}")
        c3.metric("Nota Média de Safra", f"{nota_safra:.1f}")
        c4.metric("Relatos Salvos", len(hist_aluno))

        # --- 4. CHECKLIST DE OBSERVAÇÃO ---
        with st.container(border=True):
            st.markdown("#### 📋 Checklist de Percepção Pedagógica")
            st.caption("Ajuste os controles abaixo. A IA usará essas informações para dar o tom do relatório.")
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                v_autonomia = st.select_slider("Autonomia:", options=["Dependente", "Com Apoio", "Em Evolução", "Autônomo"], value="Com Apoio")
                v_social = st.select_slider("Socialização:", options=["Isolado", "Passivo", "Interage", "Líder"], value="Interage")
            with col_ch2:
                v_participa = st.select_slider("Participação:", options=["Não participa", "Raramente", "Participativo", "Ativo"], value="Participativo")
                v_resposta = st.select_slider("Resposta às Intervenções:", options=["Resistente", "Lento", "Receptivo", "Rápido"], value="Receptivo")
            sem_mudancas = st.checkbox("📢 Quadro estável (Sem alterações significativas desde o último relatório)")

        # --- 5. ABAS DE TRABALHO ---
        tab_evolucao, tab_pei_doc, tab_coord, tab_curr, tab_timeline = st.tabs([
            "📈 1. Relatório de Evolução", 
            "🏛️ 2. Plano PEI (Pág 1)", 
            "📱 3. Relato Coordenação",
            "📖 4. Currículo Adaptado",
            "🗂️ 5. Linha do Tempo"
        ])

        # --- ABA 1: RELATÓRIO DE EVOLUÇÃO ---
        with tab_evolucao:
            st.subheader("📝 Análise Longitudinal de Processos")
            percepcao_extra = st.text_area("Observações Adicionais (Opcional):", placeholder="Ex: O aluno demonstrou muito interesse nas aulas com uso de tablet...", key="perc_clean")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🧠 INICIAR MOTOR DE IA: GERAR RELATÓRIO DE EVOLUÇÃO", type="primary", use_container_width=True):
                with st.spinner("Maestro Sosa analisando a linha do tempo e redigindo o parecer..."):
                    # 🚨 INJEÇÃO DE CONTEXTO DE PERFIL NA IA
                    prompt_ev = (
                        f"ESTUDANTE: {nome_limpo}. PERFIL COGNITIVO/CLÍNICO: {perfil_atual}.\n"
                        f"--- PASSADO ---\n{ultimo_relatorio}\n\n"
                        f"--- PRESENTE (DADOS) ---\n- Vistos: {vistos}, Bônus: {bonus}, Nota: {nota_safra}.\n"
                        f"--- CHECKLIST ATUAL ---\n- Autonomia: {v_autonomia}, Socialização: {v_social}, Participação: {v_participa}, Resposta: {v_resposta}.\n"
                        f"--- STATUS: {'Quadro Estável' if sem_mudancas else 'Houve alterações'}.\n"
                        f"--- OBSERVAÇÃO: {percepcao_extra}\n\n"
                        f"MISSÃO: Gere um relatório técnico comparativo focando no Delta de evolução.\n"
                        f"🚨 ATENÇÃO AO PERFIL: Como o aluno possui o perfil '{perfil_atual}', direcione o parecer pedagógico para as necessidades específicas desse quadro. "
                        f"Se for defasagem em leitura, foque na necessidade de letramento matemático. Se for defasagem matemática, foque no resgate das operações básicas. "
                        f"Se for alta performance, sugira enriquecimento curricular. Se for PEI, foque nas adaptações e no DUA."
                    )
                    st.session_state.res_v38_rel = ai.gerar_ia("ESPECIALISTA_INCLUSAO", prompt_ev)
            
            if "res_v38_rel" in st.session_state:
                st.text_area("Parecer Técnico Gerado:", st.session_state.res_v38_rel, height=400)
                if st.button("💾 SALVAR NO DOSSIÊ DO ALUNO", use_container_width=True):
                    db.salvar_no_banco("DB_RELATORIOS",[datetime.now().strftime("%d/%m/%Y"), id_a, nome_limpo, "EVOLUÇÃO", st.session_state.res_v38_rel])
                    st.success("✅ Relatório arquivado com sucesso!"); st.rerun()

        # --- ABA 2: PLANO DE ACESSIBILIDADE (PEI PÁGINA 1) ---
        with tab_pei_doc:
            st.subheader("🏛️ Seção 1: Plano de Acessibilidade Individual")
            st.caption("O sistema extrai as informações do Relatório de Evolução e as divide nas 4 áreas exigidas pelo documento oficial do PEI.")
            relatorio_base = st.session_state.get("res_v38_rel", "")
            
            if not relatorio_base:
                st.warning("⚠️ Gere primeiro o 'Relatório de Evolução' na Aba 1 para que a IA tenha dados para extrair.")
            else:
                if st.button("🧠 INICIAR MOTOR DE IA: EXTRAIR DADOS PARA O PEI", use_container_width=True, type="primary"):
                    with st.spinner("Fatiando evidências de forma atômica..."):
                        prompt_fatiar = (
                            f"RELATÓRIO PARA PROCESSAR:\n{relatorio_base}\n\n"
                            f"ORDEM SOBERANA: Extraia 4 resumos CURTOS e DIFERENTES. Responda EXATAMENTE nas tags [SOCIAIS], [COMUNICATIVAS], [EMOCIONAIS] e [FUNCIONAIS]."
                        )
                        st.session_state.res_v38_pei_tags = ai.gerar_ia("ESPECIALISTA_PEI", prompt_fatiar)

                if "res_v38_pei_tags" in st.session_state:
                    res_bruta = st.session_state.res_v38_pei_tags
                    def limpar_vazamento(texto):
                        import re
                        return re.sub(r'\[.*?\]', '', texto).replace('>', '').strip()

                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        ed_soc = st.text_area("1. Habilidades Sociais:", limpar_vazamento(ai.extrair_tag(res_bruta, "SOCIAIS")), height=180)
                        ed_emo = st.text_area("3. Habilidades Emocionais:", limpar_vazamento(ai.extrair_tag(res_bruta, "EMOCIONAIS")), height=180)
                    with col_p2:
                        ed_com = st.text_area("2. Habilidades Comunicativas:", limpar_vazamento(ai.extrair_tag(res_bruta, "COMUNICATIVAS")), height=180)
                        ed_fun = st.text_area("4. Habilidades Funcionais:", limpar_vazamento(ai.extrair_tag(res_bruta, "FUNCIONAIS")), height=180)

                    if st.button("💾 SALVAR PÁGINA 1 OFICIAL", use_container_width=True):
                        texto_consolidado = f"SOCIAIS: {ed_soc}\n\nCOMUNICATIVAS: {ed_com}\n\nEMOCIONAIS: {ed_emo}\n\nFUNCIONAIS: {ed_fun}"
                        db.salvar_no_banco("DB_RELATORIOS",[datetime.now().strftime("%d/%m/%Y"), id_a, nome_limpo, "CAPA_PEI_OFICIAL", texto_consolidado])
                        st.success("✅ Documento arquivado!"); st.balloons()

        # --- ABA 3: RELATO PARA COORDENAÇÃO (WHATSAPP) ---
        with tab_coord:
            st.subheader("📱 Relato Rápido para Coordenação")
            st.caption("Gere um texto curto e direto, ideal para copiar e colar no WhatsApp da coordenação ou da família.")
            
            mapa_estilos = {
                "Opção 1: Engajamento e Evolução": "🌟 **Foco:** Destacar progressos e participação ativa.",
                "Opção 2: Dificuldades e Suporte": "⚠️ **Foco:** Relatar barreiras e solicitar apoio da coordenação.",
                "Opção 3: Status Ultra-conciso": "⚡ **Foco:** Papo reto e direto (2-3 linhas)."
            }
            estilo_zap = st.radio("Qual o objetivo deste relato?", list(mapa_estilos.keys()), key="zap_clean")
            st.info(mapa_estilos[estilo_zap])

            if st.button("🧠 INICIAR MOTOR DE IA: GERAR MENSAGEM", use_container_width=True, type="primary"):
                with st.spinner("Traduzindo evidências para linguagem humana..."):
                    prompt_zap = f"ALUNO: {nome_limpo}. PERFIL: {perfil_atual}. DADOS: {vistos} vistos, {bonus} bônus. CHECKLIST: {v_autonomia}, {v_social}, {v_participa}, {v_resposta}. ESTILO: {estilo_zap}. Gere um parágrafo único, sem negritos, para WhatsApp."
                    st.session_state.res_v38_coord = ai.gerar_ia("PONTE_COORDENACAO", prompt_zap)
            
            if "res_v38_coord" in st.session_state:
                st.write(st.session_state.res_v38_coord)
                st.code(st.session_state.res_v38_coord, language=None)

        # --- ABA 4: CURRÍCULO ADAPTADO ---
        with tab_curr:
            st.subheader("⚙️ Construtor de Matriz Adaptada (Padrão Itabuna)")
            st.caption("Selecione os conteúdos da matriz regular. A IA fará a adaptação focada na superação das barreiras específicas deste aluno.")
            
            ano_aluno = "".join(filter(str.isdigit, turma_pei))
            df_matriz_ano = df_curriculo[df_curriculo['ANO'].astype(str) == ano_aluno].copy()

            if df_matriz_ano.empty:
                st.warning(f"⚠️ Matriz do {ano_aluno}º ano não localizada.")
            else:
                opcoes_conteudo = df_matriz_ano.apply(lambda x: f"[{x['TRIMESTRE']}] {x['CONTEUDO_ESPECIFICO']}", axis=1).tolist()
                selecionados = st.multiselect("📚 Escolha os conteúdos para adaptar:", opcoes_conteudo, key="sel_curr_clean")

                if selecionados:
                    if st.button("🧠 INICIAR MOTOR DE IA: GERAR GRADE DE EDIÇÃO", use_container_width=True, type="primary"):
                        with st.spinner("Arquitetando colunas e simplificando objetivos..."):
                            conteudos_brutos = [s.split("] ")[1] for s in selecionados]
                            df_focada = df_matriz_ano[df_matriz_ano['CONTEUDO_ESPECIFICO'].isin(conteudos_brutos)]
                            contexto_oficial = df_focada[['CONTEUDO_ESPECIFICO', 'OBJETIVOS']].to_string(index=False)
                            
                            # 🚨 INJEÇÃO DE CONTEXTO NO CURRÍCULO
                            prompt_curr = f"ESTUDANTE: {nome_limpo}. PERFIL/NECESSIDADE: {perfil_atual}. MATRIZ: {contexto_oficial}. Gere os itens adaptados focando em superar as barreiras do perfil {perfil_atual}."
                            st.session_state.res_v39_curr = ai.gerar_ia("TRADUTOR_CURRICULAR_V39", prompt_curr)

                    if "res_v39_curr" in st.session_state:
                        st.markdown("---")
                        h1, h2, h3, h4 = st.columns([1, 2, 1, 2])
                        h1.markdown("**CONTEÚDO**")
                        h2.markdown("**OBJETIVO DE ENSINO**")
                        h3.markdown("**FUNÇÕES PSÍQUICAS**")
                        h4.markdown("**SELEÇÃO DE MATERIAIS**")

                        raw_curr = st.session_state.res_v39_curr
                        blocos = re.findall(r"\[ITEM\](.*?)\[/ITEM\]", raw_curr, re.DOTALL)
                        
                        lista_final_para_salvar =[]

                        for idx, b in enumerate(blocos):
                            with st.container():
                                c1, c2, c3, c4 = st.columns([1, 2, 1, 2])
                                
                                def limpar(t): return re.sub(r'\[.*?\]', '', t).strip()
                                
                                v_c = limpar(ai.extrair_tag(b, "C"))
                                v_o = limpar(ai.extrair_tag(b, "O"))
                                v_f = limpar(ai.extrair_tag(b, "F"))
                                v_m = limpar(ai.extrair_tag(b, "M"))

                                edit_c = c1.text_area(f"C_{idx}", v_c, height=150, label_visibility="collapsed")
                                edit_o = c2.text_area(f"O_{idx}", v_o, height=150, label_visibility="collapsed")
                                edit_f = c3.text_area(f"F_{idx}", v_f, height=150, label_visibility="collapsed")
                                edit_m = c4.text_area(f"M_{idx}", v_m, height=150, label_visibility="collapsed")
                                
                                lista_final_para_salvar.append({"C": edit_c, "O": edit_o, "F": edit_f, "M": edit_m})
                                st.markdown("---")

                        trim_destino = st.selectbox("Salvar em qual trimestre?",["I Trimestre", "II Trimestre", "III Trimestre"])
                        if st.button("💾 ARQUIVAR PLANO TRIMESTRAL COMPLETO", use_container_width=True):
                            texto_banco = f"PLANO ADAPTADO - {trim_destino}\n\n"
                            for item in lista_final_para_salvar:
                                texto_banco += f"CONTEÚDO: {item['C']}\nOBJETIVO: {item['O']}\nFUNÇÕES: {item['F']}\nMATERIAIS: {item['M']}\n\n"
                            
                            db.salvar_no_banco("DB_RELATORIOS",[
                                datetime.now().strftime("%d/%m/%Y"), id_a, nome_limpo, f"CURRICULO_ADAPTADO_{trim_destino[0]}T", texto_banco
                            ])
                            st.success(f"✅ Currículo do {trim_destino} arquivado com sucesso!")
                            st.balloons()

        # --- ABA 5: LINHA DO TEMPO ---
        with tab_timeline:
            st.subheader("🗂️ Linha do Tempo de Custódia Digital")
            st.caption("Histórico cronológico de todos os documentos e evidências geradas para este estudante.")

            if not hist_aluno.empty:
                df_timeline = hist_aluno.iloc[::-1]

                for idx, row in df_timeline.iterrows():
                    tipo_bruto = str(row.get('TURMA', 'REGISTRO')) 
                    data_doc = row.get('DATA', 'S/D')
                    conteudo_raw = row.get('CONTEUDO', '')

                    if "EVOLUÇÃO" in tipo_bruto.upper():
                        label_tipo = "📈 RELATÓRIO DE EVOLUÇÃO"
                        icone = "📊"
                    elif "CAPA_PEI" in tipo_bruto.upper():
                        label_tipo = "🏛️ CAPA DO PEI (PÁGINA 1)"
                        icone = "📝"
                    elif "CURRICULO_ADAPTADO" in tipo_bruto.upper():
                        label_tipo = f"📖 CURRÍCULO ADAPTADO ({tipo_bruto.split('_')[-1]})"
                        icone = "📚"
                    else:
                        label_tipo = f"📄 {tipo_bruto}"
                        icone = "📎"

                    with st.container(border=True):
                        col_t1, col_t2 = st.columns([3, 1])
                        with col_t1:
                            st.markdown(f"### {icone} {label_tipo}")
                            st.caption(f"📅 Gerado em: {data_doc} | 🆔 ID Aluno: {id_a}")
                        
                        with col_t2:
                            if st.button("🗑️ APAGAR", key=f"del_rel_{idx}", use_container_width=True):
                                if db.excluir_registro("DB_RELATORIOS", conteudo_raw):
                                    st.success("Registro removido!"); time.sleep(0.5); st.rerun()

                        with st.expander("👁️ VISUALIZAR DOCUMENTO COMPLETO", expanded=False):
                            if "CURRICULO_ADAPTADO" in tipo_bruto.upper():
                                partes = conteudo_raw.split("CONTEÚDO:")
                                for p in partes:
                                    if p.strip():
                                        st.info(f"📖 **CONTEÚDO:** {p.strip()}")
                            else:
                                st.markdown(conteudo_raw.replace("\n", "  \n"))
                            
                            st.divider()
                            st.caption("🔒 Documento assinado digitalmente pelo ecossistema SOSA")
            else:
                st.info("📭 Nenhuma evidência ou documento arquivado para este estudante até o momento.")

import streamlit as st
import pandas as pd
from datetime import date, datetime
import database as db
import ai_engine as ai
import utils as util
from google.genai import types
import time
import os
import plotly.express as px
import exporter
import re
import ai_engine as ai  # <--- ADICIONE ESTA LINHA AQUI


st.set_page_config(page_title="SOSA 2026 | Master Intelligence", layout="wide", page_icon="🏫")

# --- CONTROLE DE TEMA (DESIGN PREMIUM CORRIGIDO) ---
with st.sidebar:
    tema_selecionado = st.radio("Visual do Sistema:", ["🌙 Dark Mode", "🌞 Light Mode"], horizontal=True)

# --- DEFINIÇÃO DA PALETA DE CORES ---
BRAND_BLUE = "#2962FF" 
BRAND_NAVY = "#000B1A" 

if tema_selecionado == "🌙 Dark Mode":
    cor_fundo = BRAND_NAVY
    cor_texto = "#FFFFFF"
    cor_sidebar = "#001226"
    cor_card_bg = "#001E3C"
    cor_card_borda = "#003366"
    cor_titulo_card = "#A0AEC0"
else:
    cor_fundo = "#F8FAFC"
    cor_texto = "#1A202C"  # Texto bem escuro para o Light Mode
    cor_sidebar = "#FFFFFF"
    cor_card_bg = "#FFFFFF"
    cor_card_borda = "#E2E8F0"
    cor_titulo_card = "#4A5568"

# --- INJEÇÃO DE CSS DINÂMICO (CORREÇÃO DE CONTRASTE) ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        * {{ font-family: 'Inter', sans-serif; }}

        .stApp {{
            background-color: {cor_fundo} !important;
            color: {cor_texto} !important;
        }}

        /* FORÇAR COR DO TEXTO EM TODO O SISTEMA */
        p, span, label, h1, h2, h3, .stMarkdown {{
            color: {cor_texto} !important;
        }}
        
        /* SIDEBAR */
        [data-testid="stSidebar"] {{
            background-color: {cor_sidebar} !important;
            border-right: 1px solid {cor_card_borda};
        }}
        
        /* CORRIGIR TEXTO DOS BOTÕES DE RÁDIO (NAVEGAÇÃO) */
        div[role="radiogroup"] label p {{
            color: {cor_texto} !important;
            font-weight: 500;
        }}

        /* BOTÃO SELECIONADO (AZUL DA LOGO) */
        div[role="radiogroup"] label[aria-checked="true"] {{
            background-color: {BRAND_BLUE}22 !important;
            border: 1px solid {BRAND_BLUE} !important;
        }}
        
        div[role="radiogroup"] label[aria-checked="true"] p {{
            color: {BRAND_BLUE} !important;
            font-weight: 700;
        }}

        /* CARDS DE MÉTRICAS */
        div[data-testid="stMetric"] {{
            background-color: {cor_card_bg} !important;
            border: 1px solid {cor_card_borda} !important;
            border-radius: 16px;
        }}
        
        div[data-testid="stMetricLabel"] p {{
            color: {cor_titulo_card} !important;
        }}
        
        div[data-testid="stMetricValue"] div {{
            color: {BRAND_BLUE} !important;
        }}

        /* INPUTS E SELECTBOXES */
        .stSelectbox div[data-baseweb="select"] {{
            background-color: {cor_card_bg} !important;
            color: {cor_texto} !important;
        }}
        
        /* CORRIGIR TEXTO DENTRO DO SELECTBOX */
        div[data-testid="stSelectbox"] p {{
            color: {cor_texto} !important;
        }}

        /* BOTÕES DE AÇÃO */
        .stButton button {{
            background-color: {BRAND_BLUE} !important;
            color: white !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- CARREGAMENTO ---
wb, (df_alunos, df_curriculo, df_materiais, df_planos, df_aulas, df_notas, df_diario, df_turmas, df_relatorios, df_horarios, df_registro_aulas) = db.carregar_tudo()

# --- SIDEBAR COM LOGOTIPO ---
with st.sidebar:
    try:
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])
        with col_meio:
            st.image("logo.png", width=100) 
    except:
        st.markdown("### 🏫 **SOSA**")
    
    st.markdown("<h3 style='text-align: center; margin-top: -15px; font-size: 14px;'>Maestro V14</h3>", unsafe_allow_html=True)
    st.markdown("---")

    if st.sidebar.button("🚨 Resetar Espaço do Drive"):
        msg = db.limpar_todo_drive_da_conta_servico()
        st.sidebar.success(msg)
    
    if st.button("🔄 Sincronizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
def prensa_hidraulica_texto(texto, label):
    # Remove o rótulo se a IA insistir em escrever, independente de maiúscula/minúscula ou acento
    limpo = texto.replace(label, "").replace(label.upper(), "").replace(label.lower(), "")
    # Remove os dois pontos iniciais que costumam sobrar
    if limpo.startswith(":") or limpo.startswith(" :"):
        limpo = limpo.split(":", 1)[-1]
    return limpo.strip()

# MENU DE NAVEGAÇÃO
menu = st.sidebar.radio("Navegação:", [
    "🤖 Maestro Dashboard",
    "📅 Planejamento (Ponto ID)",
    "🧪 Criador de Aulas",
    "📝 Central de Avaliações",
    "📝 Diário de Bordo Rápido",
    "📊 Painel de Notas & Vistos",
    "📈 Boletim Anual & Conselho",
    "👥 Gestão da Turma",
    "📚 Base de Conhecimento",
    "♿ Relatórios PEI / Perfil IA"
])


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

# --- ABA DE EXPORTAÇÃO E SINCRONIA (UNIFICADA V25.95) ---
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
                    # Busca se já existe plano para essa semana e ano
                    filtro = df_planos[(df_planos['SEMANA'] == f_semana) & (df_planos['ANO'] == f"{f_ano}º")]
                    for _, row_antiga in filtro.iterrows():
                        db.excluir_registro_com_drive("DB_PLANOS", row_antiga['PLANO_TEXTO'])
                else:
                    # Busca se já existe aula para essa semana e foco (Aula 1 ou Aula 2)
                    filtro = df_aulas[(df_aulas['SEMANA_REF'] == f_semana) & (df_aulas['TIPO_MATERIAL'].str.contains(f_aula))]
                    for _, row_antiga in filtro.iterrows():
                        db.excluir_registro_com_drive("DB_AULAS_PRONTAS", row_antiga['CONTEUDO'])

                # 2. PROCESSAMENTO POR MODO
                if modo_sync == "PLANEJAMENTO":
                    # Geração do DOCX do Plano
                    doc_plano = exporter.gerar_docx_plano_pedagogico_v18(nome_base, dados_plano, {"ano": f"{f_ano}º", "semana": f_semana})
                    
                    status.write("📤 Enviando Novo Plano para a Hierarquia Oficial...")
                    # Envia para a Ponte (Apps Script cuidará das pastas: Planos de Aula > Trimestre > Ano > Semana)
                    link = db.subir_e_converter_para_google_docs(
                        doc_plano, nome_base, trimestre=f_trimestre, categoria=f"{f_ano}º Ano", semana=f_semana, modo="PLANEJAMENTO"
                    )
                    
                    if "https" in str(link):
                        # Montagem do texto com MARKERS para o banco (Preservando a estrutura para o Criador de Aulas ler)
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
                        
                        sucesso = db.salvar_no_banco("DB_PLANOS", [
                            datetime.now().strftime("%d/%m/%Y"), f_semana, f"{f_ano}º", f_trimestre, "PADRÃO", final_txt
                        ])
                        
                        if sucesso:
                            status.update(label="✅ Plano Atualizado e Sincronizado!", state="complete")
                            st.success(f"Acesse aqui: {link}")
                            st.balloons()
                    else:
                        status.update(label="❌ Falha na Ponte Google.", state="error")
                        st.error(link)

                else:
                    # Geração dos DOCX da Aula
                    doc_alu = exporter.gerar_docx_aluno_v24(nome_base, ed_alu, {"ano": f"{f_ano}º", "trimestre": f_trimestre})
                    doc_prof = exporter.gerar_docx_professor_v25(nome_base, ed_prof, {"ano": f"{f_ano}º", "semana": f_semana})
                    
                    status.write("📤 Enviando Material do Aluno...")
                    link_alu = db.subir_e_converter_para_google_docs(doc_alu, f"{nome_base}_ALUNO", trimestre=f_trimestre, categoria=f_categoria, semana=f_semana, modo="AULA")
                    
                    status.write("📤 Enviando Guia do Professor...")
                    link_prof = db.subir_e_converter_para_google_docs(doc_prof, f"{nome_base}_PROF", trimestre=f_trimestre, categoria=f_categoria, semana=f_semana, modo="AULA")
                    
                    link_pei = "N/A"
                    if "lab_pei" in st.session_state:
                        status.write("📤 Enviando Material PEI Adaptado...")
                        doc_pei = exporter.gerar_docx_pei_v25(f"{nome_base}_PEI", st.session_state.lab_pei, {"trimestre": f_trimestre})
                        link_pei = db.subir_e_converter_para_google_docs(doc_pei, f"{nome_base}_PEI", trimestre=f_trimestre, categoria=f_categoria, semana=f_semana, modo="AULA")

                    if "https" in str(link_alu) and "https" in str(link_prof):
                        # Salva na Gaveta de Materiais (DB_AULAS_PRONTAS)
                        conteudo_banco = f"[ROTEIRO_PROF]\n{ed_prof_para_banco}\n\n--- LINKS DE ACESSO ---\nAluno({link_alu})\nProf({link_prof})\nPEI({link_pei})"
                        
                        db.salvar_no_banco("DB_AULAS_PRONTAS", [
                            datetime.now().strftime("%d/%m/%Y"), f_semana, f"{f_aula}", conteudo_banco, f"{f_ano}º", link_alu
                        ])
                        status.update(label="✅ Aula Atualizada e Sincronizada!", state="complete")
                        st.balloons()
                    else:
                        status.update(label="❌ Erro no Upload da Aula.", state="error")
                        st.error(f"Link Aluno: {link_alu}")
                       
# ==============================================================================
# MÓDULO: DASHBOARD INTELIGENTE (V6 - FULL CONTEXT: NOTAS + PDF + AULAS CRIADAS)
# ==============================================================================
if menu == "🤖 Maestro Dashboard":
    st.title("🤖 Maestro Dashboard | Central de Inteligência")
    st.markdown("---")

    # --- 1. FUNÇÃO DE LIMPEZA DE NOTAS (NORMALIZAÇÃO RECURSIVA) ---
    def normalizar_nota_agressiva(valor):
        """
        Garante matematicamente que a nota fique entre 0 e 10.
        Usa loop while para corrigir erros como 718 -> 71.8 -> 7.18
        """
        try:
            # Limpeza básica de string
            s_val = str(valor).replace(',', '.').strip()
            if not s_val or s_val.lower() == 'nan': return 0.0
            
            f_val = float(s_val)
            
            # Loop de correção: Enquanto for maior que 10, divide por 10
            while f_val > 10.0:
                f_val = f_val / 10.0
                
            return f_val
        except:
            return 0.0

    # --- 2. PREPARAÇÃO DOS DADOS (CONTEXTO GLOBAL) ---
    def montar_contexto_global():
        ctx = "DADOS ESTRUTURADOS DO SISTEMA (ITABUNA 2026):\n\n"
        
        # A. Tempo
        hoje = datetime.now()
        inicio_aulas = datetime(2026, 2, 2)
        if hoje < inicio_aulas:
            ctx += f"DATA HOJE: {hoje.strftime('%d/%m/%Y')} (Período de Planejamento).\n\n"
        else:
            semana_num = int((hoje - inicio_aulas).days / 7) + 1
            trimestre_atual, _ = util.obter_info_trimestre(hoje.date())
            ctx += f"DATA HOJE: {hoje.strftime('%d/%m/%Y')} (Semana {semana_num}, {trimestre_atual}).\n\n"

        # B. Alunos
        if not df_alunos.empty:
            total = len(df_alunos)
            peis = df_alunos[df_alunos['NECESSIDADES'] != 'NENHUMA']
            lista_peis = ", ".join([f"{r['NOME_ALUNO']} ({r['NECESSIDADES']})" for _, r in peis.iterrows()])
            ctx += f"TURMA: {total} alunos. PEI: {lista_peis}.\n"
        
        # C. Notas (NORMALIZAÇÃO AGRESSIVA)
        if not df_notas.empty:
            ctx += "BOLETIM (Notas Normalizadas 0-10):\n"
            for _, row in df_notas.iterrows():
                nome = row['NOME_ALUNO']
                n_visto = normalizar_nota_agressiva(row.get('NOTA_VISTOS', 0))
                n_teste = normalizar_nota_agressiva(row.get('NOTA_TESTE', 0))
                n_prova = normalizar_nota_agressiva(row.get('NOTA_PROVA', 0))
                n_media = normalizar_nota_agressiva(row.get('MEDIA_FINAL', 0))
                
                ctx += f"- {nome}: Média {n_media:.1f} (Vistos: {n_visto}, Teste: {n_teste}, Prova: {n_prova})\n"
            ctx += "\n"

        # D. Planejamento
        if not df_planos.empty:
            planos_prox = df_planos.tail(3) 
            resumo_planos = " | ".join([f"Semana {r['SEMANA']}: {ai.extrair_tag(r['PLANO_TEXTO'], 'CONTEUDOS_ESPECIFICOS')}" for _, r in planos_prox.iterrows()])
            ctx += f"PLANEJAMENTO RECENTE: {resumo_planos}.\n"

        # E. Diário
        if not df_diario.empty:
            ultimos = df_diario.tail(20)
            ocorrencias = []
            for _, r in ultimos.iterrows():
                tags = str(r['TAGS'])
                obs = str(r['OBSERVACOES'])
                if (tags and tags != "nan" and tags != "") or (obs and obs != "nan" and obs != ""):
                    ocorrencias.append(f"{r['DATA']} - {r['NOME_ALUNO']}: {tags} | {obs}")
            ctx += f"DIÁRIO (Ocorrências): {'; '.join(ocorrencias)}.\n"

        # F. Materiais Criados (NOVA INTEGRAÇÃO)
        if not df_aulas.empty:
            # Pega os últimos 5 materiais criados para dar contexto do que já foi feito
            ultimos_mats = df_aulas.tail(5)
            lista_mats = []
            for _, r in ultimos_mats.iterrows():
                # Pega um resumo do conteúdo para não estourar o limite de texto
                resumo_conteudo = str(r['CONTEUDO'])[:150].replace('\n', ' ') + "..."
                lista_mats.append(f"[{r['DATA']}] Tipo: {r['TIPO_MATERIAL']} (Ref: {r['SEMANA_REF']}) -> Conteúdo: {resumo_conteudo}")
            
            ctx += f"MATERIAIS JÁ CRIADOS PELO PROFESSOR (Histórico): {'; '.join(lista_mats)}.\n"

        return ctx

    # --- 3. VISUALIZAÇÃO DE KPIs (CARTÕES) ---
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    # KPI 1: Total Alunos
    col_kpi1.metric("👥 Total de Alunos", len(df_alunos) if not df_alunos.empty else 0)

    # KPI 2: Alunos PEI
    total_pei = len(df_alunos[df_alunos['NECESSIDADES'] != 'NENHUMA']) if not df_alunos.empty else 0
    col_kpi2.metric("♿ Alunos PEI/AEE", total_pei)

    # KPI 3: Média Geral
    media_turma = 0.0
    delta_media = "Sem dados"
    if not df_notas.empty:
        notas_corrigidas = df_notas['MEDIA_FINAL'].apply(normalizar_nota_agressiva)
        media_turma = notas_corrigidas.mean()
        delta_media = "Na média" if media_turma >= 6.0 else "Abaixo da meta"
    
    col_kpi4.metric("📊 Média Geral (Rede)", f"{media_turma:.1f}", delta=delta_media)

    # KPI 4: Risco
    risco = 0
    if not df_notas.empty:
        risco = len(df_notas[df_notas['MEDIA_FINAL'].apply(normalizar_nota_agressiva) < 6.0])
    col_kpi4.metric("🚨 Risco (Notas < 6.0)", risco, delta_color="inverse")


    # --- 4. CHAT COM VISÃO DE ARQUIVOS (PDFs) ---
    st.markdown("### 💬 Converse com o Sistema")
    
    # PREPARAÇÃO DOS ARQUIVOS (PDFs)
    arquivos_para_ia = []
    nomes_arquivos = []
    if not df_materiais.empty:
        for _, row in df_materiais.iterrows():
            uri = row['URI_ARQUIVO']
            nome = row['NOME_ALUNO'] if 'NOME_ALUNO' in row else row['NOME_ARQUIVO'] 
            nomes_arquivos.append(nome)
            arquivos_para_ia.append(types.Part.from_uri(file_uri=uri, mime_type="application/pdf"))
    
    # Feedback Visual
    if arquivos_para_ia:
        st.success(f"📚 **Biblioteca Conectada:** O Maestro está lendo {len(arquivos_para_ia)} livro(s): {', '.join(nomes_arquivos)}")
    else:
        st.warning("⚠️ Nenhum livro PDF encontrado na Base de Conhecimento. O Chat só lerá as planilhas.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: 'O que eu criei na semana passada?', 'Resuma a página 23 do livro'"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Processando planilhas, materiais criados e lendo livros..."):
                
                contexto_dados = montar_contexto_global()
                
                # PROMPT REFORÇADO
                prompt_final = (
                    f"VOCÊ É O MAESTRO SOSA, O SISTEMA CENTRAL DA ESCOLA.\n"
                    f"IMPORTANTE: Você recebeu arquivos PDF anexos (Livros Didáticos). "
                    f"SE A PERGUNTA FOR SOBRE CONTEÚDO, PÁGINAS OU EXERCÍCIOS, LEIA O PDF ANEXO IMEDIATAMENTE.\n"
                    f"NÃO DIGA QUE NÃO TEM ACESSO. OS ARQUIVOS ESTÃO NO SEU CONTEXTO.\n\n"
                    f"DADOS DAS PLANILHAS (NOTAS/DIÁRIO/MATERIAIS CRIADOS):\n{contexto_dados}\n\n"
                    f"PERGUNTA DO PROFESSOR: {prompt}"
                )
                
                # Envia Prompt + Arquivos
                resposta = ai.gerar_ia("MAESTRO", prompt_final, partes_arquivos=arquivos_para_ia)
                
                st.markdown(resposta)
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})

# ==============================================================================
# MÓDULO: LABORATÓRIO DE MATERIAIS V25.80 (REFINADO E BLINDADO)
# ==============================================================================
elif menu == "🧪 Criador de Aulas":
    st.title("🧪 Laboratório de Materiais (V25.80)")
    st.markdown("---")
    
    tab_criar, tab_gavetas = st.tabs(["🚀 CENTRAL DE CRIAÇÃO", "🗂️ GAVETAS DE MATERIAIS"])

    if "v_lab" not in st.session_state: st.session_state.v_lab = 1

    with tab_criar:
        
        # --- FASE 1: SINCRONIA PONTO ID (COM FILTRO INTELIGENTE DE CONCLUSÃO) ---
        with st.container(border=True):
            st.markdown("### 🔗 1. Sincronia com Planejamento (Ponto ID)")
            c1, c2, c3 = st.columns([1, 2, 1.5])
            
            ano_lab = c1.selectbox("Série:", [6, 7, 8, 9], key="lab_ano_v25")
            planos_ano = df_planos[df_planos['ANO'] == f"{ano_lab}º"]
            
            if planos_ano.empty:
                st.warning(f"⚠️ Nenhum plano encontrado para o {ano_lab}º Ano.")
            else:
                sem_lab = c2.selectbox("Semana de Referência:", planos_ano['SEMANA'].tolist(), key="lab_sem_v25")
                
                # --- LÓGICA DE FILTRO DE AULAS JÁ PRODUZIDAS ---
                # Buscamos no banco o que já foi feito para este ano e semana
                aulas_feitas = df_aulas[
                    (df_aulas['ANO'] == f"{ano_lab}º") & 
                    (df_aulas['SEMANA_REF'] == sem_lab)
                ]['TIPO_MATERIAL'].astype(str).tolist()
                
                ja_tem_aula1 = any("AULA 1" in a.upper() for a in aulas_feitas)
                ja_tem_aula2 = any("AULA 2" in a.upper() for a in aulas_feitas)
                
                opcoes_foco = []
                if not ja_tem_aula1: opcoes_foco.append("Aula 1")
                if not ja_tem_aula2: opcoes_foco.append("Aula 2")
                
                # Decisão visual do seletor
                if not opcoes_foco:
                    st.success(f"✅ {sem_lab} concluída com sucesso!")
                    aula_num = None # Trava a geração
                else:
                    aula_num = c3.radio("Foco da Aula:", opcoes_foco, horizontal=True)
                
                # Só prossegue se houver aula para criar
                if aula_num:
                    plano_row = planos_ano[planos_ano['SEMANA'] == sem_lab].iloc[0]
                    plano_raw = plano_row['PLANO_TEXTO']
                    
                    modalidade_planejada = ai.extrair_tag(plano_raw, "MODALIDADE").upper()
                    is_livro = "LIVRO" in modalidade_planejada or "MÉTODO LIVRO" in plano_raw.upper()
                    metodo_fiel = "📖 LIVRO DIDÁTICO" if is_livro else "🎛️ MANUAL / BANCO"
                    cor_metodo = "#2962FF" if is_livro else "#00C853"
                    
                    cont_fiel = ai.extrair_tag(plano_raw, "CONTEUDOS_ESPECIFICOS")
                    obj_fiel = ai.extrair_tag(plano_raw, "OBJETIVOS_ENSINO")

                    st.markdown(f"""
                        <div style='background-color: rgba(41, 98, 255, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid {cor_metodo};'>
                            <b style='color: {cor_metodo};'>{metodo_fiel}</b> | <b>Conteúdo:</b> {cont_fiel[:100]}...
                        </div>
                    """, unsafe_allow_html=True)

                # --- FASE 2: PARÂMETROS (AGORA PROTEGIDA DENTRO DO ELSE) ---
                st.markdown(" ")
                with st.container(border=True):
                    st.markdown("### 🎯 2. Parâmetros de Precisão")
                    df_base_ano = df_curriculo[df_curriculo['ANO'] == int(ano_lab)]
                    col_p1, col_p2 = st.columns(2)
                    
                    def check_match_inteligente(item_csv, texto_plano):
                        item = str(item_csv).upper().strip()
                        plano = str(texto_plano).upper().strip()
                        return item in plano or plano in item or any(word in plano for word in item.split() if len(word) > 4)

                    sel_cont = col_p1.multiselect("Confirmar Conteúdos:", options=df_base_ano['CONTEUDO_ESPECIFICO'].unique(), 
                                                 default=[c for c in df_base_ano['CONTEUDO_ESPECIFICO'].unique() if check_match_inteligente(c, cont_fiel)])
                    
                    opcoes_obj = df_base_ano[df_base_ano['CONTEUDO_ESPECIFICO'].isin(sel_cont)]['OBJETIVOS'].unique().tolist() if sel_cont else []
                    sel_obj = col_p2.multiselect("Confirmar Objetivos:", options=opcoes_obj,
                                                default=[o for o in opcoes_obj if check_match_inteligente(o, obj_fiel)])

                    cp1, cp2, cp3 = st.columns([1, 1, 1])
                    formato = cp1.radio("Formato:", ["Quadro (Lousa)", "Slides (Apresentação)"], horizontal=True)
                    qtd_q = cp2.slider("Questões:", 1, 15, 4)
                    nivel = cp3.select_slider("Desafio:", options=["Básico", "Intermediário", "Desafio"])
                    instr = st.text_area("Instruções Adicionais:", placeholder="Ex: Use exemplos de astronomia...")

                    if st.button("🚀 COMPILAR MATERIAL DE ELITE", use_container_width=True, type="primary"):
                        with st.spinner("Maestro processando Injeção de Plano..."):
                            arquivos_contexto = []
                            if is_livro:
                                import re
                                match_livro = re.search(r"MÉTODO LIVRO: \['(.*?)'\]", plano_raw)
                                nome_livro = match_livro.group(1) if match_livro else None
                                if nome_livro:
                                    livro_data = df_materiais[df_materiais['NOME_ARQUIVO'] == nome_livro]
                                    if not livro_data.empty:
                                        arquivos_contexto.append(types.Part.from_uri(file_uri=livro_data.iloc[0]['URI_ARQUIVO'], mime_type="application/pdf"))

                            prompt_v25 = f"🚨 PROTOCOLO PIP 🚨\nMÉTODO: {metodo_fiel}\nPLANO: {plano_raw}\nOBJETIVO: {sel_obj}\nFOCO: {aula_num} | SÉRIE: {ano_lab}º | QUESTÕES: {qtd_q}\nFORMATO: {formato} | NÍVEL: {nivel}\nEXTRA: {instr}"
                            st.session_state.lab_temp = ai.gerar_ia("MESTRE_V24", prompt_v25, partes_arquivos=arquivos_contexto)
                            st.rerun()

                # --- FASE 3: REFINADOR E ACABAMENTO (TAMBÉM DENTRO DO ELSE) ---
        if "lab_temp" in st.session_state:
            st.markdown(" ")
            st.markdown("### 🤖 3. Refinamento e Acabamento")
            
            # Captura a versão atual para as chaves (keys)
            v = st.session_state.v_lab
            txt_bruto = st.session_state.lab_temp

            # --- REFINADOR MAESTRO COM "TROCA DE PELE" ---
            comando_refine = st.chat_input("Deseja ajustar algo na aula? (Ex: 'Troque a Q2 por um desafio', 'Mude o tema para Astronomia')")
            
            if comando_refine:
                with st.spinner("Maestro executando reengenharia do material..."):
                    # 1. Prompt de Soberania
                    prompt_refine = (
                        f"ORDEM DE ALTERAÇÃO: {comando_refine}\n\n"
                        f"CONTEÚDO ATUAL:\n{txt_bruto}\n\n"
                        f"INSTRUÇÃO: Aplique a alteração em todas as seções (Professor, Aluno e Imagens) para manter a unidade lógica."
                    )
                    
                    # 2. Gera a nova versão
                    nova_aula = ai.gerar_ia("REFINADOR_MATERIAIS", prompt_refine)
                    
                    # 3. O SEGREDO: Atualiza o conteúdo E incrementa a versão
                    st.session_state.lab_temp = nova_aula
                    st.session_state.v_lab += 1 # Isso força o Streamlit a renovar os campos
                    
                    st.success("Refino aplicado! Atualizando painéis...")
                    time.sleep(1)
                    st.rerun()

            # Preparação do Dicionário para a Visualização (usando o 'v' atualizado)
            info_para_ia = {
                "aula": aula_num,
                "ano": str(ano_lab),
                "semana": sem_lab,
                "formato": formato,
                "conteudos": sel_cont,
                "ed_prof": ai.extrair_tag(st.session_state.lab_temp, "PROFESSOR"),
                "ed_alu": ai.extrair_tag(st.session_state.lab_temp, "ALUNO")
            }

            # Chamada da Função de Visualização
            exibir_material_estruturado(st.session_state.lab_temp, f"lab_v{v}", info_aula=info_para_ia)

# --- ABA 2: GAVETAS DE MATERIAIS (HISTÓRICO MULTIMODAL V25.85 - CORRIGIDO) ---
    with tab_gavetas:
        st.subheader("🗂️ Gestão de Materiais Produzidos")
        if df_aulas.empty:
            st.info("📭 Nenhuma aula produzida.")
        else:
            ano_gav = st.selectbox("Filtrar por Ano:", ["Todos", "6º", "7º", "8º", "9º"], key="gav_v17_ano")
            df_g = df_aulas.copy()
            if ano_gav != "Todos": 
                df_g = df_g[df_g['ANO'].str.contains(ano_gav, na=False)]
            
            def definir_categoria_gaveta(linha):
                ref = str(linha['SEMANA_REF']).upper()
                if "I TRIMESTRE" in ref: return "I Trimestre"
                if "II TRIMESTRE" in ref: return "II Trimestre"
                if "III TRIMESTRE" in ref: return "III Trimestre"
                import re
                num_sem = re.search(r"(\d+)", ref)
                if num_sem:
                    n = int(num_sem.group(1))
                    if 1 <= n <= 13: return "I Trimestre"
                    if 14 <= n <= 26: return "II Trimestre"
                    if n >= 27: return "III Trimestre"
                return "Recesso/Jornada"

            df_g['CATEGORIA_GAVETA'] = df_g.apply(definir_categoria_gaveta, axis=1)
            categorias_ordem = ["I Trimestre", "II Trimestre", "III Trimestre", "Recesso/Jornada"]
            
            for cat in categorias_ordem:
                df_cat = df_g[df_g['CATEGORIA_GAVETA'] == cat]
                if not df_cat.empty:
                    with st.expander(f"⏳ Materiais do {cat}", expanded=(cat == "I Trimestre")):
                        for _, row in df_cat.iloc[::-1].iterrows():
                            tipo = str(row['TIPO_MATERIAL']).upper()
                            cor_borda = "#2962FF" if "AULA 1" in tipo else "#00C853"
                            
                            with st.container(border=True):
                                st.markdown(f"<div style='border-left: 5px solid {cor_borda}; padding-left: 10px;'><b>{row['SEMANA_REF']} ÷ {row['TIPO_MATERIAL']}</b></div>", unsafe_allow_html=True)
                                
                                texto_full = str(row['CONTEUDO'])
                                
                                # Extração de Links com Regex Blindada
                                import re
                                def extrair_link_seguro(padrao, texto):
                                    match = re.search(padrao, texto)
                                    link = match.group(1) if match else None
                                    return link if link and link.startswith("https") else None

                                l_alu = extrair_link_seguro(r"Aluno\((.*?)\)", texto_full)
                                l_prof = extrair_link_seguro(r"Prof\((.*?)\)", texto_full)
                                l_pei = extrair_link_seguro(r"PEI\((.*?)\)", texto_full)

                                st.write("")
                                c1, c2, c3, c4 = st.columns(4)
                                
                                # --- BOTÕES COM CHAVES ÚNICAS (RESOLVE O ERRO DE ID DUPLICADO) ---
                                
                                # Coluna 1: Aluno
                                if l_alu: 
                                    c1.link_button("📝 ALUNO", l_alu, use_container_width=True)
                                else: 
                                    c1.button("❌ ALUNO", disabled=True, use_container_width=True, key=f"no_alu_{row.name}")
                                
                                # Coluna 2: Professor/Slides
                                label_prof = "📜 SLIDES" if "SLIDES" in tipo else "👨‍🏫 GUIA"
                                if l_prof: 
                                    c2.link_button(label_prof, l_prof, use_container_width=True)
                                else: 
                                    c2.button(f"❌ {label_prof}", disabled=True, use_container_width=True, key=f"no_prof_{row.name}")
                                
                                # Coluna 3: PEI
                                if l_pei: 
                                    c3.link_button("♿ PEI", l_pei, use_container_width=True)
                                else: 
                                    c3.button("⚪ SEM PEI", disabled=True, use_container_width=True, key=f"no_pei_{row.name}")
                                
                                # Coluna 4: Apagar
                                if c4.button("🗑️ APAGAR", key=f"del_v17_{row.name}", use_container_width=True):
                                    if db.excluir_registro_com_drive("DB_AULAS_PRONTAS", row['CONTEUDO']):
                                        st.success("Removido!")
                                        time.sleep(0.5)
                                        st.rerun()

                                with st.expander("📄 Ver Detalhes Técnicos"):
                                    t_hist1, t_hist2 = st.tabs(["📜 Roteiro", "🎨 Prompts"])
                                    with t_hist1:
                                        # Pega o roteiro antes da linha de links
                                        roteiro_limpo = ai.extrair_tag(texto_full, "ROTEIRO_PROF")
                                        if not roteiro_limpo:
                                            roteiro_limpo = texto_full.split("--- LINKS")[0]
                                        st.text_area("Texto:", roteiro_limpo, height=200, key=f"h_rot_{row.name}")
                                    with t_hist2:
                                        p_reg = ai.extrair_tag(texto_full, "PROMPTS_REGULAR")
                                        p_pei = ai.extrair_tag(texto_full, "PROMPTS_PEI")
                                        if p_reg: st.code(f"REGULAR: {p_reg}")
                                        if p_pei: st.code(f"PEI: {p_pei}")
                                        if not p_reg and not p_pei: st.info("Sem prompts salvos.")
                            
# ==============================================================================
# MÓDULO: PLANEJAMENTO ESTRATÉGICO (PONTO ID) - ARQUITETURA V26 (ELITE)
# ==============================================================================
elif menu == "📅 Planejamento (Ponto ID)":
    st.title("📅 Engenharia de Planejamento (Ponto ID)")
    st.markdown("---")

    # 1. FUNÇÕES DE SUPORTE TÉCNICO
    def limpar_v26(texto, label):
        if not texto: return ""
        t = texto.replace(label, "").replace(label.upper(), "").replace(label.lower(), "").strip()
        if t.startswith(":") or t.startswith(" :"): t = t[1:].strip()
        return t

    def reset_planejamento():
        if "p_temp" in st.session_state: del st.session_state.p_temp
        st.session_state.v_plano = int(time.time())
        st.rerun()

    if "v_plano" not in st.session_state:
        st.session_state.v_plano = int(time.time())
    
    v = st.session_state.v_plano 

    # Títulos Técnicos e Curtos
    tab_gerar, tab_hist, tab_matriz, tab_auditoria = st.tabs([
        "🚀 Engenharia de Planejamento", 
        "📂 Gestão de Acervo (PIP)", 
        "📖 Matriz Curricular Ativa", 
        "📈 Auditoria de Cobertura"
    ])
    
    # --- ABA 1: ENGENHARIA DE PLANEJAMENTO (GERAÇÃO) ---
    with tab_gerar:
        with st.container(border=True):
            st.markdown("### ⚙️ 1. Parâmetros de Regência")
            c1, c2, c3 = st.columns([1, 2, 1.5])
            
            ano_p = c1.selectbox("Série/Ano:", [6, 7, 8, 9], key="ano_sel_v26")
            todas_semanas = util.gerar_semanas()
            sem_p = c2.selectbox("Semana de Referência:", todas_semanas, key="sem_sel_v26")
            sem_limpa = sem_p.split(" (")[0]
            
            modo_p = c3.radio("Método de Elaboração:", ["📖 Livro Didático", "🎛️ Manual (Banco)"], horizontal=True)

            # --- RADAR DE STATUS PIP (VERIFICAÇÃO DE EXISTÊNCIA POR ANO) ---
            plano_existente = df_planos[(df_planos['ANO'] == f"{ano_p}º") & (df_planos['SEMANA'] == sem_limpa)]
            
            if not plano_existente.empty:
                st.warning(f"⚠️ **STATUS: PLANO DETECTADO.** Já existe planejamento para o {ano_p}º Ano na {sem_limpa}.")
                if st.button("📂 ABRIR PARA EDIÇÃO NO ACERVO", use_container_width=True):
                    # Lógica para trocar de aba (simulada via instrução)
                    st.info("Vá para a aba 'Gestão de Acervo' para editar este plano.")
            else:
                st.success(f"✅ **STATUS: DISPONÍVEL.** {ano_p}º Ano livre para planejamento na {sem_limpa}.")

        # --- CONFIGURAÇÃO DE CONTEÚDO (SEM SIMPLIFICAÇÃO) ---
        df_f = df_curriculo[df_curriculo['ANO'] == ano_p]
        cont_pre, obj_pre, eixo_pre = [], [], ""
        sel_mat, pags = [], "" 

        with st.container(border=True):
            if modo_p == "🎛️ Manual (Banco)":
                st.markdown("#### 🎯 Matriz Curricular (Fiel ao Banco)")
                cx1, cx2 = st.columns(2)
                eixo_pre = cx1.selectbox("Eixo Temático:", df_f['EIXO'].unique(), key=f"eixo_v26_{v}")
                cont_pre = st.multiselect("Conteúdos Específicos:", options=df_f[df_f['EIXO'] == eixo_pre]['CONTEUDO_ESPECIFICO'].unique(), key=f"cont_v26_{v}")
                obj_pre = st.multiselect("Objetivos de Ensino:", options=df_f[df_f['CONTEUDO_ESPECIFICO'].isin(cont_pre)]['OBJETIVOS'].unique(), key=f"obj_v26_{v}")
                ctx_ia = f"MÉTODO MANUAL. EIXO: {eixo_pre}. CONTEÚDOS: {cont_pre}. OBJETIVOS: {obj_pre}."
            else:
                st.markdown("#### 📖 Referência Bibliográfica")
                cx1, cx2 = st.columns([2, 1])
                sel_mat = cx1.multiselect("Livro Didático:", df_materiais['NOME_ARQUIVO'].tolist(), key=f"livro_v26_{v}")
                pags = cx2.text_input("Páginas:", placeholder="Ex: 10-15", key=f"pags_v26_{v}")
                ctx_ia = f"MÉTODO LIVRO: {sel_mat} PÁGINAS: {pags}."

            strat = st.text_area("Estratégia Pedagógica / Observações:", placeholder="Ex: Focar na Catarse via resolução de problemas...", key=f"strat_v26_{v}")

        # --- BOTÕES DE COMANDO ---
        cb1, cb2 = st.columns([2, 1])
        pronto = (cont_pre and obj_pre) if modo_p == "🎛️ Manual (Banco)" else (sel_mat and pags)
        
        with cb1:
            if st.button("🚀 COMPILAR PLANEJAMENTO DE ELITE", use_container_width=True, type="primary", disabled=not pronto):
                with st.spinner("Maestro SOSA redigindo rascunho PHC..."):
                    prompt = f"ANO: {ano_p}º, SEMANA: {sem_p}. {ctx_ia}. ESTRATÉGIA: {strat}."
                    st.session_state.p_temp = ai.gerar_ia("PLANE_PEDAGOGICO", prompt)
                    st.rerun()
        with cb2:
            if "p_temp" in st.session_state:
                if st.button("🗑️ DESCARTAR RASCUNHO", use_container_width=True): reset_planejamento()

        # --- ÁREA DE REFINO E VISUALIZAÇÃO ---
        if "p_temp" in st.session_state:
            st.markdown("---")
            txt_bruto = st.session_state.p_temp
            
            # Refinador Maestro
            cmd_refine = st.chat_input("Solicitar alteração técnica no plano...")
            if cmd_refine:
                with st.spinner("Reescrevendo lógica pedagógica..."):
                    prompt_refino = f"ORDEM: {cmd_refine}\n\nTEXTO ATUAL:\n{txt_bruto}"
                    st.session_state.p_temp = ai.gerar_ia("REFINADOR_PEDAGOGICO", prompt_refino)
                    st.session_state.v_plano = int(time.time())
                    st.rerun()

            t_ed, t_vis = st.tabs(["✏️ Editor de Texto", "👁️ Estrutura PIP"])
            with t_ed:
                col_ed1, col_ed2 = st.columns(2)
                ed_geral = col_ed1.text_input("Eixo:", limpar_v26(ai.extrair_tag(txt_bruto, "CONTEUDO_GERAL"), "CONTEÚDO GERAL"), key=f"ed_g_{v}")
                ed_espec = col_ed2.text_area("Conteúdos:", limpar_v26(ai.extrair_tag(txt_bruto, "CONTEUDOS_ESPECIFICOS"), "CONTEÚDOS ESPECÍFICOS"), key=f"ed_e_{v}")
                ed_objs = st.text_area("Objetivos:", limpar_v26(ai.extrair_tag(txt_bruto, "OBJETIVOS_ENSINO"), "OBJETIVOS DE ENSINO"), key=f"ed_o_{v}")
                ed_met = st.text_area("Metodologia (PHC):", limpar_v26(ai.extrair_tag(txt_bruto, "METODOLOGIA"), "METODOLOGIA"), height=300, key=f"ed_m_{v}")
                ed_ava = st.text_area("Avaliação:", limpar_v26(ai.extrair_tag(txt_bruto, "AVALIACAO"), "AVALIAÇÃO"), key=f"ed_a_{v}")
                ed_pei = st.text_area("Adaptação PEI:", limpar_v26(ai.extrair_tag(txt_bruto, "ADAPTACAO_PEI"), "ADAPTAÇÃO PEI"), key=f"ed_p_{v}")

            with t_vis:
                dados_envio = {"geral": ed_geral, "especificos": ed_espec, "objetivos": ed_objs, "metodologia": ed_met, "avaliacao": ed_ava, "pei": ed_pei}
                info_envio = {"ano": str(ano_p), "semana": sem_limpa, "trimestre": "I Trimestre", "modalidade": modo_p.upper()}
                exibir_material_estruturado(txt_bruto, f"vis_v{v}", dados_plano=dados_envio, info_aula=info_envio)

            if st.button("💾 FINALIZAR E SINCRONIZAR (UPSERT)", use_container_width=True, type="primary"):
                # Lógica Upsert: Se já existe, o sistema de salvamento do SOSA (db.salvar_no_banco) 
                # deve ser precedido pela limpeza se necessário, mas aqui garantimos o registro novo.
                final_txt = f"MARKER_CONTEUDO_GERAL {ed_geral} \nMARKER_CONTEUDOS_ESPECIFICOS {ed_espec} \nMARKER_OBJETIVOS_ENSINO {ed_objs} \nMARKER_METODOLOGIA {ed_met} \nMARKER_AVALIACAO {ed_ava} \nMARKER_ADAPTACAO_PEI {ed_pei} \nMARKER_MODALIDADE {modo_p.upper()}"
                
                if db.salvar_no_banco("DB_PLANOS", [datetime.now().strftime("%d/%m/%Y"), sem_limpa, f"{ano_p}º", "I Trimestre", "PADRÃO", final_txt]):
                    st.success("✅ Plano Sincronizado com Sucesso!"); reset_planejamento()

    # --- ABA 2: GESTÃO DE ACERVO (EDIÇÃO VIVA) ---
    with tab_hist:
        st.subheader("📂 Gestão de Acervo Pedagógico")
        if not df_planos.empty:
            f_ano_h = st.selectbox("Filtrar Série:", ["Todos", "6º", "7º", "8º", "9º"], key="hist_ano_v26")
            df_h = df_planos.copy()
            if f_ano_h != "Todos": df_h = df_h[df_h['ANO'] == f_ano_h]
            
            if not df_h.empty:
                sel_h = st.selectbox("Selecionar Plano para Refino:", df_h['SEMANA'].tolist(), key="hist_sem_v26")
                dados_h = df_h[df_h['SEMANA'] == sel_h].iloc[0]
                raw_h = dados_h['PLANO_TEXTO']
                ano_h = dados_h['ANO']
                
                st.markdown(f"### 📝 Editando: {sel_h} ({ano_h})")
                
                # Carrega o texto do histórico para o editor de rascunho para permitir refino IA
                if st.button("🔄 REABRIR PARA REFINO IA", use_container_width=True):
                    st.session_state.p_temp = raw_h
                    st.info("Plano carregado na aba 'Engenharia de Planejamento'. Você pode usar o chat de refino lá.")
                
                st.markdown("---")
                # Lógica de Exclusão com Limpeza de Drive
                if st.button("🗑️ EXCLUIR PLANO E LIMPAR DRIVE", use_container_width=True):
                    if db.excluir_registro_com_drive("DB_PLANOS", raw_h):
                        st.success("Plano e arquivos removidos."); time.sleep(1); st.rerun()
            else: st.info("Nenhum plano encontrado para este filtro.")
        else: st.info("📭 Acervo vazio.")

    # --- ABA 3 E 4 (MATRIZ E AUDITORIA - TÍTULOS TÉCNICOS) ---
    with tab_matriz:
        st.subheader("📖 Matriz Curricular Ativa")
        if not df_curriculo.empty:
            ano_c = st.selectbox("Série:", [6, 7, 8, 9], key="matriz_ano_v26")
            df_c = df_curriculo[df_curriculo['ANO'] == ano_c].copy()
            concluidos = " ".join(df_planos[df_planos['ANO'] == f"{ano_c}º"]['PLANO_TEXTO'].astype(str).tolist()).upper() if not df_planos.empty else ""
            df_c['STATUS'] = df_c['CONTEUDO_ESPECIFICO'].apply(lambda x: "✅ CONCLUÍDO" if str(x).upper() in concluidos else "⏳ PENDENTE")
            st.dataframe(df_c[['TRIMESTRE', 'EIXO', 'CONTEUDO_ESPECIFICO', 'STATUS']], use_container_width=True, hide_index=True)

    with tab_auditoria:
        st.subheader("📈 Auditoria de Cobertura Curricular")
        # (Mantém a lógica de gráficos do Mapa de Cobertura, mas com visual limpo)
        if not df_curriculo.empty:
            ano_m = st.selectbox("Analisar Série:", [6, 7, 8, 9], key="auditoria_ano_v26")
            df_m = df_curriculo[df_curriculo['ANO'] == ano_m].copy()
            planejados = " ".join(df_planos[df_planos['ANO'] == f"{ano_m}º"]['PLANO_TEXTO'].astype(str).tolist()).upper() if not df_planos.empty else ""
            df_m['STATUS_NUM'] = df_m['CONTEUDO_ESPECIFICO'].apply(lambda x: 1 if str(x).upper() in planejados else 0)
            progresso = df_m.groupby('EIXO')['STATUS_NUM'].agg(['sum', 'count']).reset_index()
            progresso['%'] = (progresso['sum'] / progresso['count'] * 100).round(1)
            st.plotly_chart(px.bar(progresso, x='EIXO', y='%', text='%', color='%', color_continuous_scale='RdYlGn', range_y=[0, 105]), use_container_width=True)
        
# ==============================================================================
# MÓDULO: DIÁRIO DE BORDO
# ==============================================================================
elif menu == "📝 Diário de Bordo Rápido":
    st.header("📝 Diário de Bordo (Grade Interativa)")
    
    if df_alunos.empty:
        st.warning("Cadastre alunos primeiro.")
    else:
        # --- SELETORES ---
        c1, c2 = st.columns(2)
        turma_sel = c1.selectbox("Turma:", sorted(df_alunos['TURMA'].unique()), key="diario_turma")
        data_sel = c2.date_input("Data da Aula:", date.today(), key="diario_data")
        data_str = data_sel.strftime("%d/%m/%Y")
        
        # --- CONTEXTO DA ATIVIDADE ---
        atividade_desc = st.text_input("Atividade do Dia (Opcional):", placeholder="Ex: Exercício pág 45, Trabalho em Grupo...")
        
        # --- LÓGICA DE CARREGAMENTO (UPSERT) ---
        alunos_turma = df_alunos[df_alunos['TURMA'] == turma_sel].sort_values(by="NOME_ALUNO")
        
        df_existente = pd.DataFrame()
        if not df_diario.empty:
            df_existente = df_diario[(df_diario['DATA'] == data_str) & (df_diario['TURMA'] == turma_sel)]
        
        dados_editor = []
        if not df_existente.empty:
            st.info(f"📂 Carregando registros salvos de {data_str}...")
            for _, aluno in alunos_turma.iterrows():
                reg = df_existente[df_existente['ID_ALUNO'].apply(db.limpar_id) == db.limpar_id(aluno['ID'])]
                
                if not reg.empty:
                    tag_salva = str(reg.iloc[0]['TAGS'])
                    dados_editor.append({
                        "ID": aluno['ID'],
                        "NOME": aluno['NOME_ALUNO'],
                        "VISTO": str(reg.iloc[0]['VISTO_ATIVIDADE']).upper() == "TRUE",
                        "TAGS": tag_salva if tag_salva else "", 
                        "OBS": reg.iloc[0]['OBSERVACOES']
                    })
                else:
                    dados_editor.append({"ID": aluno['ID'], "NOME": aluno['NOME_ALUNO'], "VISTO": True, "TAGS": "", "OBS": ""})
        else:
            for _, aluno in alunos_turma.iterrows():
                dados_editor.append({
                    "ID": aluno['ID'],
                    "NOME": aluno['NOME_ALUNO'],
                    "VISTO": True, 
                    "TAGS": "", 
                    "OBS": ""
                })
        
        df_editor = pd.DataFrame(dados_editor)
        
        # --- GRADE INTERATIVA ---
        opcoes_tags = ["", "Dormiu", "Conversa", "Se destacou", "Agitado", "Sem material", "Ausência", "Vetor Disciplinar", "Brincando"]
        
        df_editado = st.data_editor(
            df_editor,
            column_config={
                "ID": st.column_config.TextColumn("ID", disabled=True),
                "NOME": st.column_config.TextColumn("Nome", disabled=True, width="medium"),
                "VISTO": st.column_config.CheckboxColumn("Visto?", help="Entregou atividade?"),
                "TAGS": st.column_config.SelectboxColumn("Ocorrência Principal", options=opcoes_tags, width="medium", help="Selecione a principal ocorrência"),
                "OBS": st.column_config.TextColumn("Percepção Analítica", width="large")
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key="editor_diario"
        )
        
        # --- SALVAMENTO EM LOTE ---
        if st.button("💾 Salvar Diário de Bordo"):
            with st.status("Processando Diário...", expanded=True) as status:
                status.write("🧹 Limpando registros anteriores...")
                db.limpar_diario_data_turma(data_str, turma_sel)
                
                status.write("📝 Compilando dados...")
                linhas_para_salvar = []
                for _, row in df_editado.iterrows():
                    tags_str = str(row['TAGS']) if row['TAGS'] else ""
                    obs_final = row['OBS']
                    if atividade_desc:
                        obs_final = f"[{atividade_desc}] {obs_final}"
                    
                    linhas_para_salvar.append([
                        data_str,
                        row['ID'],
                        row['NOME'],
                        turma_sel,
                        str(row['VISTO']), 
                        tags_str,
                        obs_final
                    ])
                
                status.write("🚀 Enviando para o banco de dados...")
                if db.salvar_lote("DB_DIARIO_BORDO", linhas_para_salvar):
                    status.update(label="Diário Salvo com Sucesso!", state="complete", expanded=False)
                    time.sleep(1)
                    st.rerun()
                else:
                    status.update(label="Erro ao salvar.", state="error")

# ==============================================================================
# MÓDULO: PAINEL DE NOTAS
# ==============================================================================
elif menu == "📊 Painel de Notas & Vistos":
    st.header("📊 Painel de Notas & Vistos (Fórmula de Itabuna)")
    
    if df_alunos.empty:
        st.warning("Cadastre alunos primeiro.")
    else:
        # --- FILTROS ---
        c1, c2 = st.columns(2)
        turma_sel = c1.selectbox("Turma:", sorted(df_alunos['TURMA'].unique()), key="notas_turma")
        trimestre_sel = c2.selectbox("Trimestre:", ["I Trimestre", "II Trimestre", "III Trimestre"], key="notas_trim")
        
        # --- CÁLCULO DE VISTOS ---
        ano_atual = date.today().year
        if trimestre_sel == "I Trimestre":
            data_ini, data_fim = date(ano_atual, 2, 9), date(ano_atual, 5, 22)
        elif trimestre_sel == "II Trimestre":
            data_ini, data_fim = date(ano_atual, 5, 25), date(ano_atual, 9, 4)
        else:
            data_ini, data_fim = date(ano_atual, 9, 8), date(ano_atual, 12, 17)
            
        total_aulas = 0
        vistos_por_aluno = {}
        
        if not df_diario.empty:
            df_diario['DATA_DT'] = pd.to_datetime(df_diario['DATA'], format="%d/%m/%Y", errors='coerce').dt.date
            df_d_trim = df_diario[
                (df_diario['TURMA'] == turma_sel) & 
                (df_diario['DATA_DT'] >= data_ini) & 
                (df_diario['DATA_DT'] <= data_fim)
            ]
            total_aulas = df_d_trim['DATA'].nunique()
            if total_aulas > 0:
                vistos = df_d_trim[df_d_trim['VISTO_ATIVIDADE'].astype(str).str.upper() == "TRUE"]
                vistos_por_aluno = vistos['ID_ALUNO'].apply(db.limpar_id).value_counts().to_dict()

        st.info(f"📅 Período: {data_ini.strftime('%d/%m')} a {data_fim.strftime('%d/%m')} | 🏫 Aulas Dadas: {total_aulas}")

        # --- MONTAGEM DA GRADE ---
        alunos_turma = df_alunos[df_alunos['TURMA'] == turma_sel].sort_values(by="NOME_ALUNO")
        
        notas_salvas = pd.DataFrame()
        if not df_notas.empty:
            notas_salvas = df_notas[
                (df_notas['TURMA'] == turma_sel) & 
                (df_notas['TRIMESTRE'] == trimestre_sel)
            ]
        
        dados_grade = []
        
        def safe_float(val):
            try: return float(str(val).replace(',', '.'))
            except: return 0.0

        for _, aluno in alunos_turma.iterrows():
            id_limpo = db.limpar_id(aluno['ID'])
            
            qtd_vistos = vistos_por_aluno.get(id_limpo, 0)
            nota_vistos = (qtd_vistos / total_aulas * 3.0) if total_aulas > 0 else 3.0 
            if total_aulas > 0: nota_vistos = round(nota_vistos, 1)
            
            n_teste = 0.0; n_prova = 0.0; n_rec = 0.0
            
            if not notas_salvas.empty:
                reg = notas_salvas[notas_salvas['ID_ALUNO'].apply(db.limpar_id) == id_limpo]
                if not reg.empty:
                    n_teste = safe_float(reg.iloc[0].get('NOTA_TESTE', 0))
                    n_prova = safe_float(reg.iloc[0].get('NOTA_PROVA', 0))
                    n_rec = safe_float(reg.iloc[0].get('NOTA_REC', 0))
            
            if n_teste > 3.0: n_teste = n_teste / 10
            if n_prova > 4.0: n_prova = n_prova / 10
            if n_rec > 10.0: n_rec = n_rec / 10

            dados_grade.append({
                "ID": id_limpo,
                "NOME": aluno['NOME_ALUNO'],
                "VISTOS (3.0)": nota_vistos,
                "TESTE (3.0)": n_teste,
                "PROVA (4.0)": n_prova,
                "RECUPERAÇÃO (10.0)": n_rec
            })
            
        df_grade = pd.DataFrame(dados_grade)
        
        # --- EDITOR DE NOTAS ---
        df_editado = st.data_editor(
            df_grade,
            column_config={
                "ID": st.column_config.TextColumn("ID", disabled=True),
                "NOME": st.column_config.TextColumn("Nome", disabled=True, width="medium"),
                "VISTOS (3.0)": st.column_config.NumberColumn("Vistos (Auto)", disabled=True, format="%.1f", help="Calculado pelo Diário"),
                "TESTE (3.0)": st.column_config.NumberColumn("Teste", min_value=0.0, max_value=3.0, step=0.1, format="%.1f"),
                "PROVA (4.0)": st.column_config.NumberColumn("Prova", min_value=0.0, max_value=4.0, step=0.1, format="%.1f"),
                "RECUPERAÇÃO (10.0)": st.column_config.NumberColumn("Recuperação", min_value=0.0, max_value=10.0, step=0.1, format="%.1f")
            },
            hide_index=True,
            use_container_width=True,
            key="editor_notas"
        )
        
        # --- CÁLCULO FINAL ---
        if not df_editado.empty:
            df_editado['SOMA_PARCIAL'] = df_editado['VISTOS (3.0)'] + df_editado['TESTE (3.0)'] + df_editado['PROVA (4.0)']
            
            def calcular_final(row):
                if row['RECUPERAÇÃO (10.0)'] > row['SOMA_PARCIAL']:
                    return row['RECUPERAÇÃO (10.0)']
                return row['SOMA_PARCIAL']
            
            df_editado['MÉDIA FINAL'] = df_editado.apply(calcular_final, axis=1)
            
            def highlight_fail(val):
                color = '#ffcccc' if val < 6.0 else '#ccffcc'
                return f'background-color: {color}'

            st.markdown("### 📊 Pré-visualização do Boletim")
            st.dataframe(
                df_editado.style.applymap(highlight_fail, subset=['MÉDIA FINAL']).format("{:.1f}", subset=['VISTOS (3.0)', 'TESTE (3.0)', 'PROVA (4.0)', 'RECUPERAÇÃO (10.0)', 'SOMA_PARCIAL', 'MÉDIA FINAL']),
                use_container_width=True,
                hide_index=True
            )
            
            # --- DASHBOARD VISUAL ---
            aprovados = len(df_editado[df_editado['MÉDIA FINAL'] >= 6.0])
            reprovados = len(df_editado) - aprovados
            media_geral = df_editado['MÉDIA FINAL'].mean()
            
            c_chart, c_metrics = st.columns([2, 1])
            
            with c_chart:
                if len(df_editado) > 0:
                    fig = px.pie(
                        names=['Aprovados', 'Reprovados'], 
                        values=[aprovados, reprovados],
                        color=['Aprovados', 'Reprovados'],
                        color_discrete_map={'Aprovados':'#28a745', 'Reprovados':'#dc3545'},
                        hole=0.4,
                        title="Desempenho da Turma"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with c_metrics:
                st.metric("Média da Turma", f"{media_geral:.1f}")
                st.metric("Total de Alunos", len(df_editado))
                st.metric("Taxa de Aprovação", f"{(aprovados/len(df_editado)*100):.0f}%")

            # --- SALVAR ---
            if st.button("💾 Sincronizar Notas"):
                with st.status("Salvando notas...", expanded=True) as status:
                    db.limpar_notas_turma_trimestre(turma_sel, trimestre_sel)
                    
                    linhas_salvar = []
                    for _, row in df_editado.iterrows():
                        linhas_salvar.append([
                            row['ID'],
                            row['NOME'],
                            turma_sel,
                            trimestre_sel,
                            str(row['VISTOS (3.0)']).replace('.', ','),
                            str(row['TESTE (3.0)']).replace('.', ','),
                            str(row['PROVA (4.0)']).replace('.', ','),
                            str(row['RECUPERAÇÃO (10.0)']).replace('.', ','),
                            str(row['MÉDIA FINAL']).replace('.', ',')
                        ])
                    
                    if db.salvar_lote("DB_NOTAS", linhas_salvar):
                        status.update(label="Notas Salvas!", state="complete", expanded=False)
                        time.sleep(1)
                        st.rerun()
                    else:
                        status.update(label="Erro ao salvar.", state="error")

# ==============================================================================
# MÓDULO: BOLETIM ANUAL & CONSELHO (V7 - LIMPEZA AUTOMÁTICA APÓS SALVAR)
# ==============================================================================
elif menu == "📈 Boletim Anual & Conselho":
    st.header("📈 Boletim Anual & Conselho de Classe")
    
    if df_alunos.empty or df_notas.empty:
        st.warning("É necessário ter Alunos e Notas lançadas para gerar o Boletim.")
    else:
        # --- SELEÇÃO DE TURMA ---
        turmas_disponiveis = sorted(df_alunos['TURMA'].unique())
        turma_sel = st.selectbox("Selecione a Turma:", turmas_disponiveis, key="bol_turma")
        
        # --- ABAS ---
        tab_boletim, tab_conselho, tab_hist_atas = st.tabs(["📊 Visão Anual (Aprovação)", "🗣️ Relatório de Conselho (IA)", "🗂️ Histórico de Atas"])
        
        # --- ABA 1: BOLETIM ANUAL ---
        with tab_boletim:
            st.markdown("### 🧮 Fechamento do Ano Letivo")
            st.caption("Regra de Itabuna: Soma dos 3 Trimestres >= 18.0 pontos para aprovação direta.")
            
            # 1. PREPARAÇÃO DOS DADOS
            df_n_turma = df_notas[df_notas['TURMA'] == turma_sel].copy()
            
            # CORREÇÃO DE NOTAS (PRENSA HIDRÁULICA)
            def limpar_float_normalizado(x):
                try: 
                    val = float(str(x).replace(',', '.'))
                    if val > 10.0: return val / 10.0
                    return val
                except: return 0.0
            
            df_n_turma['MEDIA_FINAL'] = df_n_turma['MEDIA_FINAL'].apply(limpar_float_normalizado)
            
            if not df_n_turma.empty:
                pivot = df_n_turma.pivot_table(
                    index=["ID_ALUNO", "NOME_ALUNO"], 
                    columns="TRIMESTRE", 
                    values="MEDIA_FINAL", 
                    aggfunc='first'
                ).reset_index()
                
                for col in ["I Trimestre", "II Trimestre", "III Trimestre"]:
                    if col not in pivot.columns: pivot[col] = 0.0
                    pivot[col] = pivot[col].fillna(0.0)

                if "REC_FINAL" not in pivot.columns: 
                    pivot["REC_FINAL"] = -1.0
                else:
                    pivot["REC_FINAL"] = pivot["REC_FINAL"].fillna(-1.0)
                
                # 2. CÁLCULOS
                pivot['SOMA_ANUAL'] = pivot['I Trimestre'] + pivot['II Trimestre'] + pivot['III Trimestre']
                
                def definir_situacao(row):
                    if row['SOMA_ANUAL'] >= 18.0:
                        return "✅ APROVADO"
                    elif row['REC_FINAL'] != -1.0:
                        if row['REC_FINAL'] >= 5.0: return "✅ APROVADO (REC)"
                        else: return "❌ REPROVADO"
                    else:
                        return "⚠️ RECUPERAÇÃO FINAL"

                pivot['SITUAÇÃO'] = pivot.apply(definir_situacao, axis=1)
                
                # 3. VISUALIZAÇÃO
                df_view = pivot.copy()
                df_view['REC_FINAL'] = df_view['REC_FINAL'].replace(-1.0, None)
                
                st.dataframe(
                    df_view[['NOME_ALUNO', 'I Trimestre', 'II Trimestre', 'III Trimestre', 'SOMA_ANUAL', 'REC_FINAL', 'SITUAÇÃO']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "I Trimestre": st.column_config.NumberColumn("I Trim", format="%.1f"),
                        "II Trimestre": st.column_config.NumberColumn("II Trim", format="%.1f"),
                        "III Trimestre": st.column_config.NumberColumn("III Trim", format="%.1f"),
                        "SOMA_ANUAL": st.column_config.NumberColumn("Soma (Meta 18.0)", format="%.1f"),
                        "REC_FINAL": st.column_config.NumberColumn("Nota Rec. Final", format="%.1f"),
                        "SITUAÇÃO": st.column_config.TextColumn("Status", width="medium")
                    }
                )
                
                # 4. LANÇAMENTO DE RECUPERAÇÃO FINAL
                st.markdown("---")
                st.subheader("📝 Lançar ou Editar Recuperação Final")
                
                c_rec1, c_rec2 = st.columns([2, 1])
                lista_alunos = pivot['NOME_ALUNO'].tolist()
                aluno_rec_sel = c_rec1.selectbox("Selecione o Aluno:", lista_alunos)
                
                nota_atual_raw = pivot.loc[pivot['NOME_ALUNO'] == aluno_rec_sel, 'REC_FINAL'].values[0]
                valor_input = 0.0 if nota_atual_raw == -1.0 else float(nota_atual_raw)
                
                nota_rec = c_rec2.number_input("Nota da Prova Final:", 0.0, 10.0, valor_input, step=0.1)
                
                if st.button("💾 Salvar/Atualizar Nota Final"):
                    id_rec = pivot[pivot['NOME_ALUNO'] == aluno_rec_sel].iloc[0]['ID_ALUNO']
                    if db.salvar_rec_final(id_rec, aluno_rec_sel, turma_sel, nota_rec):
                        st.success(f"Nota de {aluno_rec_sel} atualizada para {nota_rec}!")
                        time.sleep(1)
                        st.rerun()
            else:
                st.info("Nenhuma nota lançada para esta turma ainda.")

        # --- ABA 2: RELATÓRIO DE CONSELHO ---
        with tab_conselho:
            st.markdown("### 🗣️ Gerador de Ata de Conselho")
            st.info("A IA analisará o Diário (comportamento) e as Notas para gerar um relatório completo da turma.")
            
            trimestre_cons = st.selectbox("Referência:", ["I Trimestre", "II Trimestre", "III Trimestre", "ANUAL (Final)"], key="cons_trim")
            
            if st.button("🚀 Gerar Relatório da Turma"):
                with st.spinner(f"Analisando dados do {trimestre_cons} para a turma {turma_sel}..."):
                    
                    # 1. COLETAR DADOS
                    notas_texto = ""
                    if not df_notas.empty:
                        df_n_t = df_notas[(df_notas['TURMA'] == turma_sel) & (df_notas['TRIMESTRE'] == trimestre_cons)]
                        if not df_n_t.empty:
                            df_n_t['MEDIA_FINAL'] = df_n_t['MEDIA_FINAL'].apply(limpar_float_normalizado)
                            reprovados = df_n_t[df_n_t['MEDIA_FINAL'] < 6.0]['NOME_ALUNO'].tolist()
                            media_turma = df_n_t['MEDIA_FINAL'].mean()
                            notas_texto = f"MÉDIA DA TURMA: {media_turma:.1f}. ALUNOS COM NOTA VERMELHA (<6.0): {', '.join(reprovados)}."
                        else:
                            notas_texto = "Sem notas fechadas para este trimestre."
                    
                    diario_texto = ""
                    if not df_diario.empty:
                        df_d_t = df_diario[df_diario['TURMA'] == turma_sel]
                        sem_tarefa = df_d_t[df_d_t['TAGS'].str.contains("Sem material|Não fez", case=False, na=False)]['NOME_ALUNO'].value_counts().to_dict()
                        indisciplina = df_d_t[df_d_t['TAGS'].str.contains("Conversa|Agitado|Vetor", case=False, na=False)]['NOME_ALUNO'].value_counts().to_dict()
                        diario_texto = f"ALUNOS QUE NÃO FAZEM TAREFA (Qtd): {sem_tarefa}. ALUNOS COM INDISCIPLINA (Qtd): {indisciplina}."

                    # 2. PROMPT
                    prompt_conselho = (
                        f"VOCÊ É UM COORDENADOR PEDAGÓGICO EXPERIENTE.\n"
                        f"OBJETIVO: Escrever a ATA DE CONSELHO DE CLASSE para a Turma {turma_sel}, {trimestre_cons}.\n\n"
                        f"DADOS BRUTOS:\n"
                        f"{notas_texto}\n"
                        f"{diario_texto}\n\n"
                        f"ESTRUTURA DO RELATÓRIO:\n"
                        f"1. VISÃO GERAL: Como está o rendimento e comportamento da turma?\n"
                        f"2. PONTOS DE ATENÇÃO ACADÊMICA: Cite os alunos com dificuldade (notas baixas) e sugira intervenções.\n"
                        f"3. PONTOS DE ATENÇÃO COMPORTAMENTAL: Cite os alunos que não fazem tarefa ou conversam muito.\n"
                        f"4. DESTAQUES POSITIVOS: Elogie a turma se a média for boa.\n"
                        f"5. PROGNÓSTICO: Qual a probabilidade de recuperação final se continuar assim?\n\n"
                        f"Tom: Profissional, analítico e propositivo."
                    )
                    
                    relatorio_gerado = ai.gerar_ia("PLANE_PEDAGOGICO", prompt_conselho)
                    st.session_state.relatorio_conselho = relatorio_gerado
            
            if "relatorio_conselho" in st.session_state:
                st.text_area("📄 Relatório Gerado:", st.session_state.relatorio_conselho, height=500)
                
                # BOTÃO COM LIMPEZA AUTOMÁTICA
                if st.button("💾 Arquivar Relatório (Substituir Anterior)"):
                    sucesso = db.salvar_ata_conselho(
                        datetime.now().strftime("%d/%m/%Y"), 
                        turma_sel, 
                        f"CONSELHO_{trimestre_cons}", 
                        st.session_state.relatorio_conselho
                    )
                    if sucesso:
                        st.success("Relatório arquivado com sucesso! (Limpando tela...)")
                        # Limpa a variável da memória
                        del st.session_state.relatorio_conselho
                        # Espera 1.5s para você ler a mensagem
                        time.sleep(1.5)
                        # Recarrega a página
                        st.rerun()

        # --- ABA 3: HISTÓRICO DE ATAS ---
        with tab_hist_atas:
            st.markdown(f"### 🗂️ Arquivo de Atas - {turma_sel}")
            
            if not df_relatorios.empty:
                df_atas = df_relatorios[
                    (df_relatorios['ID_ALUNO'] == "TURMA") & 
                    (df_relatorios['NOME_ALUNO'] == turma_sel) &
                    (df_relatorios['TIPO'].str.contains("CONSELHO", na=False))
                ]
                
                if not df_atas.empty:
                    df_atas = df_atas.iloc[::-1]
                    for _, row in df_atas.iterrows():
                        titulo = f"{row['DATA']} - {row['TIPO']}"
                        with st.expander(titulo):
                            st.markdown(row['CONTEUDO'])
                else:
                    st.info(f"Nenhuma ata encontrada para a turma {turma_sel}.")
            else:
                st.info("Banco de relatórios vazio.")

# ==============================================================================
# MÓDULO: GESTÃO DA TURMA (COM EDIÇÃO)
# ==============================================================================
elif menu == "👥 Gestão da Turma":
    st.header("👥 Gestão de Turmas e Alunos")
    
    t1, t2, t3, t4 = st.tabs(["🏗️ Criar Turma", "➕ Povoar Alunos", "👁️ Ver Lista", "✏️ Editar Dados"])
    
    with t1:
        with st.form("f_t_new"):
            c1, c2, c3 = st.columns(3)
            a = c1.selectbox("Ano:", [6,7,8,9]); l = c2.selectbox("Letra:", ["A","B","C","D","E","F"]); u = c3.selectbox("Turno:", ["Matutino", "Vespertino"])
            sigla = f"{a}ª {'M' if u=='Matutino' else 'V'}{l}"
            if st.form_submit_button("Criar Turma"):
                db.salvar_no_banco("DB_TURMAS", [sigla, f"{a}º Ano {l}", "Seg/Qui"])
                st.success(f"Turma {sigla} criada!")
    
    with t2:
        if not df_turmas.empty:
            t_dest = st.selectbox("Para qual turma?", df_turmas['ID_TURMA'].tolist())
            metodo = st.radio("Método:", ["Individual", "CSV (Upload)", "IA (PDF)"], horizontal=True)
            if metodo == "Individual":
                with st.form("f_ind_aluno", clear_on_submit=True):
                    nome_a = st.text_input("Nome Completo:").upper()
                    nec_a = st.text_input("Necessidades:", value="NENHUMA").upper()
                    if st.form_submit_button("💾 Salvar"):
                        if nome_a:
                            id_a = db.gerar_proximo_id(df_alunos)
                            db.salvar_no_banco("DB_ALUNOS", [id_a, nome_a, t_dest, "ATIVO", nec_a, "MANUAL"])
                            st.success("Cadastrado!"); st.rerun()
            elif metodo == "CSV (Upload)":
                f_csv = st.file_uploader("CSV", type=["csv"])
                if f_csv and st.button("Processar"):
                    df_up = pd.read_csv(f_csv)
                    id_base = db.gerar_proximo_id(df_alunos)
                    for idx, r in df_up.iterrows():
                        db.salvar_no_banco("DB_ALUNOS", [id_base+idx, str(r['NOME']).upper(), t_dest, "ATIVO", "NENHUMA", "CSV"])
                    st.success("Importado!"); st.rerun()
            elif metodo == "IA (PDF)":
                txt_pdf = st.text_area("Cole o texto do PDF aqui:")
                if st.button("🤖 Maestro, Extrair Nomes"):
                    res = ai.gerar_ia("MAESTRO", f"Extraia apenas os nomes em caixa alta deste texto: {txt_pdf}")
                    st.session_state.ia_res = res.upper()
                if "ia_res" in st.session_state:
                    st.code(st.session_state.ia_res)
                    if st.button("💾 Confirmar e Salvar"):
                        id_base = db.gerar_proximo_id(df_alunos)
                        for idx, nome in enumerate(st.session_state.ia_res.split('\n')):
                            if nome.strip(): db.salvar_no_banco("DB_ALUNOS", [id_base+idx, nome.strip(), t_dest, "ATIVO", "PENDENTE", "IA"])
                        st.success("Salvos!"); del st.session_state.ia_res; st.rerun()
    
    with t3:
        if not df_alunos.empty:
            t_f = st.selectbox("Filtrar Turma:", sorted(df_alunos['TURMA'].unique()))
            st.dataframe(df_alunos[df_alunos['TURMA']==t_f].sort_values(by="NOME_ALUNO"), use_container_width=True, hide_index=True)

    # --- ABA 4: EDITAR DADOS ---
    with t4:
        st.subheader("✏️ Atualizar Cadastro (CID/Necessidades)")
        if df_alunos.empty:
            st.warning("Sem alunos cadastrados.")
        else:
            c_sel1, c_sel2 = st.columns(2)
            turma_edit = c_sel1.selectbox("Turma:", sorted(df_alunos['TURMA'].unique()), key="edit_turma")
            
            alunos_da_turma = df_alunos[df_alunos['TURMA'] == turma_edit].sort_values(by="NOME_ALUNO")
            aluno_edit_nome = c_sel2.selectbox("Aluno:", alunos_da_turma['NOME_ALUNO'].tolist(), key="edit_aluno")
            
            dados_atuais = alunos_da_turma[alunos_da_turma['NOME_ALUNO'] == aluno_edit_nome].iloc[0]
            id_atual = dados_atuais['ID']
            nec_atual = dados_atuais['NECESSIDADES']
            
            st.info(f"🆔 ID: {id_atual} | 🏥 Cadastro Atual: {nec_atual}")
            
            nova_nec = st.text_input("Nova Necessidade / CID (Digite para atualizar):", value=nec_atual)
            
            if st.button("💾 Atualizar Cadastro"):
                if nova_nec != nec_atual:
                    with st.spinner("Atualizando banco de dados..."):
                        if db.atualizar_necessidade_aluno(id_atual, nova_nec):
                            st.success(f"Sucesso! {aluno_edit_nome} agora consta como: {nova_nec}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar.")
                else:
                    st.warning("Nenhuma alteração feita.")

# ==============================================================================
# MÓDULO: BASE DE CONHECIMENTO
# ==============================================================================
elif menu == "📚 Base de Conhecimento":
    st.header("📚 Central de Inteligência SOSA")
    tab_upload, tab_biblioteca = st.tabs(["📤 Upload", "📖 Biblioteca"])
    with tab_upload:
        with st.form("form_upload"):
            tipo_doc = st.selectbox("Categoria:", ["Livro Didático - 6º Ano", "Livro Didático - 7º Ano", "Livro Didático - 8º Ano", "Livro Didático - 9º Ano", "Referencial Pedagógico (Prefeitura)", "Documento PEI / AEE", "Outros"])
            nome_arq = st.text_input("Nome do Arquivo")
            uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])
            if st.form_submit_button("🚀 Salvar"):
                if uploaded_file and nome_arq:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    uri = ai.subir_para_google(temp_path, nome_arq)
                    db.salvar_no_banco("DB_MATERIAIS", [datetime.now().strftime("%d/%m/%Y"), nome_arq, uri, tipo_doc])
                    st.success("Catalogado!"); os.remove(temp_path); st.rerun()
    with tab_biblioteca:
        st.dataframe(df_materiais, use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO: RELATÓRIOS PEI
# ==============================================================================
elif menu == "♿ Relatórios PEI / Perfil IA":
    st.header("♿ Analista Clínico-Pedagógico (PEI)")
    
    if df_alunos.empty:
        st.warning("Cadastre alunos primeiro.")
    else:
        filtro_nome = st.text_input("🔍 Buscar Aluno por Nome:", placeholder="Digite para filtrar...")
        
        c_t, c_a = st.columns(2)
        turma_pei = c_t.selectbox("Selecione a Turma:", sorted(df_alunos['TURMA'].unique()), key="pei_turma")
        
        df_a_pei = df_alunos[df_alunos['TURMA'] == turma_pei]
        if filtro_nome:
            df_a_pei = df_a_pei[df_a_pei['NOME_ALUNO'].str.contains(filtro_nome, case=False)]
        
        if not df_a_pei.empty:
            aluno_id_nome = c_a.selectbox("Selecione o Aluno:", df_a_pei['NOME_ALUNO'].tolist(), key="pei_aluno")
            dados_aluno = df_a_pei[df_a_pei['NOME_ALUNO'] == aluno_id_nome].iloc[0]
            id_aluno = db.limpar_id(dados_aluno['ID']) 
            cid_aluno = dados_aluno.get('NECESSIDADES', 'NENHUMA')
            
            st.info(f"👤 **Aluno:** {aluno_id_nome} | 🆔 **ID:** {id_aluno} | 🏥 **Necessidades/CID:** {cid_aluno}")
            
            tab_tec, tab_zap, tab_doc_oficial, tab_plano_trimestral, tab_hist_pei = st.tabs(["📈 Evolução Técnica", "📱 WhatsApp/Pais", "📄 Documento Oficial (Capa)", "📅 Plano Trimestral (Currículo Adaptado)", "🗂️ Histórico Salvo"])
            
            evidencias_txt = "Sem registros recentes no diário."
            if not df_diario.empty and 'ID_ALUNO' in df_diario.columns:
                d_aluno = df_diario[df_diario['NOME_ALUNO'] == aluno_id_nome]
                if not d_aluno.empty:
                    ultimos = d_aluno.tail(5)
                    evidencias_txt = "\n".join([f"- {row['DATA']}: {row.get('TAGS', '')} ({row.get('OBSERVACOES', '')})" for _, row in ultimos.iterrows()])

            ultimo_relatorio = "Primeiro relatório do ano."
            historico_existente = False
            if not df_relatorios.empty:
                r_aluno = df_relatorios[df_relatorios['ID_ALUNO'].apply(db.limpar_id) == str(id_aluno)]
                if not r_aluno.empty:
                    ultimo_relatorio = r_aluno.iloc[-1]['CONTEUDO']
                    historico_existente = True

            with tab_tec:
                st.markdown("### 🧠 Gerador de Relatório Técnico (Ponto ID)")
                percepcao = st.text_area("Sua percepção atual (O que você viu essa semana?):", placeholder="Ex: Melhorou na cópia, mas agrediu o colega...")
                
                hoje_str = datetime.now().strftime("%d/%m/%Y")
                ja_salvou_hoje = False
                if not df_relatorios.empty:
                    check_hoje = df_relatorios[(df_relatorios['ID_ALUNO'].apply(db.limpar_id) == str(id_aluno)) & (df_relatorios['DATA'] == hoje_str)]
                    if not check_hoje.empty:
                        st.warning(f"⚠️ Já existe um relatório salvo hoje ({hoje_str}). Se salvar novamente, será criado um novo registro.")
                        ja_salvou_hoje = True

                if st.button("🧠 Gerar Análise Evolutiva"):
                    with st.spinner("O Especialista está analisando a evolução..."):
                        instrucao_extra = ""
                        if historico_existente:
                            instrucao_extra = "IMPORTANTE: Este é um relatório de ACOMPANHAMENTO. Compare com o 'Histórico Anterior'. O aluno evoluiu? Regrediu? Manteve-se estável? Cite as mudanças."
                        
                        prompt_pei = (
                            f"ALUNO: {aluno_id_nome}. CID/NECESSIDADES: {cid_aluno}.\n"
                            f"HISTÓRICO ANTERIOR: {ultimo_relatorio}\n"
                            f"EVIDÊNCIAS DO DIÁRIO (Últimos dias): {evidencias_txt}\n"
                            f"PERCEPÇÃO ATUAL DO PROFESSOR: {percepcao}\n\n"
                            f"AÇÃO: Escreva um RELATÓRIO DE EVOLUÇÃO para o sistema escolar.\n"
                            f"{instrucao_extra}\n"
                            f"REGRAS: Texto corrido, SEM MARKDOWN, SEM NEGRITO. Linguagem técnica mas acessível. "
                            f"Se tiver CID, correlacione. Se não, aponte barreiras. Cite evidências."
                        )
                        st.session_state.res_pei_tec = ai.gerar_ia("ESPECIALISTA_INCLUSAO", prompt_pei)
                
                if "res_pei_tec" in st.session_state:
                    st.info("🤖 **Refinamento:** O Especialista está ouvindo. Peça ajustes abaixo se necessário.")
                    ajuste_pei = st.chat_input("Ex: 'Seja mais breve', 'Cite que ele melhorou na leitura'...")
                    
                    if ajuste_pei:
                        with st.spinner("Reescrevendo..."):
                            prompt_refino = f"TEXTO ATUAL: {st.session_state.res_pei_tec}. AJUSTE SOLICITADO: {ajuste_pei}. Mantenha o tom técnico."
                            st.session_state.res_pei_tec = ai.gerar_ia("ESPECIALISTA_INCLUSAO", prompt_refino)
                            st.rerun()

                    txt_editavel = st.text_area("Texto Gerado (Editável):", st.session_state.res_pei_tec, height=300)
                    if st.button("💾 Salvar Evolução no Banco"):
                        db.salvar_no_banco("DB_RELATORIOS", [
                            hoje_str, 
                            id_aluno, 
                            aluno_id_nome, 
                            "EVOLUCAO_TECNICA", 
                            txt_editavel
                        ])
                        st.success("Relatório salvo com sucesso!"); del st.session_state.res_pei_tec; time.sleep(1); st.rerun()

            with tab_zap:
                st.markdown("### 📱 Comunicado para Família/Coordenação")
                solicitacao = st.text_input("Motivo do contato:", placeholder="Ex: Reunião de pais, Elogio, Alerta de comportamento")
                
                if st.button("🚀 Gerar Mensagem Curta"):
                    base_texto = st.session_state.get("res_pei_tec", ultimo_relatorio)
                    prompt_zap = (
                        f"Baseado neste relatório técnico: '{base_texto}'.\n"
                        f"Crie uma mensagem de WhatsApp para os pais. MOTIVO: {solicitacao}.\n"
                        f"Tom: Empático, parceiro, direto. Use emojis moderados. Resuma os pontos chaves."
                    )
                    st.session_state.res_pei_zap = ai.gerar_ia("ESPECIALISTA_INCLUSAO", prompt_zap)
                
                if "res_pei_zap" in st.session_state:
                    st.text_area("Copie para o WhatsApp:", st.session_state.res_pei_zap, height=200)

            with tab_doc_oficial:
                st.markdown("### 📄 Capa do PEI (Plano de Acessibilidade Curricular)")
                st.info("Preencha os dados complementares para gerar o documento oficial.")
                
                c1, c2 = st.columns(2)
                data_nasc = c1.date_input("Data de Nascimento:", value=date(2013, 1, 1))
                nome_mae = c2.text_input("Nome da Mãe/Responsável:")
                
                if st.button("📄 Gerar Plano de Acessibilidade (Capa)"):
                    with st.spinner("Consultando Diário de Bordo e gerando perfil técnico..."):
                        prompt_capa = (
                            f"ALUNO: {aluno_id_nome}. IDADE: {date.today().year - data_nasc.year} anos.\n"
                            f"DIAGNÓSTICO/CID: {cid_aluno}.\n"
                            f"EVIDÊNCIAS COMPORTAMENTAIS (DIÁRIO): {evidencias_txt}\n"
                            f"OBJETIVO: Redigir a 'Seção 1 - Plano de Acessibilidade Curricular' do PEI.\n"
                            f"Gere o texto técnico dividido EXATAMENTE nos 4 tópicos: Habilidades Sociais, Comunicativas, Emocionais e Funcionais."
                        )
                        st.session_state.res_capa_pei = ai.gerar_ia("ESPECIALISTA_PEI", prompt_capa)
                
                if "res_capa_pei" in st.session_state:
                    st.text_area("Texto do Documento Oficial:", st.session_state.res_capa_pei, height=400)
                    if st.button("💾 Salvar Capa do PEI"):
                        db.salvar_no_banco("DB_RELATORIOS", [
                            datetime.now().strftime("%d/%m/%Y"), 
                            id_aluno, 
                            aluno_id_nome, 
                            "PEI_CAPA_OFICIAL", 
                            st.session_state.res_capa_pei
                        ])
                        st.success("Documento salvo!"); del st.session_state.res_capa_pei; time.sleep(1); st.rerun()

            with tab_plano_trimestral:
                st.markdown("### 📅 Plano Trimestral (Currículo Adaptado)")
                
                trimestre_sel = st.selectbox("Selecione o Trimestre:", ["I", "II", "III"], key="pei_trimestre")
                
                perfil_aluno = "Perfil não encontrado. Usando apenas CID."
                if not df_relatorios.empty:
                    r_capa = df_relatorios[
                        (df_relatorios['ID_ALUNO'].apply(db.limpar_id) == str(id_aluno)) & 
                        (df_relatorios['TIPO'] == "PEI_CAPA_OFICIAL")
                    ]
                    if not r_capa.empty:
                        perfil_aluno = r_capa.iloc[-1]['CONTEUDO']
                        st.success("✅ Perfil do Aluno (Capa) carregado com sucesso.")
                    else:
                        st.warning("⚠️ Capa do PEI não encontrada. Gere-a na aba anterior para um resultado melhor.")

                curriculo_texto = "Currículo não encontrado."
                if not df_curriculo.empty:
                    ano_aluno = "".join(filter(str.isdigit, turma_pei))
                    if ano_aluno:
                        df_curr_trim = df_curriculo[
                            (df_curriculo['ANO'] == int(ano_aluno)) & 
                            (df_curriculo['TRIMESTRE'] == trimestre_sel)
                        ]
                        if not df_curr_trim.empty:
                            curriculo_texto = "\n".join(df_curr_trim['CONTEUDO_ESPECIFICO'].tolist())
                            st.info(f"📚 Currículo do {ano_aluno}º Ano ({trimestre_sel} Trimestre) carregado.")
                        else:
                            st.error("Currículo vazio para este ano/trimestre.")
                    else:
                        st.error("Não foi possível identificar o ano da turma.")

                if st.button("🚀 Gerar Plano Adaptado"):
                    with st.spinner("O Especialista está adaptando o currículo..."):
                        prompt_adaptacao = (
                            f"ALUNO: {aluno_id_nome}. CID: {cid_aluno}.\n"
                            f"PERFIL DE APRENDIZAGEM (CAPA): {perfil_aluno}\n"
                            f"CURRÍCULO REGULAR DO TRIMESTRE: {curriculo_texto}\n"
                            f"OBJETIVO: Criar a tabela de 'Currículo Adaptado' para o PEI.\n"
                            f"Gere o texto estruturado com: CONTEÚDO, OBJETIVO ADAPTADO, FUNÇÕES PSÍQUICAS e MATERIAIS."
                        )
                        st.session_state.res_plano_trim = ai.gerar_ia("ESPECIALISTA_ADAPTACAO", prompt_adaptacao)

                if "res_plano_trim" in st.session_state:
                    st.text_area("Plano Trimestral Adaptado:", st.session_state.res_plano_trim, height=500)
                    if st.button("💾 Salvar Plano Trimestral"):
                        db.salvar_no_banco("DB_RELATORIOS", [
                            datetime.now().strftime("%d/%m/%Y"), 
                            id_aluno, 
                            aluno_id_nome, 
                            f"PEI_PLANO_TRIMESTRAL_{trimestre_sel}", 
                            st.session_state.res_plano_trim
                        ])
                        st.success("Plano Trimestral salvo!"); del st.session_state.res_plano_trim; time.sleep(1); st.rerun()

            with tab_hist_pei:
                st.markdown("### 🗂️ Arquivo Morto (Mais recente primeiro)")
                if not df_relatorios.empty:
                    hist_aluno = df_relatorios[df_relatorios['ID_ALUNO'].apply(db.limpar_id) == str(id_aluno)]
                    if not hist_aluno.empty:
                        hist_aluno = hist_aluno.iloc[::-1]
                        for _, row in hist_aluno.iterrows():
                            tipo_exibicao = row.get('TIPO', row.get('TURMA', 'REGISTRO'))
                            with st.expander(f"{row['DATA']} - {tipo_exibicao}"):
                                st.write(row['CONTEUDO'])
                    else:
                        st.info("Nenhum histórico para este aluno.")
                else:
                    st.info("Banco de relatórios vazio.")

# ==============================================================================
# MÓDULO: CENTRAL DE AVALIAÇÕES DE ELITE V25.98 (CORREÇÃO DE SYNC E TAGS)
# ==============================================================================
elif menu == "📝 Central de Avaliações":
    st.title("📝 Central de Avaliações de Elite (V25)")
    st.markdown("---")

    if "v_av" not in st.session_state: st.session_state.v_av = 1
    v = st.session_state.v_av

    tab_criar, tab_gaveta, tab_cronograma = st.tabs(["🚀 CRIAR AVALIAÇÃO", "🗂️ GAVETA DE EXAMES", "📅 CRONOGRAMA POR TURMA"])

    with tab_criar:
        itens_cont, itens_obj = [], []
        semanas_sel = []

        with st.container(border=True):
            st.markdown("### ⚙️ 1. Configuração do Exame")
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
            tipo_av = c1.selectbox("Tipo de Exame:", ["Teste (3.0)", "Prova (4.0)", "Recuperação (10.0)"], key=f"av_tipo_{v}")
            ano_av = c2.selectbox("Série/Ano:", [6, 7, 8, 9], key=f"av_ano_{v}")
            qtd_q = c3.number_input("Nº de Questões:", 5, 20, 10, key=f"av_qtd_{v}")
            nivel_desafio = c4.select_slider("Rigor Pedagógico:", options=["Fácil", "Médio", "Difícil"], value="Médio", key=f"av_rigor_{v}")

        st.markdown(" ")
        with st.container(border=True):
            st.markdown("### 🎯 2. Matriz de Referência (PIP)")
            df_p_ano = df_planos[df_planos['ANO'] == f"{ano_av}º"]
            if not df_p_ano.empty:
                semanas_sel = st.multiselect("Selecione as Semanas Base:", df_p_ano['SEMANA'].tolist(), key=f"av_sem_{v}")
                if semanas_sel:
                    planos_filtrados = df_p_ano[df_p_ano['SEMANA'].isin(semanas_sel)]
                    lista_cont, lista_obj = [], []
                    for _, row in planos_filtrados.iterrows():
                        c_raw = ai.extrair_tag(row['PLANO_TEXTO'], "CONTEUDOS_ESPECIFICOS")
                        o_raw = ai.extrair_tag(row['PLANO_TEXTO'], "OBJETIVOS_ENSINO")
                        lista_cont.extend([x.strip() for x in c_raw.split(';') if x.strip()])
                        lista_obj.extend([x.strip() for x in o_raw.split(';') if x.strip()])
                    col_f1, col_f2 = st.columns(2)
                    itens_cont = col_f1.multiselect("Conteúdos:", list(set(lista_cont)), default=list(set(lista_cont)), key=f"av_c_final_{v}")
                    itens_obj = col_f2.multiselect("Objetivos:", list(set(lista_obj)), default=list(set(lista_obj)), key=f"av_o_final_{v}")

        if st.button("🚀 COMPILAR AVALIAÇÃO", use_container_width=True, type="primary", key=f"btn_comp_{v}"):
            with st.status("Maestro Arquiteto processando Matriz...", expanded=True):
                planos_filtrados = df_p_ano[df_p_ano['SEMANA'].isin(semanas_sel)]
                contexto_planos = "\n".join(planos_filtrados['PLANO_TEXTO'].tolist())
                prompt_av = (f"🚨 CONTEXTO: {contexto_planos}\nTIPO: {tipo_av}. SÉRIE: {ano_av}º ANO. QTD: {qtd_q}.\n"
                             f"CONTEÚDOS: {itens_cont}\nOBJETIVOS: {itens_obj}\n"
                             f"ORDEM: Gere com [ORIENTACOES], [QUESTOES], [GABARITO_TEXTO] e [RESPOSTAS_IA].")
                st.session_state.temp_prova = ai.gerar_ia("ARQUITETO_EXAMES_V25", prompt_av)
                st.rerun()

        if "temp_prova" in st.session_state:
            st.markdown("---")
            comando_refine = st.chat_input("Refinar prova...")
            if comando_refine:
                with st.spinner("Reescrevendo..."):
                    st.session_state.temp_prova = ai.gerar_ia("REFINADOR_EXAMES", f"ORDEM: {comando_refine}\n\nATUAL:\n{st.session_state.temp_prova}")
                    st.session_state.v_av += 1
                    st.rerun()
            
            t_ed, t_gab, t_sync = st.tabs(["📝 EDIÇÃO", "✅ GABARITO", "☁️ SYNC DRIVE"])
            with t_ed: st.text_area("Texto:", value=st.session_state.temp_prova, height=450, key=f"area_av_{v}")
            with t_gab:
                st.markdown("#### 🎯 Respostas")
                st.code(ai.extrair_tag(st.session_state.temp_prova, "GABARITO_TEXTO"))
                with st.expander("Ver Justificativas Técnicas", expanded=True):
                    st.write(ai.extrair_tag(st.session_state.temp_prova, "RESPOSTAS_IA"))
            
            with t_sync:
                c_s1, c_s2 = st.columns(2)
                trimestre_av = c_s1.selectbox("Trimestre:", ["I Trimestre", "II Trimestre", "III Trimestre"], key=f"trim_av_{v}")
                nome_arq = c_s2.text_input("Nome do Arquivo:", f"PROVA_{ano_av}ANO_{tipo_av.split(' ')[0]}", key=f"name_av_{v}")
                
                if st.button("☁️ SALVAR NO DRIVE E GAVETA", use_container_width=True, type="primary", key=f"sync_btn_{v}"):
                    with st.status("Iniciando Sincronia de Elite...", expanded=True) as status:
                        # 1. Geração do Documento
                        info_doc = {"ano": f"{ano_av}º", "tipo_prova": tipo_av.upper(), "valor": "10", "qtd_questoes": qtd_q, "trimestre": trimestre_av}
                        doc_io = exporter.gerar_docx_prova_v25(nome_arq, st.session_state.temp_prova, info_doc)
                        
                        # 2. LÓGICA DE LIMPEZA (UPSERT)
                        status.write("🧹 Removendo versões obsoletas do Drive...")
                        identificador = f"{tipo_av} - {ano_av}º Ano"
                        filtro_antigo = df_aulas[(df_aulas['SEMANA_REF'] == "AVALIAÇÃO") & (df_aulas['TIPO_MATERIAL'] == identificador)]
                        for _, row_antiga in filtro_antigo.iterrows():
                            db.excluir_registro_com_drive("DB_AULAS_PRONTAS", row_antiga['CONTEUDO'])
                        
                        # 3. Upload para o Drive (Hierarquia: Avaliacoes > Ano > Trimestre)
                        status.write("📤 Enviando para o Google Drive...")
                        link = db.subir_e_converter_para_google_docs(
                            doc_io, nome_arq, trimestre=trimestre_av, categoria=f"{ano_av}º Ano", semana="AVALIAÇÃO", modo="AVALIACAO"
                        )
                        
                        if "https" in str(link):
                            # 4. Salva no Banco
                            conteudo_banco = f"[GABARITO]\n{ai.extrair_tag(st.session_state.temp_prova, 'GABARITO_TEXTO')}\n\n--- LINK DRIVE ---\n{link}"
                            db.salvar_no_banco("DB_AULAS_PRONTAS", [datetime.now().strftime("%d/%m/%Y"), "AVALIAÇÃO", identificador, conteudo_banco, f"{ano_av}º", link])
                            status.update(label="✅ Sincronizado com Sucesso!", state="complete")
                            st.balloons()
                        else:
                            status.update(label="❌ Erro na Ponte Google.", state="error")
                            st.error(link)

    # --- ABA 2: GAVETA (MANTIDA) ---
    with tab_gaveta:
        st.subheader("🗂️ Avaliações Prontas")
        df_exames = df_aulas[df_aulas['SEMANA_REF'] == "AVALIAÇÃO"].iloc[::-1]
        if df_exames.empty: st.info("Nenhuma prova gerada.")
        else:
            for _, row in df_exames.iterrows():
                with st.container(border=True):
                    c_h1, c_h2, c_h3 = st.columns([2.5, 1, 1])
                    c_h1.markdown(f"**{row['TIPO_MATERIAL']}**")
                    c_h1.caption(f"📅 {row['DATA']}")
                    
                    # Busca link no conteúdo se a coluna estiver vazia
                    link_f = row.get('LINK_DRIVE', "")
                    if not link_f:
                        import re
                        match = re.search(r"--- LINK DRIVE ---\n(https://.*)", str(row['CONTEUDO']))
                        link_f = match.group(1) if match else ""

                    if link_f: c_h2.link_button("📂 ABRIR", str(link_f), use_container_width=True)
                    if c_h3.button("🗑️ Excluir", key=f"del_gav_{row.name}", use_container_width=True):
                        db.excluir_registro_com_drive("DB_AULAS_PRONTAS", row['CONTEUDO'])
                        st.rerun()

    # --- ABA 3: CRONOGRAMA (MANTIDA) ---
    with tab_cronograma:
        st.subheader("📅 Agendamento de Provas por Turma")
        if df_exames.empty: st.warning("Gere uma prova antes.")
        else:
            with st.container(border=True):
                col_ag1, col_ag2, col_ag3 = st.columns([2, 1, 1])
                prova_sel = col_ag1.selectbox("Selecione a Prova:", df_exames['TIPO_MATERIAL'].tolist(), key="sel_cron_av")
                dados_p = df_exames[df_exames['TIPO_MATERIAL'] == prova_sel].iloc[0]
                serie_alvo = "".join(filter(str.isdigit, str(dados_p['ANO'])))
                turmas_comp = sorted([t for t in df_alunos['TURMA'].unique() if serie_alvo in str(t)])
                turmas_sel = col_ag2.multiselect("Turmas:", turmas_comp, key="sel_cron_turmas")
                data_p = col_ag3.date_input("Data:", key="sel_cron_data")
                if st.button("🗓️ AGENDAR", use_container_width=True, type="primary"):
                    for t in turmas_sel:
                        db.salvar_no_banco("DB_REGISTRO_AULAS", [data_p.strftime("%d/%m/%Y"), "AVALIAÇÃO", t, f"Aplicação: {prova_sel}", "SIM", "AGENDADA"])
                    st.success("✅ Agendado!"); st.rerun()

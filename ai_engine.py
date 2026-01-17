# ARQUIVO: ai_engine.py
from google import genai
import streamlit as st

# MODELO ESCOLHIDO: Gemini 2.0 Flash-Lite (Maior cota gratuita: 15 RPM)
MODELO_IA = "gemini-2.0-flash-lite-preview-02-05" 

def gerar_analise_pastoral(resumo_dados):
    """Gera análise técnica e descritiva para relatórios oficiais."""
    if "cache_analise_pastoral" in st.session_state:
        return st.session_state.cache_analise_pastoral

    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Auditor de Dados da Diocese. Analise os seguintes dados da paróquia:
        DADOS: {resumo_dados}
        
        DIRETRIZES:
        1. NÃO use saudações (Olá, Paz e Bem, etc).
        2. Seja estritamente técnico e descritivo.
        3. Foque na segmentação: Infantil/Juvenil vs Adultos.
        4. Identifique tendências de crescimento ou queda.
        5. Projete necessidades de infraestrutura baseada no número de turmas e alunos.
        6. Use linguagem formal e eclesiástica técnica.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        st.session_state.cache_analise_pastoral = response.text
        return response.text
    except Exception as e:
        return "Análise técnica indisponível no momento."

def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Escreva uma mensagem curta para WhatsApp. Tema: {tema}. Presentes: {presentes}. Faltosos: {faltosos}.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Olá! Passando para agradecer a presença de todos no encontro de hoje. Deus abençoe!"

def analisar_turma_local(nome_turma, dados_resumo):
    cache_key = f"cache_turma_{nome_turma}"
    if cache_key in st.session_state: return st.session_state[cache_key]
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Analise tecnicamente a turma {nome_turma}: {dados_resumo}. Sem saudações."
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        st.session_state[cache_key] = response.text
        return response.text
    except: return "Análise indisponível."

def gerar_relatorio_sacramentos_ia(resumo_sacramentos):
    """Gera auditoria de sacramentos com foco em pendências e mutirões."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Auditor Sacramental Diocesano. Analise: {resumo_sacramentos}
        
        DIRETRIZES:
        1. NÃO use saudações ou reflexões teológicas.
        2. Identifique o 'Gargalo Sacramental' (qual sacramento está mais atrasado).
        3. Recomende mutirões de Batismo para turmas de conclusão (3ª etapa e adultos).
        4. Projete o impacto na vida paroquial se as pendências não forem resolvidas.
        5. Seja direto, numérico e técnico.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Auditoria sacramental indisponível."

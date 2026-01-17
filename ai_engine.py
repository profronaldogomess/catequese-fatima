# ARQUIVO: ai_engine.py
from google import genai
import streamlit as st

# MODELO ESTÁVEL PARA GARANTIR COTA (1.5 Flash tem limites mais altos que o 2.0 Preview)
MODELO_IA = "gemini-1.5-flash"

def gerar_analise_pastoral(resumo_dados):
    """Gera análise com Cache e Modelo Estável."""
    if "cache_analise_pastoral" in st.session_state:
        return st.session_state.cache_analise_pastoral

    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Assistente de Coordenação de Catequese experiente. 
        Analise os seguintes dados da paróquia e gere um relatório pastoral:
        DADOS: {resumo_dados}
        O relatório deve conter:
        1. Uma saudação cristã.
        2. Análise da frequência geral.
        3. Alerta sobre catequizandos em risco de evasão.
        4. Uma sugestão pedagógica ou espiritual.
        5. Uma mensagem de motivação.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        
        st.session_state.cache_analise_pastoral = response.text
        return response.text
    except Exception as e:
        if "429" in str(e):
            return ("Paz e Bem! O limite de velocidade da IA foi atingido. "
                    "Aguarde 1 minuto. Isso acontece para proteger sua cota gratuita.")
        return f"Erro na IA: {str(e)}"

def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    """Gera mensagem de WhatsApp calorosa."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Escreva uma mensagem curta e carinhosa para o grupo de WhatsApp da catequese.
        Tema: {tema} | Presentes: {", ".join(presentes)} | Faltosos: {", ".join(faltosos)}
        Use emojis e uma saudação cristã.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Olá! Passando para agradecer a presença de todos no encontro de hoje. Deus abençoe!"

def analisar_turma_local(nome_turma, dados_resumo):
    """Gera análise de turma com Cache por Turma."""
    cache_key = f"cache_turma_{nome_turma}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Analise o desempenho da turma '{nome_turma}'.
        DADOS: {dados_resumo}
        Gere um diagnóstico de engajamento e uma recomendação pedagógica.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        
        st.session_state[cache_key] = response.text
        return response.text
    except:
        return "Análise pastoral temporariamente indisponível (Limite de cota atingido)."

def gerar_relatorio_sacramentos_ia(resumo_sacramentos):
    """Gera relatório de sacramentos com Cache."""
    if "cache_sacramentos" in st.session_state:
        return st.session_state.cache_sacramentos

    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Analise os dados de sacramentos da paróquia: {resumo_sacramentos}
        Gere uma reflexão teológica e análise dos números apresentados.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        
        st.session_state.cache_sacramentos = response.text
        return response.text
    except:
        return "O relatório de IA para sacramentos está indisponível no momento."

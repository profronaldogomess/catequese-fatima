# ARQUIVO: ai_engine.py
from google import genai
import streamlit as st

def gerar_analise_pastoral(resumo_dados):
    """Gera análise com Cache para economizar cota."""
    # Verifica se já existe uma análise salva para evitar nova chamada
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
        4. Uma sugestão pedagógica ou espiritual para os catequistas baseada nos temas tratados.
        5. Uma mensagem de motivação.
        Seja acolhedor, mas profissional.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        
        # Salva no cache
        st.session_state.cache_analise_pastoral = response.text
        return response.text
    except Exception as e:
        if "429" in str(e):
            return ("Paz e Bem! O limite de mensagens por minuto da IA foi atingido. "
                    "Aguarde 60 segundos e tente novamente. Os dados estatísticos continuam disponíveis.")
        return "No momento, não foi possível gerar a análise automática."

def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    """Gera mensagem de WhatsApp (Geralmente não precisa de cache pois muda sempre)."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um catequista atencioso. Escreva uma mensagem curta para o WhatsApp.
        Tema: {tema} | Presentes: {", ".join(presentes)} | Faltosos: {", ".join(faltosos)}
        Seja breve, use emojis e uma saudação cristã.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
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
        Gere um diagnóstico de engajamento e uma recomendação pedagógica (3 parágrafos).
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        
        st.session_state[cache_key] = response.text
        return response.text
    except Exception as e:
        return "Análise pastoral temporariamente indisponível devido ao limite de cota da IA."

def gerar_relatorio_sacramentos_ia(resumo_sacramentos):
    """Gera relatório de sacramentos com Cache."""
    if "cache_sacramentos" in st.session_state:
        return st.session_state.cache_sacramentos

    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Analise os dados de sacramentos: {resumo_sacramentos}
        Gere uma reflexão teológica e análise dos números.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        
        st.session_state.cache_sacramentos = response.text
        return response.text
    except Exception as e:
        return "O relatório de IA para sacramentos está indisponível no momento."

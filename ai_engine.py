# ARQUIVO: ai_engine.py
from google import genai
import streamlit as st

def gerar_analise_pastoral(resumo_dados):
    """Envia os dados para o Gemini e retorna uma análise em texto com tratamento de erro amigável."""
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
        return response.text
    except Exception as e:
        if "429" in str(e):
            return ("Paz e Bem! Nosso assistente de inteligência pastoral atingiu o limite de consultas gratuitas "
                    "neste minuto. Por favor, aguarde cerca de 60 segundos e tente gerar este relatório novamente.")
        return "No momento, não foi possível gerar a análise automática. Por favor, verifique os dados estatísticos acima."
    
def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    """Usa IA para criar uma mensagem de WhatsApp calorosa e variada."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um catequista muito querido e atencioso. 
        Escreva uma mensagem curta para o grupo de WhatsApp da turma sobre o encontro de hoje.
        DADOS DO ENCONTRO:
        - Tema: {tema}
        - Presentes: {", ".join(presentes)}
        - Faltosos: {", ".join(faltosos) if faltosos else "Ninguém (todos foram!)"}
        DIRETRIZES:
        1. Use uma saudação cristã.
        2. Seja breve (máximo 5-6 lines).
        3. Seja natural.
        4. Varie o foco.
        5. Se houver faltosos, diga que sentimos falta deles de forma acolhedora.
        6. Use alguns emojis.
        7. NUNCA comece sempre com a mesma frase.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "Olá! Passando para agradecer a presença de todos no encontro de hoje. Sentimos falta de quem não pôde ir. Que Deus abençoe nossa caminhada!"
    
def analisar_turma_local(nome_turma, dados_resumo):
    """Gera uma análise profunda de uma turma específica com tratamento de erro amigável."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Analise o desempenho da turma de catequese '{nome_turma}'.
        DADOS: {dados_resumo}
        Gere um texto curto (3 parágrafos) contendo:
        1. Diagnóstico da frequência e engajamento.
        2. Identificação de pontos de atenção.
        3. Uma recomendação pedagógica específica.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return ("O limite de processamento da IA foi atingido. Por favor, aguarde um minuto para gerar este perfil novamente. "
                    "Os dados estatísticos acima continuam válidos para sua análise manual.")
        return "Análise pastoral temporariamente indisponível. Por favor, utilize os dados estatísticos acima para sua avaliação."

def gerar_relatorio_sacramentos_ia(resumo_sacramentos):
    """Gera um relatório inteligente sobre a vida sacramental da paróquia."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Consultor Diocesano de Pastoral. Analise os dados de sacramentos deste ano:
        {resumo_sacramentos}
        Gere um relatório contendo:
        1. Uma breve reflexão teológica sobre a importância desses sacramentos.
        2. Análise dos números de Batismo, Eucaristia e Crisma apresentados.
        3. Uma mensagem de parabenização e incentivo às turmas e catequistas.
        Seja formal, inspirador e acolhedor.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "O relatório de IA para sacramentos está indisponível no momento devido ao limite de cota."

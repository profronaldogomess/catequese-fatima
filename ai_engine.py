from google import genai
import streamlit as st

def gerar_analise_pastoral(resumo_dados):
    """Envia os dados para o Gemini e retorna uma análise em texto."""
    try:
        # Configura o cliente com a chave (buscando dos segredos do Streamlit)
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = f"""
        Você é um Assistente de Coordenação de Catequese experiente. 
        Analise os seguintes dados da paróquia e gere um relatório pastoral:
        
        DADOS:
        {resumo_dados}
        
        O relatório deve conter:
        1. Uma saudação cristã.
        2. Análise da frequência geral.
        3. Alerta sobre catequizandos em risco de evasão.
        4. Uma sugestão pedagógica ou espiritual para os catequistas baseada nos temas tratados.
        5. Uma mensagem de motivação.
        
        Seja acolhedor, mas profissional.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Erro ao gerar relatório com IA: {e}"
    
def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    """Usa IA para criar uma mensagem de WhatsApp calorosa e variada."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Lista de estilos para a IA alternar
        prompt = f"""
        Você é um catequista muito querido e atencioso. 
        Escreva uma mensagem curta para o grupo de WhatsApp da turma sobre o encontro de hoje.
        
        DADOS DO ENCONTRO:
        - Tema: {tema}
        - Presentes: {", ".join(presentes)}
        - Faltosos: {", ".join(faltosos) if faltosos else "Ninguém (todos foram!)"}
        
        DIRETRIZES:
        1. Use uma saudação cristã (ex: Paz e Bem, Salve Maria, Olá família).
        2. Seja breve (máximo 5-6 linhas).
        3. Não use palavras difíceis. Seja natural, como se estivesse digitando no celular.
        4. Varie o foco: as vezes foque na alegria do tema, as vezes na importância da presença.
        5. Se houver faltosos, diga que sentimos falta deles de forma acolhedora, sem dar bronca.
        6. Use alguns emojis, mas sem exagerar.
        7. NUNCA comece sempre com a mesma frase.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Erro ao gerar mensagem: {e}"
    
def analisar_turma_local(nome_turma, dados_resumo):
    """Gera uma análise profunda de uma turma específica."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Analise o desempenho da turma de catequese '{nome_turma}'.
        DADOS: {dados_resumo}
        
        Gere um texto curto (3 parágrafos) contendo:
        1. Diagnóstico da frequência e engajamento.
        2. Identificação de pontos de atenção (evasão ou atraso de temas).
        3. Uma recomendação pedagógica específica para os catequistas desta turma.
        """
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"Erro na análise da IA: {e}"
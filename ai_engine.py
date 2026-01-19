# ARQUIVO: ai_engine.py
from google import genai
import streamlit as st

MODELO_IA = "gemini-2.0-flash-lite-preview-02-05" 

def gerar_analise_pastoral(resumo_dados):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Auditor de Dados da Diocese. Analise os seguintes dados da paróquia:
        DADOS: {resumo_dados}
        
        DIRETRIZES:
        1. NÃO use saudações.
        2. NÃO use negrito com asteriscos (**).
        3. Use linguagem formal e eclesiástica técnica.
        4. Foque em tendências e necessidades de infraestrutura.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Análise técnica indisponível."

def gerar_relatorio_sacramentos_ia(resumo_sacramentos):
    """Gera auditoria de sacramentos com foco em impedimentos canônicos e urgência pastoral."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Auditor Sacramental Diocesano. Analise tecnicamente: {resumo_sacramentos}
        
        ESTRUTURA DA RESPOSTA (OBRIGATÓRIA):
        1. PARECER TÉCNICO: (Análise sobre a saúde sacramental da paróquia)
        2. ANÁLISE DE IMPEDIMENTOS: (Foque em situações matrimoniais e falta de batismo em turmas avançadas)
        3. PLANO DE AÇÃO: (Sugestões de mutirões e catequese de reforço)

        REGRAS CRÍTICAS:
        - NÃO use asteriscos (**) para negrito.
        - NÃO use saudações ou reflexões teológicas.
        - Seja direto, numérico e use terminologia como 'Iniciação à Vida Cristã' e 'Impedimento Canônico'.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Auditoria indisponível."

def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Escreva uma mensagem curta para WhatsApp. Tema: {tema}. Presentes: {presentes}. Faltosos: {faltosos}."
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Olá! Deus abençoe a todos pelo encontro de hoje!"

def analisar_turma_local(nome_turma, dados_resumo):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Analise tecnicamente a turma {nome_turma}: {dados_resumo}. Sem saudações ou asteriscos."
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except: return "Análise indisponível."

def analisar_turma_local(nome_turma, dados_resumo):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Analise tecnicamente a turma {nome_turma}: {dados_resumo}. Sem saudações ou asteriscos."
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except: return "Análise indisponível."

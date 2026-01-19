# ARQUIVO: ai_engine.py
# MISSÃO: Motor de Inteligência Artificial para Auditoria Pastoral e Familiar.
from google import genai
import streamlit as st

MODELO_IA = "gemini-2.0-flash-lite-preview-02-05" 

def gerar_analise_pastoral(resumo_dados):
    """Gera análise técnica para o Dashboard Principal."""
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
    """Gera auditoria de sacramentos com foco em impedimentos canônicos."""
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

def analisar_saude_familiar_ia(dados_familia):
    """
    NOVA FUNÇÃO: Analisa o perfil das famílias para sugerir ações da Pastoral Familiar.
    Detecta carências sacramentais e necessidades de regularização matrimonial.
    """
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Consultor da Pastoral Familiar Diocesana. 
        Analise o perfil socioprofissional e religioso das famílias da catequese: {dados_familia}
        
        FOCO DA ANÁLISE:
        1. REGULARIZAÇÃO MATRIMONIAL: Identifique a urgência de Casamentos Comunitários.
        2. ENGAJAMENTO: Sugira como atrair pais que não participam de grupos paroquiais.
        3. APOIO SOCIAL: Identifique necessidades baseadas na situação familiar.
        
        REGRAS CRÍTICAS:
        - NÃO use asteriscos (**) para negrito.
        - NÃO use saudações.
        - Use terminologia técnica: 'Igreja Doméstica', 'Matrimônio Religioso', 'RICA'.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except Exception as e:
        return f"Análise de saúde familiar indisponível no momento. (Erro: {str(e)})"

def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    """Gera texto para engajamento no WhatsApp da turma."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Escreva uma mensagem curta para WhatsApp. Tema: {tema}. Presentes: {presentes}. Faltosos: {faltosos}."
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Olá! Deus abençoe a todos pelo encontro de hoje!"

def analisar_turma_local(nome_turma, dados_resumo):
    """Análise específica para o Dashboard de uma turma."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Analise tecnicamente a turma {nome_turma}: {dados_resumo}. Sem saudações ou asteriscos."
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except: return "Análise indisponível."

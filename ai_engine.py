# ARQUIVO: ai_engine.py
from google import genai
import streamlit as st

def gerar_analise_pastoral(resumo_dados):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Analise os dados da paróquia e gere um relatório pastoral: {resumo_dados}"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "Erro ao gerar análise pastoral."

def gerar_mensagem_whatsapp(tema, presentes, faltosos):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Escreva uma mensagem de WhatsApp para a turma sobre o tema {tema}."
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "Olá! Obrigado pela presença de todos hoje!"

def analisar_turma_local(nome_turma, dados_resumo):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Analise o desempenho da turma {nome_turma}: {dados_resumo}"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "Análise temporariamente indisponível."

def gerar_relatorio_sacramentos_ia(resumo_sacramentos):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"Gere um relatório pastoral sobre os sacramentos realizados: {resumo_sacramentos}"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "Relatório de IA indisponível no momento."

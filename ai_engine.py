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
    """Gera auditoria com foco em Impedimentos Canônicos e Preparação Pastoral."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Auditor do Tribunal Eclesiástico e Coordenador de IVC. 
        Analise os dados de prontidão sacramental: {resumo_sacramentos}
        
        ESTRUTURA OBRIGATÓRIA DO PARECER:
        1. DIAGNÓSTICO DE IMPEDIMENTOS: Foque em adultos conviventes ou casados apenas no civil (Impedimento para Crisma/Eucaristia) e crianças sem batismo em etapas avançadas.
        2. CAMINHO DE PREPARAÇÃO: Sugira roteiros de encontros para regularização matrimonial e querigma para pais em situação irregular.
        3. ORIENTAÇÃO AO PÁROCO: Liste casos que exigem entrevista pessoal ou sanação radical.

        REGRAS:
        - Use termos: 'Impedimento Canônico', 'Regularização Matrimonial', 'Estado de Graça', 'Sanação'.
        - NÃO use asteriscos (**) para negrito.
        - Seja técnico, direto e pastoral.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return "Auditoria indisponível no momento."
    
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
    """Análise específica para o Dashboard de uma turma com rigor de IVC."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Coordenador de Catequese (IVC). Analise a turma {nome_turma}: {dados_resumo}.
        
        REGRAS CRÍTICAS DE LINGUAGEM:
        1. JAMAIS use termos como 'aula', 'prova', 'curso', 'aluno' ou 'professor'.
        2. USE: 'encontro', 'itinerário', 'experiência de fé', 'catequizando' e 'catequista'.
        3. FOQUE na caminhada comunitária e na vivência dos sacramentos como marcos da Iniciação.
        4. NÃO use asteriscos (**) para negrito.
        5. Seja direto e técnico-pastoral.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except: return "Análise pastoral indisponível."

def gerar_mensagem_reacolhida_ia(nome_catequizando, nome_turma):
    """Gera uma mensagem carinhosa e pastoral para catequizandos faltosos."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        Você é um Catequista muito acolhedor da Paróquia Nossa Senhora de Fátima. 
        Escreva uma mensagem curta para WhatsApp destinada ao catequizando {nome_catequizando} (ou aos pais dele), 
        que faz parte da turma {nome_turma} e tem faltado aos encontros.
        
        DIRETRIZES PASTORAIS:
        1. O tom deve ser de SAUDADE e ACOLHIMENTO, nunca de cobrança ou bronca.
        2. Use termos como 'sentimos sua falta', 'nossa comunidade fica mais completa com você', 'caminhada de fé'.
        3. JAMAIS use termos escolares como 'aula', 'falta', 'matéria' ou 'curso'.
        4. NÃO use asteriscos (**) para negrito.
        5. A mensagem deve ser curta (máximo 3 parágrafos pequenos).
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return f"Olá! Sentimos muito a sua falta em nosso último encontro da catequese. A turma {nome_turma} não é a mesma sem você! Esperamos te ver no próximo encontro para continuarmos nossa caminhada de fé. Deus abençoe!"

def gerar_mensagem_cobranca_doc_ia(nome, docs, turma, is_adulto):
    """Gera mensagem diplomática para regularização de documentos."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        destinatario = "você" if is_adulto else "seu(sua) filho(a)"
        prompt = f"""
        Você é o Secretário da Catequese da Paróquia Nossa Senhora de Fátima.
        Escreva uma mensagem curta e gentil para {nome}, da turma {turma}, 
        solicitando a entrega dos seguintes documentos pendentes: {docs}.
        
        REGRAS:
        1. Explique que os documentos são essenciais para completar o registro da caminhada.
        2. Se for adulto, fale diretamente com ele. Se for criança, fale com os pais.
        3. Use tom de acolhida, não de cobrança fria.
        4. NÃO use asteriscos (**) para negrito.
        5. Termine com 'Deus abençoe'.
        """
        response = client.models.generate_content(model=MODELO_IA, contents=prompt)
        return response.text
    except:
        return f"Paz e Bem! Notamos que ainda faltam alguns documentos ({docs}) para completar a inscrição de {nome} na turma {turma}. Poderia nos entregar no próximo encontro? Deus abençoe!"


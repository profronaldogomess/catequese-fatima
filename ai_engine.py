import os
import re
import io
import requests
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ==============================================================================
# DICIONÁRIO DE PERSONAS DE ELITE (V100 - SOBERANIA E CLEAN TEXT)
# ==============================================================================

PERSONAS = {
    "PLANE_PEDAGOGICO": """VOCÊ É O ARQUITETO PEDAGÓGICO SÊNIOR E ENGENHEIRO DE DNA CURRICULAR (V40 - MASTER ELITE).
    Sua missão é projetar o roteiro que servirá de base para a produção de materiais de luxo. Você é o Hub de Integração.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT - INEGOCIÁVEL):
    - É TERMINANTEMENTE PROIBIDO usar formatação Markdown (como **, ##, ###) ou símbolos Unicode decorativos (como █, ▓, ▒, ░, ✦, 🎯, ➔).
    - Use APENAS texto puro, letras MAIÚSCULAS para títulos e as tags obrigatórias entre colchetes.

    🚨 PROTOCOLO DE BLINDAGEM DE SINTAXE (ANTI-VAZAMENTO):
    - Pule DUAS LINHAS entre o fim de um bloco e o início da próxima tag [TAG].
    - É proibido escrever o nome de uma tag dentro do conteúdo de outra tag.

    🚨 LEI DA INTEGRAÇÃO TOTAL:
    - Cada aula ([AULA_1], [AULA_2]) deve ser um ciclo completo: Contextualização Crítica + Fundamentação Densa + Aplicação Real.
    - Se houver um 'ATIVO VINCULADO', use o conteúdo dele como base central.

    🚨 LEI DA TRILHA MANUAL E INTERVALOS:
    - Baseie a [AULA_1] na Trilha 1 ou no primeiro intervalo de páginas.
    - Baseie a [AULA_2] na Trilha 2 ou no segundo intervalo de páginas.

    🚨 LEI DO SÁBADO (RIGOR ABSOLUTO):
    - Se o status for 'DESATIVADO', a tag [SABADO_LETIVO] deve conter APENAS: 'N/A'.

    🚨 MODOS DE OPERAÇÃO INTEGRADOS:
    1. AVALIAÇÃO/SONDA: [AULA_1] para Aplicação (logística). [AULA_2] para Correção Comentada.
    2. REVISÃO/PROJETO: Foco em Clínica Pedagógica ou Laboratório de Investigação.
    3. AULA ABERTA: Deduza o Eixo e Objetivos da Matriz com base no evento descrito.

    🚨 SEQUÊNCIA DE ENTREGA:[HABILIDADE_BNCC], [COMPETENCIAS_FOCO],[COMPETENCIA_GERAL],[OBJETO_CONHECIMENTO], [CONTEUDOS_ESPECIFICOS],[OBJETIVOS_ENSINO],[JUSTIFICATIVA_PEDAGOGICA], [AULA_1], [AULA_2],[SABADO_LETIVO], [AVALIACAO_DE_MERITO],[ESTRATEGIA_DUA_PEI].""",

    "REFINADOR_PEDAGOGICO": """VOCÊ É O MAESTRO COPILOT (V100 - CONVERSACIONAL).
    Sua missão é atuar como um assistente de coautoria em tempo real para o Professor Ronaldo, ajustando o plano de aula.

    🚨 LEI DA SAÍDA DUPLA (OBRIGATÓRIO):
    Você DEVE retornar sua resposta dividida em DUAS partes exatas usando as tags abaixo:

    [MENSAGEM_CHAT]
    Escreva aqui uma resposta curta, humana e direta para o professor (ex: "Pronto, Mestre! Deixei a Aula 1 mais lúdica...").
    
    [CONTEUDO_ATUALIZADO]
    Cole aqui o PLANO DE AULA COMPLETO E ATUALIZADO, mantendo TODAS as tags originais ([HABILIDADE_BNCC], [AULA_1], etc).

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - Dentro do[CONTEUDO_ATUALIZADO], é PROIBIDO usar Markdown (**, #) ou Unicode decorativo. Use apenas texto puro.""",

    "MAESTRO_SOSA_V28_ELITE": """VOCÊ É O ENGENHEIRO DE PRODUÇÃO SEMIÓTICA SÊNIOR (V48 - MASTER ELITE).
    Sua missão é materializar materiais de luxo pedagógico, fundindo o LIVRO DIDÁTICO com tecnologia e densidade acadêmica.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT - INEGOCIÁVEL):
    - É TERMINANTEMENTE PROIBIDO usar formatação Markdown (como **, ##, ###) ou símbolos Unicode decorativos (como █, ▓, ▒, ░, ✦, 🎯, ➔).
    - Questões Inline: Escreva "QUESTÃO X." e o enunciado na mesma linha, sem negrito.

    🚨 LEI DAS TAGS PURAS: [PROFESSOR], [ALUNO],[GABARITO], [PEI],[GABARITO_PEI], [IMAGENS].

    🚨 [PROFESSOR] - TRATADO DE MEDIAÇÃO:
    - Inicie com explicação técnica e profunda.
    - Roteiro: 1. INÍCIO (Conexão Alpha), 2. MEIO (Uso do livro/conceito), 3. FIM (Síntese).

    🚨 LEI DO SUPORTE VISUAL:
    - ALUNO REGULAR: Insira [ PROMPT IMAGEM: descrição ] apenas se a questão exigir apoio visual (geometria, mapas).
    - ALUNO PEI: Apoio visual OBRIGATÓRIO em todas as questões. Estrutura: [PARA LEMBRAR], [PASSO A PASSO] e[ PROMPT IMAGEM: descrição ].

    🚨 CONSOLIDAÇÃO DE IMAGENS:
    - Na tag [IMAGENS], consolide todos os prompts em inglês para geração no Midjourney/DALL-E.""",

    "ARQUITETO_PEI_V24": """VOCÊ É O ESPECIALISTA EM INCLUSÃO E DESENHO UNIVERSAL PARA APRENDIZAGEM (DUA).
    Sua missão é adaptar a atividade regular fornecida para alunos com necessidades educacionais especiais (PEI).

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.

    🚨 REGRAS DE ADAPTAÇÃO:
    - Reduza a complexidade textual, mas mantenha a essência do conteúdo.
    - Estrutura obrigatória para CADA questão:[PARA LEMBRAR] -> Conceito rápido e direto.
      [PASSO A PASSO] -> Instrução de como pensar/resolver.
      [ PROMPT IMAGEM: descrição visual de apoio ] -> Obrigatório.
      QUESTÃO ADAPTADA -> Enunciado simplificado com apenas 3 alternativas (A, B, C).""",

    "ARQUITETO_EXAMES_V30_ELITE": """VOCÊ É O ARQUITETO-CHEFE DE EXAMES DE ELITE (V70 - SOBERANIA ANALÍTICA).
    Sua missão é criar avaliações de altíssima densidade acadêmica, formatadas para CORREÇÃO POR SCANNER.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT - INEGOCIÁVEL):
    - É TERMINANTEMENTE PROIBIDO usar formatação Markdown (como **, ##, ###) ou símbolos Unicode decorativos (como █, ▓, ▒, ░).
    - PROIBIDO usar LaTeX ($). Use frações lineares (1/2).
    - RÓTULO REGULAR: "QUESTÃO XX (0,XX ponto) -" Texto na mesma linha.

    🚨 LEI DO VALOR E FORMATO:
    - Inicie com[VALOR: X.X].
    - [QUESTOES] (Regular): EXCLUSIVAMENTE 5 alternativas (A, B, C, D, E).
    - [PEI]: EXCLUSIVAMENTE 3 alternativas (A, B, C).
    - PROIBIDO questões abertas.

    🚨 LEI DA SINTAXE DE PERÍCIA:
    1. [GRADE_DE_CORRECAO]: QUESTÃO XX:[CÓDIGO BNCC - DESCRIÇÃO] | JUSTIFICATIVA: Texto | DISTRATORES: A) Texto; B) Texto...
    2. [GRADE_DE_CORRECAO_PEI]: QUESTÃO PEI XX:[CÓDIGO BNCC - DESCRIÇÃO] | JUSTIFICATIVA: Texto | ANÁLISE DE LACUNA: Texto.

    🚨 PROTOCOLO DE TAGS:[VALOR], [ORIENTACOES], [QUESTOES],[GABARITO_TEXTO],[GRADE_DE_CORRECAO], [RESPOSTAS_IA], [PEI],[GABARITO_PEI], [GRADE_DE_CORRECAO_PEI],[RESPOSTAS_PEI_IA].""",

    "REFINADOR_MATERIAIS": """VOCÊ É O MAESTRO COPILOT (V100 - CONVERSACIONAL).
    Sua missão é atuar como um assistente de coautoria em tempo real para o Professor Ronaldo, ajustando o material didático.

    🚨 LEI DA SAÍDA DUPLA (OBRIGATÓRIO):
    Você DEVE retornar sua resposta dividida em DUAS partes exatas usando as tags abaixo:

    [MENSAGEM_CHAT]
    Escreva aqui uma resposta curta, humana e direta para o professor.[CONTEUDO_ATUALIZADO]
    Cole aqui o MATERIAL COMPLETO E ATUALIZADO, mantendo TODAS as tags originais ([PROFESSOR], [ALUNO], [GABARITO], [PEI], etc).

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - Dentro do[CONTEUDO_ATUALIZADO], é PROIBIDO usar Markdown (**, #) ou Unicode decorativo. Use apenas texto puro.""",

    "REFINADOR_EXAMES": """VOCÊ É O ARQUITETO REVISOR DE EXAMES DO SISTEMA SOSA V25.
    Sua missão é REESCREVER avaliações seguindo ordens exatas do Professor Ronaldo.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.

    🚨 LEI DA SOBERANIA E ESTRUTURA:
    1. A nova ordem anula a lógica anterior.
    2. MANTENHA AS TAGS: [ORIENTACOES],[QUESTOES], [GABARITO_TEXTO] e [RESPOSTAS_IA].
    3. MANTENHA A DESCRIÇÃO INTEGRAL DA HABILIDADE na [GRADE_DE_CORRECAO].
    4. PROIBIÇÃO DE CABEÇALHO: Jamais crie campos de 'Escola', 'Aluno' ou 'Data'.
    
    Retorne o documento completo e atualizado.""",

    "ARQUITETO_SONDA_DIAGNOSTICA": """VOCÊ É O PERITO EM PSICOMETRIA E AVALIAÇÃO EM LARGA ESCALA (V72 - PADRÃO SAEB).
    Sua missão é criar Sondas de Proficiência rigorosas para mapear lacunas.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT - INEGOCIÁVEL):
    - É TERMINANTEMENTE PROIBIDO usar formatação Markdown (como **, ##, ###) ou símbolos Unicode decorativos (como █, ▓, ▒, ░).
    - RÓTULO: "QUESTÃO XX (0,XX ponto) -" (enunciado na mesma linha).

    🚨 LEI DO FORMATO MÚLTIPLA ESCOLHA:
    -[QUESTOES] (Regular): 5 alternativas (A, B, C, D, E).
    - [PEI]: 3 alternativas (A, B, C).
    - Inclua OBRIGATORIAMENTE após o enunciado: [ PROMPT IMAGEM: descrição técnica ].

    🚨 LEI DA PERÍCIA DUPLA:
    1. [GRADE_DE_CORRECAO]: QUESTÃO XX:[CÓDIGO BNCC/DESCRITOR SAEB - DESCRIÇÃO]. JUSTIFICATIVA: Texto. PERÍCIA DE DISTRATORES: O que o erro revela.
    2. [GRADE_DE_CORRECAO_PEI]: QUESTÃO PEI XX:[CÓDIGO BNCC/DESCRITOR - DESCRIÇÃO]. JUSTIFICATIVA: Texto. ANÁLISE DE LACUNA PEI: Erro base.

    🚨 PROTOCOLO DE TAGS:[VALOR], [SOSA_ID], [PROFESSOR], [QUESTOES],[GABARITO_TEXTO], [GRADE_DE_CORRECAO], [RESPOSTAS_IA], [PEI],[GABARITO_PEI], [GRADE_DE_CORRECAO_PEI],[RESPOSTAS_PEI_IA].""",

    "ARQUITETO_RECOMPOSICAO_V68_ELITE": """VOCÊ É O PERITO EM PSICOMETRIA E CLÍNICA PEDAGÓGICA SOSA (V68-R).
    Sua missão é materializar uma Intervenção de Recomposição de alta performance.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT - INEGOCIÁVEL):
    - É TERMINANTEMENTE PROIBIDO usar formatação Markdown (como **, ##, ###) ou símbolos Unicode decorativos (como █, ▓, ▒, ░).
    - PROIBIDO o uso de LaTeX ($). Para frações, use o formato linear: 1/2. Para potências: 2^3.
    - PROIBIDO tabelas em Markdown (| e ---). Use listas estruturadas.

    🚨 SINFONIA PEI E VISUAL:
    - Inclua[ PROMPT IMAGEM: descrição técnica ] após enunciados que exijam suporte visual.
    - PEI: Exatamente METADE das questões. Estrutura:[PARA LEMBRAR], [PASSO A PASSO], [QUESTÃO ADAPTADA].

    🚨 PROTOCOLO DE TAGS:
    [VALOR: 0.0],[SOSA_ID], [PROFESSOR],[ALUNO], [RESPOSTAS_PEDAGOGICAS],[GRADE_DE_CORRECAO],[PEI].""",

    "ARQUITETO_CIENTIFICO_V33": """VOCÊ É O ENGENHEIRO-CHEFE DE INICIAÇÃO CIENTÍFICA E PESQUISA (V33 - MASTER ELITE).
    Sua missão é materializar roteiros de investigação profunda.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT - INEGOCIÁVEL):
    - É TERMINANTEMENTE PROIBIDO usar formatação Markdown (como **, ##, ###) ou símbolos Unicode decorativos (como █, ▓, ▒, ░).
    - Proibido usar sublinhados '_______'. Escreva conteúdo real e orientador.

    🚨 LEI DA DENSIDADE CIENTÍFICA:
    - Use a Pedagogia Histórico-Crítica (PHC) para conectar o conteúdo à realidade social de Itabuna/BA.
    - Forneça "Andaimas de Escrita" para os alunos.

    🚨 DICIONÁRIO DE TAGS OBRIGATÓRIAS:[SOSA_ID], [JUSTIFICATIVA_PHC], [CONTEXTO_INVESTIGATIVO],[MISSÃO_DE_PESQUISA], [PASSO_A_PASSO],[PRODUTO_ESPERADO],[ESTRATEGIA_DUA_PEI],[RUBRICA_DE_MERITO].""",

    "ARQUITETO_REVISAO_V29": """VOCÊ É O ENGENHEIRO DE RECOMPOSIÇÃO DE APRENDIZAGEM (V29).
    Sua missão é criar um Material de Revisão baseado em uma prova já existente.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.

    🚨 LEI DO ESPELHAMENTO (ALUNO REGULAR):
    - FORMATO: QUESTÕES ABERTAS (DISCURSIVAS). Proibido múltipla escolha para o regular.
    - LÓGICA 80/20: 80% "Gêmeas" (mesma matemática, contexto diferente), 20% "Identidade" (iguais à prova, mas abertas).

    🚨 LEI DO ANDAIME (ALUNO PEI):
    - FORMATO: MÚLTIPLA ESCOLHA (A-C). Idênticas às da prova PEI.
    - REFORÇO: Iniciar com[PARA LEMBRAR] e [PASSO A PASSO].

    🚨 PROTOCOLO DE TAGS:
    [PROFESSOR], [ALUNO], [GABARITO],[PEI].""",

    "ARQUITETO_LISTAS_HIBRIDAS": """VOCÊ É O ENGENHEIRO DE CONSOLIDAÇÃO DIDÁTICA (V50 - MASTER ELITE).
    Sua missão é criar Listas de Exercícios Híbridas baseadas estritamente no conteúdo das aulas fornecidas.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.
    - Rótulo das questões: "QUESTÃO XX." (na mesma linha do texto).

    🚨 LEI DA MESCLA DE QUESTÕES:
    Respeite a cota fornecida: TRADICIONAL, COTIDIANO REAL, ROTINA TECNOLÓGICA (ALPHA) e DESAFIO (BOSS FIGHT).

    🚨 LEI DO SUPORTE VISUAL:
    - ALUNO REGULAR: Insira [ PROMPT IMAGEM: descrição ] apenas se necessário.
    - ALUNO PEI: Metade das questões. Apoio visual OBRIGATÓRIO. Estrutura:[PARA LEMBRAR], [PASSO A PASSO] e[ PROMPT IMAGEM: descrição ].

    🚨 PROTOCOLO DE TAGS:
    [SOSA_ID],[PROFESSOR], [ALUNO],[GABARITO], [PEI], [GABARITO_PEI], [IMAGENS].""",

    "ESPECIALISTA_INCLUSAO": """VOCÊ É O ANALISTA PEDAGÓGICO LONGITUDINAL (V38 - SOBERANIA EMPÍRICA).
    Sua missão é redigir relatórios baseados em EVIDÊNCIAS e nos 4 PILARES: Autonomia, Socialização, Participação e Resposta às Intervenções.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.

    🚨 LEI DA EVOLUÇÃO E NÃO-PATOLOGIZAÇÃO:
    - Compare os dados passados e presentes. Identifique AVANÇO, ESTAGNAÇÃO ou REGRESSÃO.
    - Proibido nomes de doenças. Use termos pedagógicos (ex: 'Barreiras de processamento').

    🚨 ESTRUTURA OBRIGATÓRIA:
    1. STATUS DE SAFRA. 2. ANÁLISE DOS 4 PILARES. 3. COMPARAÇÃO LONGITUDINAL. 4. PARECER TÉCNICO.""",

    "PONTE_COORDENACAO": """VOCÊ É O PROFESSOR RONALDO GOMES (V38).
    Sua missão é gerar um relato humano, curto e direto para o WhatsApp da Coordenação.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.

    🚨 REGRAS DE OURO:
    - Texto muito curto (máximo 6 a 8 linhas).
    - Converta números em narrativa (ex: 1 visto vira 'precisa de incentivo na execução').
    - Foco em Autonomia e Resposta às intervenções.""",

    "ESPECIALISTA_PEI": """VOCÊ É O PROCESSADOR DE DADOS PEI (V38.4 - ZERO REPETIÇÃO).
    Sua missão é fatiar o relatório de evolução em 4 blocos de informações EXCLUSIVAS.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.

    🚨 LEI DA EXCLUSIVIDADE:
    1. [SOCIAIS] -> Apenas interação com pares/professor e isolamento.
    2.[COMUNICATIVAS] -> Apenas fala, silêncio e compreensão de ordens.
    3.[EMOCIONAIS] -> Apenas choro, frustração e bloqueios afetivos.
    4.[FUNCIONAIS] -> Apenas autonomia, execução de tarefas e escrita/cálculo.
    - Seja extremamente conciso. Máximo 3 linhas por bloco.""",

    "TRADUTOR_CURRICULAR_V39": """VOCÊ É O ARQUITETO DE MATRIZES PEI (V39.2).
    Sua missão é fatiar o currículo em blocos puros para as 4 colunas de Itabuna.

    🚨 LEI DA FORMATAÇÃO LIMPA (CLEAN TEXT):
    - PROIBIDO usar Markdown (**, #) ou Unicode decorativo (█▓▒░). Use apenas texto puro.
    - NÃO use textos explicativos fora das tags.

    FORMATO OBRIGATÓRIO:
    [ITEM]
    [C] Nome do Conteúdo
    [O] Objetivo Adaptado[F] Funções Psíquicas
    [M] Seleção de Materiais
    [/ITEM]"""
}

# ==============================================================================
# MOTORES DE INTELIGÊNCIA E EXTRAÇÃO
# ==============================================================================

def gerar_ia(persona_key, comando, url_drive=None, usar_busca=True):
    """MOTOR SOSA V48 - RIGOR CIENTÍFICO (FIDELIDADE TOTAL AO PDF)"""
    
    config = types.GenerateContentConfig(
        tools=[{'google_search': {}}] if usar_busca else[],
        temperature=1.0,
        media_resolution="media_resolution_high" 
    )
    
    conteudo_prompt =[]
    
    if url_drive and "drive.google.com" in url_drive:
        try:
            file_id = re.search(r"(?:id=|[dD]/)([\w-]+)", url_drive).group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            response = requests.get(download_url, timeout=60) 
            
            if response.status_code == 200 and b"%PDF" in response.content[:10]:
                arquivo_temp = client.files.upload(
                    file=io.BytesIO(response.content),
                    config=types.UploadFileConfig(mime_type="application/pdf")
                )
                conteudo_prompt.append(types.Part.from_uri(
                    file_uri=arquivo_temp.uri, 
                    mime_type="application/pdf"
                ))
                st.toast("📖 Documento anexo lido com sucesso. Iniciando extração fiel...", icon="✅")
            else:
                return "❌ ERRO DE SOBERANIA: O arquivo do Drive não pôde ser lido ou não é um PDF válido. A geração foi interrompida para evitar alucinações."
        except Exception as e:
            return f"❌ ERRO TÉCNICO NO DRIVE: {e}. Verifique se o arquivo está compartilhado como 'Qualquer pessoa com o link'."

    conteudo_prompt.append(types.Part.from_text(text=f"{PERSONAS[persona_key]}\n\n{comando}"))

    try:
        res = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=[types.Content(role="user", parts=conteudo_prompt)],
            config=config
        )
        
        if not res.text:
            return "⚠️ A IA não retornou dados. Verifique o conteúdo das páginas selecionadas."
            
        return res.text
    except Exception as e:
        return f"Erro na IA: {e}"

def extrair_tag(texto, tag):
    """EXTRATOR SOSA V45 (FUZZY MATCH & BLINDAGEM DE SINTAXE)"""
    if not texto: return ""
    
    tag_busca = tag.upper().strip()
    
    tags_mestras =[
        "SOSA_ID", "VALOR", "ORIENTACOES", "QUESTOES", "GABARITO_TEXTO", "GRADE_DE_CORRECAO", 
        "GABARITO", "RESPOSTAS_IA", "PEI", "GABARITO_PEI", "GRADE_DE_CORRECAO_PEI", "RESPOSTAS_PEI_IA", 
        "PROFESSOR", "ALUNO", "IMAGENS", "AULA_ALVO", "HABILIDADE_BNCC", "COMPETENCIAS_FOCO", 
        "COMPETENCIA_GERAL", "OBJETO_CONHECIMENTO", "CONTEUDOS_ESPECIFICOS", "OBJETIVOS_ENSINO",
        "JUSTIFICATIVA_PEDAGOGICA", "JUSTIFICATIVA_PHC", "RUBRICA_DE_MERITO", "CONTEXTO_INVESTIGATIVO", 
        "MISSÃO_DE_PESQUISA", "PASSO_A_PASSO", "PRODUTO_ESPERADO", "CONTEXTO_GLOCAL",
        "AULA_1", "AULA_2", "SABADO_LETIVO", "AVALIACAO_DE_MERITO", "ESTRATEGIA_DUA_PEI",
        "MAPA_DE_RECOMPOSICAO", "RESPOSTAS_PEDAGOGICAS", "BASE_DIDATICA",
        "MENSAGEM_CHAT", "CONTEUDO_ATUALIZADO"
    ]
    
    parada =[t for t in tags_mestras if t != tag_busca]
    lista_parada = "|".join(parada)

    padrao_interno = rf"\[[^\]]*?{tag_busca}[^\]]*?[:\-]\s*(.*?)\]"
    match_int = re.search(padrao_interno, texto, re.IGNORECASE)
    if match_int:
        res_int = match_int.group(1).strip()
        if 0 < len(res_int) < 100: return res_int

    padrao_bloco = rf"\[[^\]]*?{tag_busca}[^\]]*?\]\s*[:\-]*\s*(.*?)(?=\s*\[[^\]]*?(?:{lista_parada})[^\]]*?\]|$)"
    match_bloco = re.search(padrao_bloco, texto, re.DOTALL | re.IGNORECASE)
    
    if match_bloco:
        res = match_bloco.group(1).strip()
        res_limpo = re.sub(r'[*#$░▒▓█]', '', res)
        res_limpo = re.sub(r'-{3,}', '', res_limpo)
        return res_limpo.strip()
    
    return ""

def subir_para_google(caminho_arquivo, nome_exibicao):
    try:
        arquivo_google = client.files.upload(
            file=caminho_arquivo, 
            config=types.UploadFileConfig(display_name=nome_exibicao)
        )
        return arquivo_google.uri
    except Exception as e:
        return f"Erro no upload: {e}"
    
def realizar_diagnostico_v25(plano_raw, df_curriculo, ano_sel):
    texto_upper = plano_raw.upper()
    modalidade = "CADERNO" 
    if "LIVRO" in texto_upper: modalidade = "LIVRO"
    elif "AVALIAÇÃO" in texto_upper or "PROVA" in texto_upper: modalidade = "PROVA"
    elif "PROJETO" in texto_upper: modalidade = "PROJETO"

    cont_plano = extrair_tag(plano_raw, "CONTEUDOS_ESPECIFICOS").upper().strip()
    base_ano = df_curriculo[df_curriculo['ANO'] == int(ano_sel)]
    lista_curriculo =[str(c).upper().strip() for c in base_ano['CONTEUDO_ESPECIFICO'].unique()]
    sincronizado = any(c in cont_plano for c in lista_curriculo)
    status_msg = "Sincronizado" if sincronizado else "Divergente"
    status_cor = "🟢" if sincronizado else "🟡"

    return {
        "modalidade": modalidade,
        "status": f"{status_cor} {status_msg}",
        "conteudo_literal": extrair_tag(plano_raw, "CONTEUDOS_ESPECIFICOS"),
        "objetivo_literal": extrair_tag(plano_raw, "OBJETIVOS_ENSINO")
    }

def analisar_gabarito_vision(imagem_bytes):
    """MAESTRO VISION V6.4 - ULTRA INTELIGÊNCIA (MODELO 2.5-PRO)"""
    try:
        prompt = (
            "Você é um perito em visão computacional de alta precisão. Analise a imagem do gabarito.\n"
            "A tabela possui as colunas: Q (Questão), A, B, C, D, E.\n"
            "MISSÃO DE RACIOCÍNIO:\n"
            "1. Localize a grade de respostas (linhas 01 a 10).\n"
            "2. Analise a densidade de preenchimento de cada círculo.\n"
            "3. Se houver uma marcação única e clara, retorne a letra correspondente.\n"
            "4. Se houver DUAS ou mais marcações (mesmo que uma esteja levemente riscada), retorne 'X' (Dupla Marcação).\n"
            "5. Se a linha estiver totalmente sem marcação, retorne '?' (Vazia).\n"
            "6. Ignore anotações manuais como 'PEI' ou 'Normal' feitas pelo professor.\n"
            "Retorne APENAS um JSON puro no formato: {'01': 'A', '02': 'C', ...}"
        )
        
        conteudo_prompt =[
            types.Part.from_bytes(data=imagem_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text=prompt)
        ]
        
        res = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=[types.Content(role="user", parts=conteudo_prompt)],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        import json
        return json.loads(res.text)
    except Exception as e:
        return {"erro": str(e)}
    
def gerar_prognostico_pedagogico(dados_stats, contexto_prova):
    """MAESTRO ANALYST V59 - DIAGNÓSTICO POR DESCRITORES (PADRÃO DF/SAEB)"""
    try:
        prompt = (
            f"VOCÊ É O PERITO EM AVALIAÇÃO EDUCACIONAL SOSA.\n"
            f"Sua missão é realizar um diagnóstico no padrão dos Cadernos de Revisão do DF.\n\n"
            f"CONTEXTO DA PROVA:\n{contexto_prova}\n\n"
            f"DESEMPENHO DA TURMA:\n{dados_stats}\n\n"
            f"MISSÃO:\n"
            f"1. MAPEAMENTO DE DESCRITORES: Para cada questão, identifique o Descritor/Habilidade (Ex: D1, D5, EF06MA01).\n"
            f"2. ANÁLISE DE LACUNA: Explique o processo cognitivo que falhou.\n"
            f"3. PARÂMETROS TÉCNICOS: Gere uma lista curta de 'Tópicos de Recomposição'.\n\n"
            f"🚨 FORMATO DE SAÍDA (OBRIGATÓRIO):\n"
            f"[DIAGNOSTICO_VISUAL]\n(Escreva aqui o parecer técnico para o professor ler)\n\n"
            f"[PARAMETROS_SISTEMA]\n(Gere uma lista simples: Descritor: Nome da Habilidade | Nível de Alerta)\n"
            f"Linguagem formal. SEM MARKDOWN."
        )
        
        res = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[types.Part.from_text(text=prompt)]
        )
        return res.text.replace("**", "").replace("#", "").strip()
    except Exception as e:
        return f"Erro na perícia: {e}"

def limpar_links_antigos(texto):
    """Remove qualquer bloco de --- LINKS --- anterior para evitar duplicidade"""
    if not texto: return ""
    partes = re.split(r"--- LINKS ---", texto, flags=re.IGNORECASE)
    return partes[0].strip()

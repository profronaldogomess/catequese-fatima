# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 1.2.0 - ESTABILIDADE ABSOLUTA E AUDITORIA EXECUTIVA
# MISSÃO: Gestão de PDFs, Lógicas de Censo, Fuso Horário e Documentação Oficial.
# ESTE ARQUIVO É PARTE INTEGRANTE DO SISTEMA CATEQUESE FÁTIMA.
# ==============================================================================

from datetime import date, datetime, timedelta, timezone
import pandas as pd
from fpdf import FPDF
import os
import re

# ==============================================================================
# 1. FUNÇÕES DE APOIO, FORMATAÇÃO E TRATAMENTO DE DADOS
# ==============================================================================

def formatar_data_br(valor):
    """
    Força a conversão de qualquer formato (YYYYMMDD, ISO, etc) para DD/MM/YYYY.
    Garante que datas nulas ou 'None' retornem 'N/A' para evitar erros no PDF.
    """
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    
    s = str(valor).strip().split('.')[0]
    
    # Trata formato numérico YYYYMMDD (comum em exportações de planilhas)
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    
    # Trata formato ISO YYYY-MM-DD
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    
    try:
        dt = pd.to_datetime(valor)
        if pd.notnull(dt):
            return dt.strftime('%d/%m/%Y')
    except:
        pass
    return s

def calcular_idade(data_nascimento):
    """
    Calcula a idade exata baseada no fuso horário da paróquia (UTC-3).
    Retorna 0 se a data for inválida ou não informada.
    """
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]:
        return 0
    
    # Ajuste rigoroso de fuso horário para a Bahia/Brasília (UTC-3)
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except:
        return 0

def limpar_texto(texto):
    """
    Remove artefatos de Markdown (**, *) e garante compatibilidade Latin-1.
    Essencial para evitar erros de codificação no motor FPDF.
    """
    if not texto:
        return ""
    # Limpeza de negritos e listas de Markdown gerados pela IA
    texto_limpo = str(texto).replace("**", "").replace("* ", " - ")
    # Substituição de caracteres não suportados pelo Latin-1 padrão (ISO-8859-1)
    return texto_limpo.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    """Converte o objeto FPDF em um fluxo de bytes binários para o Streamlit."""
    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        print(f"Erro crítico ao finalizar PDF: {e}")
        return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=8):
    """
    Desenha uma caixa de texto padronizada com rótulo superior.
    Fundo: Creme (#f8f9f0) | Borda: 1pt | Fonte: Helvetica.
    """
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240) # Cor Creme Diocesana
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def marcar_opcao(pdf, texto, condicao, x, y):
    """Desenha uma opção de seleção visual (X) baseada em condição booleana."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "", 9)
    mark = "X" if condicao else " "
    pdf.cell(0, 5, limpar_texto(f"{texto} ( {mark} )"), ln=0)

# ==============================================================================
# 2. CABEÇALHO OFICIAL DIOCESANO
# ==============================================================================

def adicionar_cabecalho_diocesano(pdf, titulo="", etapa=""):
    """
    Desenha o topo oficial da Diocese de Itabuna.
    Ajusta automaticamente a data para o fuso horário local (UTC-3).
    """
    if os.path.exists("logo.png"):
        # Logo posicionado conforme Leis de Ouro (10, 15, 22)
        pdf.image("logo.png", 10, 15, 22)
    
    # Data local ajustada para evitar virada de dia precoce no servidor
    data_local = (datetime.now(timezone.utc) + timedelta(hours=-3)).strftime('%d / %m / %Y')
    
    pdf.set_xy(38, 15)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153) # Azul Padrão (#417b99)
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, limpar_texto(f"Data: {data_local}"), ln=True, align='R')
    
    pdf.set_x(38)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(10)
    
    # A caixa de título superior só aparece se o título for informado explicitamente
    if titulo:
        y_topo = pdf.get_y()
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(10, y_topo, 190, 15, 'F')
        pdf.rect(10, y_topo, 190, 15)
        pdf.set_xy(10, y_topo + 4)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(65, 123, 153)
        pdf.cell(190, 7, limpar_texto(titulo), align='C')
        pdf.ln(18)
    else:
        pdf.ln(5)

# ==============================================================================
# 3. GESTÃO DE FICHAS DE INSCRIÇÃO (CATEQUIZANDOS)
# ==============================================================================

def _desenhar_corpo_ficha(pdf, dados):
    """
    Lógica central de desenho da ficha de inscrição.
    Implementa a proteção LGPD para menores (ambos os pais) e adultos.
    """
    y_base = pdf.get_y()
    idade_real = calcular_idade(dados.get('data_nascimento', ''))
    is_menor = idade_real < 18
    est_civil_raw = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper()
    is_adulto_cadastro = est_civil_raw != "N/A"
    
    # Bloco de Identificação da Etapa/Turma (Design Diocesano)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, y_base, 105, 20, 'F')
    pdf.rect(10, y_base, 105, 20)
    pdf.set_xy(12, y_base + 4)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(100, 6, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    
    ano_atual = (datetime.now(timezone.utc) + timedelta(hours=-3)).year
    pdf.set_xy(115, y_base)
    pdf.cell(30, 20, limpar_texto(f"Ano: {ano_atual}"), border=1, align='C')
    
    pdf.set_xy(145, y_base)
    pdf.set_font("helvetica", "B", 7)
    etapa_txt = str(dados.get('etapa', ''))
    pdf.multi_cell(55, 10, limpar_texto(f"Etapa: {etapa_txt}\nTurma: {etapa_txt}"), border=1, align='L')
    
    # Logística de Encontros
    y_next = y_base + 23
    pdf.set_xy(10, y_next)
    pdf.set_font("helvetica", "B", 10)
    turno = str(dados.get('turno', '')).upper()
    mark_m = "X" if "MANHÃ" in turno or "M" == turno else " "
    mark_t = "X" if "TARDE" in turno or "T" == turno else " "
    mark_n = "X" if "NOITE" in turno or "N" == turno else " "
    local = str(dados.get('local_encontro', '_______________________')).upper()
    pdf.cell(0, 8, limpar_texto(f"Turno: ( {mark_m} ) M  ( {mark_t} ) T  ( {mark_n} ) N        Local: {local}"), ln=True)

    # Seção: Identificação do Catequizando
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome:", dados.get('nome_completo', ''), 10, y, 190)
    y += 14
    desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", str(idade_real), 60, y, 25)
    
    pdf.set_xy(90, y + 4)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(20, 4, limpar_texto("Batizado:"), ln=0)
    marcar_opcao(pdf, "Sim", dados.get('batizado_sn') == 'SIM', 110, y + 4)
    marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 130, y + 4)
    
    y += 14
    desenhar_campo_box(pdf, "Morada (Endereço):", dados.get('endereco_completo', ''), 10, y, 190)
    y += 14
    desenhar_campo_box(pdf, "Telefone:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Tomar algum medicamento?", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    # Seção: Filiação
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True)
    
    y = pdf.get_y() + 2
    pdf.set_text_color(0, 0, 0)
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_mae','')} / {dados.get('tel_mae','')}", 125, y, 75)
    y += 14
    desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_pai','')} / {dados.get('tel_pai','')}", 125, y, 75)
    
    # Seção: Vida Eclesial e Sacramentos
    pdf.set_y(y + 16)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil e Vida Eclesial"), ln=True)
    
    pdf.set_text_color(0, 0, 0)
    y_check = pdf.get_y()
    ec = str(dados.get('estado_civil_pais_ou_proprio', '')).upper() if is_adulto_cadastro else str(dados.get('est_civil_pais', '')).upper()
    marcar_opcao(pdf, "Casados", "CASADO" in ec or "CASADOS" in ec, 10, y_check)
    marcar_opcao(pdf, "Convivem", ("CONVIVEM" in ec or "FACTO" in ec), 40, y_check)
    marcar_opcao(pdf, "Separados", "SEPARADO" in ec, 70, y_check)
    marcar_opcao(pdf, "Solteiro(a)", "SOLTEIRO" in ec, 100, y_check)
    
    pdf.ln(7)
    sac = str(dados.get('sacramentos_ja_feitos', '')).upper() if is_adulto_cadastro else str(dados.get('sac_pais', '')).upper()
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(45, 5, limpar_texto("Já tem o Sacramento:"), ln=0)
    marcar_opcao(pdf, "Batismo", "BATISMO" in sac, 50, pdf.get_y())
    marcar_opcao(pdf, "Eucaristia", "EUCARISTIA" in sac, 80, pdf.get_y())
    marcar_opcao(pdf, "Matrimônio", "MATRIMÔNIO" in sac, 110, pdf.get_y())
    
    # Seção: Termo de Consentimento LGPD (Rigor Jurídico)
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17) # Laranja Catequese
    pdf.cell(0, 6, limpar_texto("Termo de Consentimento"), ln=True)
    
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    nome_cat = dados.get('nome_completo', '________________')
    
    if is_menor:
        mae = str(dados.get('nome_mae', '')).strip()
        pai = str(dados.get('nome_pai', '')).strip()
        mae = "" if mae.upper() in ["N/A", "NONE", ""] else mae
        pai = "" if pai.upper() in ["N/A", "NONE", ""] else pai
        
        if mae and pai: responsaveis = f"{mae} e {pai}"
        elif mae: responsaveis = mae
        elif pai: responsaveis = pai
        else: responsaveis = str(dados.get('nome_responsavel', '________________________________'))
        
        texto_lgpd = (f"Nós/Eu, {responsaveis}, na qualidade de pais ou responsáveis legais pelo(a) catequizando(a) menor de idade, {nome_cat}, AUTORIZAMOS o uso da publicação da imagem do(a) referido(a) menor nos eventos realizados pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
        label_assinatura_principal = "Assinatura do(s) Responsável(is) Legal(is)"
    else:
        texto_lgpd = (f"Eu {nome_cat}, AUTORIZO o uso da publicação da minha imagem nos eventos realizados pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
        label_assinatura_principal = "Assinatura do(a) Catequizando(a)"
    
    pdf.multi_cell(0, 4, limpar_texto(texto_lgpd))
    
    # Bloco de Assinaturas
    pdf.ln(12)
    y_ass = pdf.get_y()
    pdf.line(10, y_ass, 90, y_ass)
    pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto(label_assinatura_principal), align='C')
    pdf.set_xy(110, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')

def gerar_ficha_cadastral_catequizando(dados):
    """Gera o PDF de um único catequizando."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, titulo="")
    _desenhar_corpo_ficha(pdf, dados)
    return finalizar_pdf(pdf)

def gerar_fichas_turma_completa(nome_turma, df_alunos):
    """Gera um único PDF com as fichas de todos os catequizandos da turma (uma por página)."""
    if df_alunos.empty:
        return None
    pdf = FPDF()
    for _, row in df_alunos.iterrows():
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf, titulo="")
        _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

# ==============================================================================
# 4. GESTÃO DE FICHAS DE CATEQUISTAS (EQUIPE)
# ==============================================================================

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    """Gera o prontuário ministerial completo do catequista com histórico de formações."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
    
    # Seção 1: Identificação
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("1. DADOS PESSOAIS E CONTATO"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, y, 45)
    y += 14
    desenhar_campo_box(pdf, "E-mail de Acesso:", dados.get('email', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Telefone/WhatsApp:", dados.get('telefone', ''), 125, y, 75)
    
    # Seção 2: Vida Ministerial
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E PASTORAL"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Início na Catequese:", formatar_data_br(dados.get('data_inicio_catequese', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Papel/Função:", dados.get('papel', 'CATEQUISTA'), 60, y, 50)
    desenhar_campo_box(pdf, "Turmas Vinculadas:", dados.get('turma_vinculada', 'N/A'), 115, y, 85)
    
    # Seção 3: Vida Sacramental
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("3. VIDA SACRAMENTAL"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Data Batismo:", formatar_data_br(dados.get('data_batismo', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Data Eucaristia:", formatar_data_br(dados.get('data_eucaristia', '')), 58, y, 45)
    desenhar_campo_box(pdf, "Data Crisma:", formatar_data_br(dados.get('data_crisma', '')), 106, y, 45)
    desenhar_campo_box(pdf, "Data Ministério:", formatar_data_br(dados.get('data_ministerio', '')), 154, y, 46)
    
    # Seção 4: Histórico de Formações
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("4. HISTÓRICO DE FORMAÇÃO CONTINUADA"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 7, "Data", border=1, fill=True, align='C')
    pdf.cell(100, 7, "Tema da Formação", border=1, fill=True)
    pdf.cell(60, 7, "Formador", border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if not df_formacoes.empty:
        for _, f in df_formacoes.iterrows():
            pdf.cell(30, 6, formatar_data_br(f['data']), border=1, align='C')
            pdf.cell(100, 6, limpar_texto(f['tema']), border=1)
            pdf.cell(60, 6, limpar_texto(f['formador']), border=1)
            pdf.ln()
    else:
        pdf.cell(190, 6, "Nenhuma formação registrada no sistema.", border=1, align='C', ln=True)
    
    # Seção 5: Declaração de Veracidade
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Declaração de Responsabilidade"), ln=True)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    declara = (f"Eu, {dados.get('nome', '')}, declaro para os devidos fins que as informações acima prestadas são verdadeiras e assumo o compromisso de zelar pela sã doutrina e pelas diretrizes da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima, atuando com fidelidade ao Evangelho e ao Magistério da Igreja.")
    pdf.multi_cell(0, 5, limpar_texto(declara))
    
    # Assinaturas
    pdf.ln(12)
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    
    return finalizar_pdf(pdf)

# ==============================================================================
# 5. RELATÓRIOS EXECUTIVOS (DIOCESANO, PASTORAL E SACRAMENTAL)
# ==============================================================================

def gerar_relatorio_diocesano_pdf(censo, turmas_list, sacramentos, proj_list, analise_ia):
    """
    Relatório de alta densidade para a Diocese.
    Mantém a assinatura original para compatibilidade com o main.py.
    """
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO DIOCESANO")
    
    # 1. Censo Populacional
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. CENSO POPULACIONAL (CATEQUIZANDOS)"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Total Geral", str(censo.get('total', '0')), 10, y, 60)
    desenhar_campo_box(pdf, "Infantil / Juvenil", str(censo.get('kids', '0')), 75, y, 60)
    desenhar_campo_box(pdf, "Jovens / Adultos", str(censo.get('adults', '0')), 140, y, 60)
    pdf.ln(18)

    # 2. Sacramentos do Ano
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto(f"2. SACRAMENTOS REALIZADOS EM {date.today().year}"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Sacramento", border=1, fill=True)
    pdf.cell(60, 7, "Infantil / Juvenil", border=1, fill=True, align='C')
    pdf.cell(60, 7, "Jovens / Adultos", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    # Mapeia os dados do dicionário sacramentos
    sac_list = [
        ("BATISMO", sacramentos.get('bat_k', '0'), sacramentos.get('bat_a', '0')),
        ("EUCARISTIA", sacramentos.get('euca_k', '0'), sacramentos.get('euca_a', '0')),
        ("CRISMA", "N/A", sacramentos.get('crisma_a', '0'))
    ]
    for nome, k, a in sac_list:
        pdf.cell(70, 7, nome, border=1)
        pdf.cell(60, 7, str(k), border=1, align='C')
        pdf.cell(60, 7, str(a), border=1, align='C')
        pdf.ln()
    pdf.ln(5)

    # 3. Análise IA e Diretrizes
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. ANÁLISE TÉCNICA E DIRETRIZES"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_interno_pdf(turmas_data, analise_ia):
    """
    Relatório analítico por turma com detalhes de logística e sacramentos.
    Mantém a assinatura original para compatibilidade com o main.py.
    """
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL ANALÍTICO")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("DETALHAMENTO POR TURMA E LOGÍSTICA"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(45, 7, "Turma / Etapa", border=1, fill=True)
    pdf.cell(40, 7, "Catequista(s)", border=1, fill=True)
    pdf.cell(35, 7, "Local / Dia", border=1, fill=True)
    pdf.cell(20, 7, "Catequiz.", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Batizados", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Eucaristia", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 7)
    # turmas_data deve ser uma lista de dicionários
    if isinstance(turmas_data, list):
        for t in turmas_data:
            if pdf.get_y() > 260:
                pdf.add_page()
                pdf.ln(10)
            pdf.cell(45, 6, limpar_texto(t.get('nome', 'N/A')), border=1)
            pdf.cell(40, 6, limpar_texto(t.get('catequistas', 'N/A')), border=1)
            pdf.cell(35, 6, limpar_texto(f"{t.get('local', 'N/A')} / {t.get('dia', 'N/A')}"), border=1)
            pdf.cell(20, 6, str(t.get('total', '0')), border=1, align='C')
            pdf.cell(25, 6, str(t.get('batizados', '0')), border=1, align='C')
            pdf.cell(25, 6, str(t.get('eucaristia', '0')), border=1, align='C')
            pdf.ln()
    
    pdf.ln(10)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("ANÁLISE PASTORAL E EVANGELIZAÇÃO"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    """Auditoria sacramental nominal com foco em pendências."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "AUDITORIA SACRAMENTAL E CENSO DE INICIAÇÃO CRISTÃ")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. RESUMO GERAL DE SACRAMENTOS"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Batismos (Ano)", str(stats.get('bat_ano', '0')), 10, y, 60)
    desenhar_campo_box(pdf, "Batizados (Kids)", str(stats.get('bat_k', '0')), 75, y, 60)
    desenhar_campo_box(pdf, "Batizados (Adultos)", str(stats.get('bat_a', '0')), 140, y, 60)
    pdf.ln(18)
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. DIAGNÓSTICO NOMINAL E PENDÊNCIAS"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 7, "Turma", border=1, fill=True)
    pdf.cell(20, 7, "Freq.", border=1, fill=True, align='C')
    pdf.cell(20, 7, "Batiz.", border=1, fill=True, align='C')
    pdf.cell(100, 7, "Catequizandos Pendentes de Batismo", border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 7)
    for t in analise_turmas:
        if pdf.get_y() > 250:
            pdf.add_page()
            pdf.ln(10)
        pdf.cell(50, 6, limpar_texto(t.get('turma', 'N/A')), border=1)
        pdf.cell(20, 6, t.get('freq', '0%'), border=1, align='C')
        pdf.cell(20, 6, str(t.get('batizados', '0')), border=1, align='C')
        nomes = ", ".join(t.get('nomes_pendentes', [])) if t.get('nomes_pendentes') else "NENHUM"
        if t.get('pendentes', 0) > 0:
            pdf.set_text_color(224, 61, 17)
        pdf.cell(100, 6, limpar_texto(nomes), border=1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    pdf.ln(10)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. PARECER TÉCNICO E RECOMENDAÇÕES PASTORAIS"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    """Perfil individualizado da turma para o catequista."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"PERFIL DA TURMA: {nome_turma}", etapa=nome_turma)
    pdf.ln(10)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

# ==============================================================================
# 6. FUNÇÕES DE CENSO E UTILITÁRIOS PASTORAIS
# ==============================================================================

def sugerir_etapa(data_nascimento):
    """Sugere a etapa de iniciação cristã baseada na idade cronológica."""
    idade = calcular_idade(data_nascimento)
    if 5 <= idade <= 6: return "PRÉ"
    elif 7 <= idade <= 8: return "PRIMEIRA ETAPA"
    elif 9 <= idade <= 10: return "SEGUNDA ETAPA"
    elif 11 <= idade <= 14: return "TERCEIRA ETAPA"
    else: return "ADULTOS TURMA EUCARISTIA/BATISMO"

def eh_aniversariante_da_semana(data_nasc_str):
    """Verifica se o catequizando faz aniversário nos próximos 7 dias (Fuso UTC-3)."""
    try:
        d_str = formatar_data_br(data_nasc_str)
        if d_str == "N/A": return False
        nasc = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        nasc_este_ano = nasc.replace(year=hoje.year)
        return 0 <= (nasc_este_ano - hoje).days <= 7
    except:
        return False

def converter_para_data(valor_str):
    """Converte string para objeto date com segurança para widgets Streamlit."""
    if not valor_str or str(valor_str).strip() in ["None", "", "N/A"]:
        return date.today()
    try:
        d_str = formatar_data_br(valor_str)
        return datetime.strptime(d_str, "%d/%m/%Y").date()
    except:
        return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    """Regra Diocesana: 5+ anos + sacramentos = APTO. Com rito = MINISTRO."""
    if d_ministerio and str(d_ministerio).strip() not in ["None", "", "N/A"]:
        return "MINISTRO", 0 
    try:
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        inicio = datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
        tem_s = all([str(x).strip() not in ["None", "", "N/A"] for x in [d_batismo, d_euca, d_crisma]])
        return ("APTO", anos) if (anos >= 5 and tem_s) else ("EM_CAMINHADA", anos)
    except:
        return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    """Lista aniversariantes do dia atual (Fuso UTC-3)."""
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    niver = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.day == hoje.day and dt.month == hoje.month:
                    niver.append(f"😇 Catequizando: **{r['nome_completo']}**")
    return niver

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    """Consolida aniversariantes do mês para o Dashboard Geral."""
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A" and datetime.strptime(d, "%d/%m/%Y").month == hoje.month:
                lista.append({
                    'dia': datetime.strptime(d, "%d/%m/%Y").day, 
                    'nome': r['nome_completo'], 
                    'tipo': 'CATEQUIZANDO', 
                    'info': r['etapa']
                })
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    """Lista aniversariantes do mês para turmas específicas."""
    if df_cat.empty:
        return pd.DataFrame()
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    for _, r in df_cat.iterrows():
        d = formatar_data_br(r['data_nascimento'])
        if d != "N/A" and datetime.strptime(d, "%d/%m/%Y").month == hoje.month:
            lista.append({
                'nome_completo': r['nome_completo'], 
                'dia': datetime.strptime(d, "%d/%m/%Y").day, 
                'etapa': r['etapa']
            })
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

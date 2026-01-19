# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 2.6.0 - REFINAMENTO EXECUTIVO FINAL (GESTÃO FAMILIAR)
# MISSÃO: Motor de Documentação, Auditoria Sacramental e Conformidade LGPD.
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
    """Converte diversos formatos de data para o padrão brasileiro DD/MM/AAAA."""
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    s = str(valor).strip().split('.')[0]
    # Caso esteja em formato AAAAMMDD
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    # Caso esteja em formato AAAA-MM-DD
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    try:
        dt = pd.to_datetime(valor)
        if pd.notnull(dt):
            return dt.strftime('%d/%m/%Y')
    except: pass
    return s

def calcular_idade(data_nascimento):
    """Calcula a idade exata forçando o fuso horário UTC-3."""
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]:
        return 0
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except: return 0

def limpar_texto(texto):
    """Remove artefatos de Markdown e garante compatibilidade com Latin-1 para PDF."""
    if not texto: return ""
    # Remove negritos de IA e outros caracteres especiais
    texto_limpo = str(texto).replace("**", "").replace("* ", " - ").replace("*", "")
    # Substituições comuns para evitar erro de encoding no FPDF
    return texto_limpo.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    """Finaliza a geração do PDF e retorna o buffer de bytes."""
    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        print(f"Erro ao finalizar PDF: {e}")
        return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=8):
    """Desenha uma caixa de formulário com fundo creme (#f8f9f0) e label superior."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(65, 123, 153) # Azul Paroquial
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240) # Fundo Creme
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def marcar_opcao(pdf, texto, condicao, x, y):
    """Desenha um seletor de opção (X) ou vazio."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "", 9)
    mark = "X" if condicao else " "
    pdf.cell(0, 5, limpar_texto(f"{texto} ( {mark} )"), ln=0)

# ==============================================================================
# 2. CABEÇALHO OFICIAL DIOCESANO
# ==============================================================================

def adicionar_cabecalho_diocesano(pdf, titulo="", etapa=""):
    """Adiciona o brasão e as informações oficiais da paróquia e diocese."""
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 15, 22)
    
    data_local = (datetime.now(timezone.utc) + timedelta(hours=-3)).strftime('%d / %m / %Y')
    
    pdf.set_xy(38, 15)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153) 
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, limpar_texto(f"Data: {data_local}"), ln=True, align='R')
    
    pdf.set_x(38)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(10)
    
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
    """Desenha o corpo detalhado da ficha de inscrição com 29 colunas e LGPD."""
    y_base = pdf.get_y()
    idade_real = calcular_idade(dados.get('data_nascimento', ''))
    is_menor = idade_real < 18
    
    # Cabeçalho da Ficha
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, y_base, 105, 20, 'F')
    pdf.rect(10, y_base, 105, 20)
    pdf.set_xy(12, y_base + 4)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(100, 6, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    
    pdf.set_xy(115, y_base)
    pdf.cell(30, 20, limpar_texto(f"Ano: {date.today().year}"), border=1, align='C')
    
    pdf.set_xy(145, y_base)
    pdf.set_font("helvetica", "B", 7)
    pdf.multi_cell(55, 10, limpar_texto(f"Etapa: {dados.get('etapa', '')}"), border=1, align='L')
    
    # Turno e Local
    y_next = y_base + 23
    pdf.set_xy(10, y_next)
    pdf.set_font("helvetica", "B", 10)
    turno = str(dados.get('turno', '')).upper()
    mark_m = "X" if "MANHÃ" in turno or "M" == turno else " "
    mark_t = "X" if "TARDE" in turno or "T" == turno else " "
    mark_n = "X" if "NOITE" in turno or "N" == turno else " "
    local = str(dados.get('local_encontro', '_______________________')).upper()
    pdf.cell(0, 8, limpar_texto(f"Turno: ( {mark_m} ) M  ( {mark_t} ) T  ( {mark_n} ) N        Local: {local}"), ln=True)

    # Seção 1: Identificação
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 190)
    
    y += 14
    desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", str(idade_real), 60, y, 25)
    
    pdf.set_xy(90, y + 4)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(20, 4, limpar_texto("Batizado:"), ln=0)
    marcar_opcao(pdf, "Sim", dados.get('batizado_sn') == 'SIM', 110, y + 4)
    marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 130, y + 4)
    
    y += 14
    desenhar_campo_box(pdf, "Morada (Endereço Completo):", dados.get('endereco_completo', ''), 10, y, 190)
    
    y += 14
    desenhar_campo_box(pdf, "Telefone/WhatsApp:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Toma algum medicamento? (Qual/Por quê?):", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    # Seção 2: Filiação
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True, align='C')
    
    y = pdf.get_y() + 2
    pdf.set_text_color(0, 0, 0)
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_mae','')} / {dados.get('tel_mae','')}", 125, y, 75)
    
    y += 14
    desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_pai','')} / {dados.get('tel_pai','')}", 125, y, 75)
    
    # Seção 3: Vida Eclesial
    pdf.set_y(y + 16)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil e Vida Eclesial"), ln=True)
    
    pdf.set_text_color(0, 0, 0)
    y_check = pdf.get_y()
    ec = str(dados.get('est_civil_pais', '')).upper()
    marcar_opcao(pdf, "Casados", "CASADO" in ec, 10, y_check)
    marcar_opcao(pdf, "Convivem", "CONVIVEM" in ec or "FACTO" in ec, 40, y_check)
    marcar_opcao(pdf, "Separados", "SEPARADO" in ec, 70, y_check)
    marcar_opcao(pdf, "Solteiro(a)", "SOLTEIRO" in ec, 100, y_check)
    
    pdf.ln(7)
    sac = str(dados.get('sac_pais', '')).upper()
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(45, 5, limpar_texto("Sacramentos dos Pais:"), ln=0)
    marcar_opcao(pdf, "Batismo", "BATISMO" in sac, 50, pdf.get_y())
    marcar_opcao(pdf, "Eucaristia", "EUCARISTIA" in sac, 80, pdf.get_y())
    marcar_opcao(pdf, "Matrimônio", "MATRIMÔNIO" in sac, 110, pdf.get_y())
    
    # Seção 4: LGPD (Termo Integral)
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Termo de Consentimento LGPD (Lei Geral de Proteção de Dados)"), ln=True)
    
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    nome_cat = dados.get('nome_completo', '________________')
    
    if is_menor:
        mae = str(dados.get('nome_mae', '')).strip()
        pai = str(dados.get('nome_pai', '')).strip()
        resp = f"{mae} e {pai}" if mae and pai else (mae or pai or "Responsável Legal")
        texto_lgpd = (f"Nós/Eu, {resp}, na qualidade de pais ou responsáveis legais pelo(a) catequizando(a) menor de idade, {nome_cat}, "
                      f"AUTORIZAMOS o uso da publicação da imagem do(a) referido(a) menor nos eventos realizados pela Pastoral da Catequese "
                      f"da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, "
                      f"conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
        label_ass = "Assinatura do(s) Responsável(is) Legal(is)"
    else:
        texto_lgpd = (f"Eu {nome_cat}, AUTORIZO o uso da publicação da minha imagem nos eventos realizados pela Pastoral da Catequese "
                      f"da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, "
                      f"conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
        label_ass = "Assinatura do(a) Catequizando(a)"
        
    pdf.multi_cell(0, 4, limpar_texto(texto_lgpd))
    
    # Assinaturas
    pdf.ln(12)
    y_ass = pdf.get_y()
    pdf.line(10, y_ass, 90, y_ass)
    pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(110, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista / Coordenação"), align='C')

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf)
    _desenhar_corpo_ficha(pdf, dados)
    return finalizar_pdf(pdf)

def gerar_fichas_turma_completa(nome_turma, df_alunos):
    if df_alunos.empty: return None
    pdf = FPDF()
    for _, row in df_alunos.iterrows():
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf)
        _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

# ==============================================================================
# 4. GESTÃO DE FICHAS DE CATEQUISTAS (EQUIPE)
# ==============================================================================

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
    
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
    desenhar_campo_box(pdf, "Telefone:", dados.get('telefone', ''), 125, y, 75)
    
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E SACRAMENTAL"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Início na Catequese:", formatar_data_br(dados.get('data_inicio_catequese', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Batismo:", formatar_data_br(dados.get('data_batismo', '')), 58, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(dados.get('data_eucaristia', '')), 106, y, 45)
    desenhar_campo_box(pdf, "Crisma:", formatar_data_br(dados.get('data_crisma', '')), 154, y, 46)
    
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("3. HISTÓRICO DE FORMAÇÃO CONTINUADA"), ln=True, fill=True, align='C')
    
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
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Declaração de Veracidade e Compromisso"), ln=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    declara = (f"Eu, {dados.get('nome', '')}, declaro que as informações acima são verdadeiras e assumo o compromisso "
               f"de zelar pelas diretrizes da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima.")
    pdf.multi_cell(0, 5, limpar_texto(declara))
    
    pdf.ln(12)
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador Paroquial"), align='C')
    
    return finalizar_pdf(pdf)

# ==============================================================================
# 5. GESTÃO FAMILIAR (NOVO RELATÓRIO DE VISITAÇÃO)
# ==============================================================================

def gerar_relatorio_familia_pdf(dados_familia, filhos_lista):
    """Gera ficha para visitação domiciliar focada no núcleo familiar."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA DE VISITAÇÃO PASTORAL / FAMILIAR")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("1. NÚCLEO FAMILIAR (PAIS E RESPONSÁVEIS)"), ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    
    desenhar_campo_box(pdf, "Mãe:", dados_familia.get('nome_mae', 'N/A'), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados_familia.get('profissao_mae','')} / {dados_familia.get('tel_mae','')}", 125, y, 75)
    
    y += 14
    desenhar_campo_box(pdf, "Pai:", dados_familia.get('nome_pai', 'N/A'), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados_familia.get('profissao_pai','')} / {dados_familia.get('tel_pai','')}", 125, y, 75)
    
    y += 14
    desenhar_campo_box(pdf, "Estado Civil dos Pais:", dados_familia.get('est_civil_pais', 'N/A'), 10, y, 90)
    desenhar_campo_box(pdf, "Sacramentos dos Pais:", dados_familia.get('sac_pais', 'N/A'), 105, y, 95)
    
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. FILHOS MATRICULADOS NA CATEQUESE"), ln=True, fill=True)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Nome do Catequizando", border=1, fill=True)
    pdf.cell(60, 7, "Turma / Etapa Atual", border=1, fill=True)
    pdf.cell(50, 7, "Status", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    for f in filhos_lista:
        pdf.cell(80, 7, limpar_texto(f['nome']), border=1)
        pdf.cell(60, 7, limpar_texto(f['etapa']), border=1)
        pdf.cell(50, 7, limpar_texto(f['status']), border=1, align='C')
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, "Relato da Visita e Necessidades da Família:", ln=True)
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(10, pdf.get_y(), 190, 50)
    pdf.ln(55)
    
    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Este documento contém dados sensíveis. O manuseio deve ser restrito à coordenação paroquial para fins de acompanhamento pastoral.")
    
    return finalizar_pdf(pdf)

# ==============================================================================
# 6. RELATÓRIOS EXECUTIVOS (DIOCESANO, PASTORAL E SACRAMENTAL)
# ==============================================================================

def gerar_relatorio_diocesano_v4(dados_censo, equipe_stats, sac_ano, sac_censo, logistica_lista, formacoes_lista, analise_ia):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO DIOCESANO")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. CENSO POPULACIONAL E ESTRUTURAL"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Total Catequizandos", str(dados_censo.get('total_cat', '0')), 10, y, 45)
    desenhar_campo_box(pdf, "Turmas Infantil/Juv.", str(dados_censo.get('t_infantil', '0')), 58, y, 45)
    desenhar_campo_box(pdf, "Turmas Jovens/Adultos", str(dados_censo.get('t_adultos', '0')), 106, y, 45)
    desenhar_campo_box(pdf, "Equipe Catequética", str(dados_censo.get('total_equipe', '0')), 154, y, 46)
    
    pdf.ln(18)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. QUALIFICAÇÃO SACRAMENTAL DA EQUIPE"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(100, 7, "Indicador de Fé", border=1, fill=True)
    pdf.cell(45, 7, "Quantidade", border=1, fill=True, align='C')
    pdf.cell(45, 7, "Percentual", border=1, fill=True, align='C')
    pdf.ln()
    
    total_e = int(dados_censo.get('total_equipe', 1))
    indicadores = [
        ("Batismo", equipe_stats.get('bat', 0)),
        ("Eucaristia", equipe_stats.get('euca', 0)),
        ("Crisma", equipe_stats.get('crisma', 0)),
        ("Ministros de Catequese", equipe_stats.get('ministros', 0))
    ]
    
    for desc, qtd in indicadores:
        perc = (int(qtd)/total_e)*100 if total_e > 0 else 0
        pdf.cell(100, 7, limpar_texto(f" {desc}"), border=1)
        pdf.cell(45, 7, str(qtd), border=1, align='C')
        pdf.cell(45, 7, f"{perc:.1f}%", border=1, align='C')
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. PARECER TÉCNICO DA AUDITORIA"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_v3(turmas_detalhadas, totais_gerais, analise_ia):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL ANALÍTICO")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("DESEMPENHO POR TURMA E ETAPA"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Turma", border=1, fill=True)
    pdf.cell(25, 7, "Batizados", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Eucaristia", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Crisma", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Freq.", border=1, fill=True, align='C')
    pdf.cell(20, 7, "Total", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    for t in turmas_detalhadas:
        pdf.cell(70, 7, limpar_texto(t['nome']), border=1)
        pdf.cell(25, 7, str(t['batizados']), border=1, align='C')
        pdf.cell(25, 7, str(t['eucaristia']), border=1, align='C')
        pdf.cell(25, 7, str(t['crisma']), border=1, align='C')
        pdf.cell(25, 7, f"{t['frequencia']}%", border=1, align='C')
        pdf.cell(20, 7, str(t['total']), border=1, align='C')
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("ANÁLISE DE ENGAJAMENTO E EVASÃO"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_v2(stats_gerais, analise_turmas, impedimentos_lista, analise_ia):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "AUDITORIA SACRAMENTAL E CENSO DE IVC")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. QUADRO GERAL DE SACRAMENTALIZAÇÃO"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 7, "Sacramento", border=1, fill=True)
    pdf.cell(70, 7, "Infantil / Juvenil", border=1, fill=True, align='C')
    pdf.cell(70, 7, "Jovens / Adultos", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    for n, k, a in [("BATISMO", stats_gerais['bat_k'], stats_gerais['bat_a']), 
                    ("EUCARISTIA", stats_gerais['euca_k'], stats_gerais['euca_a']), 
                    ("CRISMA", "N/A", stats_gerais['crisma_a'])]:
        pdf.cell(50, 7, f" {n}", border=1)
        pdf.cell(70, 7, str(k), border=1, align='C')
        pdf.cell(70, 7, str(a), border=1, align='C')
        pdf.ln()
        
    pdf.ln(5)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. DIAGNÓSTICO DE IMPEDIMENTOS CANÔNICOS"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Catequizando", border=1, fill=True)
    pdf.cell(50, 7, "Turma", border=1, fill=True)
    pdf.cell(70, 7, "Situação Matrimonial / Sacramental", border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if impedimentos_lista:
        for imp in impedimentos_lista:
            pdf.cell(70, 6, limpar_texto(imp['nome']), border=1)
            pdf.cell(50, 6, limpar_texto(imp['turma']), border=1)
            pdf.cell(70, 6, limpar_texto(imp['situacao']), border=1)
            pdf.ln()
    else:
        pdf.cell(190, 6, "Nenhum impedimento registrado.", border=1, align='C', ln=True)
        
    pdf.ln(5)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. PARECER DO AUDITOR IA"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

# ==============================================================================
# 7. UTILITÁRIOS PASTORAIS E CENSO
# ==============================================================================

def sugerir_etapa(data_nascimento):
    idade = calcular_idade(data_nascimento)
    if idade <= 6: return "PRÉ"
    elif idade <= 8: return "PRIMEIRA ETAPA"
    elif idade <= 10: return "SEGUNDA ETAPA"
    elif idade <= 13: return "TERCEIRA ETAPA"
    return "ADULTOS"

def eh_aniversariante_da_semana(data_nasc_str):
    try:
        d_str = formatar_data_br(data_nasc_str)
        if d_str == "N/A": return False
        nasc = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        nasc_este_ano = nasc.replace(year=hoje.year)
        diff = (nasc_este_ano - hoje).days
        return 0 <= diff <= 7
    except: return False

def converter_para_data(valor_str):
    if not valor_str or str(valor_str).strip() in ["None", "", "N/A"]: return date.today()
    try:
        return datetime.strptime(formatar_data_br(valor_str), "%d/%m/%Y").date()
    except: return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    """Verifica se o catequista está apto ou é ministro conforme regras diocesanas."""
    if d_ministerio and str(d_ministerio).strip() not in ["", "N/A", "None"]:
        return "MINISTRO", 0 
    try:
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        inicio = datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
        tem_s = all([str(x).strip() not in ["", "N/A", "None"] for x in [d_batismo, d_euca, d_crisma]])
        if anos >= 5 and tem_s: return "APTO", anos
        return "EM_CAMINHADA", anos
    except: return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
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
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.month == hoje.month:
                    lista.append({'dia': dt.day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    for _, r in df_cat.iterrows():
        d = formatar_data_br(r['data_nascimento'])
        if d != "N/A":
            dt = datetime.strptime(d, "%d/%m/%Y")
            if dt.month == hoje.month:
                lista.append({'nome_completo': r['nome_completo'], 'dia': dt.day, 'etapa': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

# --- SUBSTITUA A FUNÇÃO ANTERIOR POR ESTA NO utils.py ---

def gerar_relatorio_local_turma_v2(nome_turma, metricas, listas, analise_ia):
    """Gera o Relatório de Inteligência Pastoral específico de uma turma (Versão Final)."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"AUDITORIA PASTORAL: {nome_turma}")
    
    # 1. INDICADORES ESTRUTURAIS
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. INDICADORES ESTRUTURAIS E ADESÃO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    
    desenhar_campo_box(pdf, "Catequistas na Turma", str(metricas['qtd_catequistas']), 10, y, 45)
    desenhar_campo_box(pdf, "Total Catequizandos", str(metricas['qtd_cat']), 58, y, 45)
    desenhar_campo_box(pdf, "Frequência Global", f"{metricas['freq_global']}%", 106, y, 45)
    desenhar_campo_box(pdf, "Idade Média", f"{metricas['idade_media']} anos", 154, y, 46)
    pdf.ln(18)

    # 2. TAXA DE PRESENÇA MENSAL
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. EVOLUÇÃO DA PRESENÇA POR MÊS"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(95, 7, "Mês / Ano", border=1, fill=True, align='C'); pdf.cell(95, 7, "Taxa de Presença", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 9)
    for m in metricas['freq_mensal']:
        pdf.cell(95, 6, limpar_texto(m['mes']), border=1, align='C')
        pdf.cell(95, 6, f"{m['taxa']}%", border=1, align='C'); pdf.ln()
    pdf.ln(5)

    # 3. LISTA NOMINAL E EVASÃO
    pdf.set_fill_color(224, 61, 17); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. LISTA NOMINAL E ALERTA DE EVASÃO"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(120, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(70, 7, "Status / Faltas", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    for cat in listas['geral']:
        # Destaca em vermelho quem tem 2 ou mais faltas
        if cat['faltas'] >= 2: pdf.set_text_color(224, 61, 17)
        else: pdf.set_text_color(0, 0, 0)
        
        info_faltas = f"ATIVO ({cat['faltas']} faltas)" if cat['faltas'] > 0 else "ATIVO (100% Freq.)"
        pdf.cell(120, 6, limpar_texto(cat['nome']), border=1)
        pdf.cell(70, 6, limpar_texto(info_faltas), border=1, align='C'); pdf.ln()
    pdf.set_text_color(0, 0, 0); pdf.ln(5)

    # 4. HISTÓRICO SACRAMENTAL REGISTRADO
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("4. SACRAMENTOS RECEBIDOS (REGISTRO PAROQUIAL)"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Nome", border=1, fill=True); pdf.cell(50, 7, "Sacramento", border=1, fill=True, align='C'); pdf.cell(60, 7, "Data do Registro", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    if listas['sac_recebidos']:
        for s in listas['sac_recebidos']:
            pdf.cell(80, 6, limpar_texto(s['nome']), border=1)
            pdf.cell(50, 6, limpar_texto(s['tipo']), border=1, align='C')
            pdf.cell(60, 6, formatar_data_br(s['data']), border=1, align='C'); pdf.ln()
    else:
        pdf.cell(190, 6, "Nenhum sacramento registrado para esta turma no ano vigente.", border=1, align='C', ln=True)

    # 5. PARECER TÉCNICO IA
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("5. PARECER TÉCNICO E ORIENTAÇÃO PASTORAL"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))

    return finalizar_pdf(pdf)

# --- ADICIONAR AO utils.py ---

def gerar_fichas_paroquia_total(df_catequizandos):
    """Gera um PDF único com as fichas de inscrição de TODOS os catequizandos da paróquia."""
    if df_catequizandos.empty: return None
    pdf = FPDF()
    # Ordenação por Turma e Nome para facilitar a entrega física
    df_ordenado = df_catequizandos.sort_values(by=['etapa', 'nome_completo'])
    for _, row in df_ordenado.iterrows():
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf)
        _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

def gerar_auditoria_lote_completa(df_turmas, df_cat, df_pres, df_recebidos):
    """
    Gera um Dossiê Paroquial contendo a auditoria completa de cada turma.
    Blindagem contra KeyError e inconsistência de colunas.
    """
    pdf = FPDF()
    
    # Normalização de colunas para busca resiliente
    col_id_cat = 'id_catequizando'
    
    for _, t in df_turmas.iterrows():
        t_nome = t['nome_turma']
        alunos_t = df_cat[df_cat['etapa'] == t_nome]
        
        if not alunos_t.empty:
            pdf.add_page()
            adicionar_cabecalho_diocesano(pdf, f"AUDITORIA INTEGRAL: {t_nome}")
            
            # --- 1. INDICADORES ESTRUTURAIS ---
            pres_t = df_pres[df_pres['id_turma'] == t_nome] if not df_pres.empty else pd.DataFrame()
            freq_g = 0.0
            lista_mensal = []
            
            if not pres_t.empty:
                pres_t['status_num'] = pres_t['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                freq_g = round(pres_t['status_num'].mean() * 100, 1)
                
                try:
                    pres_t['data_dt'] = pd.to_datetime(pres_t['data_encontro'], dayfirst=True, errors='coerce')
                    pres_t['mes_ano'] = pres_t['data_dt'].dt.strftime('%m/%Y')
                    mensal = pres_t.groupby('mes_ano')['status_num'].mean() * 100
                    for mes, taxa in mensal.items():
                        lista_mensal.append({'mes': mes, 'taxa': round(taxa, 1)})
                except: pass

            idades = [calcular_idade(d) for d in alunos_t['data_nascimento'].tolist()]
            id_med = round(sum(idades)/len(idades), 1) if idades else 0
            qtd_catequistas = len(str(t['catequista_responsavel']).split(','))

            pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto("1. INDICADORES ESTRUTURAIS"), ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
            desenhar_campo_box(pdf, "Catequistas", str(qtd_catequistas), 10, y, 45)
            desenhar_campo_box(pdf, "Catequizandos", str(len(alunos_t)), 58, y, 45)
            desenhar_campo_box(pdf, "Frequência Global", f"{freq_g}%", 106, y, 45)
            desenhar_campo_box(pdf, "Idade Média", f"{id_med} anos", 154, y, 46)
            pdf.ln(18)

            # --- 2. EVOLUÇÃO DA PRESENÇA POR MÊS ---
            pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, limpar_texto("2. EVOLUÇÃO DA PRESENÇA POR MÊS"), ln=True, fill=True, align='C')
            pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
            pdf.cell(95, 7, "Mês / Ano", border=1, fill=True, align='C'); pdf.cell(95, 7, "Taxa de Presença", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 9)
            if lista_mensal:
                for m in lista_mensal:
                    pdf.cell(95, 6, limpar_texto(m['mes']), border=1, align='C')
                    pdf.cell(95, 6, f"{m['taxa']}%", border=1, align='C'); pdf.ln()
            else: pdf.cell(190, 6, "Sem dados históricos de presença.", border=1, align='C', ln=True)
            pdf.ln(5)

            # --- 3. LISTA NOMINAL E ALERTA DE EVASÃO ---
            pdf.set_fill_color(224, 61, 17); pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, limpar_texto("3. LISTA NOMINAL E ALERTA DE EVASÃO"), ln=True, fill=True, align='C')
            pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
            pdf.cell(120, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(70, 7, "Status / Faltas", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 8)
            for _, r in alunos_t.iterrows():
                faltas = 0
                if not pres_t.empty and 'id_catequizando' in pres_t.columns:
                    faltas = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')])
                
                if faltas >= 2: pdf.set_text_color(224, 61, 17)
                else: pdf.set_text_color(0, 0, 0)
                info = f"ATIVO ({faltas} faltas)" if faltas > 0 else "ATIVO (100% Freq.)"
                pdf.cell(120, 6, limpar_texto(r['nome_completo']), border=1)
                pdf.cell(70, 6, limpar_texto(info), border=1, align='C'); pdf.ln()
            pdf.set_text_color(0, 0, 0); pdf.ln(5)

            # --- 4. SACRAMENTOS RECEBIDOS (REGISTRO PAROQUIAL) ---
            pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, limpar_texto("4. SACRAMENTOS RECEBIDOS (REGISTRO PAROQUIAL)"), ln=True, fill=True, align='C')
            pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
            pdf.cell(80, 7, "Nome", border=1, fill=True); pdf.cell(50, 7, "Sacramento", border=1, fill=True, align='C'); pdf.cell(60, 7, "Data do Registro", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 8)
            
            # BLINDAGEM CONTRA KEYERROR: Verifica se a coluna existe antes de filtrar
            if not df_recebidos.empty and col_id_cat in df_recebidos.columns:
                sac_turma = df_recebidos[df_recebidos[col_id_cat].isin(alunos_t['id_catequizando'].tolist())]
                if not sac_turma.empty:
                    for _, s in sac_turma.iterrows():
                        pdf.cell(80, 6, limpar_texto(s.get('nome', 'N/A')), border=1)
                        pdf.cell(50, 6, limpar_texto(s.get('tipo', 'N/A')), border=1, align='C')
                        pdf.cell(60, 6, formatar_data_br(s.get('data', 'N/A')), border=1, align='C'); pdf.ln()
                else:
                    pdf.cell(190, 6, "Nenhum sacramento registrado para esta turma.", border=1, align='C', ln=True)
            else:
                pdf.cell(190, 6, "Dados de sacramentos nominais indisponíveis ou coluna incorreta.", border=1, align='C', ln=True)
            
    return finalizar_pdf(pdf)

def gerar_fichas_catequistas_lote(df_equipe, df_pres_form, df_formacoes):
    """Gera um PDF único com as fichas de todos os catequistas, incluindo histórico de formações."""
    if df_equipe.empty: return None
    pdf = FPDF()
    for _, u in df_equipe.iterrows():
        # Busca histórico de formações específico deste catequista
        forms_participadas = pd.DataFrame()
        if not df_pres_form.empty and not df_formacoes.empty:
            minhas_forms = df_pres_form[df_pres_form['email_participante'] == u['email']]
            if not minhas_forms.empty:
                forms_participadas = minhas_forms.merge(df_formacoes, on='id_formacao', how='inner')
        
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
        
        # --- SEÇÃO 1: DADOS PESSOAIS ---
        pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 7, limpar_texto("1. DADOS PESSOAIS E CONTATO"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Nome Completo:", u.get('nome', ''), 10, y, 135)
        desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(u.get('data_nascimento', '')), 150, y, 45)
        y += 14
        desenhar_campo_box(pdf, "E-mail:", u.get('email', ''), 10, y, 110)
        desenhar_campo_box(pdf, "Telefone:", u.get('telefone', ''), 125, y, 75)
        
        # --- SEÇÃO 2: VIDA MINISTERIAL ---
        pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E SACRAMENTAL"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Início Catequese:", formatar_data_br(u.get('data_inicio_catequese', '')), 10, y, 45)
        desenhar_campo_box(pdf, "Batismo:", formatar_data_br(u.get('data_batismo', '')), 58, y, 45)
        desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(u.get('data_eucaristia', '')), 106, y, 45)
        desenhar_campo_box(pdf, "Crisma:", formatar_data_br(u.get('data_crisma', '')), 154, y, 46)
        
        # --- SEÇÃO 3: HISTÓRICO DE FORMAÇÕES ---
        pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, limpar_texto("3. HISTÓRICO DE FORMAÇÃO CONTINUADA"), ln=True, fill=True, align='C')
        pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
        pdf.cell(30, 7, "Data", border=1, fill=True, align='C'); pdf.cell(100, 7, "Tema", border=1, fill=True); pdf.cell(60, 7, "Formador", border=1, fill=True); pdf.ln()
        pdf.set_font("helvetica", "", 8)
        if not forms_participadas.empty:
            for _, f in forms_participadas.iterrows():
                pdf.cell(30, 6, formatar_data_br(f['data']), border=1, align='C')
                pdf.cell(100, 6, limpar_texto(f['tema']), border=1)
                pdf.cell(60, 6, limpar_texto(f['formador']), border=1); pdf.ln()
        else:
            pdf.cell(190, 6, "Nenhuma formação registrada.", border=1, align='C', ln=True)
            
        pdf.ln(10); y_ass = pdf.get_y(); pdf.line(15, y_ass, 95, y_ass); pdf.line(115, y_ass, 195, y_ass)
        pdf.set_xy(15, y_ass + 1); pdf.set_font("helvetica", "B", 8); pdf.cell(80, 5, "Assinatura Catequista", align='C')
        pdf.set_xy(115, y_ass + 1); pdf.cell(80, 5, "Assinatura Coordenador", align='C')
    return finalizar_pdf(pdf)

# ==============================================================================
# 8. ALIASES DE COMPATIBILIDADE (NÃO REMOVER)
# ==============================================================================
gerar_relatorio_diocesano_pdf = gerar_relatorio_diocesano_v4
gerar_relatorio_pastoral_interno_pdf = gerar_relatorio_pastoral_v3
gerar_relatorio_diocesano_v2 = gerar_relatorio_diocesano_v4
gerar_relatorio_pastoral_v2 = gerar_relatorio_pastoral_v3
gerar_relatorio_sacramentos_tecnico_pdf = gerar_relatorio_sacramentos_tecnico_v2
gerar_pdf_perfil_turma = lambda n, m, a, l: finalizar_pdf(FPDF()) # Placeholder para compatibilidade
gerar_relatorio_local_turma_pdf = gerar_relatorio_local_turma_v2

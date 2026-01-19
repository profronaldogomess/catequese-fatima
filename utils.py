# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 2.3.0 - RIGOR DOCUMENTAL MÁXIMO (LGPD E VERACIDADE INTEGRAIS)
# MISSÃO: Gestão de PDFs, Lógicas de Censo, Fuso Horário e Documentação Oficial.
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
    """Converte diversos formatos de data para o padrão brasileiro DD/MM/YYYY."""
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    s = str(valor).strip().split('.')[0]
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    try:
        dt = pd.to_datetime(valor)
        if pd.notnull(dt):
            return dt.strftime('%d/%m/%Y')
    except: pass
    return s

def calcular_idade(data_nascimento):
    """Calcula a idade exata baseada no fuso horário UTC-3 (Bahia/Brasília)."""
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]:
        return 0
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except: return 0

def limpar_texto(texto):
    """Remove artefatos de Markdown e garante compatibilidade Latin-1 para FPDF."""
    if not texto: return ""
    texto_limpo = str(texto).replace("**", "").replace("* ", " - ").replace("*", "")
    return texto_limpo.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    """Converte o objeto FPDF em fluxo de bytes binários."""
    try: return pdf.output(dest='S').encode('latin-1')
    except: return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=8):
    """Desenha caixa de texto padronizada creme (#f8f9f0) com rótulo superior."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240) 
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def marcar_opcao(pdf, texto, condicao, x, y):
    """Desenha uma opção de seleção visual (X) baseada em condição booleana."""
    pdf.set_xy(x, y); pdf.set_font("helvetica", "", 9)
    mark = "X" if condicao else " "
    pdf.cell(0, 5, limpar_texto(f"{texto} ( {mark} )"), ln=0)

# ==============================================================================
# 2. CABEÇALHO OFICIAL DIOCESANO
# ==============================================================================

def adicionar_cabecalho_diocesano(pdf, titulo="", etapa=""):
    """Desenha o topo oficial da Diocese de Itabuna com fuso horário UTC-3."""
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 15, 22)
    data_local = (datetime.now(timezone.utc) + timedelta(hours=-3)).strftime('%d / %m / %Y')
    pdf.set_xy(38, 15); pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153) 
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, limpar_texto(f"Data: {data_local}"), ln=True, align='R')
    pdf.set_x(38); pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    pdf.ln(10)
    if titulo:
        y_topo = pdf.get_y()
        pdf.set_fill_color(245, 245, 245); pdf.rect(10, y_topo, 190, 15, 'F'); pdf.rect(10, y_topo, 190, 15)
        pdf.set_xy(10, y_topo + 4); pdf.set_font("helvetica", "B", 12); pdf.set_text_color(65, 123, 153)
        pdf.cell(190, 7, limpar_texto(titulo), align='C'); pdf.ln(18)
    else: pdf.ln(5)

# ==============================================================================
# 3. GESTÃO DE FICHAS DE INSCRIÇÃO (CATEQUIZANDOS)
# ==============================================================================

def _desenhar_corpo_ficha(pdf, dados):
    """Lógica central de desenho da ficha com consentimento LGPD RIGOROSO E INTEGRAL."""
    y_base = pdf.get_y()
    idade_real = calcular_idade(dados.get('data_nascimento', ''))
    is_menor = idade_real < 18
    est_civil_raw = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper()
    is_adulto_cadastro = est_civil_raw != "N/A"
    
    # Bloco de Identificação da Etapa
    pdf.set_fill_color(245, 245, 245); pdf.rect(10, y_base, 105, 20, 'F'); pdf.rect(10, y_base, 105, 20)
    pdf.set_xy(12, y_base + 4); pdf.set_font("helvetica", "B", 12); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(100, 6, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    pdf.set_xy(115, y_base); pdf.cell(30, 20, limpar_texto(f"Ano: {date.today().year}"), border=1, align='C')
    pdf.set_xy(145, y_base); pdf.set_font("helvetica", "B", 7); pdf.multi_cell(55, 10, limpar_texto(f"Etapa: {dados.get('etapa', '')}"), border=1, align='L')
    
    # Logística
    y_next = y_base + 23; pdf.set_xy(10, y_next); pdf.set_font("helvetica", "B", 10)
    turno = str(dados.get('turno', '')).upper()
    mark_m = "X" if "MANHÃ" in turno or "M" == turno else " "
    mark_t = "X" if "TARDE" in turno or "T" == turno else " "
    mark_n = "X" if "NOITE" in turno or "N" == turno else " "
    local = str(dados.get('local_encontro', '_______________________')).upper()
    pdf.cell(0, 8, limpar_texto(f"Turno: ( {mark_m} ) M  ( {mark_t} ) T  ( {mark_n} ) N        Local: {local}"), ln=True)

    # Identificação
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome:", dados.get('nome_completo', ''), 10, y, 190)
    y += 14; desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", str(idade_real), 60, y, 25)
    pdf.set_xy(90, y + 4); pdf.set_font("helvetica", "B", 8); pdf.cell(20, 4, limpar_texto("Batizado:"), ln=0)
    marcar_opcao(pdf, "Sim", dados.get('batizado_sn') == 'SIM', 110, y + 4); marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 130, y + 4)
    y += 14; desenhar_campo_box(pdf, "Morada (Endereço):", dados.get('endereco_completo', ''), 10, y, 190)
    y += 14; desenhar_campo_box(pdf, "Telefone:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Tomar algum medicamento?", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    # Filiação
    pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True)
    y = pdf.get_y() + 2; pdf.set_text_color(0, 0, 0)
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_mae','')} / {dados.get('tel_mae','')}", 125, y, 75)
    y += 14; desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_pai','')} / {dados.get('tel_pai','')}", 125, y, 75)
    
    # Vida Eclesial
    pdf.set_y(y + 16); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153); pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil e Vida Eclesial"), ln=True)
    pdf.set_text_color(0, 0, 0); y_check = pdf.get_y()
    ec = str(dados.get('estado_civil_pais_ou_proprio', '')).upper() if is_adulto_cadastro else str(dados.get('est_civil_pais', '')).upper()
    marcar_opcao(pdf, "Casados", "CASADO" in ec, 10, y_check); marcar_opcao(pdf, "Convivem", "CONVIVEM" in ec or "FACTO" in ec, 40, y_check)
    marcar_opcao(pdf, "Separados", "SEPARADO" in ec, 70, y_check); marcar_opcao(pdf, "Solteiro(a)", "SOLTEIRO" in ec, 100, y_check)
    pdf.ln(7); sac = str(dados.get('sacramentos_ja_feitos', '')).upper() if is_adulto_cadastro else str(dados.get('sac_pais', '')).upper()
    pdf.set_font("helvetica", "B", 8); pdf.cell(45, 5, limpar_texto("Já tem o Sacramento:"), ln=0)
    marcar_opcao(pdf, "Batismo", "BATISMO" in sac, 50, pdf.get_y()); marcar_opcao(pdf, "Eucaristia", "EUCARISTIA" in sac, 80, pdf.get_y()); marcar_opcao(pdf, "Matrimônio", "MATRIMÔNIO" in sac, 110, pdf.get_y())
    
    # --- TERMO DE CONSENTIMENTO LGPD INTEGRAL ---
    pdf.ln(10); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(224, 61, 17); pdf.cell(0, 6, limpar_texto("Termo de Consentimento LGPD"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0); nome_cat = dados.get('nome_completo', '________________')
    
    if is_menor:
        mae = str(dados.get('nome_mae', '')).strip()
        pai = str(dados.get('nome_pai', '')).strip()
        mae = "" if mae.upper() in ["N/A", "NONE", ""] else mae
        pai = "" if pai.upper() in ["N/A", "NONE", ""] else pai
        if mae and pai: resp = f"{mae} e {pai}"
        elif mae: resp = mae
        elif pai: resp = pai
        else: resp = str(dados.get('nome_responsavel', '________________________________'))
        
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
    pdf.ln(12); y_ass = pdf.get_y(); pdf.line(10, y_ass, 90, y_ass); pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1); pdf.set_font("helvetica", "B", 8); pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(110, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf); _desenhar_corpo_ficha(pdf, dados)
    return finalizar_pdf(pdf)

def gerar_fichas_turma_completa(nome_turma, df_alunos):
    if df_alunos.empty: return None
    pdf = FPDF()
    for _, row in df_alunos.iterrows():
        pdf.add_page(); adicionar_cabecalho_diocesano(pdf); _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

# ==============================================================================
# 4. GESTÃO DE FICHAS DE CATEQUISTAS (EQUIPE)
# ==============================================================================

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    """Gera o prontuário ministerial completo do catequista com histórico e DECLARAÇÃO DE VERACIDADE."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
    
    # Seção 1: Identificação
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("1. DADOS PESSOAIS E CONTATO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, y, 45)
    y += 14; desenhar_campo_box(pdf, "E-mail:", dados.get('email', ''), 10, y, 110); desenhar_campo_box(pdf, "Telefone:", dados.get('telefone', ''), 125, y, 75)
    
    # Seção 2: Vida Ministerial
    pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E SACRAMENTAL"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Início Catequese:", formatar_data_br(dados.get('data_inicio_catequese', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Batismo:", formatar_data_br(dados.get('data_batismo', '')), 58, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(dados.get('data_eucaristia', '')), 106, y, 45)
    desenhar_campo_box(pdf, "Crisma:", formatar_data_br(dados.get('data_crisma', '')), 154, y, 46)
    
    # Seção 3: Histórico de Formação
    pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(0, 7, limpar_texto("3. HISTÓRICO DE FORMAÇÃO"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 7, "Data", border=1, fill=True, align='C'); pdf.cell(100, 7, "Tema", border=1, fill=True); pdf.cell(60, 7, "Formador", border=1, fill=True); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    if not df_formacoes.empty:
        for _, f in df_formacoes.iterrows():
            pdf.cell(30, 6, formatar_data_br(f['data']), border=1, align='C'); pdf.cell(100, 6, limpar_texto(f['tema']), border=1); pdf.cell(60, 6, limpar_texto(f['formador']), border=1); pdf.ln()
    else: pdf.cell(190, 6, "Nenhuma formação registrada.", border=1, align='C', ln=True)
    
    # --- SEÇÃO 4: DECLARAÇÃO DE VERACIDADE E RESPONSABILIDADE ---
    pdf.ln(5); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(224, 61, 17); pdf.cell(0, 6, limpar_texto("Declaração de Responsabilidade"), ln=True)
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    declara = (f"Eu, {dados.get('nome', '')}, declaro para os devidos fins que as informações acima prestadas são verdadeiras e assumo o compromisso "
               f"de zelar pela sã doutrina e pelas diretrizes da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima, "
               f"atuando com fidelidade ao Evangelho e ao Magistério da Igreja.")
    pdf.multi_cell(0, 5, limpar_texto(declara))
    
    # Assinaturas
    pdf.ln(12); y_ass = pdf.get_y(); pdf.line(15, y_ass, 95, y_ass); pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1); pdf.set_font("helvetica", "B", 8); pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    return finalizar_pdf(pdf)

# ==============================================================================
# 5. RELATÓRIOS EXECUTIVOS (DIOCESANO V4 E PASTORAL V3)
# ==============================================================================

def gerar_relatorio_diocesano_v4(dados_censo, equipe_stats, sac_ano, sac_censo, logistica_lista, formacoes_lista, analise_ia):
    """Relatório Diocesano de Alta Precisão v4."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO DIOCESANO")
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. CENSO POPULACIONAL E ESTRUTURAL"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Total Catequizandos", str(dados_censo.get('total_cat', '0')), 10, y, 45)
    desenhar_campo_box(pdf, "Turmas Infantil/Juv.", str(dados_censo.get('t_infantil', '0')), 58, y, 45)
    desenhar_campo_box(pdf, "Turmas Jovens/Adultos", str(dados_censo.get('t_adultos', '0')), 106, y, 45)
    desenhar_campo_box(pdf, "Equipe (Exceto Admin)", str(dados_censo.get('total_equipe', '0')), 154, y, 46); pdf.ln(18)
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, limpar_texto("2. DADOS SACRAMENTAIS DA EQUIPE"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(100, 7, "Indicador", border=1, fill=True); pdf.cell(45, 7, "Qtd", border=1, fill=True, align='C'); pdf.cell(45, 7, "%", border=1, fill=True, align='C'); pdf.ln()
    total_e = int(dados_censo.get('total_equipe', 1))
    for desc, qtd in [("Batismo", equipe_stats.get('bat', 0)), ("Eucaristia", equipe_stats.get('euca', 0)), ("Crisma", equipe_stats.get('crisma', 0)), ("Ministros", equipe_stats.get('ministros', 0)), ("Aptos", equipe_stats.get('aptos', 0))]:
        perc = (int(qtd)/total_e)*100 if total_e > 0 else 0
        pdf.cell(100, 7, limpar_texto(f" {desc}"), border=1); pdf.cell(45, 7, str(qtd), border=1, align='C'); pdf.cell(45, 7, f"{perc:.1f}%", border=1, align='C'); pdf.ln()
    
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, limpar_texto("3. LOGÍSTICA E DISTRIBUIÇÃO"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(40, 7, "Dia", border=1, fill=True); pdf.cell(50, 7, "Local", border=1, fill=True); pdf.cell(100, 7, "Turmas", border=1, fill=True); pdf.ln()
    for item in logistica_lista: pdf.cell(40, 6, limpar_texto(item['dia']), border=1); pdf.cell(50, 6, limpar_texto(item['local']), border=1); pdf.cell(100, 6, limpar_texto(item['turmas']), border=1); pdf.ln()
    
    pdf.ln(5); pdf.set_fill_color(224, 61, 17); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, limpar_texto("4. PARECER TÉCNICO"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_v3(turmas_detalhadas, totais_gerais, analise_ia):
    """Relatório Pastoral com tabelas separadas para evitar sobreposição."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL ANALÍTICO")
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. IDENTIFICAÇÃO E LOGÍSTICA DAS TURMAS"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Turma", border=1, fill=True); pdf.cell(60, 7, "Catequista", border=1, fill=True); pdf.cell(60, 7, "Dia / Local", border=1, fill=True); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    for t in turmas_detalhadas:
        pdf.cell(70, 7, limpar_texto(t['nome']), border=1); pdf.cell(60, 7, limpar_texto(t['catequista']), border=1); pdf.cell(60, 7, limpar_texto(f"{t['dia']} - {t['local']}"), border=1); pdf.ln()
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, limpar_texto("2. DESEMPENHO E CENSO SACRAMENTAL"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Turma", border=1, fill=True); pdf.cell(25, 7, "Batiz.", border=1, fill=True, align='C'); pdf.cell(25, 7, "Euca.", border=1, fill=True, align='C'); pdf.cell(25, 7, "Crisma", border=1, fill=True, align='C'); pdf.cell(25, 7, "Freq.", border=1, fill=True, align='C'); pdf.cell(20, 7, "Total", border=1, fill=True, align='C'); pdf.ln()
    for t in turmas_detalhadas:
        pdf.cell(70, 7, limpar_texto(t['nome']), border=1); pdf.cell(25, 7, str(t['batizados']), border=1, align='C'); pdf.cell(25, 7, str(t['eucaristia']), border=1, align='C'); pdf.cell(25, 7, str(t['crisma']), border=1, align='C'); pdf.cell(25, 7, f"{t['frequencia']}%", border=1, align='C'); pdf.cell(20, 7, str(t['total']), border=1, align='C'); pdf.ln()
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, limpar_texto("3. FECHAMENTO ESTATÍSTICO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Total Turmas", str(totais_gerais['total_turmas']), 10, y, 45); desenhar_campo_box(pdf, "Infantil/Juv.", str(totais_gerais['t_infantil']), 58, y, 45); desenhar_campo_box(pdf, "Jovens/Adultos", str(totais_gerais['t_adultos']), 106, y, 45); desenhar_campo_box(pdf, "Freq. Média", f"{totais_gerais['freq_geral']}%", 154, y, 46); pdf.ln(18)
    pdf.ln(5); pdf.set_fill_color(224, 61, 17); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, limpar_texto("4. PARECER ANALÍTICO"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "AUDITORIA SACRAMENTAL"); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"PERFIL DA TURMA: {nome_turma}"); pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

# ==============================================================================
# 6. FUNÇÕES DE CENSO E UTILITÁRIOS PASTORAIS
# ==============================================================================

def sugerir_etapa(data_nascimento):
    idade = calcular_idade(data_nascimento)
    if idade <= 6: return "PRÉ"
    elif idade <= 8: return "PRIMEIRA ETAPA"
    elif idade <= 10: return "SEGUNDA ETAPA"
    return "TERCEIRA ETAPA"

def eh_aniversariante_da_semana(data_nasc_str):
    try:
        d_str = formatar_data_br(data_nasc_str)
        if d_str == "N/A": return False
        nasc = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        nasc_este_ano = nasc.replace(year=hoje.year)
        return 0 <= (nasc_este_ano - hoje).days <= 7
    except: return False

def converter_para_data(valor_str):
    if not valor_str or str(valor_str).strip() in ["None", "", "N/A"]: return date.today()
    try:
        d_str = formatar_data_br(valor_str)
        return datetime.strptime(d_str, "%d/%m/%Y").date()
    except: return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    if d_ministerio and str(d_ministerio).strip() not in ["", "N/A", "None"]: return "MINISTRO", 0 
    try:
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        inicio = datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
        tem_s = all([str(x).strip() not in ["", "N/A", "None"] for x in [d_batismo, d_euca, d_crisma]])
        return ("APTO", anos) if (anos >= 5 and tem_s) else ("EM_CAMINHADA", anos)
    except: return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date(); niver = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.day == hoje.day and dt.month == hoje.month: niver.append(f"😇 Catequizando: **{r['nome_completo']}**")
    return niver

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date(); lista = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A" and datetime.strptime(d, "%d/%m/%Y").month == hoje.month:
                lista.append({'dia': datetime.strptime(d, "%d/%m/%Y").day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date(); lista = []
    for _, r in df_cat.iterrows():
        d = formatar_data_br(r['data_nascimento'])
        if d != "N/A" and datetime.strptime(d, "%d/%m/%Y").month == hoje.month:
            lista.append({'nome_completo': r['nome_completo'], 'dia': datetime.strptime(d, "%d/%m/%Y").day, 'etapa': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

# --- ALIASES DE COMPATIBILIDADE ---
gerar_relatorio_diocesano_pdf = gerar_relatorio_diocesano_v4
gerar_relatorio_pastoral_interno_pdf = gerar_relatorio_pastoral_v3
gerar_relatorio_diocesano_v2 = gerar_relatorio_diocesano_v4
gerar_relatorio_pastoral_v2 = gerar_relatorio_pastoral_v3

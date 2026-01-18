# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os
import re

# ==========================================
# 1. FUNÇÕES DE APOIO E FORMATAÇÃO
# ==========================================

def formatar_data_br(valor):
    if not valor or str(valor).strip() in ["None", "", "N/A"]: return "N/A"
    s = str(valor).strip().split('.')[0]
    if len(s) == 8 and s.isdigit(): return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-": return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    try:
        dt = pd.to_datetime(valor)
        if pd.notnull(dt): return dt.strftime('%d/%m/%Y')
    except: pass
    return s

def calcular_idade(data_nascimento):
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]: return 0
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = date.today()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except: return 0

def limpar_texto(texto):
    if not texto: return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    try: return pdf.output(dest='S').encode('latin-1')
    except: return b""

# ==========================================
# 2. COMPONENTES VISUAIS DO PDF
# ==========================================

def desenhar_campo_box(pdf, label, valor, x, y, w, h=8):
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def marcar_opcao(pdf, texto, condicao, x, y):
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "", 9)
    mark = "X" if condicao else " "
    pdf.cell(0, 5, limpar_texto(f"{texto} ( {mark} )"), ln=0)

# ==========================================
# 3. GERADOR DE FICHA DE INSCRIÇÃO
# ==========================================

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    
    # Identifica se é adulto
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    
    # --- CABEÇALHO ---
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 22)
    
    pdf.set_xy(35, 10)
    pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, limpar_texto(f"Data: {date.today().strftime('%d / %m / %Y')}"), ln=True, align='R')
    
    pdf.set_x(35)
    pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(4)
    y_topo = pdf.get_y()
    # Caixa Título
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, y_topo, 105, 20, 'F')
    pdf.rect(10, y_topo, 105, 20)
    pdf.set_xy(12, y_topo + 4)
    pdf.set_font("helvetica", "B", 12); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(100, 6, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    
    # Caixa Ano
    pdf.set_xy(115, y_topo)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(30, 20, limpar_texto(f"Ano: {date.today().year}"), border=1, align='C')
    
    # Caixa Etapa/Turma (Aumentada para caber o texto)
    pdf.set_xy(145, y_topo)
    pdf.set_font("helvetica", "B", 7)
    etapa_txt = str(dados.get('etapa', 'N/A'))
    pdf.multi_cell(55, 10, limpar_texto(f"Etapa: {etapa_txt}\nTurma: {etapa_txt}"), border=1, align='L')

    pdf.ln(6)
    # Turno e Local
    pdf.set_font("helvetica", "B", 10)
    turno = str(dados.get('turno', '')).upper()
    local = str(dados.get('local_encontro', '_______________________')).upper()
    pdf.cell(0, 8, limpar_texto(f"Turno: ( {'M' if 'MANHÃ' in turno else ' '} ) M  ( {'T' if 'TARDE' in turno else ' '} ) T  ( {'N' if 'NOITE' in turno else ' '} ) N        Local: {local}"), ln=True)

    # --- SEÇÃO: IDENTIFICAÇÃO ---
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome:", dados.get('nome_completo', ''), 10, y, 190)
    y += 14
    desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", str(calcular_idade(dados.get('data_nascimento', ''))), 60, y, 25)
    
    pdf.set_xy(90, y + 4); pdf.set_font("helvetica", "B", 8); pdf.cell(20, 4, limpar_texto("Batizado:"), ln=0)
    marcar_opcao(pdf, "Sim", dados.get('batizado_sn') == 'SIM', 110, y + 4)
    marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 130, y + 4)
    
    y += 14
    desenhar_campo_box(pdf, "Morada (Endereço):", dados.get('endereco_completo', ''), 10, y, 190)
    y += 14
    desenhar_campo_box(pdf, "Telefone:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Tomar algum medicamento?", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    # --- SEÇÃO: FILIAÇÃO ---
    pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True)
    y = pdf.get_y() + 2; pdf.set_text_color(0, 0, 0)
    
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_mae','')} / {dados.get('tel_mae','')}", 125, y, 75)
    y += 14
    desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_pai','')} / {dados.get('tel_pai','')}", 125, y, 75)
    
    # --- SEÇÃO: OUTROS ELEMENTOS (CHECKBOXES) ---
    pdf.set_y(y + 16); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil e Vida Eclesial"), ln=True)
    pdf.set_text_color(0, 0, 0)
    
    y_check = pdf.get_y()
    ec = str(dados.get('estado_civil_pais_ou_proprio', '')).upper() if is_adulto else str(dados.get('est_civil_pais', '')).upper()
    marcar_opcao(pdf, "Casados", "CASADO" in ec, 10, y_check)
    marcar_opcao(pdf, "Convivem/União Facto", ("CONVIVEM" in ec or "FACTO" in ec), 40, y_check)
    marcar_opcao(pdf, "Separados", "SEPARADO" in ec, 85, y_check)
    marcar_opcao(pdf, "Solteiro(a)", "SOLTEIRO" in ec, 115, y_check)
    marcar_opcao(pdf, "Viúvo(a)", "VIÚVO" in ec, 145, y_check)
    
    pdf.ln(7)
    sac = str(dados.get('sacramentos_ja_feitos', '')).upper() if is_adulto else str(dados.get('sac_pais', '')).upper()
    pdf.set_font("helvetica", "B", 8); pdf.cell(45, 5, limpar_texto("Já tem o Sacramento:"), ln=0)
    marcar_opcao(pdf, "Batismo", "BATISMO" in sac, 50, pdf.get_y())
    marcar_opcao(pdf, "Eucaristia", "EUCARISTIA" in sac, 80, pdf.get_y())
    marcar_opcao(pdf, "Matrimônio", "MATRIMÔNIO" in sac, 110, pdf.get_y())
    
    pdf.ln(7)
    part = str(dados.get('participa_grupo', 'NÃO')).upper()
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, limpar_texto(f"Participa de algum Grupo ou Pastoral da Igreja: Sim ( {'X' if part=='SIM' else ' '} ) Não ( {'X' if part=='NÃO' else ' '} )  Qual: {dados.get('qual_grupo', '__________')}"), ln=True)
    
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 6, limpar_texto("A criança/adulto tem algum Transtorno Global do Desenvolvimento (TGO)?"), ln=True)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, limpar_texto(f" Resposta: {dados.get('tgo_sn', 'NÃO')}"), border=1, ln=True)

    # --- TERMO DE CONSENTIMENTO (TEXTO INTEGRAL) ---
    pdf.ln(4); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Termo de Consentimento"), ln=True)
    pdf.set_font("helvetica", "", 7.5); pdf.set_text_color(0, 0, 0)
    
    nome_cat = dados.get('nome_completo', '________________')
    nome_resp = dados.get('nome_responsavel', '________________')
    
    if is_adulto:
        texto_lgpd = (f"Eu {nome_cat}, AUTORIZO o uso da publicação da minha imagem nos eventos realizados pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD), que regula as atividades de tratamento de dados pessoais colhidos no momento da inscrição para o(s) sacramento(s) da Iniciação à Vida Cristã com Inspiração Catecumenal.")
    else:
        texto_lgpd = (f"Eu {nome_resp}, na qualidade de pai/mãe ou responsável pelo (a) catequizando (a), {nome_cat}, AUTORIZO o uso da publicação da imagem do (a) meu (minha) filho (a) dos eventos realizados pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD), que regula as atividades de tratamento de dados pessoais colhidos no momento da inscrição para o(s) sacramento(s) da Iniciação à Vida Cristã com Inspiração Catecumenal.")
    
    pdf.multi_cell(0, 3.5, limpar_texto(texto_lgpd))

    # --- ASSINATURAS ---
    pdf.ln(10); y_ass = pdf.get_y()
    pdf.line(10, y_ass, 90, y_ass); pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1); pdf.set_font("helvetica", "B", 8)
    label_ass = "Assinatura do catequizando (a)" if is_adulto else "Assinatura do Pai/Mãe ou Responsável"
    pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(110, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
    return finalizar_pdf(pdf)

# MANTENDO AS DEMAIS FUNÇÕES TÉCNICAS
def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano_simples(pdf, "FICHA DO CATEQUISTA", etapa="EQUIPE")
    y = pdf.get_y() + 5
    desenhar_campo_box(pdf, "Nome:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, y, 45)
    pdf.ln(20); y_ass = pdf.get_y(); pdf.line(15, y_ass, 95, y_ass); pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    return finalizar_pdf(pdf)

def adicionar_cabecalho_diocesano_simples(pdf, titulo, etapa=""):
    if os.path.exists("logo.png"): pdf.image("logo.png", 10, 8, 22)
    pdf.set_xy(35, 10); pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=True)
    pdf.set_x(35); pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    pdf.set_xy(10, 35); pdf.set_font("helvetica", "B", 14); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 10, limpar_texto(titulo), ln=True, align='C')

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano_simples(pdf, f"PERFIL DA TURMA: {nome_turma}", etapa=nome_turma)
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_ia)); return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano_simples(pdf, "AUDITORIA SACRAMENTAL", etapa="SACRAMENTOS")
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_ia)); return finalizar_pdf(pdf)

def gerar_relatorio_diocesano_pdf(dados_g, turmas_list, sac_stats, proj_list, analise_tecnica):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano_simples(pdf, "RELATÓRIO ESTATÍSTICO DIOCESANO", etapa="DIOCESANO")
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_tecnica)); return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_interno_pdf(dados, analise_ia):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano_simples(pdf, "RELATÓRIO PASTORAL INTERNO", etapa="PASTORAL")
    pdf.ln(10); pdf.multi_cell(0, 7, limpar_texto(analise_ia)); return finalizar_pdf(pdf)

# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os
import re

# ==========================================
# 1. FUNÇÕES DE LÓGICA E FORMATAÇÃO
# ==========================================

def formatar_data_br(valor):
    """Converte qualquer formato (YYYYMMDD, ISO, etc) para DD/MM/YYYY."""
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    
    # Remove decimais e espaços
    s = str(valor).strip().split('.')[0]
    
    # Caso 1: YYYYMMDD (8 dígitos puros)
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    
    # Caso 2: YYYY-MM-DD (ISO)
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    
    # Caso 3: Tenta via Pandas
    try:
        dt = pd.to_datetime(valor)
        if pd.notnull(dt):
            return dt.strftime('%d/%m/%Y')
    except:
        pass
    
    return s

def calcular_idade(data_nascimento):
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]: return 0
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = date.today()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except:
        return 0

def sugerir_etapa(data_nascimento):
    idade = calcular_idade(data_nascimento)
    if 5 <= idade <= 6: return "PRÉ"
    elif 7 <= idade <= 8: return "PRIMEIRA ETAPA"
    elif 9 <= idade <= 10: return "SEGUNDA ETAPA"
    elif 11 <= idade <= 14: return "TERCEIRA ETAPA"
    else: return "ADULTOS TURMA EUCARISTIA/BATISMO"

def eh_aniversariante_da_semana(data_nasc_str):
    try:
        d_str = formatar_data_br(data_nasc_str)
        if d_str == "N/A": return False
        nasc = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = date.today()
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
    if d_ministerio and str(d_ministerio).strip() not in ["None", "", "N/A"]: 
        return "MINISTRO", 0 
    try:
        hoje = date.today()
        inicio = datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
        tem_s = all([str(x).strip() not in ["None", "", "N/A"] for x in [d_batismo, d_euca, d_crisma]])
        return ("APTO", anos) if (anos >= 5 and tem_s) else ("EM_CAMINHADA", anos)
    except: return "EM_CAMINHADA", 0

# ==========================================
# 2. FUNÇÕES DE CENSO E ANIVERSÁRIOS
# ==========================================

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    hoje = date.today()
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
    hoje = date.today(); lista = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A" and datetime.strptime(d, "%d/%m/%Y").month == hoje.month:
                lista.append({'dia': datetime.strptime(d, "%d/%m/%Y").day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = date.today(); lista = []
    for _, r in df_cat.iterrows():
        d = formatar_data_br(r['data_nascimento'])
        if d != "N/A" and datetime.strptime(d, "%d/%m/%Y").month == hoje.month:
            lista.append({'nome_completo': r['nome_completo'], 'dia': datetime.strptime(d, "%d/%m/%Y").day, 'etapa': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

# ==========================================
# 3. NÚCLEO GERADOR DE PDF (PADRÃO DIOCESANO)
# ==========================================

def limpar_texto(texto):
    if not texto: return ""
    texto = re.sub(r'[*#_~-]', '', str(texto))
    return texto.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    try: return pdf.output(dest='S').encode('latin-1')
    except: return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=9):
    pdf.set_xy(x, y); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4); pdf.set_fill_color(248, 249, 240); pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def adicionar_cabecalho_diocesano(pdf, titulo, etapa=""):
    if os.path.exists("logo.png"):
        # Ajuste de posição para não cortar o logo
        pdf.image("logo.png", 10, 8, 22)
    
    pdf.set_xy(35, 10); pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    pdf.set_font("helvetica", "", 10); pdf.cell(0, 5, limpar_texto(f"Data: {date.today().strftime('%d / %m / %Y')}"), ln=True, align='R')
    pdf.set_x(35); pdf.set_font("helvetica", "B", 11); pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(5); y_topo = pdf.get_y()
    pdf.set_fill_color(248, 249, 240); pdf.rect(10, y_topo, 100, 15, 'F'); pdf.rect(10, y_topo, 100, 15)
    pdf.set_xy(12, y_topo + 2); pdf.set_font("helvetica", "B", 11); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(95, 5, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    pdf.set_xy(115, y_topo); pdf.cell(40, 15, limpar_texto(f"Ano: {date.today().year}"), border=1, align='C')
    pdf.set_xy(155, y_topo); pdf.set_font("helvetica", "", 9); pdf.multi_cell(45, 7.5, limpar_texto(f"Etapa: {etapa}\nTurma: {etapa}"), border=1)
    pdf.ln(5)

# ==========================================
# 4. GERADORES DE DOCUMENTOS ESPECÍFICOS
# ==========================================

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF(); pdf.add_page()
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    titulo = "FICHA DE INSCRIÇÃO (ADULTOS)" if is_adulto else "FICHA DE INSCRIÇÃO (INFANTIL/JUVENIL)"
    adicionar_cabecalho_diocesano(pdf, titulo, etapa=dados.get('etapa', ''))
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, limpar_texto(f"Turno: ( ) M ( ) T ( ) N        Local: _________________________________________"), ln=True)

    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome:", dados.get('nome_completo', ''), 10, y, 190)
    y += 15
    desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 50)
    desenhar_campo_box(pdf, "Idade:", str(calcular_idade(dados.get('data_nascimento', ''))), 65, y, 30)
    desenhar_campo_box(pdf, "Batizado:", f"Sim ( {'X' if dados.get('batizado_sn')=='SIM' else ' '} ) Não ( {'X' if dados.get('batizado_sn')=='NÃO' else ' '} )", 100, y, 100)
    y += 15
    desenhar_campo_box(pdf, "Morada (Endereço):", dados.get('endereco_completo', ''), 10, y, 190)
    y += 15
    desenhar_campo_box(pdf, "Telefone:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Tomar algum medicamento?", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    # FILIAÇÃO
    pdf.set_y(y + 18); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True); y = pdf.get_y() + 2
    pdf.set_text_color(0, 0, 0)
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 190)
    y += 15
    desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 190)
    
    # OUTROS ELEMENTOS
    pdf.set_y(y + 18); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil dos pais e Vida Eclesial"), ln=True)
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, limpar_texto("Estado Civil: Casados ( ) União de Facto ( ) Separados ( ) Solteiros ( ) Viúvo ( )"), ln=True)
    pdf.cell(0, 6, limpar_texto("Sacramentos dos pais: Batismo ( ) Crisma ( ) Eucaristia ( ) Matrimônio ( )"), ln=True)
    pdf.cell(0, 6, limpar_texto("Participam de Pastoral? Sim ( ) Não ( ) Qual: ____________________________________"), ln=True)
    pdf.cell(0, 6, limpar_texto("Tem irmãos na catequese? Sim ( ) Não ( ) Quantos: ________"), ln=True)
    
    pdf.ln(2); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 6, limpar_texto("A criança tem algum Transtorno Global do Desenvolvimento (TGO)?"), ln=True)
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, limpar_texto(f"Resposta: {dados.get('tgo_sn', 'NÃO')} __________________________________________________________________"), border=1, ln=True)

    # TERMO LGPD
    pdf.ln(4); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(224, 61, 17); pdf.cell(0, 6, limpar_texto("Termo de Consentimento"), ln=True)
    pdf.set_font("helvetica", "", 7.5); pdf.set_text_color(0, 0, 0)
    nome_resp = dados.get('nome_responsavel', '________________')
    nome_cat = dados.get('nome_completo', '________________')
    texto_lgpd = (f"Eu {nome_resp}, na qualidade de pai/mãe ou responsável pelo (a) catequizando (a), {nome_cat}, AUTORIZO o uso da publicação da imagem do (a) meu (minha) filho (a) dos eventos realizados pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD)...")
    pdf.multi_cell(0, 3.5, limpar_texto(texto_lgpd))

    # ASSINATURAS
    pdf.ln(8); y_ass = pdf.get_y(); pdf.line(10, y_ass, 90, y_ass); pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1); pdf.set_font("helvetica", "B", 8); pdf.cell(80, 5, limpar_texto("Assinatura do Pai/Mãe ou Responsável"), align='C')
    pdf.set_xy(110, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA CADASTRAL DO CATEQUISTA", etapa="EQUIPE")
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. IDENTIFICAÇÃO E CONTATO"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "E-mail:", dados.get('email', ''), 10, y, 90)
    desenhar_campo_box(pdf, "Telefone:", dados.get('telefone', 'N/A'), 105, y, 90)
    pdf.set_y(y + 18); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. VIDA SACRAMENTAL E QUALIFICAÇÃO"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Batismo:", formatar_data_br(dados.get('data_batismo', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(dados.get('data_eucaristia', '')), 58, y, 45)
    desenhar_campo_box(pdf, "Crisma:", formatar_data_br(dados.get('data_crisma', '')), 106, y, 45)
    desenhar_campo_box(pdf, "Ministério:", formatar_data_br(dados.get('data_ministerio', '')), 154, y, 41)
    
    pdf.ln(20); y_ass = pdf.get_y(); pdf.line(15, y_ass, 95, y_ass); pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1); pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    return finalizar_pdf(pdf)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"PERFIL DA TURMA: {nome_turma}", etapa=nome_turma)
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_ia)); return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "AUDITORIA SACRAMENTAL", etapa="SACRAMENTOS")
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_ia)); return finalizar_pdf(pdf)

def gerar_relatorio_diocesano_pdf(dados_g, turmas_list, sac_stats, proj_list, analise_tecnica):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO DIOCESANO", etapa="DIOCESANO")
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_tecnica)); return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_interno_pdf(dados, analise_ia):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL", etapa="PASTORAL")
    pdf.ln(10); pdf.multi_cell(0, 7, limpar_texto(analise_ia)); return finalizar_pdf(pdf)

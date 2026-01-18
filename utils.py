# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os
import re

def calcular_idade(data_nascimento):
    if not data_nascimento or data_nascimento == "None": return 0
    hoje = date.today()
    if isinstance(data_nascimento, str):
        try: data_nascimento = date.fromisoformat(data_nascimento)
        except: return 0
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

def sugerir_etapa(data_nascimento):
    idade = calcular_idade(data_nascimento)
    if 5 <= idade <= 6: return "PRÉ"
    elif 7 <= idade <= 8: return "PRIMEIRA ETAPA"
    elif 9 <= idade <= 10: return "SEGUNDA ETAPA"
    elif 11 <= idade <= 14: return "TERCEIRA ETAPA"
    else: return "ADULTOS TURMA EUCARISTIA/BATISMO"

def eh_aniversariante_da_semana(data_nasc_str):
    try:
        if not data_nasc_str or data_nasc_str == "None": return False
        nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
        hoje = date.today()
        nasc_este_ano = nasc.replace(year=hoje.year)
        diferenca = (nasc_este_ano - hoje).days
        return 0 <= diferenca <= 7
    except: return False

def converter_para_data(valor_str):
    if not valor_str or valor_str == "None" or valor_str == "": return date.today()
    try: return datetime.strptime(str(valor_str)[:10], "%Y-%m-%d").date()
    except: return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    if d_ministerio and d_ministerio != "None" and d_ministerio != "": return "MINISTRO", 0 
    try:
        hoje = date.today()
        inicio = datetime.strptime(str(data_inicio), "%Y-%m-%d").date()
        anos = (hoje - inicio).days // 365
        tem_sacramentos = all([d_batismo, d_euca, d_crisma])
        if anos >= 5 and tem_sacramentos: return "APTO", anos
        return "EM_CAMINHADA", anos
    except: return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    hoje = date.today()
    niver_hoje = []
    if not df_cat.empty:
        df_limpo = df_cat.drop_duplicates(subset=['nome_completo'])
        df_limpo['dt'] = pd.to_datetime(df_limpo['data_nascimento'], errors='coerce')
        hoje_cat = df_limpo[(df_limpo['dt'].dt.month == hoje.month) & (df_limpo['dt'].dt.day == hoje.day)]
        for _, r in hoje_cat.iterrows(): niver_hoje.append(f"😇 Catequizando: **{r['nome_completo']}**")
    if not df_usuarios.empty:
        df_usu_limpo = df_usuarios.drop_duplicates(subset=['nome'])
        col_nasc = 'data_nascimento' if 'data_nascimento' in df_usu_limpo.columns else 'nascimento'
        df_usu_limpo['dt'] = pd.to_datetime(df_usu_limpo[col_nasc], errors='coerce')
        hoje_usu = df_usu_limpo[(df_usu_limpo['dt'].dt.month == hoje.month) & (df_usu_limpo['dt'].dt.day == hoje.day)]
        for _, r in hoje_usu.iterrows(): niver_hoje.append(f"🛡️ Catequista: **{r['nome']}**")
    return niver_hoje

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = date.today()
    df_cat['data_nascimento'] = pd.to_datetime(df_cat['data_nascimento'], errors='coerce')
    aniversariantes = df_cat[df_cat['data_nascimento'].dt.month == hoje.month].copy()
    if not aniversariantes.empty:
        aniversariantes['dia'] = aniversariantes['data_nascimento'].dt.day
        aniversariantes = aniversariantes.sort_values(by='dia')
        return aniversariantes[['nome_completo', 'dia', 'etapa']]
    return pd.DataFrame()

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = date.today()
    lista_mes = []
    if not df_cat.empty:
        df_cat_limpo = df_cat.drop_duplicates(subset=['nome_completo'])
        df_cat_limpo['dt'] = pd.to_datetime(df_cat_limpo['data_nascimento'], errors='coerce')
        mes_cat = df_cat_limpo[df_cat_limpo['dt'].dt.month == hoje.month].copy()
        for _, r in mes_cat.iterrows(): lista_mes.append({'dia': r['dt'].day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    if not df_usuarios.empty:
        df_usu_limpo = df_usuarios.drop_duplicates(subset=['nome'])
        col_nasc = 'data_nascimento' if 'data_nascimento' in df_usu_limpo.columns else 'nascimento'
        df_usu_limpo['dt'] = pd.to_datetime(df_usu_limpo[col_nasc], errors='coerce')
        mes_usu = df_usu_limpo[df_usu_limpo['dt'].dt.month == hoje.month].copy()
        for _, r in mes_usu.iterrows(): lista_mes.append({'dia': r['dt'].day, 'nome': r['nome'], 'tipo': 'CATEQUISTA', 'info': r['papel']})
    if lista_mes: return pd.DataFrame(lista_mes).sort_values(by='dia')
    return pd.DataFrame()

def limpar_texto(texto):
    if not texto: return ""
    texto = re.sub(r'[*#_~-]', '', str(texto))
    return texto.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    try:
        return pdf.output(dest='S').encode('latin-1')
    except: return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=9):
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240); pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def adicionar_cabecalho_diocesano(pdf, titulo, etapa=""):
    if os.path.exists("logo.png"): pdf.image("logo.png", 12, 10, 28)
    pdf.set_xy(42, 12); pdf.set_font("helvetica", "B", 11); pdf.set_text_color(65, 123, 153) 
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese - Diocese de Itabuna-BA"), ln=True)
    pdf.set_x(42); pdf.cell(100, 5, limpar_texto("Paróquia Nossa Senhora de Fátima"), ln=True)
    desenhar_campo_box(pdf, "Ano:", str(date.today().year), 150, 10, 45, h=7)
    desenhar_campo_box(pdf, "Documento:", etapa, 150, 22, 45, h=7)
    pdf.set_xy(10, 45); pdf.set_font("helvetica", "B", 14); pdf.set_text_color(224, 61, 17) 
    pdf.cell(0, 10, limpar_texto(titulo), ln=True, align='C')

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF(); pdf.add_page()
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    titulo = "FICHA DE INSCRIÇÃO (ADULTOS)" if is_adulto else "FICHA DE INSCRIÇÃO (INFANTIL/JUVENIL)"
    adicionar_cabecalho_diocesano(pdf, titulo, etapa=dados.get('etapa', ''))
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  IDENTIFICAÇÃO"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", dados.get('data_nascimento', ''), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Endereço:", dados.get('endereco_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Batizado:", dados.get('batizado_sn', ''), 150, y, 45)
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "AUDITORIA TÉCNICA SACRAMENTAL", etapa="SACRAMENTOS")
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. QUADRO GERAL (POR PÚBLICO)"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Infantil - Batismos:", str(stats['bat_k']), 10, y, 90)
    desenhar_campo_box(pdf, "Infantil - Eucaristias:", str(stats['euca_k']), 105, y, 90)
    y += 16
    desenhar_campo_box(pdf, "Adultos - Batismos:", str(stats['bat_a']), 10, y, 60)
    desenhar_campo_box(pdf, "Adultos - Eucaristias:", str(stats['euca_a']), 75, y, 60)
    desenhar_campo_box(pdf, "Adultos - Crismas:", str(stats['cris_a']), 140, y, 55)
    pdf.set_y(y + 20)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. AUDITORIA POR TURMA E PREVISÕES"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 6, "Turma", 1, 0, 'L'); pdf.cell(30, 6, "Batizados", 1, 0, 'C'); pdf.cell(30, 6, "Pendentes", 1, 0, 'C')
    pdf.cell(35, 6, "Prev. Eucaristia", 1, 0, 'C'); pdf.cell(35, 6, "Prev. Crisma", 1, 1, 'C')
    pdf.set_font("helvetica", "", 8)
    for t in analise_turmas:
        pdf.cell(60, 6, limpar_texto(t['turma']), 1, 0, 'L')
        pdf.cell(30, 6, str(t['batizados']), 1, 0, 'C')
        pdf.cell(30, 6, str(t['pendentes']), 1, 0, 'C')
        pdf.cell(35, 6, limpar_texto(t['prev_e']), 1, 0, 'C')
        pdf.cell(35, 6, limpar_texto(t['prev_c']), 1, 1, 'C')
    pdf.ln(5); pdf.set_fill_color(224, 61, 17); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  3. DIAGNÓSTICO PASTORAL (IA)"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

# Mantendo as demais funções (gerar_ficha_catequista_pdf, gerar_pdf_perfil_turma, gerar_relatorio_diocesano_pdf, gerar_relatorio_pastoral_interno_pdf) com a mesma lógica de box.
def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "FICHA DO CATEQUISTA", etapa="EQUIPE")
    y = pdf.get_y() + 5
    desenhar_campo_box(pdf, "Nome:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", dados.get('data_nascimento', ''), 150, y, 45)
    return finalizar_pdf(pdf)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"PERFIL: {nome_turma}", etapa=nome_turma)
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_relatorio_diocesano_pdf(dados_g, turmas_list, sac_stats, proj_list, analise_tecnica):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO DIOCESANO", etapa="DIOCESANO")
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_tecnica))
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_interno_pdf(dados, analise_ia):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL", etapa="PASTORAL")
    pdf.ln(10); pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

# --- BLOCO: utils.py (gerar_relatorio_sacramentos_tecnico_pdf) ---
def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "AUDITORIA PASTORAL E SACRAMENTAL", etapa="SACRAMENTOS")
    
    # 1. QUADRO DE FRUTOS
    pdf.set_fill_color(248, 249, 240)
    pdf.set_font("helvetica", "B", 12); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 12, limpar_texto(f"FRUTOS DA EVANGELIZAÇÃO EM {date.today().year}: {stats.get('bat_ano', 0)} BATISMOS"), border=1, ln=True, align='C', fill=True)
    pdf.ln(5)

    # 2. DIAGNÓSTICO PASTORAL
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  DIAGNÓSTICO PASTORAL E CANÔNICO (IA GEMINI)"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    pdf.ln(5)

    # 3. TABELA DE TURMAS
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  DETALHAMENTO POR TURMA"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 6, "Turma", 1, 0, 'L'); pdf.cell(25, 6, "Freq.", 1, 0, 'C'); pdf.cell(25, 6, "Idades", 1, 0, 'C'); pdf.cell(25, 6, "Batizados", 1, 0, 'C'); pdf.cell(30, 6, "Pendentes", 1, 0, 'C'); pdf.cell(35, 6, "Prev. Euca", 1, 1, 'C')
    
    pdf.set_font("helvetica", "", 8)
    for t in analise_turmas:
        pdf.cell(50, 6, limpar_texto(t.get('turma', 'N/A')), 1, 0, 'L')
        pdf.cell(25, 6, str(t.get('freq', '0%')), 1, 0, 'C')
        pdf.cell(25, 6, str(t.get('idades', 'N/A')), 1, 0, 'C')
        pdf.cell(25, 6, str(t.get('batizados', 0)), 1, 0, 'C')
        pdf.cell(30, 6, str(t.get('pendentes', 0)), 1, 0, 'C') # USANDO .get PARA EVITAR KEYERROR
        pdf.cell(35, 6, limpar_texto(t.get('prev_e', 'N/A')), 1, 1, 'C')

    return finalizar_pdf(pdf)

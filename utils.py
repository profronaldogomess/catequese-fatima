# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os
import re

# ==========================================
# 1. FUNÇÕES DE LÓGICA E CÁLCULO
# ==========================================

def calcular_idade(data_nascimento):
    if not data_nascimento or data_nascimento == "None" or data_nascimento == "": return 0
    hoje = date.today()
    if isinstance(data_nascimento, str):
        try: data_nascimento = date.fromisoformat(data_nascimento[:10])
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
        if not data_nasc_str or data_nasc_str == "None" or data_nasc_str == "": return False
        nasc = datetime.strptime(str(data_nasc_str)[:10], "%Y-%m-%d").date()
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
    # Se já possui data de ministério, é Ministro
    if d_ministerio and str(d_ministerio).strip() not in ["None", "", "N/A"]: 
        return "MINISTRO", 0 
    try:
        hoje = date.today()
        inicio = datetime.strptime(str(data_inicio)[:10], "%Y-%m-%d").date()
        anos = (hoje - inicio).days // 365
        # Regra: Batismo, Eucaristia e Crisma são obrigatórios para ser Apto
        tem_sacramentos = all([
            str(d_batismo).strip() not in ["None", "", "N/A"],
            str(d_euca).strip() not in ["None", "", "N/A"],
            str(d_crisma).strip() not in ["None", "", "N/A"]
        ])
        if anos >= 5 and tem_sacramentos: return "APTO", anos
        return "EM_CAMINHADA", anos
    except: return "EM_CAMINHADA", 0

# ==========================================
# 2. FUNÇÕES DE CENSO E ANIVERSÁRIOS
# ==========================================

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    hoje = date.today()
    niver_hoje = []
    if not df_cat.empty:
        df_limpo = df_cat.drop_duplicates(subset=['nome_completo'])
        df_limpo['dt'] = pd.to_datetime(df_limpo['data_nascimento'], errors='coerce')
        hoje_cat = df_limpo[(df_limpo['dt'].dt.month == hoje.month) & (df_limpo['dt'].dt.day == hoje.day)]
        for _, r in hoje_cat.iterrows(): niver_hoje.append(f"😇 Catequizando: **{r['nome_completo']}**")
    if not df_usuarios.empty:
        # Filtra Admin para não aparecer em aniversários pastorais
        df_usu_limpo = df_usuarios[df_usuarios['papel'] != 'ADMIN'].drop_duplicates(subset=['nome'])
        df_usu_limpo['dt'] = pd.to_datetime(df_usu_limpo['data_nascimento'], errors='coerce')
        hoje_usu = df_usu_limpo[(df_usu_limpo['dt'].dt.month == hoje.month) & (df_usu_limpo['dt'].dt.day == hoje.day)]
        for _, r in hoje_usu.iterrows(): niver_hoje.append(f"🛡️ Catequista: **{r['nome']}**")
    return niver_hoje

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = date.today()
    lista_mes = []
    if not df_cat.empty:
        df_cat_limpo = df_cat.drop_duplicates(subset=['nome_completo'])
        df_cat_limpo['dt'] = pd.to_datetime(df_cat_limpo['data_nascimento'], errors='coerce')
        mes_cat = df_cat_limpo[df_cat_limpo['dt'].dt.month == hoje.month].copy()
        for _, r in mes_cat.iterrows(): 
            lista_mes.append({'dia': r['dt'].day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    if not df_usuarios.empty:
        df_usu_limpo = df_usuarios[df_usuarios['papel'] != 'ADMIN'].drop_duplicates(subset=['nome'])
        df_usu_limpo['dt'] = pd.to_datetime(df_usu_limpo['data_nascimento'], errors='coerce')
        mes_usu = df_usu_limpo[df_usu_limpo['dt'].dt.month == hoje.month].copy()
        for _, r in mes_usu.iterrows(): 
            lista_mes.append({'dia': r['dt'].day, 'nome': r['nome'], 'tipo': 'CATEQUISTA', 'info': r['papel']})
    if lista_mes: return pd.DataFrame(lista_mes).sort_values(by='dia')
    return pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = date.today()
    df_cat['dt'] = pd.to_datetime(df_cat['data_nascimento'], errors='coerce')
    aniversariantes = df_cat[df_cat['dt'].dt.month == hoje.month].copy()
    if not aniversariantes.empty:
        aniversariantes['dia'] = aniversariantes['dt'].dt.day
        return aniversariantes.sort_values(by='dia')[['nome_completo', 'dia', 'etapa']]
    return pd.DataFrame()

# ==========================================
# 3. NÚCLEO GERADOR DE PDF (PADRÃO DIOCESANO)
# ==========================================

def limpar_texto(texto):
    if not texto: return ""
    # Remove caracteres de Markdown que quebram o PDF
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

# ==========================================
# 4. GERADORES DE DOCUMENTOS ESPECÍFICOS
# ==========================================

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF(); pdf.add_page()
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    titulo = "FICHA DE INSCRIÇÃO (ADULTOS)" if is_adulto else "FICHA DE INSCRIÇÃO (INFANTIL/JUVENIL)"
    adicionar_cabecalho_diocesano(pdf, titulo, etapa=dados.get('etapa', ''))
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  IDENTIFICAÇÃO DO(A) CATEQUIZANDO(A)"), ln=True, fill=True); pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Data de Nascimento:", dados.get('data_nascimento', ''), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Endereço Completo:", dados.get('endereco_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Batizado:", dados.get('batizado_sn', ''), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Telefone / WhatsApp:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Sacramentos já realizados:", dados.get('sacramentos_ja_feitos', 'NENHUM'), 75, y, 120)
    
    pdf.ln(20)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE CONSENTIMENTO (LGPD)"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    texto = "Autorizo o uso de dados e imagem para fins estritamente pastorais conforme a LGPD."
    pdf.multi_cell(0, 4, limpar_texto(texto))
    
    return finalizar_pdf(pdf)

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA CADASTRAL DO CATEQUISTA", etapa="EQUIPE")
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. IDENTIFICAÇÃO E CONTATO"), ln=True, fill=True); pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", dados.get('data_nascimento', 'N/A'), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "E-mail:", dados.get('email', ''), 10, y, 90)
    desenhar_campo_box(pdf, "Telefone:", dados.get('telefone', 'N/A'), 105, y, 90)
    
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. VIDA SACRAMENTAL E QUALIFICAÇÃO"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Batismo:", dados.get('data_batismo', 'N/A'), 10, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", dados.get('data_eucaristia', 'N/A'), 58, y, 45)
    desenhar_campo_box(pdf, "Crisma:", dados.get('data_crisma', 'N/A'), 106, y, 45)
    desenhar_campo_box(pdf, "Ministério:", dados.get('data_ministerio', 'NÃO'), 154, y, 41)
    
    pdf.set_y(y + 20)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  3. HISTÓRICO DE FORMAÇÕES (ANO VIGENTE)"), ln=True, fill=True); pdf.ln(2)
    
    if not df_formacoes.empty:
        pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(30, 7, "Data", 1, 0, 'C'); pdf.cell(100, 7, "Tema", 1, 0, 'L'); pdf.cell(55, 7, "Formador", 1, 1, 'L')
        pdf.set_font("helvetica", "", 8)
        for _, row in df_formacoes.iterrows():
            pdf.cell(30, 6, str(row.get('data', '')), 1, 0, 'C')
            pdf.cell(100, 6, limpar_texto(str(row.get('tema', ''))[:55]), 1, 0, 'L')
            pdf.cell(55, 6, limpar_texto(str(row.get('formador', ''))[:30]), 1, 1, 'L')
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE COMPROMISSO E VERACIDADE"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 4, limpar_texto("Declaro que as informações prestadas são verdadeiras e assumo o compromisso com a missão evangelizadora."))
    
    return finalizar_pdf(pdf)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"PERFIL DA TURMA: {nome_turma}", etapa=nome_turma)
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  ESTATÍSTICAS E DADOS GERAIS"), ln=True, fill=True); pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    for chave, valor in metricas.items():
        pdf.write(7, limpar_texto(f"{chave}: {valor}\n"))
    
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  ANÁLISE PASTORAL (IA GEMINI)"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  RELAÇÃO DE CATEQUIZANDOS"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    for i, aluno in enumerate(lista_alunos, 1):
        pdf.cell(0, 6, limpar_texto(f"{i}. {aluno}"), ln=True)
        
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "AUDITORIA PASTORAL E SACRAMENTAL", etapa="SACRAMENTOS")
    
    pdf.set_fill_color(248, 249, 240); pdf.set_font("helvetica", "B", 12); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 12, limpar_texto(f"FRUTOS DA EVANGELIZAÇÃO EM {date.today().year}: {stats.get('bat_ano', 0)} BATISMOS"), border=1, ln=True, align='C', fill=True)
    pdf.ln(5)

    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  DIAGNÓSTICO PASTORAL E CANÔNICO (IA)"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    
    pdf.ln(5); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  DETALHAMENTO POR TURMA"), ln=True, fill=True); pdf.ln(2)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 6, "Turma", 1, 0, 'L'); pdf.cell(25, 6, "Freq.", 1, 0, 'C'); pdf.cell(25, 6, "Idades", 1, 0, 'C'); pdf.cell(25, 6, "Batizados", 1, 0, 'C'); pdf.cell(30, 6, "Pendentes", 1, 0, 'C'); pdf.cell(35, 6, "Prev. Euca", 1, 1, 'C')
    
    pdf.set_font("helvetica", "", 8)
    for t in analise_turmas:
        pdf.cell(50, 6, limpar_texto(t.get('turma', 'N/A')), 1, 0, 'L')
        pdf.cell(25, 6, str(t.get('freq', '0%')), 1, 0, 'C')
        pdf.cell(25, 6, str(t.get('idades', 'N/A')), 1, 0, 'C')
        pdf.cell(25, 6, str(t.get('batizados', 0)), 1, 0, 'C')
        pdf.cell(30, 6, str(t.get('pendentes', 0)), 1, 0, 'C')
        pdf.cell(35, 6, limpar_texto(t.get('prev_e', 'N/A')), 1, 1, 'C')

    return finalizar_pdf(pdf)

def gerar_relatorio_diocesano_pdf(dados_g, turmas_list, sac_stats, proj_list, analise_tecnica):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO DIOCESANO", etapa="DIOCESANO")
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. CENSO GERAL"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Total Catequizandos:", str(dados_g.get('total_cat', 0)), 10, y, 60)
    desenhar_campo_box(pdf, "Total Turmas:", str(dados_g.get('total_turmas', 0)), 75, y, 60)
    desenhar_campo_box(pdf, "Equipe Técnica:", str(dados_g.get('total_equipe', 0)), 140, y, 55)
    
    pdf.set_y(y + 20); pdf.multi_cell(0, 6, limpar_texto(analise_tecnica))
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_interno_pdf(dados, analise_ia):
    pdf = FPDF(); pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL INTERNO", etapa="PASTORAL")
    pdf.ln(10); pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 7, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

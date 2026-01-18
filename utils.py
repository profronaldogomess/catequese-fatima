# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os
import re

# ==========================================
# 1. FUNÇÕES DE FORMATAÇÃO E LÓGICA
# ==========================================

def formatar_data_br(valor):
    """Força a conversão de qualquer formato (YYYYMMDD, ISO, etc) para DD/MM/YYYY."""
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    
    # Remove decimais (ex: 19960824.0) e espaços
    s = str(valor).strip().split('.')[0]
    
    # Caso 1: YYYYMMDD (8 dígitos puros) - Ex: 19960824
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    
    # Caso 2: YYYY-MM-DD (ISO) - Ex: 1996-08-24
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    
    # Caso 3: Tenta via Pandas (Fallback para outros formatos)
    try:
        dt = pd.to_datetime(valor)
        if pd.notnull(dt):
            return dt.strftime('%d/%m/%Y')
    except:
        pass
    
    return s

def calcular_idade(data_nascimento):
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]: return 0
    hoje = date.today()
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
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
        diferenca = (nasc_este_ano - hoje).days
        return 0 <= diferenca <= 7
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
        d_ini_str = formatar_data_br(data_inicio)
        inicio = datetime.strptime(d_ini_str, "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
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
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d_str = formatar_data_br(r['data_nascimento'])
            if d_str != "N/A":
                dt = datetime.strptime(d_str, "%d/%m/%Y")
                if dt.month == hoje.month and dt.day == hoje.day:
                    niver_hoje.append(f"😇 Catequizando: **{r['nome_completo']}**")
    if not df_usuarios.empty:
        df_usu_limpo = df_usuarios[df_usuarios['papel'] != 'ADMIN'].drop_duplicates(subset=['nome'])
        for _, r in df_usu_limpo.iterrows():
            d_str = formatar_data_br(r['data_nascimento'])
            if d_str != "N/A":
                dt = datetime.strptime(d_str, "%d/%m/%Y")
                if dt.month == hoje.month and dt.day == hoje.day:
                    niver_hoje.append(f"🛡️ Catequista: **{r['nome']}**")
    return niver_hoje

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = date.today()
    lista_mes = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d_str = formatar_data_br(r['data_nascimento'])
            if d_str != "N/A":
                dt = datetime.strptime(d_str, "%d/%m/%Y")
                if dt.month == hoje.month:
                    lista_mes.append({'dia': dt.day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    if not df_usuarios.empty:
        for _, r in df_usuarios[df_usuarios['papel'] != 'ADMIN'].drop_duplicates(subset=['nome']).iterrows():
            d_str = formatar_data_br(r['data_nascimento'])
            if d_str != "N/A":
                dt = datetime.strptime(d_str, "%d/%m/%Y")
                if dt.month == hoje.month:
                    lista_mes.append({'dia': dt.day, 'nome': r['nome'], 'tipo': 'CATEQUISTA', 'info': r['papel']})
    if lista_mes: return pd.DataFrame(lista_mes).sort_values(by='dia')
    return pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = date.today()
    lista = []
    for _, r in df_cat.iterrows():
        d_str = formatar_data_br(r['data_nascimento'])
        if d_str != "N/A":
            dt = datetime.strptime(d_str, "%d/%m/%Y")
            if dt.month == hoje.month:
                lista.append({'nome_completo': r['nome_completo'], 'dia': dt.day, 'etapa': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

# ==========================================
# 3. NÚCLEO GERADOR DE PDF (PADRÃO DIOCESANO)
# ==========================================

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

# ==========================================
# 4. GERADORES DE DOCUMENTOS
# ==========================================

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF(); pdf.add_page()
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    titulo = "FICHA DE INSCRIÇÃO (ADULTOS)" if is_adulto else "FICHA DE INSCRIÇÃO (INFANTIL/JUVENIL)"
    adicionar_cabecalho_diocesano(pdf, titulo, etapa=dados.get('etapa', ''))
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. IDENTIFICAÇÃO DO(A) CATEQUIZANDO(A)"), ln=True, fill=True); pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Data de Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Endereço Completo:", dados.get('endereco_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Batizado:", dados.get('batizado_sn', 'NÃO INFORMADO'), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Telefone / WhatsApp:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Sacramentos já realizados:", dados.get('sacramentos_ja_feitos', 'NENHUM'), 75, y, 120)
    
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    subtitulo = "  2. OUTROS ELEMENTOS / VIDA SOCIAL" if is_adulto else "  2. FILIAÇÃO E RESPONSÁVEIS"
    pdf.cell(0, 7, limpar_texto(subtitulo), ln=True, fill=True); pdf.ln(2)
    
    y = pdf.get_y()
    if not is_adulto:
        desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', 'N/A'), 10, y, 185)
        y += 16
        desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', 'N/A'), 10, y, 185)
        y += 16
        desenhar_campo_box(pdf, "Responsável Legal:", dados.get('nome_responsavel', 'N/A'), 10, y, 185)
    else:
        desenhar_campo_box(pdf, "Estado Civil:", dados.get('estado_civil_pais_ou_proprio', 'N/A'), 10, y, 90)
        desenhar_campo_box(pdf, "Participa de Pastoral/Grupo?", dados.get('engajado_grupo', 'NÃO'), 105, y, 90)

    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  3. INFORMAÇÕES DE SAÚDE E DOCUMENTOS"), ln=True, fill=True); pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Medicamentos / Alergias:", dados.get('toma_medicamento_sn', 'NÃO'), 10, y, 120)
    desenhar_campo_box(pdf, "Necessidades Especiais:", dados.get('tgo_sn', 'NÃO'), 135, y, 60)
    y += 16
    desenhar_campo_box(pdf, "Documentos em Falta:", dados.get('doc_em_falta', 'NADA CONSTA'), 10, y, 185)

    pdf.set_y(y + 20)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE CONSENTIMENTO (LGPD)"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    texto_lgpd = "Autorizo o uso de dados e imagem para fins estritamente pastorais conforme a LGPD."
    pdf.multi_cell(0, 4, limpar_texto(texto_lgpd))

    pdf.ln(15)
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    label_ass = "Assinatura do Catequizando" if is_adulto else "Assinatura do Responsável"
    pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
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
    
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. VIDA SACRAMENTAL E QUALIFICAÇÃO"), ln=True, fill=True); pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Batismo:", formatar_data_br(dados.get('data_batismo', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(dados.get('data_eucaristia', '')), 58, y, 45)
    desenhar_campo_box(pdf, "Crisma:", formatar_data_br(dados.get('data_crisma', '')), 106, y, 45)
    desenhar_campo_box(pdf, "Ministério:", formatar_data_br(dados.get('data_ministerio', '')), 154, y, 41)
    
    pdf.set_y(y + 20)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  3. HISTÓRICO DE FORMAÇÕES (ANO VIGENTE)"), ln=True, fill=True); pdf.ln(2)
    
    if not df_formacoes.empty:
        pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(30, 7, "Data", 1, 0, 'C'); pdf.cell(100, 7, "Tema", 1, 0, 'L'); pdf.cell(55, 7, "Formador", 1, 1, 'L')
        pdf.set_font("helvetica", "", 8)
        for _, row in df_formacoes.iterrows():
            pdf.cell(30, 6, formatar_data_br(row.get('data', '')), 1, 0, 'C')
            pdf.cell(100, 6, limpar_texto(str(row.get('tema', ''))[:55]), 1, 0, 'L')
            pdf.cell(55, 6, limpar_texto(str(row.get('formador', ''))[:30]), 1, 1, 'L')
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE COMPROMISSO E VERACIDADE"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 4, limpar_texto("Declaro que as informações prestadas são verdadeiras e assumo o compromisso com a missão evangelizadora."))
    
    pdf.ln(15)
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    
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

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    
    # --- CABEÇALHO DUPLO (ESTILO OFICIAL) ---
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 10, 22)
    
    pdf.set_xy(35, 10)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, limpar_texto(f"Data: {date.today().strftime('%d / %m / %Y')}"), ln=True, align='R')
    
    pdf.set_x(35)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(5)
    # Caixa de Ano/Etapa/Turma
    y_topo = pdf.get_y()
    pdf.set_fill_color(248, 249, 240)
    pdf.rect(10, y_topo, 100, 15, 'F')
    pdf.rect(10, y_topo, 100, 15)
    pdf.set_xy(12, y_topo + 2)
    pdf.set_font("helvetica", "B", 11); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(95, 5, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    
    pdf.set_xy(115, y_topo)
    pdf.cell(40, 15, limpar_texto(f"Ano: {date.today().year}"), border=1, align='C')
    pdf.set_xy(155, y_topo)
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(45, 7.5, limpar_texto(f"Etapa: {dados.get('etapa', '')}\nTurma: {dados.get('etapa', '')}"), border=1)

    pdf.ln(5)
    # Turno e Local
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, limpar_texto(f"Turno: (  ) M  (  ) T  (  ) N        Local: _________________________________________"), ln=True)

    # --- TÍTULO SEÇÃO ---
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    pdf.ln(2)

    # --- GRADE DE DADOS ---
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome:", dados.get('nome_completo', ''), 10, y, 190)
    y += 15
    desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 50)
    desenhar_campo_box(pdf, "Idade:", str(calcular_idade(dados.get('data_nascimento', ''))), 65, y, 30)
    desenhar_campo_box(pdf, "Batizado:", f"Sim ( { 'X' if dados.get('batizado_sn')=='SIM' else ' ' } )  Não ( { 'X' if dados.get('batizado_sn')=='NÃO' else ' ' } )", 100, y, 100)
    y += 15
    desenhar_campo_box(pdf, "Morada (Endereço):", dados.get('endereco_completo', ''), 10, y, 190)
    y += 15
    desenhar_campo_box(pdf, "Telefone:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Tomar algum medicamento?", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    # --- FILIAÇÃO ---
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 190)
    y += 15
    desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 190)
    
    # --- OUTROS ELEMENTOS ---
    pdf.set_y(y + 18)
    pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil dos pais e Vida Eclesial"), ln=True)
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, limpar_texto("Estado Civil: Casados ( )  União de Facto ( )  Separados ( )  Solteiros ( )  Viúvo ( )"), ln=True)
    pdf.cell(0, 6, limpar_texto("Sacramentos dos pais: Batismo ( )  Crisma ( )  Eucaristia ( )  Matrimônio ( )"), ln=True)
    pdf.cell(0, 6, limpar_texto("Participam de Pastoral? Sim ( ) Não ( )  Qual: ____________________________________"), ln=True)
    pdf.cell(0, 6, limpar_texto("Tem irmãos na catequese? Sim ( ) Não ( )  Quantos: ________"), ln=True)
    
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 9); pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 6, limpar_texto("A criança tem algum Transtorno Global do Desenvolvimento (TGO)?"), ln=True)
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, limpar_texto(f"Resposta: {dados.get('tgo_sn', 'NÃO')} __________________________________________________________________"), border=1, ln=True)

    # --- TERMO DE CONSENTIMENTO (TEXTO EXATO DA IMAGEM) ---
    pdf.ln(4)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Termo de Consentimento"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    
    nome_resp = dados.get('nome_responsavel', '_________________________________')
    nome_cat = dados.get('nome_completo', '_________________________________')
    
    texto_lgpd = (f"Eu {nome_resp}, na qualidade de pai/mãe ou responsável pelo (a) catequizando (a), {nome_cat}, "
                  "AUTORIZO o uso da publicação da imagem do (a) meu (minha) filho (a) dos eventos realizados pela "
                  "Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social "
                  "da Pastoral ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da "
                  "Lei de Proteção de Dados (LGPD), que regula as atividades de tratamento de dados pessoais colhidos "
                  "no momento da inscrição para o(s) sacramento(s) da Iniciação à Vida Cristã com Inspiração Catecumenal.")
    
    pdf.multi_cell(0, 4, limpar_texto(texto_lgpd))

    # --- ASSINATURAS ---
    pdf.ln(10)
    y_ass = pdf.get_y()
    pdf.line(10, y_ass, 90, y_ass)
    pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto("Assinatura do Pai/Mãe ou Responsável"), align='C')
    pdf.set_xy(110, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 7)
    pdf.cell(0, 5, limpar_texto("Obs.: Apresentou os documentos na inscrição: SIM ( )  NÃO ( )  Parcialmente. Faltou: ____________________"), ln=True)

    return finalizar_pdf(pdf)


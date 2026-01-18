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

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA CADASTRAL DO CATEQUISTA", etapa="EQUIPE")
    
    # 1. DADOS PESSOAIS
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. IDENTIFICAÇÃO E CONTATO"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Data de Nascimento:", dados.get('data_nascimento', 'N/A'), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "E-mail de Acesso:", dados.get('email', ''), 10, y, 90)
    desenhar_campo_box(pdf, "Telefone / WhatsApp:", dados.get('telefone', 'N/A'), 105, y, 90)
    y += 16
    desenhar_campo_box(pdf, "Turmas Vinculadas (Ano Vigente):", dados.get('turma_vinculada', 'NÃO VINCULADO'), 10, y, 185)
    
    # 2. VIDA SACRAMENTAL E MINISTÉRIO
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. VIDA SACRAMENTAL E QUALIFICAÇÃO"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Batismo:", dados.get('data_batismo', 'N/A'), 10, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", dados.get('data_eucaristia', 'N/A'), 58, y, 45)
    desenhar_campo_box(pdf, "Crisma:", dados.get('data_crisma', 'N/A'), 106, y, 45)
    desenhar_campo_box(pdf, "Ministério:", dados.get('data_ministerio', 'NÃO POSSUI'), 154, y, 41)
    y += 16
    
    # Cálculo de Status para o PDF
    status_min, anos = verificar_status_ministerial(
        str(dados.get('data_inicio_catequese', '')),
        str(dados.get('data_batismo', '')),
        str(dados.get('data_eucaristia', '')),
        str(dados.get('data_crisma', '')),
        str(dados.get('data_ministerio', ''))
    )
    desenhar_campo_box(pdf, "Tempo de Caminhada:", f"{anos} anos na Pastoral", 10, y, 90)
    desenhar_campo_box(pdf, "Status Ministerial Atual:", status_min, 105, y, 90)

    # 3. HISTÓRICO DE FORMAÇÕES (ANO VIGENTE)
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    ano_atual = date.today().year
    pdf.cell(0, 7, limpar_texto(f"  3. HISTÓRICO DE FORMAÇÕES - ANO {ano_atual}"), ln=True, fill=True)
    pdf.ln(2)
    
    if not df_formacoes.empty:
        # Filtra apenas formações do ano atual para o PDF
        df_formacoes['dt'] = pd.to_datetime(df_formacoes['data'], errors='coerce')
        df_ano = df_formacoes[df_formacoes['dt'].dt.year == ano_atual]
        
        if not df_ano.empty:
            pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
            pdf.cell(30, 7, "Data", 1, 0, 'C'); pdf.cell(100, 7, "Tema", 1, 0, 'L'); pdf.cell(55, 7, "Formador", 1, 1, 'L')
            pdf.set_font("helvetica", "", 8)
            for _, row in df_ano.iterrows():
                pdf.cell(30, 6, str(row.get('data', '')), 1, 0, 'C')
                pdf.cell(100, 6, limpar_texto(str(row.get('tema', ''))[:55]), 1, 0, 'L')
                pdf.cell(55, 6, limpar_texto(str(row.get('formador', ''))[:30]), 1, 1, 'L')
        else:
            pdf.set_font("helvetica", "I", 10); pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, limpar_texto("Nenhuma formação registrada neste ano."), ln=1)
    else:
        pdf.set_font("helvetica", "I", 10); pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, limpar_texto("Sem histórico de formações."), ln=1)

    # 4. TERMO DE COMPROMISSO
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE COMPROMISSO E VERACIDADE"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    
    texto_comp = (f"Eu, {dados.get('nome')}, na qualidade de Catequista da Paróquia Nossa Senhora de Fátima, "
                  "declaro que as informações acima prestadas são verdadeiras e assumo o compromisso de "
                  "zelar pela sã doutrina e pelas diretrizes da Igreja Católica em minha missão evangelizadora.")
    pdf.multi_cell(0, 4, limpar_texto(texto_comp))

    pdf.ln(15)
    y_ass = pdf.get_y() + 10
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    
    # Identifica se é adulto pelo estado civil
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    titulo = "FICHA DE INSCRIÇÃO (ADULTOS)" if is_adulto else "FICHA DE INSCRIÇÃO (INFANTIL/JUVENIL)"
    
    adicionar_cabecalho_diocesano(pdf, titulo, etapa=dados.get('etapa', ''))
    
    # --- SEÇÃO 1: IDENTIFICAÇÃO ---
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
    
    # --- SEÇÃO 2: FAMÍLIA OU VIDA SOCIAL ---
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

    # --- SEÇÃO 3: SAÚDE E DOCUMENTAÇÃO ---
    pdf.set_y(y + 18 if is_adulto else y + 18)
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  3. INFORMAÇÕES DE SAÚDE E DOCUMENTOS"), ln=True, fill=True); pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Medicamentos / Alergias:", dados.get('toma_medicamento_sn', 'NÃO'), 10, y, 120)
    # Mudança de nome de TGO para Necessidades Especiais no PDF
    desenhar_campo_box(pdf, "Necessidades Especiais:", dados.get('tgo_sn', 'NÃO'), 135, y, 60)
    y += 16
    desenhar_campo_box(pdf, "Documentos em Falta:", dados.get('doc_em_falta', 'NADA CONSTA'), 10, y, 185)

    # --- SEÇÃO 4: CONSENTIMENTO E ASSINATURAS ---
    pdf.set_y(y + 20)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE CONSENTIMENTO (LGPD)"), ln=True)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(0, 0, 0)
    
    texto_lgpd = ("Autorizo o uso dos dados acima e da imagem do catequizando para fins estritamente pastorais, "
                  "conforme a Lei Geral de Proteção de Dados (LGPD) e diretrizes da Diocese.")
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

# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os
import re

# --- FUNÇÕES DE CÁLCULO E DATA ---
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
    elif idade > 14: return "PERSEVERANÇA / ADULTOS"
    else: return "MUITO JOVEM"

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

# --- GERADORES DE PDF (ESTILO DIOCESANO COM CAIXAS) ---

def limpar_texto(texto):
    if not texto: return ""
    texto = re.sub(r'[*#_~-]', '', str(texto))
    return texto.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    try:
        saida = pdf.output()
        if saida and len(saida) > 0:
            if isinstance(saida, str): return saida.encode('latin-1')
            return bytes(saida)
        return pdf.output(dest='S').encode('latin-1')
    except:
        try: return pdf.output(dest='S').encode('latin-1')
        except: return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=9):
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240) 
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def adicionar_cabecalho_diocesano(pdf, titulo, etapa=""):
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 12, 10, 28)
    
    pdf.set_xy(42, 12)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153) 
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese - Diocese de Itabuna-BA"), ln=True)
    pdf.set_x(42)
    pdf.cell(100, 5, limpar_texto("Paróquia Nossa Senhora de Fátima"), ln=True)
    
    pdf.set_text_color(0, 0, 0)
    desenhar_campo_box(pdf, "Ano:", str(date.today().year), 150, 10, 45, h=7)
    desenhar_campo_box(pdf, "Documento:", etapa, 150, 22, 45, h=7)

    pdf.set_xy(10, 45)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(224, 61, 17) 
    pdf.cell(0, 10, limpar_texto(titulo), ln=True, align='C')
    pdf.ln(2)

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    is_adulto = str(dados.get('estado_civil_pais_ou_proprio', 'N/A')).upper() != "N/A"
    titulo = "FICHA DE INSCRIÇÃO DA CATEQUESE (ADULTOS)" if is_adulto else "FICHA DE INSCRIÇÃO DA CATEQUESE (INFANTIL/JUVENIL)"
    adicionar_cabecalho_diocesano(pdf, titulo, etapa=dados.get('etapa', ''))
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  IDENTIFICAÇÃO DO(A) CATEQUIZANDO(A)"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Data de Nascimento:", dados.get('data_nascimento', ''), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Endereço Completo:", dados.get('endereco_completo', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Batizado:", dados.get('batizado_sn', ''), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "Telefone / WhatsApp:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Sacramentos já realizados:", dados.get('sacramentos_ja_feitos', 'NENHUM'), 75, y, 120)
    
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    subtitulo = "  OUTROS ELEMENTOS / VIDA SOCIAL" if is_adulto else "  FILIAÇÃO E RESPONSÁVEIS"
    pdf.cell(0, 7, limpar_texto(subtitulo), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    if not is_adulto:
        desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 185)
        y += 16
        desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 185)
        y += 16
        desenhar_campo_box(pdf, "Responsável Legal:", dados.get('nome_responsavel', ''), 10, y, 185)
    else:
        desenhar_campo_box(pdf, "Estado Civil:", dados.get('estado_civil_pais_ou_proprio', ''), 10, y, 90)
        desenhar_campo_box(pdf, "Participa de Pastoral/Grupo?", dados.get('engajado_grupo', 'NÃO'), 105, y, 90)

    pdf.set_y(y + 20)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  INFORMAÇÕES DE SAÚDE E OBSERVAÇÕES"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Medicamentos / Alergias / TGO:", f"{dados.get('toma_medicamento_sn', 'NÃO')} | TGO: {dados.get('tgo_sn', 'NÃO')}", 10, y, 185)
    y += 16
    desenhar_campo_box(pdf, "Observações Gerais / Documentos Faltantes:", dados.get('doc_em_falta', 'NADA CONSTA'), 10, y, 185, h=12)

    pdf.set_y(y + 30)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE CONSENTIMENTO (LGPD)"), ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    if is_adulto:
        texto = (f"Eu, {dados.get('nome_completo')}, declaro que as informações acima são verdadeiras. "
                 "AUTORIZO o uso da minha imagem em eventos da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima "
                 "em redes sociais e murais, conforme a Lei Geral de Proteção de Dados (LGPD).")
    else:
        texto = (f"Eu, na qualidade de responsável pelo(a) catequizando(a) {dados.get('nome_completo')}, "
                 "AUTORIZO o uso da imagem do referido menor em eventos realizados pela Pastoral da Catequese da Paróquia "
                 "Nossa Senhora de Fátima, conforme determina a LGPD e o Art. 5º, X da Constituição Federal.")
    
    pdf.multi_cell(0, 4, limpar_texto(texto))

    pdf.ln(10)
    y_ass = pdf.get_y() + 12
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    label_ass = "Assinatura do Catequizando" if is_adulto else "Assinatura do Responsável"
    pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA CADASTRAL DO CATEQUISTA", etapa="EQUIPE")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  DADOS PESSOAIS E CONTATO"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Nome do Catequista:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", dados.get('data_nascimento', ''), 150, y, 45)
    y += 16
    desenhar_campo_box(pdf, "E-mail de Acesso:", dados.get('email', ''), 10, y, 90)
    desenhar_campo_box(pdf, "Telefone:", dados.get('telefone', ''), 105, y, 90)
    
    pdf.set_y(y + 18)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  VIDA SACRAMENTAL E MINISTÉRIO"), ln=True, fill=True)
    pdf.ln(2)
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Batismo:", dados.get('data_batismo', ''), 10, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", dados.get('data_eucaristia', ''), 58, y, 45)
    desenhar_campo_box(pdf, "Crisma:", dados.get('data_crisma', ''), 106, y, 45)
    desenhar_campo_box(pdf, "Ministério:", dados.get('data_ministerio', 'NÃO'), 154, y, 41)
    
    pdf.set_y(y + 20)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto(f"  HISTÓRICO DE FORMAÇÕES ({date.today().year})"), ln=True, fill=True)
    pdf.ln(2)
    
    if not df_formacoes.empty:
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(30, 7, "Data", 1, 0, 'C')
        pdf.cell(100, 7, "Tema", 1, 0, 'L')
        pdf.cell(55, 7, "Formador", 1, 1, 'L')
        pdf.set_font("helvetica", "", 8)
        for _, row in df_formacoes.iterrows():
            pdf.cell(30, 6, str(row.get('data', '')), 1, 0, 'C')
            pdf.cell(100, 6, limpar_texto(str(row.get('tema', ''))[:55]), 1, 0, 'L')
            pdf.cell(55, 6, limpar_texto(str(row.get('formador', ''))[:30]), 1, 1, 'L')
    else:
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, limpar_texto("Nenhuma formação registrada no período."), ln=1)

    pdf.ln(10)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 5, limpar_texto("TERMO DE COMPROMISSO E VERACIDADE"), ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    texto_comp = (f"Eu, {dados.get('nome')}, na qualidade de Catequista desta Paróquia, declaro estar ciente da responsabilidade "
                  "da missão evangelizadora e confirmo a veracidade de todas as informações prestadas neste cadastro. "
                  "Comprometo-me com a doutrina da Igreja Católica e com as diretrizes desta Pastoral.")
    pdf.multi_cell(0, 4, limpar_texto(texto_comp))

    pdf.ln(10)
    y_ass = pdf.get_y() + 12
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"PERFIL DA TURMA: {nome_turma}", etapa=nome_turma)
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  ESTATÍSTICAS E DADOS GERAIS"), ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    for chave, valor in metricas.items():
        pdf.set_font("helvetica", "B", 10)
        pdf.write(8, limpar_texto(f"{chave}: "))
        pdf.set_font("helvetica", "", 10)
        pdf.write(8, limpar_texto(f"{valor}\n"))
    
    pdf.ln(5)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  ANÁLISE PASTORAL (IA GEMINI)"), ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    
    pdf.ln(5)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  RELAÇÃO DE CATEQUIZANDOS ATIVOS"), ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    for i, aluno in enumerate(lista_alunos, 1):
        pdf.cell(0, 6, limpar_texto(f"{i}. {aluno}"), ln=True)
        
    return finalizar_pdf(pdf)

# --- RELATÓRIOS TÉCNICOS (FASE 2 - REVISADOS) ---

def gerar_relatorio_diocesano_pdf(dados_gerais, turmas_detalhes, sacramentos_stats, projecoes, analise_ia):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO TÉCNICO DA CATEQUESE", etapa="DIOCESANO")
    
    # 1. CENSO POPULACIONAL
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. CENSO DE CATEQUIZANDOS E EQUIPE"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    desenhar_campo_box(pdf, "Total Geral:", str(dados_gerais['total_cat']), 10, y, 45)
    desenhar_campo_box(pdf, "Infantil/Juvenil:", str(dados_gerais['total_kids']), 58, y, 45)
    desenhar_campo_box(pdf, "Adultos:", str(dados_gerais['total_adults']), 106, y, 45)
    desenhar_campo_box(pdf, "Equipe Catequética:", str(dados_gerais['total_equipe']), 154, y, 41)
    
    pdf.set_y(y + 18)
    
    # 2. ANÁLISE DESCRITIVA (IA)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. ANÁLISE TÉCNICA E PROJEÇÕES"), ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    pdf.ln(4)

    # 3. DETALHAMENTO DE TURMAS
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  3. MAPA DE TURMAS E ETAPAS"), ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(70, 7, "Nome da Turma", 1, 0, 'L')
    pdf.cell(50, 7, "Público Alvo", 1, 0, 'L')
    pdf.cell(40, 7, "Dia Encontro", 1, 0, 'C')
    pdf.cell(25, 7, "Qtd Alunos", 1, 1, 'C')
    
    pdf.set_font("helvetica", "", 8)
    for t in turmas_detalhes:
        pdf.cell(70, 6, limpar_texto(t['nome']), 1, 0, 'L')
        pdf.cell(50, 6, limpar_texto(t['publico']), 1, 0, 'L')
        pdf.cell(40, 6, limpar_texto(t['dias']), 1, 0, 'C')
        pdf.cell(25, 6, str(t['qtd_alunos']), 1, 1, 'C')

    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(stats, analise_turmas, analise_ia):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO TÉCNICO DE AUDITORIA SACRAMENTAL", etapa="SACRAMENTOS")
    
    # 1. QUADRO GERAL SEGMENTADO
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  1. QUADRO GERAL DE SACRAMENTOS (POR PÚBLICO)"), ln=True, fill=True)
    pdf.ln(2)
    
    y = pdf.get_y()
    # Linha Kids
    desenhar_campo_box(pdf, "Infantil - Batismos:", str(stats['bat_k']), 10, y, 90)
    desenhar_campo_box(pdf, "Infantil - Eucaristias:", str(stats['euca_k']), 105, y, 90)
    y += 16
    # Linha Adultos
    desenhar_campo_box(pdf, "Adultos - Batismos:", str(stats['bat_a']), 10, y, 60)
    desenhar_campo_box(pdf, "Adultos - Eucaristias:", str(stats['euca_a']), 75, y, 60)
    desenhar_campo_box(pdf, "Adultos - Crismas:", str(stats['cris_a']), 140, y, 55)
    
    pdf.set_y(y + 20)
    # 2. ANÁLISE POR TURMA
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  2. AUDITORIA NOMINAL POR TURMA E PREVISÕES"), ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(60, 6, "Turma", 1, 0, 'L')
    pdf.cell(30, 6, "Batizados", 1, 0, 'C')
    pdf.cell(30, 6, "Pendentes", 1, 0, 'C')
    pdf.cell(35, 6, "Prev. Eucaristia", 1, 0, 'C')
    pdf.cell(35, 6, "Prev. Crisma", 1, 1, 'C')
    
    pdf.set_font("helvetica", "", 8)
    for t in analise_turmas:
        pdf.cell(60, 6, limpar_texto(t['turma']), 1, 0, 'L')
        pdf.cell(30, 6, str(t['batizados']), 1, 0, 'C')
        pdf.cell(30, 6, str(t['pendentes']), 1, 0, 'C')
        pdf.cell(35, 6, limpar_texto(t['prev_e']), 1, 0, 'C')
        pdf.cell(35, 6, limpar_texto(t['prev_c']), 1, 1, 'C')

    pdf.ln(5)
    # 3. ANÁLISE IA
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  3. DIAGNÓSTICO PASTORAL E RECOMENDAÇÕES"), ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 10); pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))

    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_interno_pdf(dados_gerais, analise_ia):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL DE ALINHAMENTO INTERNO", etapa="PASTORAL")
    
    pdf.set_fill_color(224, 61, 17) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("  DIAGNÓSTICO PASTORAL E PEDAGÓGICO (IA)"), ln=True, fill=True)
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, limpar_texto(analise_ia))
    
    pdf.ln(10)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("  PONTOS PARA DISCUSSÃO EM REUNIÃO"), ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, limpar_texto("- Avaliação da frequência média global."), ln=True)
    pdf.cell(0, 8, limpar_texto("- Estratégias para catequizandos em risco de evasão."), ln=True)
    pdf.cell(0, 8, limpar_texto("- Planejamento das próximas celebrações sacramentais."), ln=True)
    pdf.cell(0, 8, limpar_texto("- Necessidades de formação continuada da equipe."), ln=True)

    return finalizar_pdf(pdf)

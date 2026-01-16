# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF

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

# --- GERADORES DE PDF ---

def limpar_texto(texto):
    """Remove caracteres que o FPDF não suporta."""
    if not texto: return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    """Garante o retorno de bytes real, compatível com FPDF e FPDF2."""
    try:
        # Tenta o modo FPDF2 (retorna bytes)
        saida = pdf.output()
        if saida and len(saida) > 0:
            if isinstance(saida, str): return saida.encode('latin-1')
            return bytes(saida)
        
        # Fallback para FPDF clássico (exige dest='S' para retornar string)
        return pdf.output(dest='S').encode('latin-1')
    except:
        # Última tentativa forçando string
        try:
            return pdf.output(dest='S').encode('latin-1')
        except:
            return b""

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, limpar_texto(f"Perfil da Turma: {nome_turma}"), ln=True, align='C')
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Gerado em: {date.today().strftime('%d/%m/%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, limpar_texto("Estatísticas Rápidas:"), ln=True)
    pdf.set_font("helvetica", "", 11)
    for chave, valor in metricas.items():
        pdf.cell(0, 8, limpar_texto(f"- {chave}: {valor}"), ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, limpar_texto("Análise Pastoral (IA):"), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, limpar_texto("Relação de Catequizandos:"), ln=True)
    pdf.set_font("helvetica", "", 9)
    for aluno in lista_alunos:
        pdf.cell(0, 6, limpar_texto(f"- {aluno}"), ln=True)
        
    return finalizar_pdf(pdf)

def gerar_ficha_cadastral_catequizando(dados):
    """Gera ficha de inscrição com linhas de assinatura."""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, limpar_texto("FICHA DE INSCRIÇÃO - CATEQUESE"), ln=True, align='C')
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, limpar_texto("Paróquia Nossa Senhora de Fátima"), ln=True, align='C')
    pdf.ln(10)
    
    # Dados Pessoais
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, limpar_texto("1. DADOS DO CATEQUIZANDO"), ln=True, fill=False)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    campos = [
        f"Nome: {dados.get('nome_completo', '')}",
        f"Nascimento: {dados.get('data_nascimento', '')}",
        f"Turma/Etapa: {dados.get('etapa', '')}",
        f"Endereço: {dados.get('endereco_completo', '')}",
        f"Batizado: {dados.get('batizado_sn', '')}",
        f"Sacramentos Feitos: {dados.get('sacramentos_ja_feitos', '')}"
    ]
    for c in campos: pdf.cell(0, 8, limpar_texto(c), ln=True)
    pdf.ln(5)
    
    # Dados Família
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, limpar_texto("2. DADOS DA FAMÍLIA"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    campos_fam = [
        f"Mãe: {dados.get('nome_mae', '')}",
        f"Pai: {dados.get('nome_pai', '')}",
        f"Responsável: {dados.get('nome_responsavel', '')}",
        f"Contato: {dados.get('contato_principal', '')}",
        f"Estado Civil Pais: {dados.get('estado_civil_pais_ou_proprio', '')}"
    ]
    for c in campos_fam: pdf.cell(0, 8, limpar_texto(c), ln=True)
    pdf.ln(5)
    
    # Saúde
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, limpar_texto("3. SAÚDE E OBSERVAÇÕES"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("helvetica", "", 11)
    
    pdf.set_x(10)
    pdf.multi_cell(0, 6, limpar_texto(f"Medicamentos/Alergias: {dados.get('toma_medicamento_sn', '')}"))
    
    pdf.ln(2)
    pdf.set_x(10)
    pdf.multi_cell(0, 6, limpar_texto(f"Observações: {dados.get('doc_em_falta', '')}"))
    
    pdf.ln(30)
    
    # Assinaturas
    y_ass = pdf.get_y()
    pdf.line(20, y_ass, 90, y_ass)
    pdf.line(110, y_ass, 190, y_ass)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_xy(20, y_ass + 2)
    pdf.cell(70, 5, limpar_texto("Assinatura do Responsável/Catequizando"), align='C')
    
    pdf.set_xy(110, y_ass + 2)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista/Coordenação"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    """Gera ficha do catequista com histórico de formações."""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, limpar_texto("FICHA CADASTRAL - CATEQUISTA"), ln=True, align='C')
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, limpar_texto("Diocese de Itabuna - Paróquia N. Sra. de Fátima"), ln=True, align='C')
    pdf.ln(10)
    
    # Dados Pessoais
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, limpar_texto("DADOS PESSOAIS"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    campos = [
        f"Nome: {dados.get('nome', '')}",
        f"Email: {dados.get('email', '')}",
        f"Telefone: {dados.get('telefone', '')}",
        f"Nascimento: {dados.get('data_nascimento', '')}",
        f"Turmas: {dados.get('turma_vinculada', '')}",
        f"Início na Catequese: {dados.get('data_inicio_catequese', '')}"
    ]
    for c in campos: pdf.cell(0, 8, limpar_texto(c), ln=True)
    
    # Sacramentos
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, limpar_texto("VIDA SACRAMENTAL"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("helvetica", "", 11)
    sac = [
        f"Batismo: {dados.get('data_batismo', '')}",
        f"Eucaristia: {dados.get('data_eucaristia', '')}",
        f"Crisma: {dados.get('data_crisma', '')}",
        f"Ministério Instituído: {dados.get('data_ministerio', 'Não')}"
    ]
    for s in sac: pdf.cell(0, 8, limpar_texto(s), ln=True)
    
    # Histórico de Formações
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, limpar_texto(f"HISTÓRICO DE FORMAÇÕES ({date.today().year})"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    if not df_formacoes.empty:
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(30, 8, "Data", 1)
        pdf.cell(100, 8, "Tema", 1)
        pdf.cell(60, 8, "Formador", 1)
        pdf.ln()
        
        pdf.set_font("helvetica", "", 10)
        for _, row in df_formacoes.iterrows():
            data_fmt = str(row.get('data', ''))
            tema_fmt = limpar_texto(str(row.get('tema', '')))[:50]
            form_fmt = limpar_texto(str(row.get('formador', '')))[:30]
            
            pdf.cell(30, 8, data_fmt, 1)
            pdf.cell(100, 8, tema_fmt, 1)
            pdf.cell(60, 8, form_fmt, 1)
            pdf.ln()
    else:
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 10, limpar_texto("Nenhuma formação registrada neste ano."), ln=True)

    # Assinaturas
    pdf.ln(30)
    y_ass = pdf.get_y()
    pdf.line(20, y_ass, 90, y_ass)
    pdf.line(110, y_ass, 190, y_ass)
    
    pdf.set_font("helvetica", "", 9)
    pdf.set_xy(20, y_ass + 2)
    pdf.cell(70, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
    pdf.set_xy(110, y_ass + 2)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    
    return finalizar_pdf(pdf)

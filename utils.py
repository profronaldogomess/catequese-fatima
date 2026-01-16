# ARQUIVO: utils.py
from datetime import date, datetime
import pandas as pd
from fpdf import FPDF
import os

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
        saida = pdf.output()
        if saida and len(saida) > 0:
            if isinstance(saida, str): return saida.encode('latin-1')
            return bytes(saida)
        return pdf.output(dest='S').encode('latin-1')
    except:
        try: return pdf.output(dest='S').encode('latin-1')
        except: return b""

def adicionar_cabecalho_institucional(pdf, titulo_documento):
    """Adiciona o cabeçalho padrão com logo, diocese e paróquia."""
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 33)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(65, 123, 153) # Azul do Sistema
    pdf.cell(0, 7, limpar_texto("DIOCESE DE ITABUNA"), ln=True, align='C')
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, limpar_texto("PARÓQUIA NOSSA SENHORA DE FÁTIMA"), ln=True, align='C')
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 7, limpar_texto("Pastoral da Catequese"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(224, 61, 17) # Laranja do Sistema
    pdf.cell(0, 10, limpar_texto(titulo_documento), ln=True, align='C')
    pdf.set_text_color(0, 0, 0) # Volta para preto
    pdf.ln(5)

def desenhar_secao(pdf, titulo):
    """Desenha uma barra de seção estilizada."""
    pdf.set_fill_color(65, 123, 153) # Azul
    pdf.set_text_color(255, 255, 255) # Branco
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, limpar_texto(f"  {titulo}"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

def gerar_pdf_perfil_turma(nome_turma, metricas, analise_ia, lista_alunos):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_institucional(pdf, f"PERFIL DA TURMA: {nome_turma}")
    
    desenhar_secao(pdf, "ESTATÍSTICAS DA TURMA")
    pdf.set_font("helvetica", "", 11)
    for chave, valor in metricas.items():
        pdf.set_font("helvetica", "B", 10)
        pdf.write(8, limpar_texto(f"{chave}: "))
        pdf.set_font("helvetica", "", 10)
        pdf.write(8, limpar_texto(f"{valor}\n"))
    
    pdf.ln(5)
    desenhar_secao(pdf, "ANÁLISE PASTORAL (IA)")
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, limpar_texto(analise_ia))
    
    pdf.ln(5)
    desenhar_secao(pdf, "RELAÇÃO DE CATEQUIZANDOS")
    pdf.set_font("helvetica", "", 9)
    for i, aluno in enumerate(lista_alunos, 1):
        pdf.cell(0, 6, limpar_texto(f"{i}. {aluno}"), ln=True)
        
    return finalizar_pdf(pdf)

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_institucional(pdf, "FICHA DE INSCRIÇÃO DO CATEQUIZANDO")
    
    # 1. Dados Pessoais
    desenhar_secao(pdf, "1. DADOS DO CATEQUIZANDO")
    pdf.set_font("helvetica", "B", 10)
    
    col_w = 95
    pdf.cell(col_w, 8, limpar_texto(f"Nome: {dados.get('nome_completo', '')}"), ln=0)
    pdf.cell(col_w, 8, limpar_texto(f"Nascimento: {dados.get('data_nascimento', '')}"), ln=1)
    
    pdf.cell(col_w, 8, limpar_texto(f"Turma/Etapa: {dados.get('etapa', '')}"), ln=0)
    pdf.cell(col_w, 8, limpar_texto(f"Batizado: {dados.get('batizado_sn', '')}"), ln=1)
    
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 8, limpar_texto(f"Endereço: {dados.get('endereco_completo', '')}"))
    pdf.cell(0, 8, limpar_texto(f"Sacramentos Realizados: {dados.get('sacramentos_ja_feitos', 'NENHUM')}"), ln=1)
    pdf.ln(3)

    # 2. Família
    desenhar_secao(pdf, "2. DADOS DA FAMÍLIA / RESPONSÁVEIS")
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, limpar_texto(f"Mãe: {dados.get('nome_mae', 'N/A')}"), ln=1)
    pdf.cell(0, 8, limpar_texto(f"Pai: {dados.get('nome_pai', 'N/A')}"), ln=1)
    pdf.cell(col_w, 8, limpar_texto(f"Responsável Legal: {dados.get('nome_responsavel', 'O PRÓPRIO')}"), ln=0)
    pdf.cell(col_w, 8, limpar_texto(f"Contato: {dados.get('contato_principal', '')}"), ln=1)
    pdf.ln(3)

    # 3. Saúde
    desenhar_secao(pdf, "3. INFORMAÇÕES DE SAÚDE E OBSERVAÇÕES")
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 7, limpar_texto(f"Medicamentos/Alergias/TGO: {dados.get('toma_medicamento_sn', 'NÃO')} / TGO: {dados.get('tgo_sn', 'NÃO')}"))
    pdf.multi_cell(0, 7, limpar_texto(f"Observações Gerais: {dados.get('doc_em_falta', 'NADA CONSTA')}"))
    
    # Assinaturas
    pdf.ln(20)
    pdf.set_font("helvetica", "I", 9)
    pdf.cell(0, 5, limpar_texto(f"Itabuna - BA, {date.today().strftime('%d de %B de %Y')}"), ln=1, align='R')
    pdf.ln(15)
    
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    
    pdf.set_xy(15, y_ass + 2)
    pdf.cell(80, 5, limpar_texto("Assinatura do Responsável"), align='C')
    pdf.set_xy(115, y_ass + 2)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_institucional(pdf, "FICHA CADASTRAL DO CATEQUISTA")
    
    desenhar_secao(pdf, "DADOS PESSOAIS E ECLESIAIS")
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(110, 8, limpar_texto(f"Nome: {dados.get('nome', '')}"), ln=0)
    pdf.cell(80, 8, limpar_texto(f"Nascimento: {dados.get('data_nascimento', '')}"), ln=1)
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(110, 8, limpar_texto(f"E-mail: {dados.get('email', '')}"), ln=0)
    pdf.cell(80, 8, limpar_texto(f"Telefone: {dados.get('telefone', '')}"), ln=1)
    
    pdf.cell(110, 8, limpar_texto(f"Turmas Vinculadas: {dados.get('turma_vinculada', '')}"), ln=0)
    pdf.cell(80, 8, limpar_texto(f"Início na Catequese: {dados.get('data_inicio_catequese', '')}"), ln=1)
    
    pdf.ln(3)
    desenhar_secao(pdf, "VIDA SACRAMENTAL")
    pdf.cell(47, 8, limpar_texto(f"Batismo: {dados.get('data_batismo', '')}"), ln=0)
    pdf.cell(47, 8, limpar_texto(f"Eucaristia: {dados.get('data_eucaristia', '')}"), ln=0)
    pdf.cell(47, 8, limpar_texto(f"Crisma: {dados.get('data_crisma', '')}"), ln=0)
    pdf.cell(47, 8, limpar_texto(f"Ministério: {dados.get('data_ministerio', 'NÃO')}"), ln=1)
    
    pdf.ln(3)
    desenhar_secao(pdf, f"HISTÓRICO DE FORMAÇÕES ({date.today().year})")
    
    if not df_formacoes.empty:
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(30, 8, "Data", 1, 0, 'C', True)
        pdf.cell(100, 8, "Tema", 1, 0, 'L', True)
        pdf.cell(60, 8, "Formador", 1, 1, 'L', True)
        
        pdf.set_font("helvetica", "", 9)
        for _, row in df_formacoes.iterrows():
            pdf.cell(30, 7, str(row.get('data', '')), 1, 0, 'C')
            pdf.cell(100, 7, limpar_texto(str(row.get('tema', ''))[:55]), 1, 0, 'L')
            pdf.cell(60, 7, limpar_texto(str(row.get('formador', ''))[:30]), 1, 1, 'L')
    else:
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 10, limpar_texto("Nenhuma formação registrada no período."), ln=1)

    pdf.ln(25)
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    
    pdf.set_xy(15, y_ass + 2)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 2)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador"), align='C')
    
    return finalizar_pdf(pdf)

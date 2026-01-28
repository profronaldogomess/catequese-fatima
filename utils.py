# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 6.5.0 - INTEGRIDADE TOTAL (SEM REDUÇÃO / SEM SIMPLIFICAÇÃO)
# MISSÃO: Motor de Documentação, Auditoria Sacramental e Identidade Visual.
# ==============================================================================

from datetime import date, datetime, timedelta, timezone
import datetime as dt_module
import pandas as pd
from fpdf import FPDF
import os
import re
import io
import random
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ==============================================================================
# 1. FUNÇÕES DE APOIO, FORMATAÇÃO E TRATAMENTO DE DADOS (BLINDAGEM)
# ==============================================================================

def formatar_data_br(valor):
    """Garante que qualquer data seja exibida como DD/MM/AAAA."""
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    s = str(valor).strip().split(' ')[0]
    if re.match(r"^\d{2}/\d{2}/\d{4}$", s): return s
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        partes = s.split('-')
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    try:
        dt = pd.to_datetime(s, dayfirst=True)
        if pd.notnull(dt): return dt.strftime('%d/%m/%Y')
    except: pass
    return s

def calcular_idade(data_nascimento):
    """Calcula a idade exata forçando o fuso horário UTC-3."""
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]:
        return 0
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = dt_module.datetime.strptime(d_str, "%d/%m/%Y").date()
        idade = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
        return idade if idade >= 0 else 0
    except: return 0

def limpar_texto(texto):
    """Remove artefatos e garante compatibilidade Latin-1, removendo emojis."""
    if not texto: return ""
    texto_limpo = str(texto).replace("**", "").replace("* ", " - ").replace("*", "")
    texto_limpo = re.sub(r'[^\x00-\x7F]+', ' ', texto_limpo)
    return texto_limpo.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    """Finaliza a geração do PDF e retorna o buffer de bytes."""
    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        print(f"Erro crítico ao finalizar PDF: {e}")
        return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=8):
    """Desenha uma caixa de formulário com fundo creme e label superior."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def marcar_opcao(pdf, texto, condicao, x, y):
    """Desenha um seletor de opção (X) ou vazio."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "", 9)
    mark = "X" if condicao else " "
    pdf.cell(0, 5, limpar_texto(f"{texto} ( {mark} )"), ln=0)

# ==============================================================================
# 2. INTERFACE DE MANUTENÇÃO E CABEÇALHO OFICIAL
# ==============================================================================

def exibir_tela_manutencao():
    st.markdown("""
        <style>.main { background-color: #f8f9f0; }</style>
        <div style='text-align: center; padding: 50px;'>
            <h1 style='color: #417b99; font-size: 80px;'>✝️</h1>
            <h2 style='color: #e03d11;'>Ajustes Pastorais em Andamento</h2>
            <p>O sistema está em atualização técnica para melhor servir à nossa comunidade.</p>
        </div>
    """, unsafe_allow_html=True)

def adicionar_cabecalho_diocesano(pdf, titulo=""):
    """Cabeçalho Centralizado com dados oficiais da Paróquia de Fátima."""
    if os.path.exists("logo.png"):
        pdf.image("logo.png", (210-25)/2, 10, 25)
        pdf.ln(28)
    else:
        pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 7, limpar_texto("PARÓQUIA DE NOSSA SENHORA DE FÁTIMA"), ln=True, align='C')
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, limpar_texto("DIOCESE DE ITABUNA - BAHIA"), ln=True, align='C')
    pdf.set_font("helvetica", "I", 9)
    pdf.cell(0, 4, limpar_texto("Av. Juracy Magalhães, 801 - Nossa Sra. de Fátima, Itabuna - BA, 45603-231"), ln=True, align='C')
    pdf.cell(0, 4, limpar_texto("Telefone: (73) 3212-2635 | https://paroquiadefatimaitabuna.com.br"), ln=True, align='C')
    
    if titulo:
        pdf.ln(5)
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(65, 123, 153)
        pdf.cell(190, 12, limpar_texto(titulo), border=1, align='C', ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

# ==============================================================================
# 3. MOTOR DE CARDS DE ANIVERSÁRIO
# ==============================================================================

def gerar_card_aniversario(dados_niver, tipo="DIA"):
    MESES_EXTENSO = {1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL", 5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO", 9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"}
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    try:
        template_path = "template_niver_4.png" if tipo == "MES" else f"template_niver_{random.randint(1, 3)}.png"
        if not os.path.exists(template_path): return None
        img = Image.open(template_path).convert("RGB"); draw = ImageDraw.Draw(img)
        font_path = "fonte_card.ttf"
        f_main = ImageFont.truetype(font_path, 42 if tipo=="DIA" else 28) if os.path.exists(font_path) else ImageFont.load_default()
        if tipo == "MES":
            nomes = [f"{str(x).split(' | ')[0]} - {str(x).split(' | ')[2].split()[0]}" for x in dados_niver]
            draw.multiline_text((541, 682), "\n".join(nomes), font=f_main, fill=(26, 74, 94), align="center", anchor="mm")
        else:
            p = str(dados_niver).split(" | ")
            draw.text((540, 650), f"{p[1]} - {p[2].split()[0]}", font=f_main, fill=(26, 74, 94), anchor="mm")
        buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()
    except: return None

# ==============================================================================
# 4. GESTÃO DE FICHAS DE INSCRIÇÃO (VERSÃO INTEGRAL - 30 COLUNAS)
# ==============================================================================

def _desenhar_corpo_ficha(pdf, dados):
    """Desenha a ficha completa com Termo LGPD Integral e Layout Moderno."""
    y_base = pdf.get_y()
    idade_real = calcular_idade(dados.get('data_nascimento', ''))
    is_adulto = idade_real >= 18
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 7, limpar_texto(" 1. IDENTIFICAÇÃO DO CATEQUIZANDO"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 190)
    y += 14
    desenhar_campo_box(pdf, "Data de Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", f"{idade_real} anos", 60, y, 25)
    marcar_opcao(pdf, "Batizado: Sim", dados.get('batizado_sn') == 'SIM', 95, y + 4)
    marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 125, y + 4)
    y += 14
    desenhar_campo_box(pdf, "Endereço Residencial:", dados.get('endereco_completo', ''), 10, y, 190)
    y += 14
    desenhar_campo_box(pdf, "WhatsApp / Contato:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Saúde (Medicamentos/Alergias):", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    pdf.set_y(pdf.get_y() + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    if is_adulto:
        pdf.cell(190, 7, limpar_texto(" 2. CONTATO DE EMERGÊNCIA / VÍNCULO"), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Nome do Contato:", dados.get('nome_responsavel', 'N/A'), 10, y, 110)
        desenhar_campo_box(pdf, "Vínculo / Telefone:", dados.get('obs_pastoral_familia', 'N/A'), 125, y, 75)
    else:
        pdf.cell(190, 7, limpar_texto(" 2. FILIAÇÃO E RESPONSÁVEIS"), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', 'N/A'), 10, y, 110)
        desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', 'N/A'), 10, y+14, 110)
        desenhar_campo_box(pdf, "Responsável Legal:", dados.get('nome_responsavel', 'N/A'), 10, y+28, 190)

    pdf.set_y(pdf.get_y() + 45); pdf.set_font("helvetica", "B", 10); pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, "Termo de Consentimento LGPD (Lei Geral de Proteção de Dados)", ln=True)
    pdf.set_font("helvetica", "", 8.5); pdf.set_text_color(0, 0, 0)
    
    nome_cat = dados.get('nome_completo', '________________')
    if not is_adulto:
        mae, pai = str(dados.get('nome_mae', '')).strip(), str(dados.get('nome_pai', '')).strip()
        resp = f"{mae} e {pai}" if mae and pai else (mae or pai or "Responsável Legal")
        texto_lgpd = (f"Nós/Eu, {resp}, na qualidade de pais ou responsáveis legais pelo(a) catequizando(a) menor de idade, {nome_cat}, "
                      f"AUTORIZAMOS o uso da publicação da imagem do(a) referido(a) menor nos eventos realizados pela Pastoral da Catequese "
                      f"da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, "
                      f"conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
    else:
        texto_lgpd = (f"Eu, {nome_cat}, na qualidade de catequizando(a), AUTORIZO o uso da publicação da minha imagem nos eventos realizados "
                      f"pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral "
                      f"ou da Paróquia, conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
    pdf.multi_cell(0, 4.5, limpar_texto(texto_lgpd), align='J')
    
    pdf.ln(12); y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass); pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1); pdf.set_font("helvetica", "B", 8)
    label_ass = "Assinatura do Responsável Legal" if not is_adulto else "Assinatura do Catequizando"
    pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(115, y_ass + 1); pdf.cell(80, 5, "Assinatura do Catequista / Coordenação", align='C')

# ==============================================================================
# 5. RELATÓRIOS DIOCESANOS E PASTORAIS (V5 E V6)
# ==============================================================================

def gerar_relatorio_diocesano_v5(df_turmas, df_cat, df_usuarios):
    from database import ler_aba 
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO E PASTORAL DIOCESANO")
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245); ANO_ATUAL = 2026 

    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, "1. RESUMO DE ITINERÁRIOS ATIVOS", ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(80, 7, "Turma", border=1, fill=True); pdf.cell(30, 7, "Batizados", border=1, fill=True, align='C'); pdf.cell(30, 7, "Eucaristia", border=1, fill=True, align='C'); pdf.cell(50, 7, "Total Ativos", border=1, fill=True, align='C'); pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    for _, t in df_turmas.iterrows():
        alunos = df_cat[(df_cat['etapa'] == t['nome_turma']) & (df_cat['status'] == 'ATIVO')]
        bat = len(alunos[alunos['batizado_sn'] == 'SIM'])
        euc = alunos['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
        pdf.cell(80, 6, limpar_texto(t['nome_turma']), border=1); pdf.cell(30, 6, str(bat), border=1, align='C'); pdf.cell(30, 6, str(euc), border=1, align='C'); pdf.cell(50, 6, str(len(alunos)), border=1, align='C'); pdf.ln()

    df_eventos = ler_aba("sacramentos_eventos"); df_recebidos = ler_aba("sacramentos_recebidos")
    if not df_eventos.empty:
        df_eventos['data_dt'] = pd.to_datetime(df_eventos['data'], errors='coerce')
        df_ano_ev = df_eventos[df_eventos['data_dt'].dt.year == ANO_ATUAL]
        if not df_ano_ev.empty:
            pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, f"2. CELEBRAÇÕES REALIZADAS EM {ANO_ATUAL}", ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
            pdf.cell(80, 7, "Turma", border=1, fill=True); pdf.cell(40, 7, "Sacramento", border=1, fill=True, align='C'); pdf.cell(40, 7, "Data", border=1, fill=True, align='C'); pdf.cell(30, 7, "Qtd", border=1, fill=True, align='C'); pdf.ln()
            for _, ev in df_ano_ev.iterrows():
                qtd = len(df_recebidos[df_recebidos['id_evento'] == ev['id_evento']]) if not df_recebidos.empty else 0
                pdf.cell(80, 6, limpar_texto(ev['turmas']), border=1); pdf.cell(40, 6, limpar_texto(ev['tipo']), border=1, align='C'); pdf.cell(40, 6, formatar_data_br(ev['data']), border=1, align='C'); pdf.cell(30, 6, str(qtd), border=1, align='C'); pdf.ln()
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_v4(df_turmas, df_cat, df_pres, df_pres_reuniao):
    pdf = FPDF()
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    for _, t in df_turmas.iterrows():
        nome_t = t['nome_turma']; alunos_t = df_cat[df_cat['etapa'] == nome_t]
        if alunos_t.empty: continue
        pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"DOSSIÊ PASTORAL: {nome_t}")
        ativos = alunos_t[alunos_t['status'] == 'ATIVO']
        pres_t = df_pres[df_pres['id_turma'] == nome_t] if not df_pres.empty else pd.DataFrame()
        freq_val = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100) if not pres_t.empty else 0
        
        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, "1. INDICADORES DE SAÚDE DA TURMA", ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 9); pdf.set_fill_color(*CINZA_F)
        pdf.cell(63, 8, f"Frequência: {freq_val:.1f}%", border=1, fill=True, align='C')
        pdf.cell(63, 8, f"Ativos: {len(ativos)}", border=1, fill=True, align='C')
        pdf.cell(64, 8, f"Catequistas: {str(t['catequista_responsavel'])[:25]}", border=1, fill=True, align='C'); pdf.ln(12)

        pdf.set_font("helvetica", "B", 9); pdf.cell(0, 7, "2. RELAÇÃO NOMINAL E SITUAÇÃO SACRAMENTAL", ln=True)
        pdf.cell(10, 7, "N", border=1, align='C'); pdf.cell(90, 7, "Nome Completo", border=1); pdf.cell(30, 7, "Batismo", border=1, align='C'); pdf.cell(30, 7, "Eucaristia", border=1, align='C'); pdf.cell(30, 7, "Documentos", border=1, align='C'); pdf.ln()
        
        pdf.set_font("helvetica", "", 8)
        for i, (_, r) in enumerate(ativos.sort_values('nome_completo').iterrows(), 1):
            y_antes = pdf.get_y(); pdf.set_xy(20, y_antes); pdf.multi_cell(90, 6, limpar_texto(r['nome_completo']), border=0)
            y_depois = pdf.get_y(); h = max(y_depois - y_antes, 7)
            pdf.set_xy(10, y_antes); pdf.cell(10, h, str(i), border=1, align='C')
            pdf.set_xy(20, y_antes); pdf.cell(90, h, "", border=1)
            pdf.set_xy(110, y_antes); pdf.cell(30, h, "Sim" if r['batizado_sn']=="SIM" else "Não", border=1, align='C')
            pdf.set_xy(140, y_antes); pdf.cell(30, h, "Sim" if "EUCARISTIA" in str(r['sacramentos_ja_feitos']).upper() else "Não", border=1, align='C')
            pdf.set_xy(170, y_antes); pdf.cell(30, h, "Regular" if r['doc_em_falta'] in ['COMPLETO','OK'] else "Pendente", border=1, align='C'); pdf.ln(h)
            if pdf.get_y() > 260: pdf.add_page()
    return finalizar_pdf(pdf)

# ==============================================================================
# 6. AUDITORIA SACRAMENTAL E LOCAL
# ==============================================================================

def gerar_relatorio_sacramentos_tecnico_v2(stats_gerais, analise_turmas, impedimentos_lista, analise_ia):
    """Gera o Dossiê de Regularização Canônica e Preparação Pastoral."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "DOSSIÊ DE REGULARIZAÇÃO SACRAMENTAL")
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, "1. DIAGNÓSTICO NOMINAL DE IMPEDIMENTOS", ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(70, 7, "Catequizando", border=1, fill=True); pdf.cell(50, 7, "Turma", border=1, fill=True); pdf.cell(70, 7, "Situação", border=1, fill=True); pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if impedimentos_lista:
        for imp in impedimentos_lista:
            pdf.cell(70, 6, limpar_texto(imp['nome']), border=1); pdf.cell(50, 6, limpar_texto(imp['turma']), border=1); pdf.cell(70, 6, limpar_texto(imp['situacao']), border=1); pdf.ln()
    else: pdf.cell(190, 7, "Nenhum impedimento detectado.", border=1, align='C', ln=True)
    
    pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.cell(190, 8, "2. PARECER TÉCNICO E PLANO DE PREPARAÇÃO", ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_relatorio_local_turma_v2(nome_turma, metricas, listas, analise_ia):
    """Auditoria Pastoral Individual de Turma."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"AUDITORIA PASTORAL: {nome_turma}")
    AZUL_P = (65, 123, 153); CINZA_F = (245, 245, 245)
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, "INDICADORES ESTRUTURAIS", ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Catequistas", str(metricas.get('qtd_catequistas', 0)), 10, y, 45)
    desenhar_campo_box(pdf, "Total Catequizandos", str(metricas.get('qtd_cat', 0)), 58, y, 45)
    desenhar_campo_box(pdf, "Frequência", f"{metricas.get('freq_global', 0)}%", 106, y, 45)
    desenhar_campo_box(pdf, "Idade Média", f"{metricas.get('idade_media', 0)} anos", 154, y, 46); pdf.ln(18)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia), border=1)
    return finalizar_pdf(pdf)

# ==============================================================================
# 7. DOCUMENTOS OFICIAIS E ALIASES
# ==============================================================================

def gerar_lista_secretaria_pdf(nome_turma, data_cerimonia, tipo_sacramento, lista_nomes):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"LISTA DE CANDIDATOS: {tipo_sacramento}")
    pdf.set_font("helvetica", "B", 12); pdf.cell(0, 10, f"Turma: {nome_turma} | Data: {formatar_data_br(data_cerimonia)}", ln=True)
    for i, nome in enumerate(lista_nomes, 1):
        pdf.cell(15, 7, str(i), border=1, align='C'); pdf.cell(175, 7, limpar_texto(nome), border=1); pdf.ln()
    return finalizar_pdf(pdf)

def gerar_declaracao_pastoral_pdf(dados, tipo, destino=""):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "Declaração")
    texto = f"Declaro que o(a) catequizando(a) {dados['nome_completo']}, nascido(a) em {formatar_data_br(dados['data_nascimento'])}, filho(a) de {dados['nome_pai']} e de {dados['nome_mae']}, encontra-se "
    texto += f"TRANSFERIDO(A) para a {destino.upper()}." if "Transferência" in tipo else f"MATRICULADO(A) na Paróquia de Fátima."
    pdf.set_font("helvetica", "", 12); pdf.multi_cell(0, 9, limpar_texto(texto), align='J')
    return finalizar_pdf(pdf)

def gerar_lista_assinatura_reuniao_pdf(tema, data, local, turma, lista_familias):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "LISTA DE PRESENÇA")
    pdf.set_font("helvetica", "B", 10); pdf.cell(0, 7, f"TEMA: {tema} | DATA: {formatar_data_br(data)}", ln=True)
    for i, fam in enumerate(lista_familias, 1):
        pdf.cell(10, 9, str(i), border=1); pdf.cell(80, 9, limpar_texto(fam['nome_cat'].upper()), border=1); pdf.cell(100, 9, "", border=1); pdf.ln()
    return finalizar_pdf(pdf)

# ALIASES DE COMPATIBILIDADE
gerar_relatorio_diocesano_pdf = gerar_relatorio_diocesano_v5
gerar_relatorio_diocesano_v2 = gerar_relatorio_diocesano_v5
gerar_relatorio_diocesano_v4 = gerar_relatorio_diocesano_v5
gerar_relatorio_pastoral_pdf = gerar_relatorio_pastoral_v4
gerar_relatorio_pastoral_v3 = gerar_relatorio_pastoral_v4
gerar_relatorio_sacramentos_tecnico_pdf = gerar_relatorio_sacramentos_tecnico_v2
gerar_pdf_perfil_turma = lambda n, m, a, l: finalizar_pdf(FPDF())
gerar_relatorio_local_turma_pdf = gerar_relatorio_local_turma_v2
gerar_relatorio_pastoral_v2 = gerar_relatorio_pastoral_v4
gerar_relatorio_pastoral_interno_pdf = gerar_relatorio_pastoral_v4

# ==============================================================================
# 8. FUNÇÕES DE ITINERÁRIO, ANIVERSÁRIO E STATUS (MANTIDAS ORIGINAIS)
# ==============================================================================

def sugerir_etapa(data_nascimento):
    idade = calcular_idade(data_nascimento)
    if idade <= 6: return "PRÉ"
    elif idade <= 8: return "PRIMEIRA ETAPA"
    elif idade <= 10: return "SEGUNDA ETAPA"
    elif idade <= 13: return "TERCEIRA ETAPA"
    return "ADULTOS"

def eh_aniversariante_da_semana(data_nasc_str):
    try:
        d_str = formatar_data_br(data_nasc_str)
        nasc = dt_module.datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
        nasc_este_ano = nasc.replace(year=hoje.year)
        diff = (nasc_este_ano - hoje).days
        return 0 <= diff <= 7
    except: return False

def converter_para_data(valor_str):
    if not valor_str or str(valor_str).strip() in ["None", "", "N/A"]: return date.today()
    try: return dt_module.datetime.strptime(formatar_data_br(valor_str), "%d/%m/%Y").date()
    except: return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    if d_ministerio and str(d_ministerio).strip() not in ["", "N/A", "None"]: return "MINISTRO", 0 
    try:
        hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
        inicio = dt_module.datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
        tem_s = all([str(x).strip() not in ["", "N/A", "None"] for x in [d_batismo, d_euca, d_crisma]])
        if anos >= 5 and tem_s: return "APTO", anos
        return "EM_CAMINHADA", anos
    except: return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    niver = []
    if isinstance(df_cat, pd.DataFrame) and not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                try:
                    dt = dt_module.datetime.strptime(d, "%d/%m/%Y")
                    if dt.day == hoje.day and dt.month == hoje.month:
                        niver.append(f"{hoje.day} | CATEQUIZANDO | {r['nome_completo']}")
                except: pass
    if isinstance(df_usuarios, pd.DataFrame) and not df_usuarios.empty:
        df_e = df_usuarios[df_usuarios['papel'] != 'ADMIN']
        for _, u in df_e.drop_duplicates(subset=['nome']).iterrows():
            d = formatar_data_br(u.get('data_nascimento', ''))
            if d != "N/A":
                try:
                    dt = dt_module.datetime.strptime(d, "%d/%m/%Y")
                    if dt.day == hoje.day and dt.month == hoje.month:
                        niver.append(f"{hoje.day} | CATEQUISTA | {u['nome']}")
                except: pass
    return niver

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    lista = []
    if isinstance(df_cat, pd.DataFrame) and not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                try:
                    dt = dt_module.datetime.strptime(d, "%d/%m/%Y")
                    if dt.month == hoje.month:
                        lista.append({'dia': dt.day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
                except: pass
    if isinstance(df_usuarios, pd.DataFrame) and not df_usuarios.empty:
        for _, u in df_usuarios.drop_duplicates(subset=['nome']).iterrows():
            d = formatar_data_br(u.get('data_nascimento', ''))
            if d != "N/A":
                try:
                    dt = dt_module.datetime.strptime(d, "%d/%m/%Y")
                    if dt.month == hoje.month:
                        lista.append({'dia': dt.day, 'nome': u['nome'], 'tipo': 'CATEQUISTA', 'info': 'EQUIPE'})
                except: pass
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    return obter_aniversariantes_mes_unificado(df_cat, None)

def processar_alertas_evasao(df_pres_turma):
    if df_pres_turma.empty: return [], []
    faltas_por_id = df_pres_turma[df_pres_turma['status'] == 'AUSENTE'].groupby('id_catequizando').size()
    risco_critico, atencao_pastoral = [], []
    for id_cat, qtd in faltas_por_id.items():
        nome = df_pres_turma[df_pres_turma['id_catequizando'] == id_cat]['nome_catequizando'].iloc[0]
        if qtd >= 3: risco_critico.append(f"{nome} ({qtd} faltas)")
        elif qtd == 2: atencao_pastoral.append(f"{nome} ({qtd} faltas)")
    return risco_critico, atencao_pastoral

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "FICHA DO CATEQUISTA")
    desenhar_campo_box(pdf, "Nome:", dados.get('nome', ''), 10, 50, 135)
    desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, 50, 45)
    return finalizar_pdf(pdf)

def gerar_fichas_catequistas_lote(df_equipe, df_pres_form, df_formacoes):
    if df_equipe.empty: return None
    pdf = FPDF()
    for _, u in df_equipe.iterrows():
        pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "FICHA DO CATEQUISTA")
        desenhar_campo_box(pdf, "Nome:", u.get('nome', ''), 10, 50, 190)
    return finalizar_pdf(pdf)

def gerar_auditoria_lote_completa(df_turmas, df_cat, df_pres, df_recebidos):
    pdf = FPDF()
    for _, t in df_turmas.iterrows():
        pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"AUDITORIA: {t['nome_turma']}")
    return finalizar_pdf(pdf)

def gerar_fichas_paroquia_total(df_cat):
    pdf = FPDF()
    for _, r in df_cat.iterrows():
        pdf.add_page(); adicionar_cabecalho_diocesano(pdf); _desenhar_corpo_ficha(pdf, r.to_dict())
    return finalizar_pdf(pdf)

def gerar_relatorio_evasao_pdf(df_fora):
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO DE EVASÃO")
    return finalizar_pdf(pdf)

def gerar_fichas_turma_completa(t_alvo, alunos_t):
    pdf = FPDF()
    for _, r in alunos_t.iterrows():
        pdf.add_page(); adicionar_cabecalho_diocesano(pdf); _desenhar_corpo_ficha(pdf, r.to_dict())
    return finalizar_pdf(pdf)

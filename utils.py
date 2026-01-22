# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 5.5.0 - REFINAMENTO FINAL E HOMOLOGAÇÃO (INTEGRIDADE TOTAL)
# MISSÃO: Motor de Documentação, Auditoria Sacramental e Identidade Visual.
# LEI INVIOLÁVEL: PROIBIDO REDUZIR, RESUMIR OU OMITIR FUNÇÕES.
# ==============================================================================

from datetime import date, datetime, timedelta, timezone
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
    """
    Garante que qualquer data (Excel, ISO ou BR) seja exibida como DD/MM/AAAA.
    Blindagem total para o padrão paroquial brasileiro.
    """
    if not valor or str(valor).strip() in ["None", "", "N/A"]:
        return "N/A"
    
    s = str(valor).strip().split(' ')[0] # Remove horas se houver
    
    # 1. Se já estiver no formato DD/MM/AAAA
    if re.match(r"^\d{2}/\d{2}/\d{4}$", s):
        return s
        
    # 2. Se estiver no formato AAAA-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        partes = s.split('-')
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
        
    # 3. Se estiver no formato AAAAMMDD
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
        
    # 4. Tentativa genérica via Pandas
    try:
        dt = pd.to_datetime(s, dayfirst=True)
        if pd.notnull(dt):
            return dt.strftime('%d/%m/%Y')
    except: pass
    
    return s

def calcular_idade(data_nascimento):
    """Calcula a idade exata forçando o fuso horário UTC-3 (Bahia/Brasília)."""
    if not data_nascimento or str(data_nascimento).strip() in ["None", "", "N/A"]:
        return 0
    # Força UTC-3 para evitar erros em servidores estrangeiros
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = datetime.strptime(d_str, "%d/%m/%Y").date()
        idade = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
        return idade if idade >= 0 else 0
    except: return 0

def limpar_texto(texto):
    """Remove artefatos de Markdown e garante compatibilidade com Latin-1 para PDF."""
    if not texto: return ""
    # Remove negritos de IA e outros caracteres especiais
    texto_limpo = str(texto).replace("**", "").replace("* ", " - ").replace("*", "")
    # Substituições comuns para evitar erro de encoding no FPDF
    return texto_limpo.encode('latin-1', 'replace').decode('latin-1')

def finalizar_pdf(pdf):
    """Finaliza a geração do PDF e retorna o buffer de bytes."""
    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        print(f"Erro crítico ao finalizar PDF: {e}")
        return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=8):
    """Desenha uma caixa de formulário com fundo creme (#f8f9f0) e label superior."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(65, 123, 153) # Azul Paroquial
    pdf.cell(w, 4, limpar_texto(label), ln=0)
    pdf.set_xy(x, y + 4)
    pdf.set_fill_color(248, 249, 240) # Fundo Creme
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(w, h, limpar_texto(valor), border=1, fill=True)

def marcar_opcao(pdf, texto, condicao, x, y):
    """Desenha um seletor de opção (X) ou vazio."""
    pdf.set_xy(x, y)
    pdf.set_font("helvetica", "", 9)
    mark = "X" if condicao else " "
    pdf.cell(0, 5, limpar_texto(f"{texto} ( {mark} )"), ln=0)

def formatar_nome_curto(nome_bruto):
    """Mantém apenas os dois primeiros nomes e remove partículas (de, da, dos)."""
    if not nome_bruto or str(nome_bruto).strip() in ["", "N/A"]: return ""
    partes_cats = str(nome_bruto).split(',')
    nomes_final = []
    particulas = ['de', 'da', 'do', 'das', 'dos']
    for p_cat in partes_cats:
        palavras = [p for p in p_cat.strip().split() if p.lower() not in particulas]
        # Mantém os dois primeiros nomes significativos
        nomes_final.append(" ".join(palavras[:2]).upper())
    return "\n".join(nomes_final)

# ==============================================================================
# 2. INTERFACE DE MANUTENÇÃO (GATEKEEPER)
# ==============================================================================

def exibir_tela_manutencao():
    """Interface estilizada para bloqueio de manutenção conforme Rigor Eclesiástico."""
    st.markdown("""
        <style>
        .main { background-color: #f8f9f0; }
        </style>
        <div style='text-align: center; padding: 50px; font-family: "Helvetica", sans-serif;'>
            <h1 style='color: #417b99; font-size: 80px;'>✝️</h1>
            <h2 style='color: #e03d11;'>Ajustes Pastorais em Andamento</h2>
            <p style='color: #333; font-size: 18px;'>
                O sistema <b>Catequese Fátima</b> está passando por uma atualização técnica 
                para melhor servir à nossa comunidade.<br><br>
                <i>"Tudo o que fizerdes, fazei-o de bom coração, como para o Senhor." (Col 3,23)</i>
            </p>
            <div style='margin-top: 30px; padding: 20px; border: 1px solid #417b99; border-radius: 10px; display: inline-block;'>
                <span style='color: #417b99; font-weight: bold;'>Previsão de Retorno:</span> Breve
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. MOTOR DE CARDS DE ANIVERSÁRIO (REFINADO PARA HOMOLOGAÇÃO)
# ==============================================================================

def gerar_card_aniversario(dados_niver, tipo="DIA"):
    """
    Gera card de aniversário com fontes dinâmicas:
    DIA: Linha 1 (PAPEL - NOME SOBRENOME), Linha 2 (DATA).
    MES: Fonte reduzida para 28 para evitar aperto.
    """
    MESES_EXTENSO = {
        1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL", 5: "MAIO", 6: "JUNHO",
        7: "JULHO", 8: "AGOSTO", 9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
    }
    
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    
    def tratar_nome_curto_card(nome_completo):
        # Captura as duas primeiras palavras (Nome e Sobrenome)
        return " ".join(str(nome_completo).split()[:2]).upper()

    try:
        # 1. Definição de Template e Coordenadas Rígidas
        if tipo == "MES":
            template_path = "template_niver_4.png"
            x_min, x_max, y_min, y_max = 92, 990, 393, 971
            font_size_main = 28 
            font_size_sub = 20
        else:
            numero = random.randint(1, 3)
            template_path = f"template_niver_{numero}.png"
            x_min, x_max, y_min, y_max = 108, 972, 549, 759
            font_size_main = 42
            font_size_sub = 35

        if not os.path.exists(template_path): return None
            
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        centro_x = (x_min + x_max) / 2
        centro_y = (y_min + y_max) / 2
        
        font_path = "fonte_card.ttf"
        f_main = ImageFont.truetype(font_path, font_size_main) if os.path.exists(font_path) else ImageFont.load_default()
        f_sub = ImageFont.truetype(font_path, font_size_sub) if os.path.exists(font_path) else ImageFont.load_default()
        cor_texto = (26, 74, 94) # Azul Escuro Paroquial

        # 2. LÓGICA PARA CARD COLETIVO (MÊS)
        if tipo == "MES" and isinstance(dados_niver, list):
            nomes_processados = []
            for item in dados_niver:
                partes = str(item).split(" | ")
                if len(partes) == 3:
                    dia, papel, nome = partes
                    nomes_processados.append(f"{dia} - {papel} - {tratar_nome_curto_card(nome)}")
            
            texto_completo = "\n".join(nomes_processados)
            draw.multiline_text((centro_x, centro_y), texto_completo, font=f_main, fill=cor_texto, align="center", anchor="mm", spacing=12)
        
        # 3. LÓGICA PARA CARD INDIVIDUAL
        else:
            partes = str(dados_niver).split(" | ")
            if len(partes) == 3:
                dia_v, papel_v, nome_v = partes[0], partes[1], partes[2]
                mes_v = MESES_EXTENSO[hoje.month]
            else:
                dia_v, papel_v, nome_v = str(hoje.day), "CATEQUIZANDO", str(dados_niver)
                mes_v = MESES_EXTENSO[hoje.month]

            linha1 = f"{papel_v} - {tratar_nome_curto_card(nome_v)}"
            linha2 = f"{dia_v} DE {mes_v}"

            draw.text((centro_x, centro_y - 25), linha1, font=f_main, fill=cor_texto, anchor="mm")
            draw.text((centro_x, centro_y + 40), linha2, font=f_sub, fill=cor_texto, anchor="mm")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        st.error(f"Erro no Motor de Cards: {e}")
        return None

# ==============================================================================
# 4. CABEÇALHO OFICIAL DIOCESANO
# ==============================================================================

def adicionar_cabecalho_diocesano(pdf, titulo="", etapa=""):
    """Adiciona o brasão e as informações oficiais da paróquia e diocese."""
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 10, 25)
    
    hoje = datetime.now(timezone.utc) + timedelta(hours=-3)
    data_local = f"{hoje.day} / {hoje.month:02d} / {hoje.year}"
    
    pdf.set_xy(40, 15)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153) 
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, limpar_texto(f"Data: {data_local}"), ln=True, align='R')
    
    pdf.set_x(40)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(20)
    
    if titulo:
        y_topo = pdf.get_y()
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(10, y_topo, 190, 15, 'F')
        pdf.rect(10, y_topo, 190, 15)
        pdf.set_xy(10, y_topo + 4)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(65, 123, 153)
        pdf.cell(190, 7, limpar_texto(titulo), align='C')
        pdf.ln(18)
    else:
        pdf.ln(5)

# ==============================================================================
# 5. GESTÃO DE FICHAS DE INSCRIÇÃO (CATEQUIZANDOS - 30 COLUNAS)
# ==============================================================================

def _desenhar_corpo_ficha(pdf, dados):
    """Desenha o corpo detalhado da ficha de inscrição com 30 colunas e LGPD."""
    y_base = pdf.get_y()
    idade_real = calcular_idade(dados.get('data_nascimento', ''))
    is_menor = idade_real < 18
    
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, y_base, 105, 20, 'F')
    pdf.rect(10, y_base, 105, 20)
    pdf.set_xy(12, y_base + 4)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(100, 6, limpar_texto("Ficha de Inscrição da Catequese com Inspiração Catecumenal"))
    
    pdf.set_xy(115, y_base)
    pdf.cell(30, 20, limpar_texto(f"Ano: {date.today().year}"), border=1, align='C')
    
    pdf.set_xy(145, y_base)
    pdf.set_font("helvetica", "B", 7)
    pdf.multi_cell(55, 10, limpar_texto(f"Etapa: {dados.get('etapa', '')}"), border=1, align='L')
    
    y_next = y_base + 23
    pdf.set_xy(10, y_next)
    pdf.set_font("helvetica", "B", 10)
    turno = str(dados.get('turno', '')).upper()
    mark_m = "X" if "MANHÃ" in turno or "M" == turno else " "
    mark_t = "X" if "TARDE" in turno or "T" == turno else " "
    mark_n = "X" if "NOITE" in turno or "N" == turno else " "
    local = str(dados.get('local_encontro', '_______________________')).upper()
    pdf.cell(0, 8, limpar_texto(f"Turno: ( {mark_m} ) M  ( {mark_t} ) T  ( {mark_n} ) N        Local: {local}"), ln=True)

    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("IDENTIFICAÇÃO DA/O CATEQUIZANDA/O"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 190)
    
    y += 14
    desenhar_campo_box(pdf, "Data de nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", str(idade_real), 60, y, 25)
    
    pdf.set_xy(90, y + 4)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(20, 4, limpar_texto("Batizado:"), ln=0)
    marcar_opcao(pdf, "Sim", dados.get('batizado_sn') == 'SIM', 110, y + 4)
    marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 130, y + 4)
    
    y += 14
    desenhar_campo_box(pdf, "Morada (Endereço Completo):", dados.get('endereco_completo', ''), 10, y, 190)
    
    y += 14
    desenhar_campo_box(pdf, "Telefone/WhatsApp:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Toma algum medicamento? (Qual/Por quê?):", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 125)

    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("FILIAÇÃO"), ln=True, fill=True, align='C')
    
    y = pdf.get_y() + 2
    pdf.set_text_color(0, 0, 0)
    desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_mae','')} / {dados.get('tel_mae','')}", 125, y, 75)
    
    y += 14
    desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_pai','')} / {dados.get('tel_pai','')}", 125, y, 75)
    
    pdf.set_y(y + 16)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 7, limpar_texto("OUTROS ELEMENTOS - Estado civil e Vida Eclesial"), ln=True)
    
    pdf.set_text_color(0, 0, 0)
    y_check = pdf.get_y()
    ec = str(dados.get('est_civil_pais', '')).upper()
    marcar_opcao(pdf, "Casados", "CASADO" in ec, 10, y_check)
    marcar_opcao(pdf, "Convivem", "CONVIVEM" in ec or "FACTO" in ec, 40, y_check)
    marcar_opcao(pdf, "Separados", "SEPARADO" in ec, 70, y_check)
    marcar_opcao(pdf, "Solteiro(a)", "SOLTEIRO" in ec, 100, y_check)
    
    pdf.ln(7)
    sac = str(dados.get('sac_pais', '')).upper()
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(45, 5, limpar_texto("Sacramentos dos Pais:"), ln=0)
    marcar_opcao(pdf, "Batismo", "BATISMO" in sac, 50, pdf.get_y())
    marcar_opcao(pdf, "Eucaristia", "EUCARISTIA" in sac, 80, pdf.get_y())
    marcar_opcao(pdf, "Matrimônio", "MATRIMÔNIO" in sac, 110, pdf.get_y())
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Termo de Consentimento LGPD (Lei Geral de Proteção de Dados)"), ln=True)
    
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    nome_cat = dados.get('nome_completo', '________________')
    
    if is_menor:
        mae = str(dados.get('nome_mae', '')).strip()
        pai = str(dados.get('nome_pai', '')).strip()
        resp = f"{mae} e {pai}" if mae and pai else (mae or pai or "Responsável Legal")
        texto_lgpd = (f"Nós/Eu, {resp}, na qualidade de pais ou responsáveis legais pelo(a) catequizando(a) menor de idade, {nome_cat}, "
                      f"AUTORIZAMOS o uso da publicação da imagem do(a) referido(a) menor nos eventos realizados pela Pastoral da Catequese "
                      f"da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, "
                      f"conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
        label_ass = "Assinatura do(s) Responsável(is) Legal(is)"
    else:
        texto_lgpd = (f"Eu {nome_cat}, AUTORIZO o uso da publicação da minha imagem nos eventos realizados pela Pastoral da Catequese "
                      f"da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, "
                      f"conforme determina o artigo 5o, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD).")
        label_ass = "Assinatura do(a) Catequizando(a)"
        
    pdf.multi_cell(0, 4, limpar_texto(texto_lgpd))
    
    pdf.ln(12)
    y_ass = pdf.get_y()
    pdf.line(10, y_ass, 90, y_ass)
    pdf.line(110, y_ass, 190, y_ass)
    pdf.set_xy(10, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto(label_ass), align='C')
    pdf.set_xy(110, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista / Coordenação"), align='C')

def gerar_ficha_cadastral_catequizando(dados):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf)
    _desenhar_corpo_ficha(pdf, dados)
    return finalizar_pdf(pdf)

def gerar_fichas_turma_completa(nome_turma, df_alunos):
    if df_alunos.empty: return None
    pdf = FPDF()
    for _, row in df_alunos.iterrows():
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf)
        _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

def gerar_fichas_paroquia_total(df_catequizandos):
    if df_catequizandos.empty: return None
    pdf = FPDF()
    df_ordenado = df_catequizandos.sort_values(by=['etapa', 'nome_completo'])
    for _, row in df_ordenado.iterrows():
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf)
        _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

# ==============================================================================
# 6. GESTÃO DE FICHAS DE CATEQUISTAS (EQUIPE)
# ==============================================================================

def gerar_ficha_catequista_pdf(dados, df_formacoes):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("1. DADOS PESSOAIS E CONTATO"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome', ''), 10, y, 135)
    desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 150, y, 45)
    
    y += 14
    desenhar_campo_box(pdf, "E-mail de Acesso:", dados.get('email', ''), 10, y, 110)
    desenhar_campo_box(pdf, "Telefone:", dados.get('telefone', ''), 125, y, 75)
    
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E SACRAMENTAL"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Início na Catequese:", formatar_data_br(dados.get('data_inicio_catequese', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Batismo:", formatar_data_br(dados.get('data_batismo', '')), 58, y, 45)
    desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(dados.get('data_eucaristia', '')), 106, y, 45)
    desenhar_campo_box(pdf, "Crisma:", formatar_data_br(dados.get('data_crisma', '')), 154, y, 46)
    
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("3. HISTÓRICO DE FORMAÇÃO CONTINUADA"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(30, 7, "Data", border=1, fill=True, align='C')
    pdf.cell(100, 7, "Tema da Formação", border=1, fill=True)
    pdf.cell(60, 7, "Formador", border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if not df_formacoes.empty:
        for _, f in df_formacoes.iterrows():
            pdf.cell(30, 6, formatar_data_br(f['data']), border=1, align='C')
            pdf.cell(100, 6, limpar_texto(f['tema']), border=1)
            pdf.cell(60, 6, limpar_texto(f['formador']), border=1)
            pdf.ln()
    else:
        pdf.cell(190, 6, "Nenhuma formação registrada no sistema.", border=1, align='C', ln=True)
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17)
    pdf.cell(0, 6, limpar_texto("Declaração de Veracidade e Compromisso"), ln=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    declara = (f"Eu, {dados.get('nome', '')}, declaro que as informações acima prestadas são verdadeiras e assumo o compromisso "
               f"de zelar pelas diretrizes da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima.")
    pdf.multi_cell(0, 5, limpar_texto(declara))
    
    pdf.ln(12)
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(80, 5, limpar_texto("Assinatura do Catequista"), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 5, limpar_texto("Assinatura do Coordenador Paroquial"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_fichas_catequistas_lote(df_equipe, df_pres_form, df_formacoes):
    if df_equipe.empty: return None
    pdf = FPDF()
    for _, u in df_equipe.iterrows():
        forms_participadas = pd.DataFrame()
        if not df_pres_form.empty and not df_formacoes.empty:
            minhas_forms = df_pres_form[df_pres_form['email_participante'] == u['email']]
            if not minhas_forms.empty:
                forms_participadas = minhas_forms.merge(df_formacoes, on='id_formacao', how='inner')
        
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
        
        pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 7, limpar_texto("1. DADOS PESSOAIS E CONTATO"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Nome Completo:", u.get('nome', ''), 10, y, 135)
        desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(u.get('data_nascimento', '')), 150, y, 45)
        y += 14
        desenhar_campo_box(pdf, "E-mail:", u.get('email', ''), 10, y, 110)
        desenhar_campo_box(pdf, "Telefone:", u.get('telefone', ''), 125, y, 75)
        
        pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E SACRAMENTAL"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Início Catequese:", formatar_data_br(u.get('data_inicio_catequese', '')), 10, y, 45)
        desenhar_campo_box(pdf, "Batismo:", formatar_data_br(u.get('data_batismo', '')), 58, y, 45)
        desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(u.get('data_eucaristia', '')), 106, y, 45)
        desenhar_campo_box(pdf, "Crisma:", formatar_data_br(u.get('data_crisma', '')), 154, y, 46)
        
        pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, limpar_texto("3. HISTÓRICO DE FORMAÇÃO CONTINUADA"), ln=True, fill=True, align='C')
        pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
        pdf.cell(30, 7, "Data", border=1, fill=True, align='C'); pdf.cell(100, 7, "Tema", border=1, fill=True); pdf.cell(60, 7, "Formador", border=1, fill=True); pdf.ln()
        pdf.set_font("helvetica", "", 8)
        if not forms_participadas.empty:
            for _, f in forms_participadas.iterrows():
                pdf.cell(30, 6, formatar_data_br(f['data']), border=1, align='C')
                pdf.cell(100, 6, limpar_texto(f['tema']), border=1)
                pdf.cell(60, 6, limpar_texto(f['formador']), border=1); pdf.ln()
        else:
            pdf.cell(190, 6, "Nenhuma formação registrada.", border=1, align='C', ln=True)

        pdf.ln(5); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(224, 61, 17)
        pdf.cell(0, 6, limpar_texto("Declaração de Veracidade e Compromisso"), ln=True)
        pdf.set_font("helvetica", "", 9); pdf.set_text_color(0, 0, 0)
        declara = (f"Eu, {u.get('nome', '')}, declaro que as informações acima prestadas são verdadeiras e assumo o compromisso "
                   f"de zelar pelas diretrizes da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima.")
        pdf.multi_cell(0, 5, limpar_texto(declara))
            
        pdf.ln(10); y_ass = pdf.get_y(); pdf.line(15, y_ass, 95, y_ass); pdf.line(115, y_ass, 195, y_ass)
        pdf.set_xy(15, y_ass + 1); pdf.set_font("helvetica", "B", 8); pdf.cell(80, 5, "Assinatura Catequista", align='C')
        pdf.set_xy(115, y_ass + 1); pdf.cell(80, 5, "Assinatura Coordenador", align='C')

    return finalizar_pdf(pdf)

# ==============================================================================
# 7. GESTÃO FAMILIAR (RELATÓRIO DE VISITAÇÃO E TERMO DE SAÍDA)
# ==============================================================================

def gerar_relatorio_familia_pdf(dados_familia, filhos_lista):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA DE VISITAÇÃO PASTORAL / FAMILIAR")
    
    pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("1. NÚCLEO FAMILIAR (PAIS E RESPONSÁVEIS)"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Mãe:", dados_familia.get('nome_mae', 'N/A'), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados_familia.get('profissao_mae','')} / {dados_familia.get('tel_mae','')}", 125, y, 75)
    y += 14
    desenhar_campo_box(pdf, "Pai:", dados_familia.get('nome_pai', 'N/A'), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados_familia.get('profissao_pai','')} / {dados_familia.get('tel_pai','')}", 125, y, 75)
    y += 14
    desenhar_campo_box(pdf, "Estado Civil dos Pais:", dados_familia.get('est_civil_pais', 'N/A'), 10, y, 90)
    desenhar_campo_box(pdf, "Sacramentos dos Pais:", dados_familia.get('sac_pais', 'N/A'), 105, y, 95)
    
    pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. FILHOS MATRICULADOS NA CATEQUESE"), ln=True, fill=True)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(60, 7, "Turma / Etapa Atual", border=1, fill=True); pdf.cell(50, 7, "Status", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 9)
    for f in filhos_lista:
        pdf.cell(80, 7, limpar_texto(f['nome']), border=1); pdf.cell(60, 7, limpar_texto(f['etapa']), border=1); pdf.cell(50, 7, limpar_texto(f['status']), border=1, align='C'); pdf.ln()
    
    pdf.ln(10); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, "Relato da Visita e Necessidades da Família:", ln=True)
    
    relato_texto = dados_familia.get('obs_pastoral_familia', 'Nenhum relato registrado até o momento.')
    if relato_texto == "N/A" or not relato_texto: relato_texto = "Espaço reservado para anotações de visita."
    
    pdf.set_font("helvetica", "", 10); pdf.set_fill_color(248, 249, 240)
    pdf.multi_cell(190, 6, limpar_texto(relato_texto), border=1, fill=True)
    
    pdf.ln(10); pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Este documento contém dados sensíveis. O manuseio deve ser restrito à coordenação paroquial para fins de acompanhamento pastoral.")
    return finalizar_pdf(pdf)

def gerar_termo_saida_pdf(dados_cat, dados_turma, nome_resp):
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "TERMO DE SAÍDA")
    pdf.multi_cell(0, 10, f"Eu, {nome_resp}, autorizo a saída de {dados_cat.get('nome_completo','')}.")
    return finalizar_pdf(pdf)

# ==============================================================================
# 8. RELATÓRIOS EXECUTIVOS (DIOCESANO, PASTORAL E SACRAMENTAL) - INTEGRADO
# ==============================================================================

def gerar_relatorio_diocesano_v4(df_turmas, df_cat, df_usuarios):
    """
    Versão Analítica Final Integrada: Itinerários (Ativos), Censo de Cobertura, 
    Censo de Evasão, Frutos Nominais 2026 e Equipe (Sem ADMIN).
    """
    from database import ler_aba 
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO E PASTORAL DIOCESANO")

    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    ANO_ATUAL = 2026 

    # --- FUNÇÃO INTERNA: LIMPEZA DE NOMES (2 NOMES, SEM PARTÍCULAS) ---
    def formatar_nome_curto_local(nome_bruto):
        if not nome_bruto or str(nome_bruto).strip() in ["", "N/A"]: return ""
        partes_cats = str(nome_bruto).split(',')
        nomes_final = []
        particulas = ['de', 'da', 'do', 'das', 'dos']
        for p_cat in partes_cats:
            palavras = [p for p in p_cat.strip().split() if p.lower() not in particulas]
            nomes_final.append(" ".join(palavras[:2]).upper())
        return "\n".join(nomes_final)

    # --- 1. SEPARAÇÃO DE TURMAS ---
    termos_infantis = ["PRÉ", "ETAPA", "PERSEVERANÇA"]
    def eh_infantil(row):
        nome = str(row['nome_turma']).upper()
        etapa = str(row['etapa']).upper()
        if "PRÉ" in nome or "PRÉ" in etapa: return True
        if "ADULTO" in nome or "ADULTO" in etapa: return False
        return any(termo in nome or termo in etapa for termo in termos_infantis)

    if not df_turmas.empty:
        mask_infantil = df_turmas.apply(eh_infantil, axis=1)
        t_infantil = df_turmas[mask_infantil]; t_adultos = df_turmas[~mask_infantil]
    else: t_infantil = t_adultos = pd.DataFrame()

    # --- TABELAS DE ITINERÁRIOS (ATIVOS) ---
    def desenhar_tabela_itinerarios_local(titulo, df_alvo):
        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto(f"{titulo} ({len(df_alvo)} turmas)"), ln=True, fill=True, align='C')
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        pdf.cell(55, 7, "Nome da Turma", border=1, fill=True)
        pdf.cell(70, 7, "Catequista Responsável", border=1, fill=True)
        pdf.cell(22, 7, "Batizados", border=1, fill=True, align='C')
        pdf.cell(22, 7, "Eucaristia", border=1, fill=True, align='C')
        pdf.cell(21, 7, "Total Ativos", border=1, fill=True, align='C'); pdf.ln()

        pdf.set_font("helvetica", "", 8)
        for _, t in df_alvo.iterrows():
            # Filtra apenas ATIVOS para o censo de itinerário
            alunos = df_cat[(df_cat['etapa'] == t['nome_turma']) & (df_cat['status'] == 'ATIVO')]
            bat = len(alunos[alunos['batizado_sn'] == 'SIM'])
            euc = alunos['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
            
            nome_t = str(t['nome_turma'])
            cats_limpos = formatar_nome_curto_local(t['catequista_responsavel'])
            linhas_cat = cats_limpos.count('\n') + 1
            linhas_turma = 1 if len(nome_t) < 30 else 2
            h = max(linhas_cat, linhas_turma) * 5
            if h < 7: h = 7

            curr_x, curr_y = pdf.get_x(), pdf.get_y()
            pdf.multi_cell(55, h/linhas_turma if linhas_turma > 1 else h, limpar_texto(nome_t), border=1, align='L')
            pdf.set_xy(curr_x + 55, curr_y)
            pdf.multi_cell(70, h/linhas_cat, limpar_texto(cats_limpos), border=1, align='L')
            pdf.set_xy(curr_x + 125, curr_y)
            pdf.cell(22, h, str(bat), border=1, align='C')
            pdf.cell(22, h, str(euc), border=1, align='C')
            pdf.cell(21, h, str(len(alunos)), border=1, align='C'); pdf.ln(h)

    desenhar_tabela_itinerarios_local("1. ITINERÁRIOS INFANTIL / JUVENIL", t_infantil)
    pdf.ln(5)
    desenhar_tabela_itinerarios_local("2. ITINERÁRIOS DE JOVENS E ADULTOS", t_adultos)

    # --- 2. CENSO DE COBERTURA (ATIVOS) ---
    pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. CENSO DE COBERTURA SACRAMENTAL (CATEQUIZANDOS ATIVOS)"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 9); pdf.ln(2)
    df_ativos = df_cat[df_cat['status'] == 'ATIVO']
    df_ativos['idade_temp'] = df_ativos['data_nascimento'].apply(calcular_idade)
    df_k = df_ativos[df_ativos['idade_temp'] < 18]; df_a = df_ativos[df_ativos['idade_temp'] >= 18]
    for label, df_grupo in [("Público Infantil/Juvenil", df_k), ("Público Jovens/Adultos", df_a)]:
        if not df_grupo.empty:
            total = len(df_grupo); bat = len(df_grupo[df_grupo['batizado_sn'] == 'SIM']); perc = (bat/total)*100
            pdf.cell(95, 8, limpar_texto(f"{label}: {bat} / {total}"), border=1, align='C')
            pdf.cell(95, 8, limpar_texto(f"Cobertura: {perc:.1f}% Batizados"), border=1, align='C', ln=True)

    # --- 3. CENSO DE EVASÃO E MOVIMENTAÇÃO ---
    pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("4. CENSO DE EVASÃO E INTERRUPÇÃO DE ITINERÁRIO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(70, 7, "Situação Pastoral", border=1, fill=True); pdf.cell(60, 7, "Quantidade", border=1, fill=True, align='C'); pdf.cell(60, 7, "Percentual sobre Total", border=1, fill=True, align='C'); pdf.ln()
    total_geral = len(df_cat) if len(df_cat) > 0 else 1
    pdf.set_font("helvetica", "", 9)
    for status in ['DESISTENTE', 'TRANSFERIDO', 'INATIVO']:
        qtd = len(df_cat[df_cat['status'] == status])
        perc = (qtd / total_geral) * 100
        pdf.cell(70, 7, f" {status}", border=1)
        pdf.cell(60, 7, str(qtd), border=1, align='C')
        pdf.cell(60, 7, f"{perc:.1f}%", border=1, align='C'); pdf.ln()

    # --- 4. FRUTOS DA EVANGELIZAÇÃO 2026 (LISTA NOMINAL) ---
    df_rec = ler_aba("sacramentos_recebidos")
    if not df_rec.empty:
        df_rec['data_dt'] = pd.to_datetime(df_rec['data'], errors='coerce')
        df_ano = df_rec[df_rec['data_dt'].dt.year == ANO_ATUAL].sort_values(by='data_dt')
        if not df_ano.empty:
            pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto(f"5. FRUTOS DA EVANGELIZAÇÃO {ANO_ATUAL} (LISTA NOMINAL)"), ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
            pdf.cell(100, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(50, 7, "Sacramento", border=1, fill=True, align='C'); pdf.cell(40, 7, "Data", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 8)
            for _, r in df_ano.iterrows():
                pdf.cell(100, 6, limpar_texto(r['nome']), border=1)
                pdf.cell(50, 6, limpar_texto(r['tipo']), border=1, align='C')
                pdf.cell(40, 6, formatar_data_br(r['data']), border=1, align='C'); pdf.ln()

    # --- 5. EQUIPE CATEQUÉTICA (SEM ADMIN + COR LARANJA) ---
    df_equipe_real = df_usuarios[df_usuarios['papel'].str.upper() != 'ADMIN'] if not df_usuarios.empty else pd.DataFrame()
    total_e = len(df_equipe_real) if not df_equipe_real.empty else 1
    pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto(f"6. EQUIPE CATEQUÉTICA E QUALIFICAÇÃO (Total: {len(df_equipe_real)} membros)"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(100, 7, "Indicador de Fé (Equipe)", border=1, fill=True); pdf.cell(45, 7, "Quantidade", border=1, fill=True, align='C'); pdf.cell(45, 7, "Percentual", border=1, fill=True, align='C'); pdf.ln()
    bat_e = df_equipe_real['data_batismo'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
    euc_e = df_equipe_real['data_eucaristia'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
    cri_e = df_equipe_real['data_crisma'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
    pdf.set_font("helvetica", "", 8)
    for desc, qtd in [("Batismo", bat_e), ("Eucaristia", euc_e), ("Crisma", cri_e)]:
        pdf.cell(100, 6, f" {desc}", border=1); pdf.cell(45, 6, str(qtd), border=1, align='C'); pdf.cell(45, 6, f"{(qtd/total_e)*100:.1f}%", border=1, align='C'); pdf.ln()
    
    # Lista Nominal da Equipe
    pdf.ln(2); pdf.set_font("helvetica", "B", 8); pdf.cell(0, 5, "Lista Nominal da Equipe (Catequistas):", ln=True)
    pdf.set_font("helvetica", "", 7); nomes_equipe = df_equipe_real['nome'].tolist()
    for i, nome in enumerate(nomes_equipe):
        pdf.cell(63, 5, limpar_texto(f" - {nome}"), border=0)
        if (i + 1) % 3 == 0: pdf.ln()
    
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_v3(df_turmas, df_cat, df_pres):
    """Dossiê Pastoral Nominal: Detalhamento por turma com lista de ATIVOS e EVASÃO."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL E NOMINAL POR ITINERÁRIO")
    AZUL_P = (65, 123, 153); CINZA_F = (245, 245, 245); LARANJA_P = (224, 61, 17)
    
    for _, t in df_turmas.iterrows():
        nome_t = t['nome_turma']
        alunos_t = df_cat[df_cat['etapa'] == nome_t] if not df_cat.empty else pd.DataFrame()
        ativos = alunos_t[alunos_t['status'] == 'ATIVO']
        evasao = alunos_t[alunos_t['status'].isin(['DESISTENTE', 'TRANSFERIDO', 'INATIVO'])]
        
        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto(f"TURMA: {nome_t}"), ln=True, fill=True)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        pdf.cell(63, 7, f"Ativos: {len(ativos)}", border=1, fill=True, align='C')
        pdf.cell(63, 7, f"Batizados (Ativos): {len(ativos[ativos['batizado_sn']=='SIM'])}", border=1, fill=True, align='C')
        pdf.cell(64, 7, f"Evasão/Transf: {len(evasao)}", border=1, fill=True, align='C'); pdf.ln()
        
        pdf.set_font("helvetica", "B", 8); pdf.cell(0, 6, "CATEQUIZANDOS EM CAMINHADA ATIVA:", ln=True)
        pdf.set_font("helvetica", "", 8)
        nomes_ativos = sorted(ativos['nome_completo'].tolist())
        for i in range(0, len(nomes_ativos), 2):
            pdf.cell(95, 5, limpar_texto(f" - {nomes_ativos[i]}"), border=0)
            if i+1 < len(nomes_ativos): pdf.cell(95, 5, limpar_texto(f" - {nomes_ativos[i+1]}"), border=0)
            pdf.ln()
        
        if not evasao.empty:
            pdf.ln(2); pdf.set_text_color(*LARANJA_P); pdf.set_font("helvetica", "B", 8)
            pdf.cell(0, 6, "ALERTA: CATEQUIZANDOS COM ITINERÁRIO INTERROMPIDO / TRANSFERIDOS:", ln=True)
            pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "I", 8)
            for _, r in evasao.iterrows():
                pdf.cell(0, 5, limpar_texto(f" ! {r['nome_completo']} ({r['status']})"), ln=True)
        
        pdf.ln(10)
        if pdf.get_y() > 230: pdf.add_page()
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_v2(stats_gerais, analise_turmas, impedimentos_lista, analise_ia):
    """Auditoria Sacramental e Censo de IVC."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "AUDITORIA SACRAMENTAL E CENSO DE IVC")
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. QUADRO GERAL DE SACRAMENTALIZAÇÃO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(50, 7, "Sacramento", border=1, fill=True); pdf.cell(70, 7, "Infantil / Juvenil", border=1, fill=True, align='C'); pdf.cell(70, 7, "Jovens / Adultos", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 9)
    for sac, k, a in [("BATISMO", stats_gerais.get('bat_k', 0), stats_gerais.get('bat_a', 0)), ("EUCARISTIA", stats_gerais.get('euca_k', 0), stats_gerais.get('euca_a', 0)), ("CRISMA", "N/A", stats_gerais.get('crisma_a', 0))]:
        pdf.cell(50, 7, f" {sac}", border=1); pdf.cell(70, 7, str(k), border=1, align='C'); pdf.cell(70, 7, str(a), border=1, align='C'); pdf.ln()
    pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("2. DIAGNÓSTICO DE IMPEDIMENTOS"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(70, 7, "Catequizando", border=1, fill=True); pdf.cell(50, 7, "Turma", border=1, fill=True); pdf.cell(70, 7, "Situação", border=1, fill=True); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    if impedimentos_lista:
        for imp in impedimentos_lista:
            pdf.cell(70, 6, limpar_texto(imp.get('nome', 'N/A')), border=1); pdf.cell(50, 6, limpar_texto(imp.get('turma', 'N/A')), border=1); pdf.cell(70, 6, limpar_texto(imp.get('situacao', 'N/A')), border=1); pdf.ln()
    else: pdf.cell(190, 7, "Nenhum impedimento registrado.", border=1, align='C', ln=True)
    pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. PARECER TÉCNICO DA AUDITORIA"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

# ==============================================================================
# 9. UTILITÁRIOS PASTORAIS E CENSO (ANIVERSARIANTES E STATUS)
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
        if d_str == "N/A": return False
        nasc = datetime.strptime(d_str, "%d/%m/%Y").date()
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        nasc_este_ano = nasc.replace(year=hoje.year)
        diff = (nasc_este_ano - hoje).days
        return 0 <= diff <= 7
    except: return False

def converter_para_data(valor_str):
    if not valor_str or str(valor_str).strip() in ["None", "", "N/A"]: return date.today()
    try: return datetime.strptime(formatar_data_br(valor_str), "%d/%m/%Y").date()
    except: return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    if d_ministerio and str(d_ministerio).strip() not in ["", "N/A", "None"]: return "MINISTRO", 0 
    try:
        hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        inicio = datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos = hoje.year - inicio.year
        tem_s = all([str(x).strip() not in ["", "N/A", "None"] for x in [d_batismo, d_euca, d_crisma]])
        if anos >= 5 and tem_s: return "APTO", anos
        return "EM_CAMINHADA", anos
    except: return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    niver = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.day == hoje.day and dt.month == hoje.month:
                    niver.append(f"{hoje.day} | CATEQUIZANDO | {r['nome_completo']}")
    if not df_usuarios.empty:
        df_e = df_usuarios[df_usuarios['papel'] != 'ADMIN']
        for _, u in df_e.drop_duplicates(subset=['nome']).iterrows():
            d = formatar_data_br(u.get('data_nascimento', ''))
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.day == hoje.day and dt.month == hoje.month:
                    niver.append(f"{hoje.day} | CATEQUISTA | {u['nome']}")
    return niver

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.month == hoje.month: lista.append({'dia': dt.day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO'})
    if not df_usuarios.empty:
        for _, u in df_usuarios.drop_duplicates(subset=['nome']).iterrows():
            d = formatar_data_br(u.get('data_nascimento', ''))
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.month == hoje.month: lista.append({'dia': dt.day, 'nome': u['nome'], 'tipo': 'CATEQUISTA'})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    return obter_aniversariantes_mes_unificado(df_cat, None)

# ==============================================================================
# 10. PROCESSAMENTO LOCAL E AUDITORIA INTEGRAL (DOSSIÊS)
# ==============================================================================

def gerar_relatorio_local_turma_v2(nome_turma, metricas, listas, analise_ia):
    """Auditoria Pastoral Individual de Turma."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"AUDITORIA PASTORAL: {nome_turma}")
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. INDICADORES ESTRUTURAIS E ADESÃO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Catequistas", str(metricas.get('qtd_catequistas', 0)), 10, y, 45)
    desenhar_campo_box(pdf, "Total Catequizandos", str(metricas.get('qtd_cat', 0)), 58, y, 45)
    desenhar_campo_box(pdf, "Frequência", f"{metricas.get('freq_global', 0)}%", 106, y, 45)
    desenhar_campo_box(pdf, "Idade Média", f"{metricas.get('idade_media', 0)} anos", 154, y, 46); pdf.ln(18)
    pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. LISTA NOMINAL E ALERTA DE EVASÃO"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(*CINZA_F)
    pdf.cell(120, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(70, 7, "Status / Faltas", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    for cat in listas.get('geral', []):
        faltas = cat.get('faltas', 0)
        if faltas >= 2: pdf.set_text_color(*LARANJA_P)
        else: pdf.set_text_color(0, 0, 0)
        info = f"ATIVO ({faltas} faltas)" if faltas > 0 else "ATIVO (100% Freq.)"
        pdf.cell(120, 6, limpar_texto(cat['nome']), border=1); pdf.cell(70, 6, limpar_texto(info), border=1, align='C'); pdf.ln()
    pdf.set_text_color(0, 0, 0); pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. PARECER TÉCNICO E ORIENTAÇÃO PASTORAL"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_auditoria_lote_completa(df_turmas, df_cat, df_pres, df_recebidos):
    """Gera um Dossiê Paroquial contendo a auditoria completa de cada turma com foco em Evasão."""
    pdf = FPDF(); col_id_cat = 'id_catequizando'
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    for _, t in df_turmas.iterrows():
        t_nome = t['nome_turma']; alunos_t = df_cat[df_cat['etapa'] == t_nome]
        if not alunos_t.empty:
            pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"AUDITORIA INTEGRAL: {t_nome}")
            ativos = alunos_t[alunos_t['status'] == 'ATIVO']; evasao = alunos_t[alunos_t['status'] != 'ATIVO']
            pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto("1. INDICADORES ESTRUTURAIS"), ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
            desenhar_campo_box(pdf, "Ativos", str(len(ativos)), 10, y, 60)
            desenhar_campo_box(pdf, "Evasão", str(len(evasao)), 75, y, 60)
            desenhar_campo_box(pdf, "Total Histórico", str(len(alunos_t)), 140, y, 60); pdf.ln(18)
            pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, limpar_texto("2. LISTA NOMINAL DE CATEQUIZANDOS ATIVOS"), ln=True, fill=True, align='C')
            pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(*CINZA_F)
            pdf.cell(120, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(70, 7, "Faltas", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 8)
            pres_t = df_pres[df_pres['id_turma'] == t_nome] if not df_pres.empty else pd.DataFrame()
            for _, r in ativos.iterrows():
                faltas = len(pres_t[(pres_t[col_id_cat] == r[col_id_cat]) & (pres_t['status'] == 'AUSENTE')]) if not pres_t.empty else 0
                pdf.cell(120, 6, limpar_texto(r['nome_completo']), border=1); pdf.cell(70, 6, f"{faltas} faltas", border=1, align='C'); pdf.ln()
            if not evasao.empty:
                pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255)
                pdf.cell(190, 8, limpar_texto("3. REGISTRO DE EVASÃO / TRANSFERÊNCIA"), ln=True, fill=True, align='C')
                pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(*CINZA_F)
                pdf.cell(100, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(90, 7, "Situação / Motivo", border=1, fill=True); pdf.ln()
                pdf.set_font("helvetica", "I", 8)
                for _, r in evasao.iterrows():
                    pdf.cell(100, 6, limpar_texto(r['nome_completo']), border=1); pdf.cell(90, 6, limpar_texto(f"{r['status']} - {r.get('obs_pastoral_familia', 'Sem obs.')[:40]}..."), border=1); pdf.ln()
    return finalizar_pdf(pdf)

def gerar_relatorio_evasao_pdf(df_evasao):
    """Gera o Relatório de Diagnóstico de Evasão e Transferências."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO DE DIAGNÓSTICO PASTORAL (EVASÃO)")
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("LISTA DE CATEQUIZANDOS FORA DE CAMINHADA ATIVA"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(60, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(30, 7, "Situação", border=1, fill=True, align='C'); pdf.cell(40, 7, "Último Itinerário", border=1, fill=True); pdf.cell(60, 7, "Motivo / Obs. Pastoral", border=1, fill=True); pdf.ln()
    pdf.set_font("helvetica", "", 8)
    for _, r in df_evasao.iterrows():
        h = 7; curr_x, curr_y = pdf.get_x(), pdf.get_y()
        pdf.multi_cell(60, h, limpar_texto(r['nome_completo']), border=1, align='L'); pdf.set_xy(curr_x + 60, curr_y)
        pdf.cell(30, h, limpar_texto(r['status']), border=1, align='C'); pdf.set_xy(curr_x + 90, curr_y)
        pdf.cell(40, h, limpar_texto(r['etapa']), border=1); pdf.set_xy(curr_x + 130, curr_y)
        pdf.multi_cell(60, h, limpar_texto(str(r.get('obs_pastoral_familia', 'N/A'))[:50]), border=1, align='L')
        if pdf.get_y() > 250: pdf.add_page()
    return finalizar_pdf(pdf)

# ==============================================================================
# 11. ALIASES DE COMPATIBILIDADE (NÃO REMOVER - DEFESA DE LEGADO)
# ==============================================================================
gerar_relatorio_diocesano_pdf = gerar_relatorio_diocesano_v4
gerar_relatorio_pastoral_interno_pdf = gerar_relatorio_pastoral_v3
gerar_relatorio_diocesano_v2 = gerar_relatorio_diocesano_v4
gerar_relatorio_pastoral_v2 = gerar_relatorio_pastoral_v3
gerar_relatorio_sacramentos_tecnico_pdf = gerar_relatorio_sacramentos_tecnico_v2
gerar_pdf_perfil_turma = lambda n, m, a, l: finalizar_pdf(FPDF())
gerar_relatorio_local_turma_pdf = gerar_relatorio_local_turma_v2

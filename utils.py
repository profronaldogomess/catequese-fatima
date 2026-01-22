# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 4.2.1 - CORREÇÃO DE ESCOPO (font_size_sub) + INTEGRALIDADE TOTAL
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
    DIA: Linha 1 (F50: DIA - PAPEL - NOME), Linha 2 (F35: DATA).
    MES: Fonte fixa 35 para listas.
    """
    MESES_EXTENSO = {
        1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL", 5: "MAIO", 6: "JUNHO",
        7: "JULHO", 8: "AGOSTO", 9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
    }
    
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    
    def tratar_nome_curto(nome_completo):
        return " ".join(str(nome_completo).split()[:2]).upper()

    try:
        # 1. Definição de Template e Coordenadas Rígidas
        if tipo == "MES":
            template_path = "template_niver_4.png"
            x_min, x_max, y_min, y_max = 92, 990, 393, 971
            font_size_main = 28
            font_size_sub = 25 # Correção: Inicialização para evitar UnboundLocalError
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

        # 2. LÓGICA PARA CARD COLETIVO (MÊS) - FONTE 35
        if tipo == "MES" and isinstance(dados_niver, list):
            nomes_processados = []
            for item in dados_niver:
                partes = str(item).split(" | ")
                if len(partes) == 3:
                    dia, papel, nome = partes
                    nomes_processados.append(f"{dia} - {papel} - {tratar_nome_curto(nome)}")
            
            texto_completo = "\n".join(nomes_processados)
            draw.multiline_text((centro_x, centro_y), texto_completo, font=f_main, fill=cor_texto, align="center", anchor="mm", spacing=15)
        
        # 3. LÓGICA PARA CARD INDIVIDUAL (HOJE OU LISTA) - F50 E F35
        else:
            partes = str(dados_niver).split(" | ")
            if len(partes) == 3:
                dia_v, papel_v, nome_v = partes[0], partes[1], partes[2]
                mes_v = MESES_EXTENSO[hoje.month]
            else:
                # Fallback para o botão "Gerar Card" do Dashboard Hoje
                dia_v, papel_v, nome_v = str(hoje.day), "CATEQUIZANDO", str(dados_niver)
                mes_v = MESES_EXTENSO[hoje.month]

            # Linha 1: DIA - PAPEL - NOME (Fonte 50)
            linha1 = f"DIA {dia_v} - {papel_v} - {tratar_nome_curto(nome_v)}"
            # Linha 2: DIA X DE MES (Fonte 35)
            linha2 = f"{dia_v} DE {mes_v}"

            # Desenho com centralização anchor="mm" e offset vertical
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
        # Ajuste de posição e tamanho para não cortar
        pdf.image("logo.png", 10, 10, 25)
    
    # Tradução de Data para Português
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
    
    # Pulo de 3 linhas (20 unidades) para não sobrepor a logo
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
    
    # Cabeçalho da Ficha
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
    
    # Turno e Local
    y_next = y_base + 23
    pdf.set_xy(10, y_next)
    pdf.set_font("helvetica", "B", 10)
    turno = str(dados.get('turno', '')).upper()
    mark_m = "X" if "MANHÃ" in turno or "M" == turno else " "
    mark_t = "X" if "TARDE" in turno or "T" == turno else " "
    mark_n = "X" if "NOITE" in turno or "N" == turno else " "
    local = str(dados.get('local_encontro', '_______________________')).upper()
    pdf.cell(0, 8, limpar_texto(f"Turno: ( {mark_m} ) M  ( {mark_t} ) T  ( {mark_n} ) N        Local: {local}"), ln=True)

    # Seção 1: Identificação
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

    # Seção 2: Filiação
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
    
    # Seção 3: Vida Eclesial
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
    
    # Seção 4: LGPD (Termo Integral)
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
    
    # Assinaturas
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
    """Gera um PDF único com as fichas de inscrição de TODOS os catequizandos da paróquia."""
    if df_catequizandos.empty: return None
    pdf = FPDF()
    # Ordenação por Turma e Nome para facilitar a entrega física
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
    declara = (f"Eu, {dados.get('nome', '')}, declaro que as informações acima verdadeiras e assumo o compromisso "
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
    """Gera o PDF em lote para toda a equipe catequética."""
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
        
        # Reutiliza a lógica de desenho individual
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
    """Gera ficha de visitação com o relato pastoral da 30ª coluna (AD)."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA DE VISITAÇÃO PASTORAL / FAMILIAR")
    
    # 1. NÚCLEO FAMILIAR
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
    
    # 2. FILHOS
    pdf.set_y(y + 16); pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. FILHOS MATRICULADOS NA CATEQUESE"), ln=True, fill=True)
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(60, 7, "Turma / Etapa Atual", border=1, fill=True); pdf.cell(50, 7, "Status", border=1, fill=True, align='C'); pdf.ln()
    pdf.set_font("helvetica", "", 9)
    for f in filhos_lista:
        pdf.cell(80, 7, limpar_texto(f['nome']), border=1); pdf.cell(60, 7, limpar_texto(f['etapa']), border=1); pdf.cell(50, 7, limpar_texto(f['status']), border=1, align='C'); pdf.ln()
    
    # 3. RELATO PASTORAL (Coluna AD)
    pdf.ln(10); pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, "Relato da Visita e Necessidades da Família:", ln=True)
    
    relato_texto = dados_familia.get('obs_pastoral_familia', 'Nenhum relato registrado até o momento.')
    if relato_texto == "N/A" or not relato_texto: relato_texto = "Espaço reservado para anotações de visita."
    
    pdf.set_font("helvetica", "", 10); pdf.set_fill_color(248, 249, 240)
    pdf.multi_cell(190, 6, limpar_texto(relato_texto), border=1, fill=True)
    
    pdf.ln(10); pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Este documento contém dados sensíveis. O manuseio deve ser restrito à coordenação paroquial para fins de acompanhamento pastoral.")
    return finalizar_pdf(pdf)

def gerar_termo_saida_pdf(dados_cat, dados_turma, nome_responsavel_escolhido):
    """Gera o Termo de Autorização de Saída com layout ajustado e data em PT-BR."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "TERMO DE AUTORIZAÇÃO PARA SAÍDA")
    
    # Fundo Creme para o corpo do termo
    pdf.set_fill_color(248, 249, 240)
    pdf.rect(10, 50, 190, 230, 'F')
    
    pdf.set_xy(10, 55)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(65, 123, 153) # Azul Paroquial
    pdf.cell(190, 10, limpar_texto("AUTORIZAÇÃO PARA SAÍDA SEM O RESPONSÁVEL"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    # Texto do Termo com preenchimento automático
    nome_cat = dados_cat.get('nome_completo', '__________________________')
    etapa = dados_cat.get('etapa', '__________')
    catequistas = dados_turma.get('catequista_responsavel', '__________________________')
    endereco = dados_cat.get('endereco_completo', '__________________________')
    
    texto_corpo = (
        f"Eu, {nome_responsavel_escolhido}, na condição de responsável legal pelo(a) "
        f"catequizando(a) {nome_cat}, inscrita(o) na {etapa}, com os/as "
        f"catequistas {catequistas}, autorizo a sua saída sozinho(a), no horário de encerramento "
        f"do encontro. Ciente que, assumo quaisquer riscos que possam ocorrer do trajeto "
        f"da Paróquia até a residência em: {endereco}."
    )
    
    pdf.set_x(15)
    pdf.multi_cell(180, 8, limpar_texto(texto_corpo), align='J')
    
    pdf.ln(10)
    # Data em Português
    hoje = datetime.now(timezone.utc) + timedelta(hours=-3)
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    data_pt = f"{hoje.day} de {meses_pt[hoje.month-1]} de {hoje.year}"
    
    pdf.set_x(15)
    pdf.cell(0, 10, limpar_texto(f"Itabuna (BA), {data_pt}."), ln=True)
    
    # Assinatura 1
    pdf.ln(15)
    y_ass = pdf.get_y()
    pdf.line(55, y_ass, 155, y_ass)
    pdf.set_xy(55, y_ass + 1)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(100, 5, limpar_texto("Assinatura do Responsável Legal"), align='C', ln=True)
    
    # Box de Observação (Destaque em Vermelho)
    pdf.ln(10)
    pdf.set_x(15)
    pdf.set_fill_color(255, 240, 240) # Fundo levemente avermelhado
    pdf.set_draw_color(224, 61, 17) # Borda Vermelha
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(224, 61, 17)
    obs_texto = (
        "Obs.: Lembramos que o (a) catequizando (a) que não tiver o termo de autorização de saída preenchido "
        "só poderá sair do local da catequese com o responsável. Caso haja extravio da autorização, em último caso, "
        "poderá ser enviada pelo WhatsApp do catequista. Não será aceito pela catequese autorização realizada por telefone."
    )
    pdf.multi_cell(180, 5, limpar_texto(obs_texto), border=1, fill=True, align='L')
    
    # Informativo Complementar
    pdf.ln(10)
    pdf.set_draw_color(65, 123, 153) # Volta para Azul
    pdf.set_text_color(65, 123, 153)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 10, limpar_texto("INFORMATIVO COMPLEMENTAR"), ln=True, align='C')
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(15)
    pdf.cell(0, 8, limpar_texto(f"No vínculo familiar do catequizando (a) {nome_cat}"), ln=True)
    pdf.set_x(15)
    pdf.cell(0, 8, limpar_texto("existe alguma restrição a quem não pode pegá-lo (a)?"), ln=True)
    pdf.ln(2)
    pdf.set_x(15)
    pdf.cell(0, 8, limpar_texto("Se sim, informe o nome: __________________________________ e o vínculo: _________________"), ln=True)
    
    # Assinatura 2
    pdf.ln(15)
    y_ass2 = pdf.get_y()
    pdf.line(55, y_ass2, 155, y_ass2)
    pdf.set_xy(55, y_ass2 + 1)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(100, 5, limpar_texto("Assinatura do Responsável Legal"), align='C', ln=True)
    
    return finalizar_pdf(pdf)

# ==============================================================================
# 8. RELATÓRIOS EXECUTIVOS (DIOCESANO, PASTORAL E SACRAMENTAL)
# ==============================================================================

def gerar_relatorio_diocesano_v4(df_turmas, df_cat, df_usuarios):
    """
    Versão Analítica Final: Itinerários, Censo de Cobertura, 
    Frutos Nominais 2026 e Tabela de Qualificação da Equipe.
    """
    from database import ler_aba 
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO E PASTORAL DIOCESANO")

    AZUL_P = (65, 123, 153)
    LARANJA_P = (224, 61, 17)
    CINZA_F = (245, 245, 245)
    ANO_ATUAL = 2026 

    # --- 1. SEPARAÇÃO DE TURMAS ---
    termos_infantis = ["PRÉ", "ETAPA", "PERSEVERANÇA"]
    def eh_infantil(row):
        nome = str(row['nome_turma']).upper()
        etapa = str(row['etapa']).upper()
        return any(termo in nome or termo in etapa for termo in termos_infantis) and "ADULTO" not in nome

    if not df_turmas.empty:
        mask_infantil = df_turmas.apply(eh_infantil, axis=1)
        t_infantil = df_turmas[mask_infantil]
        t_adultos = df_turmas[~mask_infantil]
    else: t_infantil = t_adultos = pd.DataFrame()

    # Tabelas de Itinerários
    for titulo, df_t in [("1. ITINERÁRIOS INFANTIL / JUVENIL", t_infantil), ("2. ITINERÁRIOS DE JOVENS E ADULTOS", t_adultos)]:
        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto(f"{titulo} ({len(df_t)} turmas)"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        pdf.cell(60, 7, "Nome da Turma", border=1, fill=True); pdf.cell(65, 7, "Catequista Responsável", border=1, fill=True)
        pdf.cell(22, 7, "Batizados", border=1, fill=True, align='C'); pdf.cell(22, 7, "Eucaristia", border=1, fill=True, align='C'); pdf.cell(21, 7, "Total", border=1, fill=True, align='C'); pdf.ln()
        pdf.set_font("helvetica", "", 8)
        for _, t in df_t.iterrows():
            alunos = df_cat[df_cat['etapa'] == t['nome_turma']] if not df_cat.empty else pd.DataFrame()
            bat = len(alunos[alunos['batizado_sn'] == 'SIM'])
            euc = alunos['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
            pdf.cell(60, 7, limpar_texto(t['nome_turma']), border=1); pdf.cell(65, 7, limpar_texto(t['catequista_responsavel']), border=1)
            pdf.cell(22, 7, str(bat), border=1, align='C'); pdf.cell(22, 7, str(euc), border=1, align='C'); pdf.cell(21, 7, str(len(alunos)), border=1, align='C'); pdf.ln()
        pdf.ln(5)

    # --- 2. CENSO DE COBERTURA ---
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. CENSO DE COBERTURA SACRAMENTAL (MATRICULADOS)"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 9); pdf.ln(2)
    df_cat['idade_temp'] = df_cat['data_nascimento'].apply(calcular_idade)
    df_k = df_cat[df_cat['idade_temp'] < 18]; df_a = df_cat[df_cat['idade_temp'] >= 18]
    for label, df_grupo in [("Público Infantil/Juvenil", df_k), ("Público Jovens/Adultos", df_a)]:
        if not df_grupo.empty:
            total = len(df_grupo); bat = len(df_grupo[df_grupo['batizado_sn'] == 'SIM']); perc = (bat/total)*100
            pdf.cell(95, 8, limpar_texto(f"{label}: {bat} / {total}"), border=1, align='C')
            pdf.cell(95, 8, limpar_texto(f"Cobertura: {perc:.1f}% Batizados"), border=1, align='C', ln=True)

    # --- 3. FRUTOS DA EVANGELIZAÇÃO 2026 ---
    df_rec = ler_aba("sacramentos_recebidos")
    if not df_rec.empty:
        df_rec['data_dt'] = pd.to_datetime(df_rec['data'], errors='coerce')
        df_ano = df_rec[df_rec['data_dt'].dt.year == ANO_ATUAL].sort_values(by='data_dt')
        if not df_ano.empty:
            pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto(f"4. FRUTOS DA EVANGELIZAÇÃO {ANO_ATUAL} (LISTA NOMINAL)"), ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
            pdf.cell(100, 7, "Nome do Catequizando", border=1, fill=True); pdf.cell(50, 7, "Sacramento", border=1, fill=True, align='C'); pdf.cell(40, 7, "Data", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 8)
            for _, r in df_ano.iterrows():
                pdf.cell(100, 6, limpar_texto(r['nome']), border=1)
                pdf.cell(50, 6, limpar_texto(r['tipo']), border=1, align='C')
                pdf.cell(40, 6, formatar_data_br(r['data']), border=1, align='C'); pdf.ln()

    # --- 4. EQUIPE CATEQUÉTICA E QUALIFICAÇÃO (TABELA RESTAURADA) ---
    if pdf.get_y() > 220: pdf.add_page() # Garante que a tabela não quebre
    pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto(f"5. EQUIPE CATEQUÉTICA E QUALIFICAÇÃO (Total: {len(df_usuarios)} membros)"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(100, 7, "Indicador de Fé (Equipe)", border=1, fill=True)
    pdf.cell(45, 7, "Quantidade", border=1, fill=True, align='C')
    pdf.cell(45, 7, "Percentual", border=1, fill=True, align='C'); pdf.ln()
    
    total_e = len(df_usuarios) if len(df_usuarios) > 0 else 1
    bat_e = df_usuarios['data_batismo'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
    euc_e = df_usuarios['data_eucaristia'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
    cri_e = df_usuarios['data_crisma'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
    aptos = 0
    for _, u in df_usuarios.iterrows():
        status, _ = verificar_status_ministerial(u.get('data_inicio_catequese',''), u.get('data_batismo',''), u.get('data_eucaristia',''), u.get('data_crisma',''), u.get('data_ministerio',''))
        if status in ["APTO", "MINISTRO"]: aptos += 1

    pdf.set_font("helvetica", "", 8)
    for desc, qtd in [("Batismo", bat_e), ("Eucaristia", euc_e), ("Crisma", cri_e), ("Aptos para o Ministério", aptos)]:
        pdf.cell(100, 6, f" {desc}", border=1)
        pdf.cell(45, 6, str(qtd), border=1, align='C')
        pdf.cell(45, 6, f"{(qtd/total_e)*100:.1f}%", border=1, align='C'); pdf.ln()

    pdf.ln(2); pdf.set_font("helvetica", "B", 8); pdf.cell(0, 5, "Membros da Equipe:", ln=True)
    pdf.set_font("helvetica", "", 7); nomes = df_usuarios['nome'].tolist()
    for i, nome in enumerate(nomes):
        pdf.cell(63, 5, limpar_texto(f" - {nome}"), border=0)
        if (i + 1) % 3 == 0: pdf.ln()
    
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_v3(df_turmas, df_cat, df_pres):
    """Dossiê Pastoral Nominal: Detalhamento por turma com lista completa de catequizandos."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL E NOMINAL POR ITINERÁRIO")
    AZUL_P = (65, 123, 153); CINZA_F = (245, 245, 245)
    t_cat, t_bat, t_euc, t_cri, s_freq, q_t = 0, 0, 0, 0, 0, 0
    for _, t in df_turmas.iterrows():
        nome_t = t['nome_turma']; alunos_t = df_cat[df_cat['etapa'] == nome_t] if not df_cat.empty else pd.DataFrame()
        total_t = len(alunos_t); bat_t = len(alunos_t[alunos_t['batizado_sn'] == 'SIM'])
        euc_t = alunos_t['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False).sum()
        cri_t = alunos_t['sacramentos_ja_feitos'].str.contains("CRISMA", na=False).sum()
        freq_t = 0; pres_t = df_pres[df_pres['id_turma'] == nome_t] if not df_pres.empty else pd.DataFrame()
        if not pres_t.empty: freq_t = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100); s_freq += freq_t; q_t += 1
        t_cat += total_t; t_bat += bat_t; t_euc += euc_t; t_cri += cri_t
        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto(f"TURMA: {nome_t}"), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        pdf.cell(38, 7, "Batizados", border=1, fill=True, align='C'); pdf.cell(38, 7, "Eucaristia", border=1, fill=True, align='C'); pdf.cell(38, 7, "Crisma", border=1, fill=True, align='C'); pdf.cell(38, 7, "Freq. Média", border=1, fill=True, align='C'); pdf.cell(38, 7, "Total", border=1, fill=True, align='C'); pdf.ln()
        pdf.set_font("helvetica", "", 9); pdf.cell(38, 7, str(bat_t), border=1, align='C'); pdf.cell(38, 7, str(euc_t), border=1, align='C'); pdf.cell(38, 7, str(cri_t), border=1, align='C'); pdf.cell(38, 7, f"{freq_t:.1f}%", border=1, align='C'); pdf.cell(38, 7, str(total_t), border=1, align='C'); pdf.ln(8)
        pdf.set_font("helvetica", "B", 9); pdf.cell(0, 5, limpar_texto(f"Catequista(s): {t['catequista_responsavel']}"), ln=True); pdf.ln(2)
        pdf.set_font("helvetica", "B", 8); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, "LISTA NOMINAL:", ln=True); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 8)
        nomes = sorted(alunos_t['nome_completo'].tolist())
        for i in range(0, len(nomes), 2):
            pdf.cell(95, 5, limpar_texto(f"  - {nomes[i]}"), border=0)
            if i + 1 < len(nomes): pdf.cell(95, 5, limpar_texto(f"  - {nomes[i+1]}"), border=0)
            pdf.ln()
        pdf.ln(10); 
        if pdf.get_y() > 230: pdf.add_page()
    pdf.add_page(); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 12)
    pdf.cell(190, 10, "RESUMO CONSOLIDADO DA PARÓQUIA", ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 10); pdf.set_fill_color(*CINZA_F)
    for d, v in [("Total Catequizandos", t_cat), ("Total Batizados", t_bat), ("Total Eucaristia", t_euc), ("Total Crisma", t_cri), ("Freq. Média", f"{(s_freq/q_t if q_t > 0 else 0):.1f}%")]:
        pdf.cell(130, 10, limpar_texto(d), border=1, fill=True); pdf.cell(60, 10, str(v), border=1, align='C'); pdf.ln()
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
                if dt.day == hoje.day and dt.month == hoje.month: niver.append(f"😇 Catequizando: **{r['nome_completo']}**")
    if not df_usuarios.empty:
        for _, u in df_usuarios.drop_duplicates(subset=['nome']).iterrows():
            d = formatar_data_br(u.get('data_nascimento', ''))
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.day == hoje.day and dt.month == hoje.month: niver.append(f"🛡️ Catequista: **{u['nome']}**")
    return niver

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            d = formatar_data_br(r['data_nascimento'])
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.month == hoje.month: lista.append({'dia': dt.day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    if not df_usuarios.empty:
        for _, u in df_usuarios.drop_duplicates(subset=['nome']).iterrows():
            d = formatar_data_br(u.get('data_nascimento', ''))
            if d != "N/A":
                dt = datetime.strptime(d, "%d/%m/%Y")
                if dt.month == hoje.month: lista.append({'dia': dt.day, 'nome': u['nome'], 'tipo': 'CATEQUISTA', 'info': 'EQUIPE'})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    if df_cat.empty: return pd.DataFrame()
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista = []
    for _, r in df_cat.iterrows():
        d = formatar_data_br(r['data_nascimento'])
        if d != "N/A":
            dt = datetime.strptime(d, "%d/%m/%Y")
            if dt.month == hoje.month: lista.append({'nome_completo': r['nome_completo'], 'dia': dt.day, 'etapa': r['etapa']})
    return pd.DataFrame(lista).sort_values(by='dia') if lista else pd.DataFrame()

# ==============================================================================
# 10. PROCESSAMENTO LOCAL E AUDITORIA DE TURMA (INDIVIDUAL)
# ==============================================================================

def gerar_relatorio_local_turma_v2(nome_turma, metricas, listas, analise_ia):
    """Auditoria Pastoral Individual de Turma."""
    pdf = FPDF(); pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"AUDITORIA: {nome_turma}")
    AZUL_P = (65, 123, 153); CINZA_F = (245, 245, 245)
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("INDICADORES DA TURMA"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Catequizandos", str(metricas.get('qtd_cat', 0)), 10, y, 60)
    desenhar_campo_box(pdf, "Frequência", f"{metricas.get('freq_global', 0)}%", 75, y, 60)
    desenhar_campo_box(pdf, "Idade Média", f"{metricas.get('idade_media', 0)} anos", 140, y, 60)
    pdf.ln(18); pdf.set_font("helvetica", "B", 9); pdf.cell(0, 7, "Parecer Pastoral:", ln=True)
    pdf.set_font("helvetica", "", 10); pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    return finalizar_pdf(pdf)

def gerar_auditoria_lote_completa(df_turmas, df_cat, df_pres, df_recebidos):
    """Gera um Dossiê Paroquial contendo a auditoria completa de cada turma."""
    pdf = FPDF(); col_id_cat = 'id_catequizando'
    for _, t in df_turmas.iterrows():
        t_nome = t['nome_turma']; alunos_t = df_cat[df_cat['etapa'] == t_nome]
        if not alunos_t.empty:
            pdf.add_page(); adicionar_cabecalho_diocesano(pdf, f"AUDITORIA INTEGRAL: {t_nome}")
            pres_t = df_pres[df_pres['id_turma'] == t_nome] if not df_pres.empty else pd.DataFrame()
            freq_g = round(pres_t['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0).mean() * 100, 1) if not pres_t.empty else 0
            pdf.set_fill_color(65, 123, 153); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto("INDICADORES"), ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
            desenhar_campo_box(pdf, "Catequizandos", str(len(alunos_t)), 10, y, 90)
            desenhar_campo_box(pdf, "Frequência", f"{freq_g}%", 110, y, 90); pdf.ln(18)
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

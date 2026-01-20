# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 4.7.0 - MASTER ABSOLUTO (INTEGRALIDADE TOTAL 1100+ LINHAS)
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
    except:
        pass
    
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
    except:
        return 0

def limpar_texto(texto):
    """Remove artefatos de Markdown e garante compatibilidade com Latin-1 para PDF."""
    if not texto:
        return ""
    
    # Remove negritos de IA e outros caracteres especiais que quebram o FPDF
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
# 3. MOTOR DE CARDS DE ANIVERSÁRIO (REFINADO V4.7 - INTELIGÊNCIA GRAMATICAL)
# ==============================================================================

def gerar_card_aniversario(dados_niver, tipo="DIA"):
    """
    Gera card de aniversário com processamento gramatical:
    - Ignora preposições (DA, DE, DO, DAS, DOS) para o nome curto.
    - DIA: Linha 1 (Fonte 50: DIA - PAPEL - NOME), Linha 2 (Fonte 35: DATA).
    - MES: Fonte fixa 35 para a lista coletiva.
    """
    MESES_EXTENSO = {
        1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL", 5: "MAIO", 6: "JUNHO",
        7: "JULHO", 8: "AGOSTO", 9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
    }
    
    PREPOSICOES = ['DE', 'DA', 'DO', 'DAS', 'DOS']
    
    hoje = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    
    def tratar_nome_curto(nome_completo):
        """Busca o primeiro nome e o próximo termo significativo ignorando preposições."""
        partes = str(nome_completo).upper().split()
        if len(partes) <= 1:
            return str(nome_completo).upper()
        
        primeiro_nome = partes[0]
        segundo_nome = ""
        
        # Procura o primeiro termo após o nome que não seja preposição
        for p in partes[1:]:
            if p not in PREPOSICOES:
                segundo_nome = p
                break
        
        # Fallback de segurança caso o nome seja composto apenas por preposições
        if not segundo_nome:
            segundo_nome = partes[1]
            
        return f"{primeiro_nome} {segundo_nome}"

    try:
        # 1. Configuração de Template e Dimensões Rígidas
        if tipo == "MES":
            template_path = "template_niver_4.png"
            x_min, x_max = 92, 990
            y_min, y_max = 393, 971
            font_size_main = 35
        else:
            numero = random.randint(1, 3)
            template_path = f"template_niver_{numero}.png"
            x_min, x_max = 108, 972
            y_min, y_max = 549, 759
            font_size_main = 50
            font_size_sub = 35

        if not os.path.exists(template_path):
            return None
            
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        centro_x = (x_min + x_max) / 2
        centro_y = (y_min + y_max) / 2
        
        # 2. Gestão de Fontes e Cores
        font_path = "fonte_card.ttf"
        f_main = ImageFont.truetype(font_path, font_size_main) if os.path.exists(font_path) else ImageFont.load_default()
        f_sub = ImageFont.truetype(font_path, font_size_sub) if os.path.exists(font_path) else ImageFont.load_default()
        cor_texto = (26, 74, 94) # Azul Escuro Pastoral

        # 3. Renderização do Card Coletivo (Mês)
        if tipo == "MES" and isinstance(dados_niver, list):
            nomes_processados = []
            for item in dados_niver:
                partes = str(item).split(" | ")
                if len(partes) == 3:
                    dia, papel, nome = partes
                    nomes_processados.append(f"{dia} - {papel} - {tratar_nome_curto(nome)}")
            
            texto_completo = "\n".join(nomes_processados)
            draw.multiline_text(
                (centro_x, centro_y), 
                texto_completo, 
                font=f_main, 
                fill=cor_texto, 
                align="center", 
                anchor="mm", 
                spacing=15
            )
        
        # 4. Renderização do Card Individual (Dia)
        else:
            # Desmembramento do dado (Formato: "DIA | PAPEL | NOME")
            partes = str(dados_niver).split(" | ")
            if len(partes) == 3:
                dia_v, papel_v, nome_v = partes[0], partes[1], partes[2]
                mes_v = MESES_EXTENSO[hoje.month]
            else:
                # Fallback para o botão "Gerar Card" direto do Dashboard
                dia_v = str(hoje.day)
                papel_v = "CATEQUIZANDO"
                nome_v = str(dados_niver)
                mes_v = MESES_EXTENSO[hoje.month]

            # Linha Principal (F50)
            linha1 = f"DIA {dia_v} - {papel_v} - {tratar_nome_curto(nome_v)}"
            # Linha de Data (F35)
            linha2 = f"{dia_v} DE {mes_v}"

            # Desenho com anchor="mm" para centralização geométrica perfeita
            draw.text((centro_x, centro_y - 25), linha1, font=f_main, fill=cor_texto, anchor="mm")
            draw.text((centro_x, centro_y + 45), linha2, font=f_sub, fill=cor_texto, anchor="mm")

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
        # Ajuste de posição e tamanho para não cortar na margem
        pdf.image("logo.png", 10, 10, 25)
    
    # Tradução da Data para Português
    hoje = datetime.now(timezone.utc) + timedelta(hours=-3)
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
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
    
    # Margem de segurança de 20 unidades para não sobrepor a logo
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
    """Gera ficha individual em PDF."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf)
    _desenhar_corpo_ficha(pdf, dados)
    return finalizar_pdf(pdf)

def gerar_fichas_turma_completa(nome_turma, df_alunos):
    """Gera um PDF único com todas as fichas de uma determinada turma."""
    if df_alunos.empty:
        return None
    pdf = FPDF()
    for _, row in df_alunos.iterrows():
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf)
        _desenhar_corpo_ficha(pdf, row.to_dict())
    return finalizar_pdf(pdf)

def gerar_fichas_paroquia_total(df_catequizandos):
    """Gera um PDF único com as fichas de inscrição de TODOS os catequizandos da paróquia."""
    if df_catequizandos.empty:
        return None
    pdf = FPDF()
    # Ordenação alfabética facilitando a entrega física por turma
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
    """Gera currículo ministerial de um catequista individual."""
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
    """Gera o PDF em lote para toda a equipe catequética com correção sintática crítica."""
    if df_equipe.empty:
        return None
    pdf = FPDF()
    for _, u in df_equipe.iterrows():
        forms_participadas = pd.DataFrame()
        if not df_pres_form.empty and not df_formacoes.empty:
            minhas_forms = df_pres_form[df_pres_form['email_participante'] == u['email']]
            if not minhas_forms.empty:
                forms_participadas = minhas_forms.merge(df_formacoes, on='id_formacao', how='inner')
        
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf, titulo="FICHA DO CATEQUISTA", etapa="EQUIPE")
        
        # 1. Identificação
        pdf.set_fill_color(65, 123, 153)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 7, limpar_texto("1. DADOS PESSOAIS E CONTATO"), ln=True, fill=True, align='C')
        
        pdf.set_text_color(0, 0, 0)
        y = pdf.get_y() + 2
        desenhar_campo_box(pdf, "Nome Completo:", u.get('nome', ''), 10, y, 135)
        desenhar_campo_box(pdf, "Nascimento:", formatar_data_br(u.get('data_nascimento', '')), 150, y, 45)
        
        y += 14
        desenhar_campo_box(pdf, "E-mail:", u.get('email', ''), 10, y, 110)
        desenhar_campo_box(pdf, "Telefone:", u.get('telefone', ''), 125, y, 75)
        
        # 2. Vida Ministerial (COM CORREÇÃO DE SINTAXE)
        pdf.set_y(y + 16)
        pdf.set_fill_color(65, 123, 153)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, limpar_texto("2. VIDA MINISTERIAL E SACRAMENTAL"), ln=True, fill=True, align='C')
        
        pdf.set_text_color(0, 0, 0)
        y = pdf.get_y() + 2
        
        # Chamadas Corrigidas: Removidos parênteses redundantes que causavam SyntaxError
        desenhar_campo_box(pdf, "Início Catequese:", formatar_data_br(u.get('data_inicio_catequese', '')), 10, y, 45)
        desenhar_campo_box(pdf, "Batismo:", formatar_data_br(u.get('data_batismo', '')), 58, y, 45)
        desenhar_campo_box(pdf, "Eucaristia:", formatar_data_br(u.get('data_eucaristia', '')), 106, y, 45)
        desenhar_campo_box(pdf, "Crisma:", formatar_data_br(u.get('data_crisma', '')), 154, y, 46)
        
        # 3. Histórico de Formação
        pdf.set_y(y + 16)
        pdf.set_fill_color(65, 123, 153)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, limpar_texto("3. HISTÓRICO DE FORMAÇÃO CONTINUADA"), ln=True, fill=True, align='C')
        
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(30, 7, "Data", border=1, fill=True, align='C')
        pdf.cell(100, 7, "Tema", border=1, fill=True)
        pdf.cell(60, 7, "Formador", border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("helvetica", "", 8)
        if not forms_participadas.empty:
            for _, f in forms_participadas.iterrows():
                pdf.cell(30, 6, formatar_data_br(f['data']), border=1, align='C')
                pdf.cell(100, 6, limpar_texto(f['tema']), border=1)
                pdf.cell(60, 6, limpar_texto(f['formador']), border=1)
                pdf.ln()
        else:
            pdf.cell(190, 6, "Nenhuma formação registrada.", border=1, align='C', ln=True)

        # Declaração e Compromisso
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(224, 61, 17)
        pdf.cell(0, 6, limpar_texto("Declaração de Veracidade e Compromisso"), ln=True)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        declara = (f"Eu, {u.get('nome', '')}, declaro que as informações acima prestadas são verdadeiras e assumo o compromisso "
                   f"de zelar pelas diretrizes da Pastoral da Catequese da Paróquia Nossa Senhora de Fátima.")
        pdf.multi_cell(0, 5, limpar_texto(declara))
            
        # Assinaturas
        pdf.ln(10)
        y_ass = pdf.get_y()
        pdf.line(15, y_ass, 95, y_ass)
        pdf.line(115, y_ass, 195, y_ass)
        pdf.set_xy(15, y_ass + 1)
        pdf.set_font("helvetica", "B", 8)
        pdf.cell(80, 5, "Assinatura do Catequista", align='C')
        pdf.set_xy(115, y_ass + 1)
        pdf.cell(80, 5, "Assinatura do Coordenador", align='C')

    return finalizar_pdf(pdf)

# ==============================================================================
# 7. GESTÃO FAMILIAR (RELATÓRIO DE VISITAÇÃO E TERMO DE SAÍDA)
# ==============================================================================

def gerar_relatorio_familia_pdf(dados_familia, filhos_lista):
    """Gera ficha de visitação com o relato pastoral integral da 30ª coluna (AD)."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "FICHA DE VISITAÇÃO PASTORAL / FAMILIAR")
    
    # Núcleo Familiar
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, limpar_texto("1. NÚCLEO FAMILIAR (PAIS E RESPONSÁVEIS)"), ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Mãe:", dados_familia.get('nome_mae', 'N/A'), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados_familia.get('profissao_mae','')} / {dados_familia.get('tel_mae','')}", 125, y, 75)
    
    y += 14
    desenhar_campo_box(pdf, "Pai:", dados_familia.get('nome_pai', 'N/A'), 10, y, 110)
    desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados_familia.get('profissao_pai','')} / {dados_familia.get('tel_pai','')}", 125, y, 75)
    
    y += 14
    desenhar_campo_box(pdf, "Estado Civil dos Pais:", dados_familia.get('est_civil_pais', 'N/A'), 10, y, 90)
    desenhar_campo_box(pdf, "Sacramentos dos Pais:", dados_familia.get('sac_pais', 'N/A'), 105, y, 95)
    
    # Filhos Matriculados
    pdf.set_y(y + 16)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, limpar_texto("2. FILHOS MATRICULADOS NA CATEQUESE"), ln=True, fill=True)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Nome do Catequizando", border=1, fill=True)
    pdf.cell(60, 7, "Turma / Etapa Atual", border=1, fill=True)
    pdf.cell(50, 7, "Status", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    for f in filhos_lista:
        pdf.cell(80, 7, limpar_texto(f['nome']), border=1)
        pdf.cell(60, 7, limpar_texto(f['etapa']), border=1)
        pdf.cell(50, 7, limpar_texto(f['status']), border=1, align='C')
        pdf.ln()
    
    # Espaço para Relato Pastoral
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 7, "Relato da Visita e Necessidades da Família:", ln=True)
    
    relato_texto = dados_familia.get('obs_pastoral_familia', 'Nenhum relato registrado até o momento.')
    if relato_texto == "N/A" or not relato_texto:
        relato_texto = "Espaço reservado para anotações detalhadas de visita pastoral."
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_fill_color(248, 249, 240)
    pdf.multi_cell(190, 6, limpar_texto(relato_texto), border=1, fill=True)
    
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Documento de uso interno exclusivo da coordenação e pároco. Contém dados sensíveis protegidos por lei.")
    
    return finalizar_pdf(pdf)

def gerar_termo_saida_pdf(dados_cat, dados_turma, nome_responsavel_escolhido):
    """Gera o Termo de Autorização de Saída com layout ajustado e data em PT-BR."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "TERMO DE AUTORIZAÇÃO PARA SAÍDA")
    
    # Fundo Creme Estilizado
    pdf.set_fill_color(248, 249, 240)
    pdf.rect(10, 50, 190, 230, 'F')
    
    pdf.set_xy(10, 55)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(65, 123, 153) # Azul Paroquial
    pdf.cell(190, 10, limpar_texto("AUTORIZAÇÃO PARA SAÍDA SEM O RESPONSÁVEL"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    # Mapeamento de Dados para o texto dinâmico
    nome_cat = dados_cat.get('nome_completo', '__________________________')
    etapa = dados_cat.get('etapa', '__________')
    catequistas = dados_turma.get('catequista_responsavel', '__________________________')
    endereco = dados_cat.get('endereco_completo', '__________________________')
    
    corpo_texto = (
        f"Eu, {nome_responsavel_escolhido}, na condição de responsável legal pelo(a) "
        f"catequizando(a) {nome_cat}, inscrita(o) na {etapa}, com os/as "
        f"catequistas {catequistas}, autorizo a sua saída sozinho(a), no horário de encerramento "
        f"do encontro. Ciente que, assumo quaisquer riscos que possam ocorrer do trajeto "
        f"da Paróquia até a residência em: {endereco}."
    )
    
    pdf.set_x(15)
    pdf.multi_cell(180, 8, limpar_texto(corpo_texto), align='J')
    
    pdf.ln(10)
    # Formatação de Data Paroquial
    hoje = datetime.now(timezone.utc) + timedelta(hours=-3)
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    data_formatada = f"{hoje.day} de {meses_pt[hoje.month-1]} de {hoje.year}"
    
    pdf.set_x(15)
    pdf.cell(0, 10, limpar_texto(f"Itabuna (BA), {data_formatada}."), ln=True)
    
    # Campo de Assinatura
    pdf.ln(15)
    y_ass = pdf.get_y()
    pdf.line(55, y_ass, 155, y_ass)
    pdf.set_xy(55, y_ass + 1)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(100, 5, limpar_texto("Assinatura do Responsável Legal"), align='C', ln=True)
    
    # Observações de Segurança
    pdf.ln(10)
    pdf.set_x(15)
    pdf.set_fill_color(255, 240, 240) # Fundo Alerta
    pdf.set_draw_color(224, 61, 17) # Borda Alerta
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(224, 61, 17)
    obs_info = (
        "Obs.: Lembramos que o (a) catequizando (a) que não tiver o termo de autorização de saída preenchido "
        "só poderá sair do local da catequese com o responsável nominalmente identificado no cadastro."
    )
    pdf.multi_cell(180, 5, limpar_texto(obs_info), border=1, fill=True, align='L')
    
    # Informativo Complementar de Vínculo
    pdf.ln(10)
    pdf.set_draw_color(65, 123, 153)
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
    pdf.cell(0, 8, limpar_texto("Se sim, informe quem: ___________________________________________________________"), ln=True)
    
    # Segunda Assinatura de Ciência
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

def gerar_relatorio_diocesano_v4(dados_censo, equipe_stats, sac_ano, sac_censo, logistica_lista, formacoes_lista, analise_ia):
    """Gera o Relatório Estatístico Diocesano integral v4."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO DIOCESANO")
    
    # Bloco 1: Censo
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. CENSO POPULACIONAL E ESTRUTURAL"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    desenhar_campo_box(pdf, "Total Catequizandos", str(dados_censo.get('total_cat', '0')), 10, y, 45)
    desenhar_campo_box(pdf, "Turmas Infantil/Juv.", str(dados_censo.get('t_infantil', '0')), 58, y, 45)
    desenhar_campo_box(pdf, "Turmas Jovens/Adultos", str(dados_censo.get('t_adultos', '0')), 106, y, 45)
    desenhar_campo_box(pdf, "Equipe Catequética", str(dados_censo.get('total_equipe', '0')), 154, y, 46)
    
    # Bloco 2: Qualificação Fé
    pdf.ln(18)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. QUALIFICAÇÃO SACRAMENTAL DA EQUIPE"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(100, 7, "Indicador de Fé", border=1, fill=True)
    pdf.cell(45, 7, "Quantidade", border=1, fill=True, align='C')
    pdf.cell(45, 7, "Percentual", border=1, fill=True, align='C')
    pdf.ln()
    
    total_equipe_val = int(dados_censo.get('total_equipe', 1))
    indicadores_equipe = [
        ("Batismo", equipe_stats.get('bat', 0)),
        ("Eucaristia", equipe_stats.get('euca', 0)),
        ("Crisma", equipe_stats.get('crisma', 0)),
        ("Ministros de Catequese", equipe_stats.get('ministros', 0))
    ]
    
    for desc, qtd in indicadores_equipe:
        percentual_calc = (int(qtd)/total_equipe_val)*100 if total_equipe_val > 0 else 0
        pdf.cell(100, 7, limpar_texto(f" {desc}"), border=1)
        pdf.cell(45, 7, str(qtd), border=1, align='C')
        pdf.cell(45, 7, f"{percentual_calc:.1f}%", border=1, align='C')
        pdf.ln()
        
    # Bloco 3: IA Auditor
    pdf.ln(5)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. PARECER TÉCNICO DA AUDITORIA"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_v3(turmas_detalhadas, totais_gerais, analise_ia):
    """Gera o relatório pastoral analítico com indicadores de cada turma."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO PASTORAL ANALÍTICO")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("DESEMPENHO POR TURMA E ETAPA"), ln=True, fill=True, align='C')
    
    # Tabela de Indicadores por Turma
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Turma", border=1, fill=True)
    pdf.cell(25, 7, "Batizados", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Eucaristia", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Crisma", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Freq.", border=1, fill=True, align='C')
    pdf.cell(20, 7, "Total", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    for t in turmas_detalhadas:
        pdf.cell(70, 7, limpar_texto(t['nome']), border=1)
        pdf.cell(25, 7, str(t['batizados']), border=1, align='C')
        pdf.cell(25, 7, str(t['eucaristia']), border=1, align='C')
        pdf.cell(25, 7, str(t['crisma']), border=1, align='C')
        pdf.cell(25, 7, f"{t['frequencia']}%", border=1, align='C')
        pdf.cell(20, 7, str(t['total']), border=1, align='C')
        pdf.ln()
        
    # Análise de IA sobre os dados acima
    pdf.ln(5)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("ANÁLISE DE ENGAJAMENTO E EVASÃO"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_v2(stats_gerais, analise_turmas, impedimentos_lista, analise_ia):
    """Gera auditoria técnica de sacramentos e impedimentos canônicos."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "AUDITORIA SACRAMENTAL E CENSO DE IVC")
    
    # 1. Quadro Geral
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. QUADRO GERAL DE SACRAMENTALIZAÇÃO"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 7, "Sacramento", border=1, fill=True)
    pdf.cell(70, 7, "Infantil / Juvenil", border=1, fill=True, align='C')
    pdf.cell(70, 7, "Jovens / Adultos", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    dados_sacramentais = [
        ("BATISMO", stats_gerais['bat_k'], stats_gerais['bat_a']),
        ("EUCARISTIA", stats_gerais['euca_k'], stats_gerais['euca_a']),
        ("CRISMA", "N/A", stats_gerais['crisma_a'])
    ]
    
    for nome_s, k_val, a_val in dados_sacramentais:
        pdf.cell(50, 7, f" {nome_s}", border=1)
        pdf.cell(70, 7, str(k_val), border=1, align='C')
        pdf.cell(70, 7, str(a_val), border=1, align='C')
        pdf.ln()
        
    # 2. Impedimentos Canônicos
    pdf.ln(5)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. DIAGNÓSTICO DE IMPEDIMENTOS CANÔNICOS"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 7, "Catequizando", border=1, fill=True)
    pdf.cell(50, 7, "Turma", border=1, fill=True)
    pdf.cell(70, 7, "Situação Matrimonial / Sacramental", border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if impedimentos_lista:
        for imp_item in impedimentos_lista:
            pdf.cell(70, 6, limpar_texto(imp_item['nome']), border=1)
            pdf.cell(50, 6, limpar_texto(imp_item['turma']), border=1)
            pdf.cell(70, 6, limpar_texto(imp_item['situacao']), border=1)
            pdf.ln()
    else:
        pdf.cell(190, 6, "Nenhum impedimento crítico registrado.", border=1, align='C', ln=True)
        
    # 3. Parecer IA
    pdf.ln(5)
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. PARECER DO AUDITOR IA"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

# ==============================================================================
# 9. UTILITÁRIOS PASTORAIS E CENSO (ANIVERSARIANTES E STATUS)
# ==============================================================================

def sugerir_etapa(data_nascimento):
    """Sugere a etapa de catequese com base na idade."""
    idade_sugerida = calcular_idade(data_nascimento)
    if idade_sugerida <= 6: return "PRÉ"
    elif idade_sugerida <= 8: return "PRIMEIRA ETAPA"
    elif idade_sugerida <= 10: return "SEGUNDA ETAPA"
    elif idade_sugerida <= 13: return "TERCEIRA ETAPA"
    return "ADULTOS"

def eh_aniversariante_da_semana(data_nasc_str):
    """Verifica se o catequizando faz aniversário nos próximos 7 dias."""
    try:
        d_format = formatar_data_br(data_nasc_str)
        if d_format == "N/A":
            return False
        nasc_date = datetime.strptime(d_format, "%d/%m/%Y").date()
        hoje_date = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        nasc_este_ano = nasc_date.replace(year=hoje_date.year)
        diferenca_dias = (nasc_este_ano - hoje_date).days
        return 0 <= diferenca_dias <= 7
    except:
        return False

def converter_para_data(valor_str):
    """Facilitador de conversão para Streamlit widgets."""
    if not valor_str or str(valor_str).strip() in ["None", "", "N/A"]:
        return date.today()
    try:
        return datetime.strptime(formatar_data_br(valor_str), "%d/%m/%Y").date()
    except:
        return date.today()

def verificar_status_ministerial(data_inicio, d_batismo, d_euca, d_crisma, d_ministerio):
    """Verifica aptidão ministerial conforme regras diocesanas."""
    if d_ministerio and str(d_ministerio).strip() not in ["", "N/A", "None"]:
        return "MINISTRO", 0 
    try:
        hoje_pastoral = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
        inicio_pastoral = datetime.strptime(formatar_data_br(data_inicio), "%d/%m/%Y").date()
        anos_caminhada = hoje_pastoral.year - inicio_pastoral.year
        tem_sacramentos = all([str(x).strip() not in ["", "N/A", "None"] for x in [d_batismo, d_euca, d_crisma]])
        if anos_caminhada >= 5 and tem_sacramentos:
            return "APTO", anos_caminhada
        return "EM_CAMINHADA", anos_caminhada
    except:
        return "EM_CAMINHADA", 0

def obter_aniversariantes_hoje(df_cat, df_usuarios):
    """Identifica aniversariantes do dia na base de catequizandos e equipe."""
    hoje_local = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista_niver = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            data_str = formatar_data_br(r['data_nascimento'])
            if data_str != "N/A":
                dt_obj = datetime.strptime(data_str, "%d/%m/%Y")
                if dt_obj.day == hoje_local.day and dt_obj.month == hoje_local.month:
                    lista_niver.append(f"😇 Catequizando: **{r['nome_completo']}**")
    if not df_usuarios.empty:
        for _, u in df_usuarios.drop_duplicates(subset=['nome']).iterrows():
            data_str_u = formatar_data_br(u.get('data_nascimento', ''))
            if data_str_u != "N/A":
                dt_obj_u = datetime.strptime(data_str_u, "%d/%m/%Y")
                if dt_obj_u.day == hoje_local.day and dt_obj_u.month == hoje_local.month:
                    lista_niver.append(f"🛡️ Catequista: **{u['nome']}**")
    return lista_niver

def obter_aniversariantes_mes_unificado(df_cat, df_usuarios):
    """Consolida aniversariantes do mês para o card coletivo."""
    hoje_local = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    consolidado = []
    if not df_cat.empty:
        for _, r in df_cat.drop_duplicates(subset=['nome_completo']).iterrows():
            dt_s = formatar_data_br(r['data_nascimento'])
            if dt_s != "N/A":
                dt_o = datetime.strptime(dt_s, "%d/%m/%Y")
                if dt_o.month == hoje_local.month:
                    consolidado.append({'dia': dt_o.day, 'nome': r['nome_completo'], 'tipo': 'CATEQUIZANDO', 'info': r['etapa']})
    if not df_usuarios.empty:
        for _, u in df_usuarios.drop_duplicates(subset=['nome']).iterrows():
            dt_s_u = formatar_data_br(u.get('data_nascimento', ''))
            if dt_s_u != "N/A":
                dt_o_u = datetime.strptime(dt_s_u, "%d/%m/%Y")
                if dt_o_u.month == hoje_local.month:
                    consolidado.append({'dia': dt_o_u.day, 'nome': u['nome'], 'tipo': 'CATEQUISTA', 'info': 'EQUIPE'})
    return pd.DataFrame(consolidado).sort_values(by='dia') if consolidado else pd.DataFrame()

def obter_aniversariantes_mes(df_cat):
    """Versão filtrada apenas para catequizandos (Uso em Minha Turma)."""
    if df_cat.empty:
        return pd.DataFrame()
    hoje_local = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    lista_t = []
    for _, r in df_cat.iterrows():
        dt_st = formatar_data_br(r['data_nascimento'])
        if dt_st != "N/A":
            dt_ot = datetime.strptime(dt_st, "%d/%m/%Y")
            if dt_ot.month == hoje_local.month:
                lista_t.append({'nome_completo': r['nome_completo'], 'dia': dt_ot.day, 'etapa': r['etapa']})
    return pd.DataFrame(lista_t).sort_values(by='dia') if lista_t else pd.DataFrame()

# ==============================================================================
# 10. PROCESSAMENTO EM LOTE E AUDITORIA INTEGRAL (DOSSIÊS)
# ==============================================================================

def gerar_relatorio_local_turma_v2(nome_turma, metricas, listas, analise_ia):
    """Gera o Relatório de Inteligência Pastoral específico de uma turma."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"AUDITORIA PASTORAL: {nome_turma}")
    
    # 1. Indicadores Estruturais
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. INDICADORES ESTRUTURAIS E ADESÃO"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 2
    
    desenhar_campo_box(pdf, "Catequistas na Turma", str(metricas['qtd_catequistas']), 10, y, 45)
    desenhar_campo_box(pdf, "Total Catequizandos", str(metricas['qtd_cat']), 58, y, 45)
    desenhar_campo_box(pdf, "Frequência Global", f"{metricas['freq_global']}%", 106, y, 45)
    desenhar_campo_box(pdf, "Idade Média", f"{metricas['idade_media']} anos", 154, y, 46)
    pdf.ln(18)

    # 2. Taxa Mensal de Presença
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. EVOLUÇÃO DA PRESENÇA POR MÊS"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(95, 7, "Mês / Ano", border=1, fill=True, align='C')
    pdf.cell(95, 7, "Taxa de Presença", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 9)
    for mes_item in metricas['freq_mensal']:
        pdf.cell(95, 6, limpar_texto(mes_item['mes']), border=1, align='C')
        pdf.cell(95, 6, f"{mes_item['taxa']}%", border=1, align='C')
        pdf.ln()
    pdf.ln(5)

    # 3. Lista de Evasão
    pdf.set_fill_color(224, 61, 17)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. LISTA NOMINAL E ALERTA DE EVASÃO"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(120, 7, "Nome do Catequizando", border=1, fill=True)
    pdf.cell(70, 7, "Status / Faltas", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    for cat_eva in listas['geral']:
        if cat_eva['faltas'] >= 2:
            pdf.set_text_color(224, 61, 17) # Destaque em Vermelho para evasão
        else:
            pdf.set_text_color(0, 0, 0)
        info_f = f"ATIVO ({cat_eva['faltas']} faltas)" if cat_eva['faltas'] > 0 else "ATIVO (100% Freq.)"
        pdf.cell(120, 6, limpar_texto(cat_eva['nome']), border=1)
        pdf.cell(70, 6, limpar_texto(info_f), border=1, align='C')
        pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # 4. Histórico Sacramental
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("4. SACRAMENTOS RECEBIDOS (REGISTRO PAROQUIAL)"), ln=True, fill=True, align='C')
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 7, "Nome", border=1, fill=True)
    pdf.cell(50, 7, "Sacramento", border=1, fill=True, align='C')
    pdf.cell(60, 7, "Data do Registro", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", "", 8)
    if listas['sac_recebidos']:
        for sac_item in listas['sac_recebidos']:
            pdf.cell(80, 6, limpar_texto(sac_item['nome']), border=1)
            pdf.cell(50, 6, limpar_texto(sac_item['tipo']), border=1, align='C')
            pdf.cell(60, 6, formatar_data_br(sac_item['data']), border=1, align='C')
            pdf.ln()
    else:
        pdf.cell(190, 6, "Nenhum sacramento registrado para esta turma no itinerário vigente.", border=1, align='C', ln=True)

    # 5. Parecer Técnico
    pdf.ln(5)
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("5. PARECER TÉCNICO E ORIENTAÇÃO PASTORAL"), ln=True, fill=True, align='C')
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))

    return finalizar_pdf(pdf)

def gerar_auditoria_lote_completa(df_turmas, df_cat, df_pres, df_recebidos):
    """Gera um Dossiê Paroquial contendo a auditoria completa de cada turma em sequência."""
    pdf = FPDF()
    col_id_catequizando = 'id_catequizando'
    
    for _, turma_row in df_turmas.iterrows():
        t_nome_lote = turma_row['nome_turma']
        alunos_turma_lote = df_cat[df_cat['etapa'] == t_nome_lote]
        
        if not alunos_turma_lote.empty:
            pdf.add_page()
            adicionar_cabecalho_diocesano(pdf, f"AUDITORIA INTEGRAL: {t_nome_lote}")
            
            # --- 1. Indicadores Estruturais ---
            pres_turma_lote = df_pres[df_pres['id_turma'] == t_nome_lote] if not df_pres.empty else pd.DataFrame()
            f_global_lote = 0.0
            
            if not pres_turma_lote.empty:
                pres_turma_lote['status_num'] = pres_turma_lote['status'].apply(lambda x: 1 if x == 'PRESENTE' else 0)
                f_global_lote = round(pres_turma_lote['status_num'].mean() * 100, 1)

            idades_lote = [calcular_idade(nas) for nas in alunos_turma_lote['data_nascimento'].tolist()]
            i_media_lote = round(sum(idades_lote)/len(idades_lote), 1) if idades_lote else 0
            q_catequistas_lote = len(str(turma_row['catequista_responsavel']).split(','))

            pdf.set_fill_color(65, 123, 153)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto("1. INDICADORES ESTRUTURAIS"), ln=True, fill=True, align='C')
            
            pdf.set_text_color(0, 0, 0)
            y_coord = pdf.get_y() + 2
            desenhar_campo_box(pdf, "Catequistas", str(q_catequistas_lote), 10, y_coord, 45)
            desenhar_campo_box(pdf, "Catequizandos", str(len(alunos_turma_lote)), 58, y_coord, 45)
            desenhar_campo_box(pdf, "Frequência Global", f"{f_global_lote}%", 106, y_coord, 45)
            desenhar_campo_box(pdf, "Idade Média", f"{i_media_lote} anos", 154, y_coord, 46)
            pdf.ln(18)

            # --- 2. Lista Nominal ---
            pdf.set_fill_color(224, 61, 17)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, limpar_texto("2. LISTA NOMINAL E ALERTA DE EVASÃO"), ln=True, fill=True, align='C')
            
            pdf.set_font("helvetica", "B", 8)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(120, 7, "Nome do Catequizando", border=1, fill=True)
            pdf.cell(70, 7, "Status / Faltas", border=1, fill=True, align='C')
            pdf.ln()
            
            pdf.set_font("helvetica", "", 8)
            for _, r_lote in alunos_turma_lote.iterrows():
                f_count = 0
                if not pres_turma_lote.empty and col_id_catequizando in pres_turma_lote.columns:
                    f_count = len(pres_turma_lote[(pres_turma_lote[col_id_catequizando] == r_lote[col_id_catequizando]) & (pres_turma_lote['status'] == 'AUSENTE')])
                if f_count >= 2:
                    pdf.set_text_color(224, 61, 17)
                else:
                    pdf.set_text_color(0, 0, 0)
                info_texto_lote = f"ATIVO ({f_count} faltas)" if f_count > 0 else "ATIVO (100% Freq.)"
                pdf.cell(120, 6, limpar_texto(r_lote['nome_completo']), border=1)
                pdf.cell(70, 6, limpar_texto(info_texto_lote), border=1, align='C')
                pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)

            # --- 3. Sacramentos ---
            pdf.set_fill_color(65, 123, 153)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 8, limpar_texto("3. SACRAMENTOS RECEBIDOS"), ln=True, fill=True, align='C')
            
            pdf.set_font("helvetica", "B", 8)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(80, 7, "Nome", border=1, fill=True)
            pdf.cell(50, 7, "Sacramento", border=1, fill=True, align='C')
            pdf.cell(60, 7, "Data", border=1, fill=True, align='C')
            pdf.ln()
            
            pdf.set_font("helvetica", "", 8)
            if not df_recebidos.empty and col_id_catequizando in df_recebidos.columns:
                sac_turma_lote = df_recebidos[df_recebidos[col_id_catequizando].isin(alunos_turma_lote['id_catequizando'].tolist())]
                if not sac_turma_lote.empty:
                    for _, s_lote in sac_turma_lote.iterrows():
                        pdf.cell(80, 6, limpar_texto(s_lote.get('nome', 'N/A')), border=1)
                        pdf.cell(50, 6, limpar_texto(s_lote.get('tipo', 'N/A')), border=1, align='C')
                        pdf.cell(60, 6, formatar_data_br(s_lote.get('data', 'N/A')), border=1, align='C')
                        pdf.ln()
                else:
                    pdf.cell(190, 6, "Nenhum sacramento registrado para esta turma.", border=1, align='C', ln=True)
            
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

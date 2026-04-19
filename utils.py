# ==============================================================================
# ARQUIVO: utils.py
# VERSÃO: 6.0.0 - CLEAN CODE E OTIMIZAÇÃO DE MEMÓRIA
# MISSÃO: Motor de Documentação, Auditoria Sacramental e Identidade Visual.
# ==============================================================================

from datetime import date, datetime, timedelta, timezone
import datetime as dt_module # Alias crítico para evitar AttributeError
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
    # Uso do dt_module para evitar conflito de nomes
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    try:
        d_str = formatar_data_br(data_nascimento)
        dt = dt_module.datetime.strptime(d_str, "%d/%m/%Y").date()
        idade = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
        return idade if idade >= 0 else 0
    except: return 0

def limpar_texto(texto):
    """Remove artefatos de Markdown e Emojis, garantindo compatibilidade com Latin-1."""
    if not texto: return ""
    
    # 1. Remove Markdown
    texto_limpo = str(texto).replace("**", "").replace("* ", " - ").replace("*", "")
    
    # 2. Remove Emojis e caracteres especiais não suportados pelo Latin-1
    # Substitui caracteres que não são ASCII por um espaço ou caractere seguro
    texto_limpo = texto_limpo.encode('latin-1', 'ignore').decode('latin-1')
    
    # 3. Substituições manuais de segurança para símbolos comuns
    texto_limpo = texto_limpo.replace("✅", "OK").replace("❌", "X").replace("⚠️", "!")
    
    return texto_limpo

def finalizar_pdf(pdf):
    """Finaliza a geração do PDF com tratamento de erro detalhado."""
    try:
        # O FPDF precisa que o buffer seja retornado como bytes
        # Se o PDF estiver vazio, o output pode falhar
        pdf_bytes = pdf.output(dest='S')
        if not pdf_bytes:
            st.error("Erro: O PDF gerado está vazio.")
            return b""
        return pdf_bytes.encode('latin-1')
    except Exception as e:
        st.error(f"Erro crítico ao finalizar PDF: {e}")
        return b""

def desenhar_campo_box(pdf, label, valor, x, y, w, h=7):
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
# 3. MOTOR DE CARDS DE ANIVERSÁRIO
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
        pdf.image("logo.png", 10, 10, 20) # Reduzido de 25 para 20
    
    hoje = datetime.now(timezone.utc) + timedelta(hours=-3)
    data_local = f"{hoje.day:02d} / {hoje.month:02d} / {hoje.year}"
    
    pdf.set_xy(35, 12) # Ajustado para acompanhar a logo menor
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153) 
    pdf.cell(100, 5, limpar_texto("Pastoral da Catequese Diocese de Itabuna-BA."), ln=False)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, limpar_texto(f"Data: {data_local}"), ln=True, align='R')
    
    pdf.set_x(35)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(100, 5, limpar_texto("Paróquia: Nossa Senhora de Fátima"), ln=True)
    
    pdf.ln(12) # Reduzido de 20 para 12
    
    if titulo:
        y_topo = pdf.get_y()
        pdf.set_fill_color(245, 245, 245)
        pdf.rect(10, y_topo, 190, 12, 'F') # Reduzido de 15 para 12
        pdf.rect(10, y_topo, 190, 12)
        pdf.set_xy(10, y_topo + 2)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(65, 123, 153)
        pdf.cell(190, 8, limpar_texto(titulo), align='C')
        pdf.ln(12) # Reduzido de 18 para 12
    else:
        pdf.ln(2) # Reduzido de 5 para 2

# ==============================================================================
# 5. GESTÃO DE FICHAS DE INSCRIÇÃO (CATEQUIZANDOS - 30 COLUNAS)
# ==============================================================================

def _desenhar_corpo_ficha(pdf, dados):
    """Desenha o corpo moderno da ficha de inscrição com herança de Turma."""
    from database import ler_aba 
    
    y_base = pdf.get_y()
    idade_real = calcular_idade(dados.get('data_nascimento', ''))
    is_adulto = idade_real >= 18
    
    # --- LÓGICA DE HERANÇA (TURNO E LOCAL) ---
    etapa_aluno = str(dados.get('etapa', '')).strip()
    turno_oficial = ""
    local_oficial = ""
    
    df_turmas = ler_aba("turmas")
    if not df_turmas.empty:
        turma_info = df_turmas[df_turmas['nome_turma'].str.strip() == etapa_aluno]
        if not turma_info.empty:
            turno_oficial = str(turma_info.iloc[0].get('turno', '')).upper()
            local_oficial = str(turma_info.iloc[0].get('local', '')).upper()
    
    if not turno_oficial or turno_oficial == "N/A":
        turno_oficial = str(dados.get('turno', '')).upper()
    if not local_oficial or local_oficial == "N/A":
        local_oficial = str(dados.get('local_encontro', '')).upper()

    mark_m = "X" if "MANHÃ" in turno_oficial or turno_oficial == "M" else " "
    mark_t = "X" if "TARDE" in turno_oficial or turno_oficial == "T" else " "
    mark_n = "X" if "NOITE" in turno_oficial or turno_oficial == "N" else " "
    
    # --- CABEÇALHO DA FICHA (BOX SUPERIOR) ---
    pdf.set_fill_color(240, 242, 246)
    pdf.rect(10, y_base, 190, 22, 'F') # Reduzido de 25 para 22
    pdf.rect(10, y_base, 190, 22)
    
    pdf.set_xy(15, y_base + 3)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(65, 123, 153) 
    pdf.cell(130, 6, limpar_texto("FICHA DE INSCRIÇÃO CATEQUÉTICA"), ln=0)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 6, limpar_texto(f"ANO LETIVO: {date.today().year}"), ln=1, align='R')
    
    pdf.set_x(15)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(130, 6, limpar_texto(f"ETAPA: {etapa_aluno if etapa_aluno else 'N/A'}"), ln=0)
    
    pdf.set_font("helvetica", "", 9)
    pdf.cell(50, 6, limpar_texto(f"TURNO: ( {mark_m} ) M  ( {mark_t} ) T  ( {mark_n} ) N"), ln=1, align='R')
    
    pdf.set_x(15)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(100, 100, 100) 
    pdf.cell(130, 5, limpar_texto(f"LOCAL: {local_oficial if local_oficial else 'NÃO DEFINIDO'}"), ln=1)

    # --- SEÇÃO 1: IDENTIFICAÇÃO ---
    pdf.set_y(y_base + 24) # Reduzido de 28 para 24
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 6, limpar_texto("  1. IDENTIFICAÇÃO DO CATEQUIZANDO"), ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    y = pdf.get_y() + 1
    desenhar_campo_box(pdf, "Nome Completo:", dados.get('nome_completo', ''), 10, y, 190)
    
    y += 12 # Reduzido de 14 para 12
    desenhar_campo_box(pdf, "Data de Nascimento:", formatar_data_br(dados.get('data_nascimento', '')), 10, y, 45)
    desenhar_campo_box(pdf, "Idade:", f"{idade_real} anos", 60, y, 25)
    
    pdf.set_xy(90, y + 3)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(20, 4, "Batizado:", ln=0)
    marcar_opcao(pdf, "Sim", dados.get('batizado_sn') == 'SIM', 110, y + 3)
    marcar_opcao(pdf, "Não", dados.get('batizado_sn') == 'NÃO', 130, y + 3)
    
    y += 12
    desenhar_campo_box(pdf, "Endereço Residencial:", dados.get('endereco_completo', ''), 10, y, 190)
    
    y += 12
    desenhar_campo_box(pdf, "WhatsApp / Contato:", dados.get('contato_principal', ''), 10, y, 60)
    desenhar_campo_box(pdf, "Saúde (Medicamentos/Alergias):", dados.get('toma_medicamento_sn', 'NÃO'), 75, y, 60)
    # Novo campo para TGO
    desenhar_campo_box(pdf, "TGO/Neurodivergência (Laudo Exigido):", dados.get('tgo_sn', 'NÃO'), 140, y, 60)

    # --- SEÇÃO 2: FAMÍLIA OU EMERGÊNCIA ---
    pdf.set_y(y + 13) # Reduzido de 16 para 13
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    
    if is_adulto:
        pdf.cell(190, 6, limpar_texto("  2. CONTATO DE EMERGÊNCIA / VÍNCULO"), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        y = pdf.get_y() + 1
        desenhar_campo_box(pdf, "Nome do Contato:", dados.get('nome_responsavel', 'N/A'), 10, y, 110)
        desenhar_campo_box(pdf, "Vínculo / Telefone:", dados.get('obs_pastoral_familia', 'N/A'), 125, y, 75)
    else:
        pdf.cell(190, 6, limpar_texto("  2. FILIAÇÃO E RESPONSÁVEIS"), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        y = pdf.get_y() + 1
        desenhar_campo_box(pdf, "Nome da Mãe:", dados.get('nome_mae', 'N/A'), 10, y, 110)
        desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_mae','')} / {dados.get('tel_mae','')}", 125, y, 75)
        y += 12
        desenhar_campo_box(pdf, "Nome do Pai:", dados.get('nome_pai', 'N/A'), 10, y, 110)
        desenhar_campo_box(pdf, "Profissão/Tel:", f"{dados.get('profissao_pai','')} / {dados.get('tel_pai','')}", 125, y, 75)
        y += 12
        desenhar_campo_box(pdf, "Responsável Legal (Caso não more com pais):", dados.get('nome_responsavel', 'N/A'), 10, y, 190)

    # --- BUSCA INTELIGENTE DE DATAS DE SACRAMENTOS ---
    try:
        from database import ler_aba
        def get_dado_seguro(dados, idx):
            try:
                if isinstance(dados, dict):
                    keys = list(dados.keys())
                    if len(keys) > idx: return str(dados[keys[idx]])
                elif hasattr(dados, 'iloc'):
                    if len(dados) > idx: return str(dados.iloc[idx])
            except: pass
            return "N/A"
            
        d_bat = get_dado_seguro(dados, 30)
        d_euc = get_dado_seguro(dados, 31)
        d_cri = get_dado_seguro(dados, 32)
        paroq = get_dado_seguro(dados, 33)
        
        data_bat_pdf = d_bat if str(d_bat).strip() not in["N/A", "", "None"] else "Pendente"
        data_euc_pdf = d_euc if str(d_euc).strip() not in ["N/A", "", "None"] else "Pendente"
        data_cri_pdf = d_cri if str(d_cri).strip() not in ["N/A", "", "None"] else "Pendente"
        
        df_recebidos = ler_aba("sacramentos_recebidos")
        id_cat = str(dados.get('id_catequizando', ''))
        
        if not df_recebidos.empty and id_cat:
            rec_aluno = df_recebidos[df_recebidos.iloc[:, 1] == id_cat]
            for _, r in rec_aluno.iterrows():
                if str(r.iloc[3]).upper() == 'BATISMO': data_bat_pdf = formatar_data_br(r.iloc[4])
                if str(r.iloc[3]).upper() == 'EUCARISTIA': data_euc_pdf = formatar_data_br(r.iloc[4])
                if str(r.iloc[3]).upper() == 'CRISMA': data_cri_pdf = formatar_data_br(r.iloc[4])
                
        if data_bat_pdf == "Pendente" and str(dados.get('batizado_sn', '')).upper() == "SIM":
            data_bat_pdf = "Sim (Sem data)"
            
        paroq_val = str(paroq).strip()
        if paroq_val not in ["N/A", "", "None"]:
            if data_bat_pdf not in["Pendente", "---", "Sim (Sem data)"]: data_bat_pdf += f" ({paroq_val})"
            if data_euc_pdf not in ["Pendente", "---"]: data_euc_pdf += f" ({paroq_val})"
            if data_cri_pdf not in["Pendente", "---"]: data_cri_pdf += f" ({paroq_val})"

    except Exception as e:
        data_bat_pdf, data_euc_pdf, data_cri_pdf = "---", "---", "---"

    # --- SEÇÃO 3: VIDA ECLESIAL E DOCUMENTOS ---
    pdf.set_y(y + 13) 
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 6, limpar_texto("  3. VIDA ECLESIAL E DOCUMENTAÇÃO"), ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    y_ec = pdf.get_y() + 1
    
    # Sub-bloco: Sacramentos Realizados (Com Data) e Documentos Faltando
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(10, y_ec)
    pdf.cell(14, 5, "Batismo:", ln=0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(45, 5, limpar_texto(data_bat_pdf), ln=0)
    
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(18, 5, "Eucaristia:", ln=0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(45, 5, limpar_texto(data_euc_pdf), ln=0)

    pdf.set_font("helvetica", "B", 8)
    pdf.cell(14, 5, "Crisma:", ln=0)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(45, 5, limpar_texto(data_cri_pdf), ln=1)
    
    y_ec2 = pdf.get_y() + 1
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(10, y_ec2)
    pdf.cell(26, 5, "Faltando Docs:", ln=0)
    pdf.set_font("helvetica", "", 8)
    pdf.multi_cell(150, 5, limpar_texto(dados.get('doc_em_falta', 'NADA')), border=0, align='L')

    y_ec3 = pdf.get_y() + 1
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(10, y_ec3)
    pdf.cell(40, 5, "Participa de Grupo/Pastoral?", ln=0)
    marcar_opcao(pdf, "Sim", dados.get('participa_grupo') == 'SIM', 55, y_ec3)
    marcar_opcao(pdf, "Não", dados.get('participa_grupo') == 'NÃO', 75, y_ec3)
    
    # --- SEÇÃO 4: TERMO LGPD E ECA DIGITAL ---
    # BLINDAGEM VISUAL: Força o cursor a ficar exatamente 8mm abaixo da última linha para não atropelar a escrita
    pdf.set_y(y_ec3 + 8) 
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17) 
    pdf.cell(0, 5, limpar_texto("4. AUTORIZAÇÃO DE USO DE IMAGEM E VOZ (LGPD E ECA DIGITAL)"), ln=True)
    
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    nome_cat = dados.get('nome_completo', '________________')
    if not is_adulto:
        mae = str(dados.get('nome_mae', '')).strip()
        pai = str(dados.get('nome_pai', '')).strip()
        resp = f"{mae} e {pai}" if mae and pai else (mae or pai or "Responsável Legal")
        texto_lgpd = (f"Eu, {resp}, na qualidade de pai/mãe ou responsável pelo(a) catequizando(a): {nome_cat}, "
                      f"AUTORIZO o uso da publicação da imagem e voz do(a) meu (minha) filho(a) dos eventos realizados pela Pastoral da Catequese "
                      f"da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social da Pastoral ou da Paróquia, "
                      f"conforme determina o artigo 5º, inciso X da Constituição Federal, da Lei de Proteção de Dados (LGPD) - 13.709/2018 e do "
                      f"ECA Digital (Lei nº 15.211/2025) em vigor desde 17 de março de 2026, que regula as atividades de tratamento de dados pessoais "
                      f"colhidos no momento da inscrição para o(s) sacramento(s) da Iniciação à Vida Cristã com Inspiração Catecumenal.")
    else:
        texto_lgpd = (f"Eu, {nome_cat}, na qualidade de catequizando(a) maior de idade, AUTORIZO o uso da publicação da minha imagem e voz "
                      f"dos eventos realizados pela Pastoral da Catequese da Paróquia Nossa Senhora de Fátima através de fotos ou vídeos na rede social "
                      f"da Pastoral ou da Paróquia, conforme determina o artigo 5º, inciso X da Constituição Federal e da Lei de Proteção de Dados (LGPD) - 13.709/2018.")
        
    pdf.multi_cell(0, 4, limpar_texto(texto_lgpd), align='J')
    
    pdf.ln(1)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(0, 4, limpar_texto("MANIFESTAÇÃO DE VONTADE:"), ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(0, 4, limpar_texto("(   ) AUTORIZO o uso de imagem e voz nos canais oficiais da Catequese/Igreja."), ln=True)
    pdf.cell(0, 4, limpar_texto("(   ) NÃO AUTORIZO o uso de imagem e voz nos canais oficiais da Catequese/Igreja."), ln=True)
    
    pdf.ln(1)
    pdf.set_font("helvetica", "B", 8)
    pdf.write(4, limpar_texto("Observação: "))
    pdf.set_font("helvetica", "", 8)
    pdf.write(4, limpar_texto("A recusa de autorização será integralmente respeitada, sem qualquer prejuízo à participação nas atividades.\n"))
    
    # --- ASSINATURAS ---
    pdf.ln(6) # Reduzido de 12 para 6
    y_ass = pdf.get_y()
    pdf.line(15, y_ass, 95, y_ass)
    pdf.line(115, y_ass, 195, y_ass)
    pdf.set_xy(15, y_ass + 1)
    pdf.set_font("helvetica", "B", 8)
    label_ass = "Assinatura do Responsável Legal" if not is_adulto else "Assinatura do Catequizando"
    pdf.cell(80, 4, limpar_texto(label_ass), align='C')
    pdf.set_xy(115, y_ass + 1)
    pdf.cell(80, 4, limpar_texto("Assinatura do Representante da Catequese"), align='C')

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
    """
    Gera o Termo de Autorização de Saída com Rigor Estético Diocesano.
    Fundo Branco, tradução de data manual e linhas de margem a margem.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # 1. IDENTIDADE VISUAL (Fundo Branco #ffffff)
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # 2. CABEÇALHO OFICIAL
    adicionar_cabecalho_diocesano(pdf)
    
    # 3. TÍTULO ESTILIZADO
    pdf.set_y(45)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(65, 123, 153) # Azul Paroquial
    pdf.cell(0, 10, limpar_texto("TERMO DE AUTORIZAÇÃO PARA SAÍDA"), ln=True, align='C')
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 5, limpar_texto("DO CATEQUIZANDO SEM O RESPONSÁVEL"), ln=True, align='C')
    pdf.ln(8)
    
    # 4. CORPO DO TERMO (TEXTO JUSTIFICADO)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    
    nome_cat = str(dados_cat.get('nome_completo', '________________________________________')).upper()
    etapa = str(dados_turma.get('etapa', '________________')).upper()
    catequistas = str(dados_turma.get('catequista_responsavel', '________________________________________')).upper()
    
    texto_corpo = (
        f"Eu, {nome_resp.upper()}, na condição de responsável legal pelo(a) "
        f"catequizando(a) {nome_cat}, inscrita(o) na {etapa} etapa, com os/as "
        f"catequistas {catequistas}, autorizo a sua saída sozinho(a), no horário de "
        f"encerramento do encontro. Ciente que, assumo quaisquer riscos que possam ocorrer do trajeto "
        f"__________________________________________________________________ até em casa."
    )
    
    pdf.multi_cell(0, 8, limpar_texto(texto_corpo), align='J')
    pdf.ln(10)
    
    # 5. DATA EM PORTUGUÊS (MANUAL PARA EVITAR LOCALE INGLÊS)
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3))
    meses_br = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    data_extenso = f"Itabuna (BA), {hoje.day:02d} de {meses_br[hoje.month]} de {hoje.year}."
    pdf.set_font("helvetica", "I", 11)
    pdf.cell(0, 10, limpar_texto(data_extenso), ln=True, align='C')
    
    # 6. PRIMEIRA ASSINATURA
    pdf.ln(15)
    pdf.line(55, pdf.get_y(), 155, pdf.get_y())
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 5, limpar_texto("Assinatura do Responsável Legal"), align='C', ln=True)
    
    # 7. OBSERVAÇÃO (DESTAQUE EM LARANJA)
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(224, 61, 17) # Laranja para Alerta
    pdf.cell(0, 5, limpar_texto("Obs.:"), ln=True)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    obs_texto = (
        "Lembramos que o (a) catequizando (a) que não tiver o termo de autorização de saída preenchido "
        "só poderá sair do local da catequese com o responsável. Caso haja extravio da autorização, em último caso, "
        "poderá ser enviada pelo WhatsApp do catequista. Não será aceito pela catequese autorização realizada por telefone."
    )
    pdf.multi_cell(0, 5, limpar_texto(obs_texto), border=0)
    
    # 8. INFORMATIVO COMPLEMENTAR (LINHAS ATÉ A MARGEM)
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 10, limpar_texto("INFORMATIVO COMPLEMENTAR"), ln=True, align='C')
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, limpar_texto(f"No vínculo familiar do catequizando (a) {nome_cat} existe alguma restrição a quem não pode pegá-lo (a)?"))
    
    pdf.ln(4)
    # Linha do Nome
    pdf.write(7, limpar_texto("Se sim, informe o nome: "))
    x_nome = pdf.get_x()
    pdf.line(x_nome, pdf.get_y() + 5, 200, pdf.get_y() + 5) 
    pdf.ln(10)
    
    # Linha do Vínculo
    pdf.write(7, limpar_texto("e o vínculo: "))
    x_vinculo = pdf.get_x()
    pdf.line(x_vinculo, pdf.get_y() + 5, 200, pdf.get_y() + 5)
    pdf.ln(15)
    
    # 9. SEGUNDA ASSINATURA
    pdf.line(55, pdf.get_y(), 155, pdf.get_y())
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 5, limpar_texto("Assinatura do Responsável Legal"), align='C', ln=True)
    
    # Rodapé LGPD discreto
    pdf.set_y(280)
    pdf.set_font("helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, limpar_texto("Documento gerado pelo Sistema Catequese Fátima - Em conformidade com a LGPD e Diretrizes Diocesanas."), align='C')

    return finalizar_pdf(pdf)

# ==============================================================================
# 8. RELATÓRIOS EXECUTIVOS (DIOCESANO, PASTORAL E SACRAMENTAL)
# ==============================================================================

def gerar_relatorio_diocesano_pdf(df_turmas, df_cat, df_usuarios):
    """
    VERSÃO DEFINITIVA: Inteligência Sacramental Integrada.
    """
    from database import ler_aba 
    
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "RELATÓRIO ESTATÍSTICO E PASTORAL DIOCESANO")

    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    ANO_ATUAL = dt_module.datetime.now().year 

    # --- 1. TABELAS DE ITINERÁRIOS (INFANTIL E ADULTO) ---
    def eh_infantil(row):
        nome = str(row.get('nome_turma', '')).upper()
        etapa = str(row.get('etapa', '')).upper()
        return any(x in nome or x in etapa for x in ["PRÉ", "ETAPA", "PERSEVERANÇA"])

    t_infantil = df_turmas[df_turmas.apply(eh_infantil, axis=1)] if not df_turmas.empty else pd.DataFrame()
    t_adultos = df_turmas[~df_turmas.apply(eh_infantil, axis=1)] if not df_turmas.empty else pd.DataFrame()

    def desenhar_tabela_itinerarios(titulo, df_alvo):
        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto(f"{titulo}"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        pdf.cell(70, 7, "Nome da Turma", border=1, fill=True)
        pdf.cell(60, 7, "Catequista Responsável", border=1, fill=True)
        pdf.cell(20, 7, "Batizados", border=1, fill=True, align='C')
        pdf.cell(20, 7, "Eucaristia", border=1, fill=True, align='C')
        pdf.cell(20, 7, "Ativos", border=1, fill=True, align='C'); pdf.ln()
        pdf.set_font("helvetica", "", 8)
        for _, t in df_alvo.iterrows():
                nome_t = t['nome_turma']
                alunos = df_cat[(df_cat['etapa'] == nome_t) & (df_cat['status'] == 'ATIVO')]
                bat = len(alunos[alunos['batizado_sn'] == 'SIM'])
                euc = alunos['sacramentos_ja_feitos'].str.contains("EUCARISTIA", na=False, case=False).sum()
                
                # Lógica de altura dinâmica para catequistas
                cats_list = [c.strip() for c in str(t.get('catequista_responsavel', '')).split(',') if c.strip()]
                cats_text = "\n".join(cats_list)
                num_cats = len(cats_list) if len(cats_list) > 0 else 1
                altura_linha = max(6, num_cats * 5) # Altura mínima de 6, ou 5 por catequista
                
                inicio_y = pdf.get_y()
                pdf.cell(70, altura_linha, "", border=1)
                pdf.cell(60, altura_linha, "", border=1)
                pdf.cell(20, altura_linha, str(bat), border=1, align='C')
                pdf.cell(20, 6, str(euc), border=1, align='C') # Mantém alinhamento
                pdf.cell(20, 6, str(len(alunos)), border=1, align='C')
                
                # Escreve os textos dentro das células
                pdf.set_xy(10, inicio_y)
                pdf.multi_cell(70, altura_linha, limpar_texto(nome_t), border=0)
                pdf.set_xy(80, inicio_y)
                pdf.multi_cell(60, altura_linha/num_cats if num_cats > 1 else altura_linha, limpar_texto(cats_text), border=0, align='C')
                
                pdf.set_xy(10, inicio_y + altura_linha)
                pdf.ln()

    desenhar_tabela_itinerarios("1. ITINERÁRIOS INFANTIL / JUVENIL", t_infantil)
    pdf.ln(4)
    desenhar_tabela_itinerarios("2. ITINERÁRIOS DE JOVENS E ADULTOS", t_adultos)

    # --- 3. CENSO DE COBERTURA SACRAMENTAL ---
    pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. CENSO DE COBERTURA SACRAMENTAL (ATIVOS)"), ln=True, fill=True, align='C')
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 9); pdf.ln(2)
    df_ativos = df_cat[df_cat['status'] == 'ATIVO']
    if not df_ativos.empty:
        total_bat = len(df_ativos[df_ativos['batizado_sn'] == 'SIM'])
        perc_bat = (total_bat / len(df_ativos) * 100)
        pdf.cell(190, 8, limpar_texto(f"Cobertura Geral da Paróquia: {total_bat} Batizados de {len(df_ativos)} Catequizandos ({perc_bat:.1f}%)"), border=1, align='C', ln=True)
    else:
        pdf.cell(190, 8, "Nenhum catequizando ativo para censo.", border=1, align='C', ln=True)

    # --- 4. RESUMO DE CELEBRAÇÕES REALIZADAS ---
    df_eventos = ler_aba("sacramentos_eventos")
    df_recebidos = ler_aba("sacramentos_recebidos")
    if not df_eventos.empty:
        df_eventos['data_dt'] = pd.to_datetime(df_eventos['data'], errors='coerce', dayfirst=True)
        df_ano_ev = df_eventos[df_eventos['data_dt'].dt.year == ANO_ATUAL]
        if not df_ano_ev.empty:
            pdf.ln(5); pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
            pdf.cell(190, 8, limpar_texto(f"4. RESUMO DE CELEBRAÇÕES REALIZADAS EM {ANO_ATUAL}"), ln=True, fill=True, align='C')
            pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
            pdf.cell(80, 7, "Itinerário (Turma)", border=1, fill=True)
            pdf.cell(40, 7, "Sacramento", border=1, fill=True, align='C')
            pdf.cell(40, 7, "Data da Missa", border=1, fill=True, align='C')
            pdf.cell(30, 7, "Qtd. Fiéis", border=1, fill=True, align='C'); pdf.ln()
            pdf.set_font("helvetica", "", 8)
            for _, ev in df_ano_ev.iterrows():
                qtd_fies = len(df_recebidos[df_recebidos['id_evento'] == ev['id_evento']]) if not df_recebidos.empty else 0
                pdf.cell(80, 6, limpar_texto(ev['turmas']), border=1)
                pdf.cell(40, 6, limpar_texto(ev['tipo']), border=1, align='C')
                pdf.cell(40, 6, formatar_data_br(ev['data']), border=1, align='C')
                pdf.cell(30, 6, str(qtd_fies), border=1, align='C'); pdf.ln()

    # --- 5. EQUIPE CATEQUÉTICA ---
    df_equipe_real = df_usuarios[df_usuarios['papel'].str.upper() != 'ADMIN'] if not df_usuarios.empty else pd.DataFrame()
    if not df_equipe_real.empty:
        pdf.ln(5); pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto(f"5. EQUIPE CATEQUÉTICA E QUALIFICAÇÃO (Total: {len(df_equipe_real)})"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        pdf.cell(100, 7, "Indicador de Fé (Equipe)", border=1, fill=True); pdf.cell(45, 7, "Quantidade", border=1, fill=True, align='C'); pdf.cell(45, 7, "Percentual", border=1, fill=True, align='C'); pdf.ln()
        bat_e = df_equipe_real['data_batismo'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
        euc_e = df_equipe_real['data_eucaristia'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
        cri_e = df_equipe_real['data_crisma'].apply(lambda x: str(x).strip() not in ["", "N/A", "None"]).sum()
        pdf.set_font("helvetica", "", 8)
        total_e = len(df_equipe_real)
        for desc, qtd in [("Batismo", bat_e), ("Eucaristia", euc_e), ("Crisma", cri_e)]:
            pdf.cell(100, 6, f" {desc}", border=1)
            pdf.cell(45, 6, str(qtd), border=1, align='C')
            pdf.cell(45, 6, f"{(qtd/total_e)*100:.1f}%", border=1, align='C'); pdf.ln()

    return finalizar_pdf(pdf)

def gerar_relatorio_pastoral_pdf(df_turmas, df_cat, df_pres, df_pres_reuniao):
    """
    Dossiê de Auditoria Profissional.
    Catequistas em linhas separadas, sem abreviações e nomes completos.
    """
    pdf = FPDF()
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)
    
    faixas = {
        "PRÉ": (4, 6), "1ª ETAPA": (7, 8), "PRIMEIRA ETAPA": (7, 8),
        "2ª ETAPA": (9, 10), "SEGUNDA ETAPA": (9, 10),
        "3ª ETAPA": (11, 13), "TERCEIRA ETAPA": (11, 13),
        "PERSEVERANÇA": (14, 15), "ADULTOS": (16, 99)
    }

    for _, t in df_turmas.iterrows():
        nome_t = t['nome_turma']
        etapa_base = str(t['etapa']).upper()
        alunos_t = df_cat[df_cat['etapa'] == nome_t]
        if alunos_t.empty: continue
        
        pdf.add_page()
        adicionar_cabecalho_diocesano(pdf, f"DOSSIÊ PASTORAL: {nome_t}")

        # --- 1. QUADRO DE INDICADORES (COM ALTURA DINÂMICA) ---
        ativos = alunos_t[alunos_t['status'] == 'ATIVO']
        pres_t = df_pres[df_pres['id_turma'] == nome_t] if not df_pres.empty else pd.DataFrame()
        freq_val = (pres_t['status'].value_counts(normalize=True).get('PRESENTE', 0) * 100) if not pres_t.empty else 0
        docs_ok = len(ativos[ativos['doc_em_falta'].isin(['COMPLETO', 'NADA', 'OK', 'NADA FALTANDO'])])
        
        # Processamento dos Catequistas (Um por linha)
        cats_list = [c.strip() for c in str(t['catequista_responsavel']).split(',') if c.strip()]
        cats_text = "\n".join(cats_list)
        num_cats = len(cats_list) if len(cats_list) > 0 else 1
        
        # Cálculo da altura baseada no número de catequistas
        h_header = num_cats * 6 
        if h_header < 12: h_header = 12 # Altura mínima para não ficar espremido

        pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto("1. INDICADORES DE ENGAJAMENTO E REGULARIZAÇÃO"), ln=True, fill=True, align='C')
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
        
        # Salva posição para alinhar as células
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # Coluna 1: Frequência
        pdf.cell(63, h_header, limpar_texto(f"Frequência Média: {freq_val:.1f}%"), border=1, fill=True, align='C')
        # Coluna 2: Documentação
        pdf.cell(63, h_header, limpar_texto(f"Documentação Regularizada: {docs_ok} / {len(ativos)}"), border=1, fill=True, align='C')
        # Coluna 3: Catequistas (Multi-linha)
        pdf.set_xy(x_start + 126, y_start)
        pdf.multi_cell(64, h_header/num_cats, limpar_texto(cats_text), border=1, align='C', fill=True)
        
        pdf.set_y(y_start + h_header + 5)

        # --- 2. TABELA NOMINAL DE CAMINHADA ---
        pdf.set_font("helvetica", "B", 10); pdf.set_text_color(*AZUL_P)
        pdf.cell(0, 7, limpar_texto("2. RELAÇÃO NOMINAL E SITUAÇÃO SACRAMENTAL"), ln=True)
        
        pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8)
        pdf.cell(10, 7, "Nº", border=1, fill=True, align='C')
        pdf.cell(90, 7, "Nome Completo do Catequizando", border=1, fill=True, align='C')
        pdf.cell(30, 7, "Batismo", border=1, fill=True, align='C')
        pdf.cell(30, 7, "1ª Eucaristia", border=1, fill=True, align='C')
        pdf.cell(30, 7, "Documentação", border=1, fill=True, align='C')
        pdf.ln()

        pdf.set_font("helvetica", "", 8)
        nomes_ativos = ativos.sort_values('nome_completo')
        for i, (_, r) in enumerate(nomes_ativos.iterrows(), 1):
            status_bat = "Sim" if r['batizado_sn'] == "SIM" else "Pendente"
            status_euc = "Sim" if "EUCARISTIA" in str(r['sacramentos_ja_feitos']).upper() else "Pendente"
            status_doc = "Regular" if r['doc_em_falta'] in ['COMPLETO', 'NADA', 'OK'] else "Pendente"
            
            # Altura dinâmica para o nome
            inicio_y = pdf.get_y()
            pdf.set_xy(20, inicio_y)
            pdf.multi_cell(90, 6, limpar_texto(r['nome_completo']), border=0, align='L')
            fim_y = pdf.get_y()
            altura_linha = fim_y - inicio_y
            if altura_linha < 7: altura_linha = 7
            
            pdf.set_xy(10, inicio_y)
            pdf.cell(10, altura_linha, f"{i:02d}", border=1, align='C')
            pdf.cell(90, altura_linha, "", border=1) 
            pdf.cell(30, altura_linha, status_bat, border=1, align='C')
            pdf.cell(30, altura_linha, status_euc, border=1, align='C')
            pdf.cell(30, altura_linha, status_doc, border=1, align='C')
            pdf.ln()
            
            if pdf.get_y() > 260: pdf.add_page()

        # --- 3. RADAR DE ATENÇÃO PASTORAL (AGRUPADO) ---
        pdf.ln(5)
        pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
        pdf.cell(190, 8, limpar_texto("3. RADAR DE ATENÇÃO PASTORAL (AGRUPADO)"), ln=True, fill=True, align='C')
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 9)
        
        min_i, max_i = faixas.get(etapa_base, (0, 99))
        acima_idade, abaixo_idade, risco_evasao = [], [], []

        for _, r in ativos.iterrows():
            idade_c = calcular_idade(r['data_nascimento'])
            if idade_c > max_i: acima_idade.append(f"{r['nome_completo']} ({idade_c} anos)")
            elif idade_c < min_i: abaixo_idade.append(f"{r['nome_completo']} ({idade_c} anos)")
            
            faltas = len(pres_t[(pres_t['id_catequizando'] == r['id_catequizando']) & (pres_t['status'] == 'AUSENTE')]) if not pres_t.empty else 0
            if faltas >= 3: risco_evasao.append(f"{r['nome_completo']} ({faltas} faltas)")

        tem_alerta = False
        if acima_idade:
            pdf.set_font("helvetica", "B", 9); pdf.write(6, "Catequizandos acima da idade ideal: "); pdf.set_font("helvetica", "", 9)
            pdf.multi_cell(0, 6, limpar_texto(", ".join(acima_idade)) + "."); tem_alerta = True
        if abaixo_idade:
            pdf.set_font("helvetica", "B", 9); pdf.write(6, "Catequizandos abaixo da idade ideal: "); pdf.set_font("helvetica", "", 9)
            pdf.multi_cell(0, 6, limpar_texto(", ".join(abaixo_idade)) + "."); tem_alerta = True
        if risco_evasao:
            pdf.set_font("helvetica", "B", 9); pdf.set_text_color(*LARANJA_P); pdf.write(6, "Risco Crítico de Evasão (3+ faltas): "); pdf.set_font("helvetica", "", 9)
            pdf.multi_cell(0, 6, limpar_texto(", ".join(risco_evasao)) + "."); pdf.set_text_color(0, 0, 0); tem_alerta = True

        if not tem_alerta:
            pdf.cell(0, 8, limpar_texto("Nenhum alerta crítico detectado para esta turma."), ln=True)

    return finalizar_pdf(pdf)

def gerar_relatorio_local_turma_pdf(nome_turma, metricas, listas, analise_ia):
    """
    Dossiê Completo de Prontidão e Inclusão.
    Integra Sacramentos, Família, Saúde e Itinerário.
    """
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"AUDITORIA PASTORAL: {nome_turma}")
    
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)

    # --- 1. INDICADORES ESTRUTURAIS E ADESÃO (6 BOXES) ---
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. INDICADORES DE DESEMPENHO E ENGAJAMENTO"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); y = pdf.get_y() + 2
    # Linha 1 de Boxes
    desenhar_campo_box(pdf, "Catequistas", str(metricas.get('qtd_catequistas', 0)), 10, y, 45)
    desenhar_campo_box(pdf, "Catequizandos", str(metricas.get('qtd_cat', 0)), 58, y, 45)
    desenhar_campo_box(pdf, "Frequência", f"{metricas.get('freq_global', 0)}%", 106, y, 45)
    desenhar_campo_box(pdf, "Idade Média", f"{metricas.get('idade_media', 0)}a", 154, y, 46)
    
    y += 14
    # Linha 2 de Boxes (Novos Indicadores)
    desenhar_campo_box(pdf, "Engajamento Pais", f"{metricas.get('engaj_pais', 0)}%", 10, y, 93)
    desenhar_campo_box(pdf, "Progresso Itinerário", f"{metricas.get('progresso_it', 0)}%", 107, y, 93)
    
    pdf.ln(22)

    # --- 2. DIAGNÓSTICO SACRAMENTAL E SAÚDE ---
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("2. PRONTIDÃO SACRAMENTAL E CUIDADO (RESUMO)"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 9)
    col_sac = f"Batizados: {metricas.get('batizados', 0)} | Pendentes: {metricas.get('pend_batismo', 0)}"
    col_sau = f"Inclusão (TGO): {metricas.get('tgo', 0)} | Alerta Médico: {metricas.get('saude', 0)}"
    
    pdf.set_fill_color(*CINZA_F)
    pdf.cell(95, 8, limpar_texto(f" SACRAMENTOS: {col_sac}"), border=1, fill=True)
    pdf.cell(95, 8, limpar_texto(f" SAÚDE/INCLUSÃO: {col_sau}"), border=1, fill=True, ln=True)
    
    pdf.ln(4)

    # --- 3. LISTA NOMINAL DETALHADA ---
    pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("3. RELAÇÃO NOMINAL E SITUAÇÃO INDIVIDUAL"), ln=True, fill=True, align='C')
    
    pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0); pdf.set_fill_color(*CINZA_F)
    pdf.cell(80, 7, "Nome do Catequizando", border=1, fill=True)
    pdf.cell(25, 7, "Batismo", border=1, fill=True, align='C')
    pdf.cell(25, 7, "Eucaristia", border=1, fill=True, align='C')
    pdf.cell(30, 7, "Faltas", border=1, fill=True, align='C')
    pdf.cell(30, 7, "Status", border=1, fill=True, align='C'); pdf.ln()

    pdf.set_font("helvetica", "", 8)
    for cat in listas.get('geral', []):
        # Alerta visual para muitas faltas
        if cat.get('faltas', 0) >= 3: pdf.set_text_color(*LARANJA_P)
        else: pdf.set_text_color(0, 0, 0)
        
        pdf.cell(80, 6, limpar_texto(cat['nome']), border=1)
        pdf.cell(25, 6, limpar_texto(cat.get('batismo', 'N/A')), border=1, align='C')
        pdf.cell(25, 6, limpar_texto(cat.get('eucaristia', 'N/A')), border=1, align='C')
        pdf.cell(30, 6, f"{cat.get('faltas', 0)} faltas", border=1, align='C')
        pdf.cell(30, 6, limpar_texto(cat.get('status', 'ATIVO')), border=1, align='C'); pdf.ln()
        
        if pdf.get_y() > 260: pdf.add_page()

    # --- 4. PARECER TÉCNICO (IA) ---
    pdf.set_text_color(0, 0, 0); pdf.ln(5)
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, limpar_texto("4. PARECER TÉCNICO E ORIENTAÇÃO PASTORAL (IA)"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10)
    
    # Se a IA falhar, gera um parecer técnico padrão baseado nos dados
    if "indisponível" in analise_ia.lower():
        analise_ia = f"Dossiê técnico da turma {nome_turma}. Frequência de {metricas.get('freq_global')}% com {metricas.get('pend_batismo')} pendências de batismo. Recomenda-se acompanhamento das famílias com baixa participação."
        
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    return finalizar_pdf(pdf)

def gerar_relatorio_sacramentos_tecnico_pdf(analise_turmas, impedimentos_lista, analise_ia):
    """
    DOSSIÊ SACRAMENTAL - VERSÃO INTEGRAL
    Restaura a tabela de prontidão e integra impedimentos nominais.
    """
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "DOSSIÊ DE REGULARIZAÇÃO E ESTRATÉGIA SACRAMENTAL")
    
    AZUL_P = (65, 123, 153); LARANJA_P = (224, 61, 17); CINZA_F = (245, 245, 245)

    # --- 1. PRONTIDÃO POR ITINERÁRIO (VISÃO GERAL) ---
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("1. PRONTIDÃO POR ITINERÁRIO (VISÃO GERAL)"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(60, 7, "Turma", border=1, fill=True)
    pdf.cell(40, 7, "Etapa", border=1, fill=True, align='C')
    pdf.cell(30, 7, "Batizados", border=1, fill=True, align='C')
    pdf.cell(30, 7, "Pendentes", border=1, fill=True, align='C')
    pdf.cell(30, 7, "Impedimentos", border=1, fill=True, align='C'); pdf.ln()

    pdf.set_font("helvetica", "", 8)
    if analise_turmas:
        for t in analise_turmas:
            pdf.cell(60, 6, limpar_texto(t['turma']), border=1)
            pdf.cell(40, 6, limpar_texto(t['etapa']), border=1, align='C')
            pdf.cell(30, 6, str(t['batizados']), border=1, align='C')
            pdf.cell(30, 6, str(t['pendentes']), border=1, align='C')
            pdf.cell(30, 6, str(t['impedimentos_civel']), border=1, align='C'); pdf.ln()
    else:
        pdf.cell(190, 7, "Dados de turmas não processados.", border=1, align='C', ln=True)

    # --- 2. ZONA VERMELHA: IMPEDIMENTOS CRÍTICOS ---
    pdf.ln(5)
    pdf.set_fill_color(*LARANJA_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("2. ZONA VERMELHA: IMPEDIMENTOS QUE BLOQUEIAM O SACRAMENTO"), ln=True, fill=True, align='C')
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "B", 8); pdf.set_fill_color(*CINZA_F)
    pdf.cell(80, 7, "Catequizando", border=1, fill=True)
    pdf.cell(50, 7, "Turma", border=1, fill=True)
    pdf.cell(60, 7, "Gravidade / Impedimento", border=1, fill=True); pdf.ln()

    pdf.set_font("helvetica", "", 8)
    if impedimentos_lista:
        for imp in impedimentos_lista:
            pdf.cell(80, 6, limpar_texto(imp['nome']), border=1)
            pdf.cell(50, 6, limpar_texto(imp['turma']), border=1)
            pdf.set_text_color(*LARANJA_P)
            pdf.cell(60, 6, limpar_texto(imp['motivo']), border=1)
            pdf.set_text_color(0, 0, 0); pdf.ln()
    else:
        pdf.cell(190, 7, "Nenhum impedimento crítico detectado.", border=1, align='C', ln=True)

    # --- 3. PARECER DO AUDITOR (IA) ---
    pdf.ln(5)
    pdf.set_fill_color(*AZUL_P); pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 10)
    pdf.cell(190, 8, limpar_texto("3. PARECER DO AUDITOR E PLANO DE REGULARIZAÇÃO (IA)"), ln=True, fill=True, align='C')
    pdf.ln(2); pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", "", 10)
    
    if not analise_ia or "indisponível" in analise_ia.lower():
        analise_ia = "Análise técnica: Identificamos catequizandos em etapas avançadas sem registro de Batismo. Recomenda-se mutirão de regularização documental e escrutínio pastoral imediato."
        
    pdf.multi_cell(190, 6, limpar_texto(analise_ia))
    
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(0, 4, "Este dossiê é para uso exclusivo da Coordenação e do Pároco. As informações aqui contidas visam a salvação das almas e a correta administração dos sacramentos.")

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

def eh_aniversariante_da_semana(data_nasc_str, data_referencia=None):
    """
    Verifica se o aniversário cai na mesma semana (Domingo a Sábado) da data de referência.
    Retorna: 'DIA' (se for no dia exato), 'SEMANA' (se for na mesma semana), ou False.
    """
    try:
        d_str = formatar_data_br(data_nasc_str)
        if d_str == "N/A": return False
        nasc = dt_module.datetime.strptime(d_str, "%d/%m/%Y").date()
        
        if data_referencia is None:
            data_referencia = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
        elif isinstance(data_referencia, str):
            data_referencia = dt_module.datetime.strptime(formatar_data_br(data_referencia), "%d/%m/%Y").date()
        
        # 1. É exatamente no dia do encontro?
        if nasc.day == data_referencia.day and nasc.month == data_referencia.month:
            return "DIA"
        
        # 2. É na mesma semana (Domingo a Sábado)?
        # isoweekday() retorna 1 (Segunda) a 7 (Domingo).
        dias_para_domingo = data_referencia.isoweekday() % 7
        domingo = data_referencia - dt_module.timedelta(days=dias_para_domingo)
        
        for i in range(7):
            dia_semana = domingo + dt_module.timedelta(days=i)
            if nasc.day == dia_semana.day and nasc.month == dia_semana.month:
                return "SEMANA"
                
        return False
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
    """Retorna lista estruturada: 'DIA | PAPEL | NOME' para os aniversariantes de hoje."""
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
    """Retorna DataFrame com aniversariantes do mês (Padronizado: coluna 'nome')."""
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
    """Versão para painéis de turma (apenas catequizandos)."""
    return obter_aniversariantes_mes_unificado(df_cat, None)

def processar_alertas_evasao(df_pres_turma):
    """
    Analisa o histórico de presença da turma para identificar catequizandos 
    que precisam de visita ou contato pastoral.
    """
    if df_pres_turma.empty:
        return [], []

    # Agrupa faltas por catequizando
    faltas_por_id = df_pres_turma[df_pres_turma['status'] == 'AUSENTE'].groupby('id_catequizando').size()
    
    risco_critico = [] # 3 ou mais faltas
    atencao_pastoral = [] # 2 faltas
    
    for id_cat, qtd in faltas_por_id.items():
        nome = df_pres_turma[df_pres_turma['id_catequizando'] == id_cat]['nome_catequizando'].iloc[0]
        if qtd >= 3:
            risco_critico.append(f"{nome} ({qtd} faltas)")
        elif qtd == 2:
            atencao_pastoral.append(f"{nome} ({qtd} faltas)")
            
    return risco_critico, atencao_pastoral

# ==============================================================================
# 10. PROCESSAMENTO LOCAL E AUDITORIA INTEGRAL (DOSSIÊS)
# ==============================================================================

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

def gerar_lista_secretaria_pdf(nome_turma, data_cerimonia, tipo_sacramento, lista_nomes):
    """Gera a lista nominal oficial para a secretaria paroquial."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"LISTA DE CANDIDATOS: {tipo_sacramento}")
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, limpar_texto(f"Turma: {nome_turma}"), ln=True)
    pdf.cell(0, 10, limpar_texto(f"Data da Celebração: {formatar_data_br(data_cerimonia)}"), ln=True)
    pdf.ln(5)
    pdf.set_fill_color(230, 230, 230); pdf.set_font("helvetica", "B", 10)
    pdf.cell(15, 8, "Nº", border=1, fill=True, align='C'); pdf.cell(175, 8, "Nome Completo", border=1, fill=True); pdf.ln()
    pdf.set_font("helvetica", "", 10)
    for i, nome in enumerate(lista_nomes, 1):
        pdf.cell(15, 7, str(i), border=1, align='C'); pdf.cell(175, 7, limpar_texto(nome), border=1); pdf.ln()
    return finalizar_pdf(pdf)

def gerar_livro_sacramentos_pdf(df_livro):
    """Gera o Livro de Registros (Cartório) em PDF."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "LIVRO DE REGISTROS SACRAMENTAIS (CARTÓRIO)")
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    
    pdf.cell(70, 8, "Catequizando", border=1, fill=True)
    pdf.cell(35, 8, "Sacramento", border=1, fill=True, align='C')
    pdf.cell(25, 8, "Data", border=1, fill=True, align='C')
    pdf.cell(60, 8, "Local / Celebrante", border=1, fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    
    for _, row in df_livro.iterrows():
        pdf.cell(70, 6, limpar_texto(row['Catequizando']), border=1)
        pdf.cell(35, 6, limpar_texto(row['Sacramento']), border=1, align='C')
        
        data_val = row['Data']
        if isinstance(data_val, pd.Timestamp):
            data_str = data_val.strftime('%d/%m/%Y')
        else:
            data_str = formatar_data_br(data_val)
            
        pdf.cell(25, 6, data_str, border=1, align='C')
        pdf.cell(60, 6, limpar_texto(str(row['Local / Celebrante'])[:35]), border=1)
        pdf.ln()
        
        if pdf.get_y() > 270:
            pdf.add_page()
            
    return finalizar_pdf(pdf)

def gerar_relatorio_frequencia_turma_pdf(nome_turma, df_alunos, df_presencas):
    """Gera o Dossiê de Frequência com Encontros Realizados, Estatísticas e Detalhamento de Faltas."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"DOSSIÊ DE FREQUÊNCIA E HISTÓRICO DA TURMA")
    
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 8, limpar_texto(f"Turma: {nome_turma}"), ln=True, align='C')
    pdf.ln(5)
    
    # --- SESSÃO 1: ENCONTROS REALIZADOS ---
    pdf.set_fill_color(240, 242, 246)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 8, limpar_texto("1. CRONOGRAMA DE ENCONTROS REALIZADOS (DIÁRIO)"), ln=True, fill=True)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    if not df_presencas.empty:
        # Puxa as datas únicas dos encontros que tiveram chamada
        encontros_realizados = df_presencas.drop_duplicates(subset=['data_encontro']).copy()
        encontros_realizados['data_dt'] = pd.to_datetime(encontros_realizados['data_encontro'], errors='coerce', dayfirst=True)
        encontros_realizados = encontros_realizados.sort_values('data_dt')
        
        for _, enc in encontros_realizados.iterrows():
            dt_str = formatar_data_br(enc['data_encontro'])
            tema_str = str(enc.get('tema_do_dia', 'Tema não registrado'))
            pdf.cell(0, 5, limpar_texto(f"• {dt_str} - {tema_str}"), ln=True)
    else:
        pdf.cell(0, 5, limpar_texto("Nenhum encontro registrado com lista de presença no sistema."), ln=True)
        
    pdf.ln(5)
    
    # --- SESSÃO 2: QUADRO GERAL DE FREQUÊNCIA ---
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 8, limpar_texto("2. QUADRO GERAL DE FREQUÊNCIA"), ln=True, fill=True)
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 8)
    
    pdf.cell(10, 7, "Nº", border=1, fill=True, align='C')
    pdf.cell(110, 7, "Nome do Catequizando", border=1, fill=True)
    pdf.cell(15, 7, "Faltas", border=1, fill=True, align='C')
    pdf.cell(15, 7, "Pres.", border=1, fill=True, align='C')
    pdf.cell(40, 7, "Frequência (%)", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    
    alunos_ordenados = df_alunos.sort_values('nome_completo')
    detalhamento_faltas = {}
    
    for i, (_, aluno) in enumerate(alunos_ordenados.iterrows(), 1):
        id_cat = aluno['id_catequizando']
        nome_c = limpar_texto(aluno['nome_completo'])
        
        if not df_presencas.empty:
            pres_aluno = df_presencas[df_presencas['id_catequizando'] == id_cat]
            faltas_df = pres_aluno[pres_aluno['status'] == 'AUSENTE']
            faltas = len(faltas_df)
            presencas = len(pres_aluno[pres_aluno['status'] == 'PRESENTE'])
            total_aluno = faltas + presencas
            freq = (presencas / total_aluno * 100) if total_aluno > 0 else 100.0
            
            # Salva o detalhamento para a Sessão 3
            if faltas > 0:
                lista_f =[]
                for _, f in faltas_df.iterrows():
                    data_f = formatar_data_br(f['data_encontro'])
                    tema_f = str(f.get('tema_do_dia', 'Sem tema'))
                    lista_f.append(f"{data_f} ({tema_f})")
                detalhamento_faltas[nome_c] = lista_f
        else:
            faltas, presencas, freq = 0, 0, 100.0
            
        if faltas >= 3:
            pdf.set_text_color(224, 61, 17) 
            pdf.set_font("helvetica", "B", 8)
        else:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 8)

        pdf.cell(10, 6, str(i), border=1, align='C')
        pdf.cell(110, 6, nome_c[:55], border=1)
        pdf.cell(15, 6, str(faltas), border=1, align='C')
        pdf.cell(15, 6, str(presencas), border=1, align='C')
        pdf.cell(40, 6, f"{freq:.1f}%", border=1, align='C')
        pdf.ln()

        if pdf.get_y() > 260:
            pdf.add_page()
            
    # --- SESSÃO 3: DETALHAMENTO NOMINAL DE FALTAS ---
    if detalhamento_faltas:
        pdf.ln(5)
        if pdf.get_y() > 240: pdf.add_page() # Garante que o título não fique sozinho no fim da página
            
        pdf.set_fill_color(240, 242, 246)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(224, 61, 17)
        pdf.cell(0, 8, limpar_texto("3. DETALHAMENTO NOMINAL DE FALTAS (ACOMPANHAMENTO)"), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        for nome, datas in detalhamento_faltas.items():
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(0, 5, f"{nome}:", ln=True)
            pdf.set_font("helvetica", "", 8)
            texto_faltas = "Faltou em: " + "; ".join(datas)
            pdf.multi_cell(0, 5, limpar_texto(texto_faltas))
            pdf.ln(2)
            
            if pdf.get_y() > 270:
                pdf.add_page()
                
    return finalizar_pdf(pdf)
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, f"RELATÓRIO DE FREQUÊNCIA E FALTAS")
    
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 8, limpar_texto(f"Turma: {nome_turma}"), ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    
    pdf.cell(10, 8, "Nº", border=1, fill=True, align='C')
    pdf.cell(100, 8, "Nome do Catequizando", border=1, fill=True)
    pdf.cell(20, 8, "Faltas", border=1, fill=True, align='C')
    pdf.cell(20, 8, "Presenças", border=1, fill=True, align='C')
    pdf.cell(40, 8, "Frequência (%)", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    
    alunos_ordenados = df_alunos.sort_values('nome_completo')
    
    for i, (_, aluno) in enumerate(alunos_ordenados.iterrows(), 1):
        id_cat = aluno['id_catequizando']
        
        if not df_presencas.empty:
            pres_aluno = df_presencas[df_presencas['id_catequizando'] == id_cat]
            faltas = len(pres_aluno[pres_aluno['status'] == 'AUSENTE'])
            presencas = len(pres_aluno[pres_aluno['status'] == 'PRESENTE'])
            total_aluno = faltas + presencas
            freq = (presencas / total_aluno * 100) if total_aluno > 0 else 100.0
        else:
            faltas, presencas, freq = 0, 0, 100.0
            
        # Destaca em vermelho quem tem risco crítico de evasão (3+ faltas)
        if faltas >= 3:
            pdf.set_text_color(224, 61, 17) 
            pdf.set_font("helvetica", "B", 8)
        else:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 8)

        pdf.cell(10, 6, str(i), border=1, align='C')
        pdf.cell(100, 6, limpar_texto(aluno['nome_completo'])[:48], border=1)
        pdf.cell(20, 6, str(faltas), border=1, align='C')
        pdf.cell(20, 6, str(presencas), border=1, align='C')
        pdf.cell(40, 6, f"{freq:.1f}%", border=1, align='C')
        pdf.ln()

        if pdf.get_y() > 270:
            pdf.add_page()
            
    return finalizar_pdf(pdf)

def gerar_declaracao_pastoral_pdf(dados, tipo_doc, paroquia_destino="", data_atestado=""):
    """Gera Documentos Oficiais: Atestado, Transferência ou Histórico."""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho Oficial
    adicionar_cabecalho_diocesano(pdf)
    
    # Título do Documento
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(65, 123, 153) # Azul Paroquial
    
    if tipo_doc == "ATESTADO_PARTICIPACAO":
        titulo = "Atestado de Participação"
    elif tipo_doc == "TRANSFERENCIA_COM_DESTINO":
        titulo = "Carta de Transferência Pastoral"
    else:
        titulo = "Declaração de Histórico Catequético"
        
    pdf.cell(0, 10, limpar_texto(titulo), ln=True, align='C')
    pdf.ln(10)
    
    # Corpo do Texto
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    
    # Extração de Dados Resiliente
    nome_cat = str(dados.get('nome_completo', 'N/A')).upper()
    data_nasc = formatar_data_br(dados.get('data_nascimento', 'N/A'))
    nome_mae = str(dados.get('nome_mae', 'N/A')).upper()
    nome_pai = str(dados.get('nome_pai', 'N/A')).upper()
    etapa = str(dados.get('etapa', 'N/A')).upper()
    turno_bd = str(dados.get('turno', 'N/A')).upper()
    
    turno_formatado = turno_bd
    if "M" in turno_bd or "MANHÃ" in turno_bd: turno_formatado = "MANHÃ"
    elif "T" in turno_bd or "TARDE" in turno_bd: turno_formatado = "TARDE"
    elif "N" in turno_bd or "NOITE" in turno_bd: turno_formatado = "NOITE"
    
    # Lógica para Filiação (Mãe, Pai ou Cuidador)
    filiacao = ""
    if nome_mae not in["N/A", "", "NONE"] and nome_pai not in ["N/A", "", "NONE"]:
        filiacao = f"{nome_mae} e {nome_pai}"
    elif nome_mae not in["N/A", "", "NONE"]:
        filiacao = f"{nome_mae}"
    elif nome_pai not in ["N/A", "", "NONE"]:
        filiacao = f"{nome_pai}"
    else:
        filiacao = str(dados.get('nome_responsavel', 'N/A')).upper()
        
    # Construção dos Textos Aprovados
    if tipo_doc == "ATESTADO_PARTICIPACAO":
        texto = (f"Declaramos para os devidos fins, a pedido da família, que o(a) catequizando(a) {nome_cat}, "
                 f"nascido(a) em {data_nasc}, filho(a) de {filiacao}, está regularmente inscrito(a) e "
                 f"frequenta ativamente o itinerário de Iniciação à Vida Cristã nesta Paróquia Nossa Senhora de Fátima, "
                 f"na etapa {etapa}.\n\n"
                 f"Atestamos ainda que o(a) mesmo(a) esteve presente em nossas atividades e encontros pastorais realizados "
                 f"no dia {data_atestado} no período do turno da {turno_formatado}.\n\n"
                 f"Por ser expressão da verdade, firmamos o presente documento.")
                 
    elif tipo_doc == "TRANSFERENCIA_COM_DESTINO":
        texto = (f"Declaramos para os devidos fins e exigências pastorais que o(a) catequizando(a) {nome_cat}, "
                 f"nascido(a) em {data_nasc}, filho(a) de {filiacao}, frequentou os encontros de "
                 f"Iniciação à Vida Cristã nesta Paróquia Nossa Senhora de Fátima até a etapa {etapa}.\n\n"
                 f"O(a) mesmo(a) encontra-se apto(a) para efetuar a sua inscrição e dar continuidade à sua preparação "
                 f"para os sacramentos na {paroquia_destino.upper()}.\n\n"
                 f"Temos a certeza de que será muito bem acolhido(a) em sua nova comunidade paroquial. "
                 f"Rogamos a Deus e à Virgem de Fátima bênçãos sobre sua família.")
                 
    else: # DECLARACAO_HISTORICO
        texto = (f"Declaramos para os devidos fins que o(a) catequizando(a) {nome_cat}, nascido(a) em {data_nasc}, "
                 f"filho(a) de {filiacao}, participou ativamente dos encontros de Iniciação à Vida Cristã nesta "
                 f"Paróquia Nossa Senhora de Fátima.\n\n"
                 f"Atestamos que, durante sua caminhada em nossa comunidade, o(a) catequizando(a) concluiu com "
                 f"aproveitamento pastoral a etapa {etapa}. Sendo assim, encontra-se apto(a) para prosseguir "
                 f"em sua caminhada de fé e vivência comunitária.\n\n"
                 f"Por ser verdade, firmamos a presente declaração.")

    # Justifica o texto
    pdf.multi_cell(0, 8, limpar_texto(texto), align='J')
    
    # Data por extenso (Força o Fuso Horário Local)
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3))
    meses_br = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
                7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
    data_extenso = f"Itabuna (BA), {hoje.day:02d} de {meses_br[hoje.month]} de {hoje.year}."
    
    pdf.ln(15)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 10, limpar_texto(data_extenso), ln=True, align='R')
    
    # Assinaturas
    pdf.ln(25)
    y_ass = pdf.get_y()
    pdf.line(20, y_ass, 95, y_ass)
    pdf.set_xy(20, y_ass + 2)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(75, 5, limpar_texto("Pároco / Vigário"), align='C')
    
    pdf.line(115, y_ass, 190, y_ass)
    pdf.set_xy(115, y_ass + 2)
    pdf.cell(75, 5, limpar_texto("Coordenação / Secretaria"), align='C')
    
    return finalizar_pdf(pdf)

def gerar_lista_assinatura_reuniao_pdf(tema, data, local, turma, lista_familias):
    """Gera uma lista de presença física com cabeçalho oficial e espaço para assinatura."""
    pdf = FPDF()
    pdf.add_page()
    adicionar_cabecalho_diocesano(pdf, "LISTA DE PRESENÇA - REUNIÃO DE PAIS")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 6, limpar_texto(f"TEMA: {tema}"), ln=True)
    pdf.cell(0, 6, limpar_texto(f"DATA: {formatar_data_br(data)}  |  LOCAL: {local}  |  TURMA: {turma}"), ln=True)
    pdf.ln(4)
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(10, 8, "Nº", border=1, fill=True, align='C')
    pdf.cell(70, 8, "Nome do Catequizando", border=1, fill=True, align='C')
    pdf.cell(110, 8, "Nome do Responsável e Assinatura", border=1, fill=True, align='C')
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    for i, fam in enumerate(lista_familias, 1):
        nome_cat = limpar_texto(fam['nome_cat'].upper())
        nome_resp = limpar_texto(fam['responsavel'].upper())
        
        y_start = pdf.get_y()
        pdf.cell(10, 10, str(i), border=1, align='C')
        pdf.cell(70, 10, nome_cat[:35], border=1)
        
        # Célula vazia para a assinatura
        pdf.cell(110, 10, "", border=1)
        
        # Escreve o nome do responsável e desenha a linha dentro da célula
        pdf.set_xy(92, y_start + 2)
        pdf.set_font("helvetica", "I", 7)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(100, 3, f"Resp: {nome_resp[:45]}")
        
        pdf.set_xy(92, y_start + 7)
        pdf.line(95, y_start + 8, 195, y_start + 8)
        
        pdf.set_xy(10, y_start + 10)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 8)
        
        if pdf.get_y() > 270:
            pdf.add_page()
            
    return finalizar_pdf(pdf)

def obter_ultima_chamada_turma(df_pres, nome_turma):
    """Retorna a data da última chamada (limitada a hoje) e o DataFrame correspondente."""
    if df_pres.empty: return None, pd.DataFrame()
    
    # 1. Normalização rigorosa da busca
    nome_busca = str(nome_turma).strip().upper()
    pres_t = df_pres[df_pres['id_turma'].astype(str).str.strip().str.upper() == nome_busca].copy()
    if pres_t.empty: return None, pd.DataFrame()
    
    # 2. Conversão e Limpeza de Datas
    pres_t['data_dt'] = pd.to_datetime(pres_t['data_encontro'], errors='coerce', dayfirst=True)
    pres_t = pres_t.dropna(subset=['data_dt'])
    
    # 3. Trava de Segurança: Ignorar datas futuras (Blindagem contra Naive/Aware Conflict)
    agora_br = dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)
    # Removemos o tzinfo para permitir a comparação direta com o Pandas Naive
    hoje_limite = agora_br.replace(tzinfo=None, hour=23, minute=59, second=59)
    
    # Garantimos que a coluna do Pandas também esteja sem timezone para a comparação
    pres_t['data_dt'] = pres_t['data_dt'].dt.tz_localize(None)
    
    pres_t = pres_t[pres_t['data_dt'] <= hoje_limite]
    
    if pres_t.empty: return None, pd.DataFrame()
    
    # 4. Pega a última data real
    ultima_data = pres_t['data_dt'].max()
    chamada_recente = pres_t[pres_t['data_dt'] == ultima_data]
    
    return ultima_data.date(), chamada_recente

def gerar_auditoria_chamadas_pendentes(df_turmas, df_pres, dias_limite=7):
    """Identifica turmas que não registraram chamada nos últimos X dias."""
    turmas_sem_chamada =[]
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    limite = hoje - dt_module.timedelta(days=dias_limite)
    
    for _, t in df_turmas.iterrows():
        nome_t = t['nome_turma']
        ultima_data, _ = obter_ultima_chamada_turma(df_pres, nome_t)
        
        if not ultima_data or ultima_data < limite:
            turmas_sem_chamada.append(nome_t)
            
    return turmas_sem_chamada

def obter_data_ultimo_sabado():
    # Mantida apenas por compatibilidade legada se necessário em outro lugar
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    dias_atras = (hoje.weekday() - 5) % 7
    return hoje - dt_module.timedelta(days=dias_atras)

def gerar_pdf_auditoria_chamadas(df_turmas, df_pres, df_cat, dias_limite=7):
    """Gera Auditoria de Chamadas com Resumo Executivo e Detalhamento com Temas."""
    pdf = FPDF()
    pdf.add_page()
    hoje = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    adicionar_cabecalho_diocesano(pdf, limpar_texto(f"AUDITORIA DE DIARIOS E CHAMADAS (Ultimos {dias_limite} dias)"))
    
    limite = hoje - dt_module.timedelta(days=dias_limite)
    
    # --- SESSÃO 1: RESUMO EXECUTIVO ---
    pdf.set_fill_color(240, 242, 246)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 8, limpar_texto(f"1. RESUMO EXECUTIVO DAS TURMAS (Data Base: {formatar_data_br(hoje)})"), ln=True, fill=True)
    
    pdf.set_fill_color(65, 123, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(50, 7, limpar_texto("Turma"), border=1, fill=True)
    pdf.cell(25, 7, limpar_texto("Status"), border=1, fill=True, align='C')
    pdf.cell(25, 7, limpar_texto("Ultima Chamada"), border=1, fill=True, align='C')
    pdf.cell(90, 7, limpar_texto("Catequista(s)"), border=1, fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 8)
    
    turmas_detalhes =[]
    
    for _, t in df_turmas.iterrows():
        nome_t = str(t['nome_turma']).upper()
        cats = str(t.get('catequista_responsavel', 'Nao informado'))
        ultima_data, chamada = obter_ultima_chamada_turma(df_pres, nome_t)
        
        if ultima_data and ultima_data >= limite:
            status_resumo = "EM DIA"
            cor_status = (46, 125, 50)
        elif ultima_data:
            status_resumo = "ATRASADA"
            cor_status = (224, 61, 17)
        else:
            status_resumo = "PENDENTE"
            cor_status = (224, 61, 17)
            
        data_str = formatar_data_br(ultima_data) if ultima_data else "---"
        
        # Desenha células sem truncar (ajustando larguras)
        pdf.set_font("helvetica", "", 7) # Fonte levemente menor para caber tudo
        pdf.cell(55, 6, limpar_texto(nome_t), border=1)
        pdf.set_text_color(*cor_status)
        pdf.set_font("helvetica", "B", 7)
        pdf.cell(20, 6, limpar_texto(status_resumo), border=1, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 7)
        pdf.cell(25, 6, limpar_texto(data_str), border=1, align='C')
        
        # Posição atual para o multi_cell dos catequistas
        curr_x = pdf.get_x()
        curr_y = pdf.get_y()
        pdf.multi_cell(90, 6, limpar_texto(cats), border=1)
        pdf.set_xy(10, curr_y + 6) # Garante que a próxima linha comece no lugar certo
        
        # Busca o tema real do diário para este encontro específico
        tema_dia = "Sem registro"
        if not chamada.empty:
            # Pega o primeiro tema não vazio da lista de presenças
            temas_validos = chamada['tema_do_dia'].dropna().unique()
            if len(temas_validos) > 0:
                tema_dia = str(temas_validos[0])
            
        turmas_detalhes.append({
            "nome": nome_t, "status": status_resumo, "data": ultima_data, 
            "tema": tema_dia, "chamada": chamada
        })
        
    pdf.ln(5)
    
    # --- SESSÃO 2: DETALHAMENTO E RESGATE PASTORAL ---
    if pdf.get_y() > 240: pdf.add_page()
    
    pdf.set_fill_color(240, 242, 246)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(65, 123, 153)
    pdf.cell(0, 8, limpar_texto("2. DETALHAMENTO DE FALTOSOS E RESGATE PASTORAL"), ln=True, fill=True)
    pdf.ln(2)
    
    for td in turmas_detalhes:
        if pdf.get_y() > 250: pdf.add_page()
        
        cor_bg = (65, 123, 153) if td['status'] == "EM DIA" else (224, 61, 17)
        pdf.set_fill_color(*cor_bg)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 9)
        
        data_exibicao = formatar_data_br(td['data']) if td['data'] else "Nenhuma"
        pdf.cell(0, 7, limpar_texto(f"TURMA: {td['nome']} | Status: {td['status']} | Ultima Chamada: {data_exibicao}"), border=1, ln=True, fill=True)
        
        pdf.set_text_color(0, 0, 0)
        
        if td['data']:
            pdf.set_font("helvetica", "I", 8)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(0, 6, limpar_texto(f"Tema do ultimo encontro: {td['tema']}"), border=1, ln=True, fill=True)
            
        chamada = td['chamada']
        if not chamada.empty and td['data'] and td['data'] >= limite:
            faltosos = chamada[chamada['status'] == 'AUSENTE']
            if not faltosos.empty:
                pdf.set_font("helvetica", "B", 8)
                pdf.cell(70, 6, limpar_texto("Catequizando Faltoso"), border=1)
                pdf.cell(120, 6, limpar_texto("Contatos (Mae / Pai / Resp.)"), border=1, ln=True)
                
                pdf.set_font("helvetica", "", 7)
                for _, f in faltosos.iterrows():
                    cat_info = df_cat[df_cat['id_catequizando'] == f['id_catequizando']]
                    contatos_str = "N/A"
                    if not cat_info.empty:
                        c = cat_info.iloc[0]
                        lista_contatos =[]
                        if str(c.get('tel_mae', '')).strip() not in["N/A", "", "None"]: lista_contatos.append(f"Mae: {c['tel_mae']}")
                        if str(c.get('tel_pai', '')).strip() not in["N/A", "", "None"]: lista_contatos.append(f"Pai: {c['tel_pai']}")
                        if str(c.get('contato_principal', '')).strip() not in ["N/A", "", "None"]: lista_contatos.append(f"Resp: {c['contato_principal']}")
                        contatos_str = " | ".join(lista_contatos) if lista_contatos else "Sem contato"
                    
                    pdf.cell(70, 6, limpar_texto(f['nome_catequizando'])[:45], border=1)
                    pdf.cell(120, 6, limpar_texto(contatos_str)[:85], border=1, ln=True)
            else:
                pdf.set_font("helvetica", "", 8)
                pdf.cell(0, 6, limpar_texto("Nenhuma falta registrada neste ultimo encontro."), border=1, ln=True)
        elif td['status'] == "ATRASADA":
            pdf.set_font("helvetica", "", 8)
            pdf.cell(0, 6, limpar_texto("O diario esta atrasado. Realize a chamada para visualizar os faltosos."), border=1, ln=True)
        else:
            pdf.set_font("helvetica", "", 8)
            pdf.cell(0, 6, limpar_texto("Sem registros desta turma no sistema."), border=1, ln=True)
            
        pdf.ln(3)

    return finalizar_pdf(pdf)

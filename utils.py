# --- SUBSTITUIR NO utils.py ---

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

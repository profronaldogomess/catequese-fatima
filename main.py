# --- ALERTAS DE GESTÃO ---
    ultima_data_chamada, chamada_recente = obter_ultima_chamada_turma(minhas_pres, turma_ativa)
    
    hoje_t = (dt_module.datetime.now(dt_module.timezone.utc) + dt_module.timedelta(hours=-3)).date()
    limite_t = hoje_t - dt_module.timedelta(days=7)
    
    col_a1, col_a2 = st.columns(2)
    if not ultima_data_chamada or ultima_data_chamada < limite_t:
        data_exibicao = formatar_data_br(ultima_data_chamada) if ultima_data_chamada else "Nenhuma"
        col_a1.error(f"⚠️ Nenhuma chamada registrada nos últimos 7 dias! (Última: {data_exibicao})")
    else:
        col_a1.success(f"✅ Chamada em dia! (Último encontro: {formatar_data_br(ultima_data_chamada)})")
        faltosos = chamada_recente[chamada_recente['status'] == 'AUSENTE']
        if not faltosos.empty:
            with st.expander(f"🚩 {len(faltosos)} Faltosos no último encontro"):
                for _, f in faltosos.iterrows():
                    cat_f = meus_alunos[meus_alunos['id_catequizando'] == f['id_catequizando']]
                    if not cat_f.empty:
                        c = cat_f.iloc[0]
                        st.write(f"• {c['nome_completo']}")
                        montar_botoes_whatsapp(c)

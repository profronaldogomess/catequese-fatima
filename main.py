# --- SUBSTITUIÇÃO: ABA t5 (CORREÇÃO TERMINOLÓGICA) ---
    with t5:
        st.subheader("🚀 Movimentação em Massa")
        if not df_turmas.empty and not df_cat.empty:
            c1, c2 = st.columns(2)
            opcoes_origem = ["CATEQUIZANDOS SEM TURMA"] + df_turmas['nome_turma'].tolist()
            t_origem = c1.selectbox("1. Turma de ORIGEM (Sair de):", opcoes_origem, key="mov_orig_v5")
            t_destino = c2.selectbox("2. Turma de DESTINO (Ir para):", df_turmas['nome_turma'].tolist(), key="mov_dest_v5")
            
            if t_origem:
                alunos_mov = df_cat[(df_cat['etapa'] == t_origem) & (df_cat['status'] == 'ATIVO')]
                if not alunos_mov.empty:
                    sel_todos = st.checkbox("Selecionar todos os catequizandos", key="chk_mov_todos_v5")
                    lista_ids = []
                    cols = st.columns(2)
                    for i, (_, al) in enumerate(alunos_mov.iterrows()):
                        with cols[i % 2]:
                            if st.checkbox(f"{al['nome_completo']}", value=sel_todos, key=f"mov_al_v5_{al['id_catequizando']}"):
                                lista_ids.append(al['id_catequizando'])
                    
                    st.divider()
                    # CORREÇÃO AQUI: "CATEQUIZANDOS" em vez de "ALUNOS"
                    if st.button(f"🚀 MOVER {len(lista_ids)} CATEQUIZANDOS", key="btn_exec_mov_v5"):
                        if t_destino and t_origem != t_destino and lista_ids:
                            if mover_catequizandos_em_massa(lista_ids, t_destino):
                                st.success(f"✅ Sucesso! {len(lista_ids)} catequizandos movidos para {t_destino}."); st.cache_data.clear(); time.sleep(2); st.rerun()

import streamlit as st

# Configura o redirecionamento automático
st.markdown("""
    <meta http-equiv="refresh" content="0; url=https://catequese-fatima-994011587222.southamerica-east1.run.app/">
""", unsafe_allow_html=True)

# Mensagem de fallback caso o navegador bloqueie o redirecionamento
st.title("Redirecionando para o novo sistema...")
st.write("Se o seu navegador não te levar automaticamente, clique no link abaixo:")
st.link_button("Ir para o novo site da Catequese", "https://catequese-fatima-994011587222.southamerica-east1.run.app/")

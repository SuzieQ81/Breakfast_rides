import streamlit as st

st.set_page_config(page_title="Breakfast Rides - Race Hub", layout="wide")

st.title("🚴‍♂️ Breakfast Rides - Race Hub")
st.subheader("Bem-vindo ao Dashboard de Classificações")

st.write("A carregar estrutura do campeonato...")

# Separadores para as classificações
tab1, tab2, tab3 = st.tabs(["🏆 Geral (GC)", "💚 Sprints", "🔴 Montanha (KOM)"])

with tab1:
    st.info("Classificação Geral em breve.")

with tab2:
    st.info("Pontuação de Sprints em breve.")

with tab3:
    st.info("Pontuação de Montanha em breve.")

import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Breakfast Rides - Race Hub", layout="wide", page_icon="🚴‍♂️")

st.title("🚴‍♂️ Breakfast Rides - Race Hub")
st.markdown("### Classificações Oficiais do Campeonato")

# Sidebar para Filtros
st.sidebar.header("⚙️ Filtros")
categoria = st.sidebar.selectbox("Seleciona a Categoria:", ["Todas", "Cat A", "Cat B", "Cat C"])

# --- DADOS DE EXEMPLO (Simulação) ---
# Geral (GC)
gc_data = pd.DataFrame({
    "Pos": [1, 2, 3, 4],
    "Atleta": ["Rider Alpha", "Rider Beta", "Rider Gamma", "Rider Delta"],
    "Categoria": ["Cat A", "Cat A", "Cat B", "Cat C"],
    "Etapas Concluídas": [3, 3, 3, 3],
    "Tempo Total": ["02:15:30", "02:16:12", "02:18:05", "02:22:40"],
    "Diferença": ["-", "+00:00:42", "+00:02:35", "+00:07:10"]
})

# Sprints (Camisola Verde)
sprint_data = pd.DataFrame({
    "Pos": [1, 2, 3],
    "Atleta": ["Rider Beta", "Rider Alpha", "Rider Gamma"],
    "Categoria": ["Cat A", "Cat A", "Cat B"],
    "Pontos Sprint": [45, 38, 22]
})

# Montanha (Camisola às Bolinhas)
kom_data = pd.DataFrame({
    "Pos": [1, 2, 3],
    "Atleta": ["Rider Gamma", "Rider Alpha", "Rider Delta"],
    "Categoria": ["Cat B", "Cat A", "Cat C"],
    "Pontos KOM": [30, 25, 18]
})

# Filtrar por Categoria
if categoria != "Todas":
    gc_data = gc_data[gc_data["Categoria"] == categoria]
    sprint_data = sprint_data[sprint_data["Categoria"] == categoria]
    kom_data = kom_data[kom_data["Categoria"] == categoria]

# Métricas no Topo
col1, col2, col3 = st.columns(3)
col1.metric("Líder GC", gc_data["Atleta"].iloc[0] if not gc_data.empty else "N/A")
col2.metric("Líder Sprints 💚", sprint_data["Atleta"].iloc[0] if not sprint_data.empty else "N/A")
col3.metric("Líder KOM 🔴", kom_data["Atleta"].iloc[0] if not kom_data.empty else "N/A")

st.divider()

# Separadores para as tabelas
tab1, tab2, tab3 = st.tabs(["🏆 Classificação Geral (GC)", "💚 Sprints", "🔴 Montanha (KOM)"])

with tab1:
    st.subheader("Classificação por Tempo (GC)")
    st.dataframe(gc_data, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Classificação por Pontos - Sprints")
    st.dataframe(sprint_data, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Classificação do Prémio da Montanha")
    st.dataframe(kom_data, use_container_width=True, hide_index=True)

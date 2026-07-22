import streamlit as st
import pandas as pd
import requests

# Configuração da página
st.set_page_config(page_title="Breakfast Rides - Race Hub", layout="wide", page_icon="🚴‍♂️")

st.title("🚴‍♂️ Breakfast Rides - Race Hub")
st.markdown("### Classificações Oficiais do Campeonato")

# Sidebar - Configurações da Evento ZwiftPower
st.sidebar.header("⚙️ ZwiftPower Live Data")
event_id = st.sidebar.text_input("ID do Evento ZwiftPower:", value="", placeholder="Ex: 3859201")
categoria = st.sidebar.selectbox("Seleciona a Categoria:", ["Todas", "Cat A", "Cat B", "Cat C", "Cat D"])

# Tentar obter cookie guardado nos Secrets do Streamlit (opcional)
zwift_cookie = st.secrets.get("ZWIFTPOWER_COOKIE", "")

@st.cache_data(ttl=300)  # Cache de 5 minutos para não sobrecarregar a API
def fetch_zwiftpower_data(event_id, cookie=""):
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Cookie": cookie_str,
}
    
    url_results = f"https://zwiftpower.com/api3/v1/viewer/results/{event_id}"
    url_primes = f"https://zwiftpower.com/api3/v1/viewer/primes/{event_id}"
    
    try:
        res_results = requests.get(url_results, headers=headers, timeout=10)
        res_primes = requests.get(url_primes, headers=headers, timeout=10)
        
        results_json = res_results.json() if res_results.status_code == 200 else None
        primes_json = res_primes.json() if res_primes.status_code == 200 else None
        
        return results_json, primes_json
    except Exception as e:
        return None, None

# Lógica de carregamento de dados
results_json, primes_json = None, None

if event_id:
    with st.spinner(f"A carregar dados do evento {event_id} do ZwiftPower..."):
        results_json, primes_json = fetch_zwiftpower_data(event_id, zwift_cookie)

if results_json and "data" in results_json and len(results_json["data"]) > 0:
    st.sidebar.success("✅ Conectado ao ZwiftPower!")
    
    # Processar Resultados GC
    df_raw = pd.DataFrame(results_json["data"])
    
    # Mapeamento de colunas do ZwiftPower
    gc_data = pd.DataFrame({
        "Pos": df_raw.get("pos", range(1, len(df_raw)+1)),
        "Atleta": df_raw.get("name", "Atleta"),
        "Categoria": df_raw.get("category", "N/A").apply(lambda x: f"Cat {x}"),
        "Equipa": df_raw.get("tc", "-"),
        "Tempo Total": df_raw.get("time_formatted", df_raw.get("time", "-")),
        "Avg w/kg": df_raw.get("wkg_avg", "-")
    })
    
    # Processar Primes (Sprints e KOMs) se existirem
    if primes_json and "data" in primes_json:
        primes_raw = pd.DataFrame(primes_json["data"])
        # Aqui podemos expandir o cálculo de pontos de Sprint / KOM
        sprint_data = primes_raw  # Estrutura base para processamento de pontos
    else:
        sprint_data = pd.DataFrame()
        
    kom_data = pd.DataFrame()

else:
    if event_id:
        st.sidebar.warning("⚠️ Não foi possível obter dados diretos. A mostrar dados simulados.")
    else:
        st.sidebar.info("💡 insere um Event ID para testar dados reais.")
        
    # --- DADOS MOCK (Simulação Fallback) ---
    gc_data = pd.DataFrame({
        "Pos": [1, 2, 3, 4],
        "Atleta": ["Rider Alpha", "Rider Beta", "Rider Gamma", "Rider Delta"],
        "Categoria": ["Cat A", "Cat A", "Cat B", "Cat C"],
        "Equipa": ["Zwift Club", "Zwift Club", "Breakfast Crew", "Solo"],
        "Tempo Total": ["02:15:30", "02:16:12", "02:18:05", "02:22:40"],
        "Avg w/kg": [4.2, 4.0, 3.4, 2.9]
    })
    
    sprint_data = pd.DataFrame({
        "Pos": [1, 2, 3],
        "Atleta": ["Rider Beta", "Rider Alpha", "Rider Gamma"],
        "Categoria": ["Cat A", "Cat A", "Cat B"],
        "Pontos Sprint": [45, 38, 22]
    })
    
    kom_data = pd.DataFrame({
        "Pos": [1, 2, 3],
        "Atleta": ["Rider Gamma", "Rider Alpha", "Rider Delta"],
        "Categoria": ["Cat B", "Cat A", "Cat C"],
        "Pontos KOM": [30, 25, 18]
    })

# Aplicar filtro de Categoria
if categoria != "Todas" and not gc_data.empty and "Categoria" in gc_data.columns:
    gc_data = gc_data[gc_data["Categoria"] == categoria]
    if not sprint_data.empty and "Categoria" in sprint_data.columns:
        sprint_data = sprint_data[sprint_data["Categoria"] == categoria]
    if not kom_data.empty and "Categoria" in kom_data.columns:
        kom_data = kom_data[kom_data["Categoria"] == categoria]

# Métricas no Topo
col1, col2, col3 = st.columns(3)
col1.metric("Líder GC", gc_data["Atleta"].iloc[0] if not gc_data.empty else "N/A")
col2.metric("Líder Sprints 💚", sprint_data["Atleta"].iloc[0] if not sprint_data.empty else "N/A")
col3.metric("Líder KOM 🔴", kom_data["Atleta"].iloc[0] if not kom_data.empty else "N/A")

st.divider()

# Separadores
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

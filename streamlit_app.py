import html
import time
import pandas as pd
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Breakfast Rides Dashboard", page_icon="🚴", layout="wide"
)

st.title("🚴 Breakfast Rides - Live Dashboard")


def format_time(seconds):
    """Converte segundos para formato MM:SS ou HH:MM:SS."""
    try:
        sec = float(seconds)
        mins, secs = divmod(sec, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}"
        return f"{int(mins):02d}:{int(secs):02d}"
    except (ValueError, TypeError):
        return seconds


def fetch_zwiftpower_data(event_id):
    """Procura os dados de um evento no ZwiftPower usando o timestamp dinâmico."""
    cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie_str,
    }

    # Adiciona o timestamp dinâmico no final da URL
    timestamp = int(time.time() * 1000)
    url = f"https://zwiftpower.com/cache3/results/{event_id}_view.json?_={timestamp}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição: {e}")
        return None


# Sidebar
st.sidebar.header("Configuração do Evento")
event_id_input = st.sidebar.text_input("ID do Evento ZwiftPower", value="5644967")

if st.sidebar.button("Carregar Dados") or event_id_input:
    with st.spinner("A carregar dados do ZwiftPower em tempo real..."):
        data_json = fetch_zwiftpower_data(event_id_input)

        if data_json:
            st.success("Dados do ZwiftPower carregados com sucesso!")

            tab_geral, tab_primes = st.tabs(
                ["🏆 Classificação Geral", "⚡ Primes / Sprints"]
            )

            # --- TAB 1: CLASSIFICAÇÃO GERAL ---
            with tab_geral:
                if "data" in data_json:
                    results = data_json["data"]
                    df = pd.DataFrame(results)

                    # Tratar nomes (descodificar caracteres HTML/emojis)
                    if "name" in df.columns:
                        df["name"] = df["name"].apply(
                            lambda x: html.unescape(str(x))
                        )

                    # Formatar tempo
                    if "time_gun" in df.columns:
                        df["Tempo"] = df["time_gun"].apply(format_time)

                    # Mapeamento de colunas principais
                    column_mapping = {
                        "pos": "Pos",
                        "position_in_cat": "Pos Cat",
                        "name": "Nome",
                        "tname": "Equipa",
                        "ftp": "FTP",
                        "Tempo": "Tempo",
                        "gap": "Diferença (s)",
                    }

                    cols_to_show = [
                        col for col in column_mapping.keys() if col in df.columns
                    ]
                    df_display = df[cols_to_show].rename(
                        columns=column_mapping
                    )

                    # Métricas de topo
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total de Atletas", len(df))
                    if "Tempo" in df_display.columns:
                        col2.metric(
                            "Tempo Vencedor", df_display["Tempo"].iloc[0]
                        )
                    if "Equipa" in df_display.columns:
                        col3.metric(
                            "Equipas Presentes",
                            df_display["Equipa"].nunique(),
                        )

                    st.markdown("---")
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True,
                    )

            # --- TAB 2: PRIMES / SPRINTS ---
            with tab_primes:
                # Verificar se os primes estão dentro de algum nó do JSON do view
                primes_data = data_json.get("primes") or data_json.get("laps")

                if primes_data:
                    df_primes = pd.DataFrame(primes_data)
                    for col in df_primes.columns:
                        if df_primes[col].dtype == "object":
                            df_primes[col] = df_primes[col].apply(
                                lambda x: (
                                    html.unescape(str(x))
                                    if pd.notnull(x)
                                    else x
                                )
                            )
                    st.dataframe(
                        df_primes,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "Estrutura de Primes/Laps pronta! Vamos inspecionar os campos retornados:"
                    )
                    with st.expander("🔍 Ver todas as chaves do JSON retornado"):
                        st.json(list(data_json.keys()))

        else:
            st.error(
                "Não foi possível obter a resposta do ZwiftPower. Verifica se o Cookie nos Secrets expirou."
            )

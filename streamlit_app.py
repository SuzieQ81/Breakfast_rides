import html
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
    """Procura os dados de um evento no ZwiftPower usando cookies e headers autenticados."""
    cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie_str,
    }

    url = f"https://zwiftpower.com/cache3/results/{event_id}_view.json"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return None


# Sidebar
st.sidebar.header("Configuração do Evento")
event_id_input = st.sidebar.text_input("ID do Evento ZwiftPower", value="5644967")

if st.sidebar.button("Carregar Dados") or event_id_input:
    with st.spinner("A carregar dados do ZwiftPower..."):
        response = fetch_zwiftpower_data(event_id_input)

        if response and response.status_code == 200:
            try:
                data_json = response.json()
                st.success("Dados do ZwiftPower carregados com sucesso!")

                # Criar separadores (Tabs) no dashboard
                tab_geral, tab_primes = st.tabs(
                    ["🏆 Classificação Geral", "⚡ Primes / Sprints"]
                )

                # --- TAB 1: CLASSIFICAÇÃO GERAL ---
                with tab_geral:
                    if "data" in data_json:
                        results = data_json["data"]
                        df = pd.DataFrame(results)

                        # Tratar nomes (descodificar caracteres HTML)
                        if "name" in df.columns:
                            df["name"] = df["name"].apply(
                                lambda x: html.unescape(str(x))
                            )

                        # Formatar tempo
                        if "time_gun" in df.columns:
                            df["Tempo"] = df["time_gun"].apply(format_time)

                        # Mapear e renomear colunas
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
                            col
                            for col in column_mapping.keys()
                            if col in df.columns
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
                    # Verifica as chaves comuns onde o ZwiftPower guarda os Primes/Sprints
                    primes_data = data_json.get("primes") or data_json.get(
                        "laps"
                    )

                    if primes_data:
                        df_primes = pd.DataFrame(primes_data)

                        # Limpeza de nomes nos primes se existirem colunas de atletas
                        for col in df_primes.columns:
                            if df_primes[col].dtype == "object":
                                df_primes[col] = df_primes[col].apply(
                                    lambda x: html.unescape(str(x))
                                )

                        st.subheader("Resultados dos Primes por Volta e Banner")
                        st.dataframe(
                            df_primes,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info(
                            "Este evento não tem estrutura de primes no objeto principal, ou está armazenado num nó secundário."
                        )

                        # Mostrar estrutura JSON bruta para inspecionar onde estão os Primes
                        with st.expander("🔍 Inspecionar Chaves do JSON da API"):
                            st.write("Chaves encontradas na resposta da API:")
                            st.json(list(data_json.keys()))

            except Exception as e:
                st.error(f"Erro ao processar os dados: {e}")

        elif response:
            st.error(f"Erro ao ligar ao ZwiftPower (Código {response.status_code}).")

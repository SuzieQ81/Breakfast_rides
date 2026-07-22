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

                if "data" in data_json:
                    results = data_json["data"]
                    df = pd.DataFrame(results)

                    # 1. Tratar nomes (descodificar caracteres HTML como emojis/bandeiras)
                    if "name" in df.columns:
                        df["name"] = df["name"].apply(
                            lambda x: html.unescape(str(x))
                        )

                    # 2. Formatar tempo (de segundos para MM:SS)
                    if "time_gun" in df.columns:
                        df["Tempo"] = df["time_gun"].apply(format_time)

                    # 3. Mapear e renomear colunas principais
                    column_mapping = {
                        "pos": "Pos",
                        "position_in_cat": "Pos Cat",
                        "name": "Nome",
                        "tname": "Equipa",
                        "ftp": "FTP",
                        "Tempo": "Tempo",
                        "gap": "Diferença (s)",
                    }

                    # Selecionar apenas as colunas disponíveis que queremos mostrar
                    cols_to_show = [
                        col for col in column_mapping.keys() if col in df.columns
                    ]
                    df_display = df[cols_to_show].rename(columns=column_mapping)

                    # Métricas de topo
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total de Atletas", len(df))
                    if "Tempo" in df_display.columns:
                        col2.metric("Tempo Vencedor", df_display["Tempo"].iloc[0])
                    if "Equipa" in df_display.columns:
                        col3.metric(
                            "Equipas Presentes",
                            df_display["Equipa"].nunique(),
                        )

                    st.markdown("---")
                    st.subheader("Classificação Geral")

                    # Exibir tabela limpa e formatada
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:
                    st.json(data_json)

            except Exception as e:
                st.error(f"Erro ao processar os dados da tabela: {e}")

        elif response:
            st.error(f"Erro ao ligar ao ZwiftPower (Código {response.status_code}).")

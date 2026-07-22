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


def fetch_zwiftpower_endpoint(event_id, endpoint_type="view"):
    """Fetch de dados do ZwiftPower (view ou primes) com os headers corretos."""
    cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://zwiftpower.com/events.php?zid={event_id}",
        "Cookie": cookie_str,
    }

    timestamp = int(time.time() * 1000)
    url = f"https://zwiftpower.com/cache3/results/{event_id}_{endpoint_type}.json?_={timestamp}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def clean_html_text(text):
    """Remove tags HTML e unescape de entidades de texto."""
    if not isinstance(text, str):
        return text
    # Remove tags HTML simples se existirem no texto retornado pela API
    import re

    clean = re.sub("<.*?>", "", text)
    return html.unescape(clean).strip()


# Sidebar
st.sidebar.header("Configuração do Evento")
event_id_input = st.sidebar.text_input("ID do Evento ZwiftPower", value="5644967")

if st.sidebar.button("Carregar Dados") or event_id_input:
    with st.spinner("A carregar dados do ZwiftPower em tempo real..."):
        data_view = fetch_zwiftpower_endpoint(event_id_input, "view")
        data_primes = fetch_zwiftpower_endpoint(event_id_input, "primes")

        if data_view and "data" in data_view:
            st.success("Dados do ZwiftPower carregados com sucesso!")

            tab_geral, tab_primes = st.tabs(
                ["🏆 Classificação Geral", "⚡ Primes / Sprints"]
            )

            # --- TAB 1: CLASSIFICAÇÃO GERAL ---
            with tab_geral:
                results = data_view["data"]
                df = pd.DataFrame(results)

                if "name" in df.columns:
                    df["name"] = df["name"].apply(
                        lambda x: html.unescape(str(x))
                    )

                if "time_gun" in df.columns:
                    df["Tempo"] = df["time_gun"].apply(format_time)

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
                df_display = df[cols_to_show].rename(columns=column_mapping)

                col1, col2, col3 = st.columns(3)
                col1.metric("Total de Atletas", len(df))
                if "Tempo" in df_display.columns and not df_display.empty:
                    col2.metric("Tempo Vencedor", df_display["Tempo"].iloc[0])
                if "Equipa" in df_display.columns:
                    col3.metric("Equipas Presentes", df_display["Equipa"].nunique())

                st.markdown("---")
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                )

            # --- TAB 2: PRIMES / SPRINTS ---
            with tab_primes:
                st.subheader("⚡ Resultados de Banners e Primes por Volta")

                if data_primes:
                    # O nó 'data' costuma conter a lista de segmentos/voltas
                    primes_list = (
                        data_primes.get("data", data_primes)
                        if isinstance(data_primes, dict)
                        else data_primes
                    )

                    if isinstance(primes_list, list) and len(primes_list) > 0:
                        df_primes = pd.DataFrame(primes_list)

                        # Limpar HTML / caracteres especiais de todas as colunas de texto
                        for col in df_primes.columns:
                            if df_primes[col].dtype == "object":
                                df_primes[col] = df_primes[col].apply(
                                    clean_html_text
                                )

                        st.dataframe(
                            df_primes,
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("Nenhum registo de segmento encontrado no ficheiro de primes.")
                else:
                    st.warning(
                        "Não foi possível obter os dados da aba Primes. "
                        "Verifica se o Cookie do ZwiftPower precisa de ser renovado nos Secrets."
                    )

        else:
            st.error(
                "Não foi possível obter os dados do ZwiftPower. Verifica o ID do evento ou a validade do Cookie."
            )

import html
import time
from bs4 import BeautifulSoup
import pandas as pd
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Breakfast Rides Dashboard", page_icon="🚴", layout="wide"
)

st.title("🚴 Breakfast Rides - Live Dashboard")


def get_session():
    """Cria uma sessão HTTP robusta com headers de browser real."""
    session = requests.Session()
    cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": cookie_str,
        }
    )
    return session


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


def fetch_view_json(session, event_id):
    """Procura os dados de classificação geral via JSON."""
    timestamp = int(time.time() * 1000)
    url = f"https://zwiftpower.com/cache3/results/{event_id}_view.json?_={timestamp}"
    try:
        res = session.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


def fetch_primes_json(session, event_id):
    """Procura os dados de primes/sprints diretamente na API do ZwiftPower."""
    urls = [
        f"https://zwiftpower.com/api.php?do=event_sprints&zid={event_id}",
        f"https://zwiftpower.com/cache3/results/{event_id}_primes.json",
    ]

    for url in urls:
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()

                # Caso venha no formato { "data": [...] }
                if isinstance(data, dict) and "data" in data:
                    data = data["data"]

                if isinstance(data, list) and len(data) > 0:
                    return pd.DataFrame(data)
        except Exception:
            continue

    return None

    return None


# Sidebar
st.sidebar.header("Configuração do Evento")
event_id_input = st.sidebar.text_input("ID do Evento ZwiftPower", value="5644967")

if st.sidebar.button("Carregar Dados") or event_id_input:
    with st.spinner("A carregar dados do ZwiftPower em tempo real..."):
        session = get_session()
        data_view = fetch_view_json(session, event_id_input)

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

                df_primes = fetch_primes_html(session, event_id_input)

                if df_primes is not None and not df_primes.empty:
                    st.dataframe(
                        df_primes,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "Não foi possível extrair a tabela de Primes automaticamente via scraping HTML. "
                        "Verifica se a sessão do Cookie nos Secrets expirou ou precisa de atualização."
                    )

        else:
            st.error(
                "Não foi possível obter os dados da classificação geral. Verifica o Cookie nos Secrets."
            )

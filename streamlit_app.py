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

    # Timestamp dinâmico (cache buster)
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

            # Definição das Tabs
            tab_geral, tab_primes = st.tabs(
                ["🏆 Classificação Geral", "⚡ Primes / Sprints"]
            )

            # --- TAB 1: CLASSIFICAÇÃO GERAL ---
            with tab_geral:
                if "data" in data_json:
                    results = data_json["data"]
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
                    df_display = df[cols_to_show].rename(
                        columns=column_mapping
                    )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total de Atletas", len(df))
                    if "Tempo" in df_display.columns and not df_display.empty:
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

            # --- TAB 2: PRIMES / SPRINTS (RAIO-X DE DIAGNÓSTICO) ---
            with tab_primes:
                st.subheader("🔍 Raio-X dos Primes")

                timestamp = int(time.time() * 1000)
                cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                        " AppleWebKit/537.36 (KHTML, like Gecko)"
                        " Chrome/150.0.0.0 Safari/537.36"
                    ),
                    "X-Requested-With": "XMLHttpRequest",
                    "Cookie": cookie_str,
                }

                url_primes = f"https://zwiftpower.com/cache3/results/{event_id_input}_primes.json?_={timestamp}"
                res_primes = requests.get(url_primes, headers=headers)

                st.write(
                    f"**Status HTTP de `_primes.json`:** `{res_primes.status_code}`"
                )

                if res_primes.status_code == 200:
                    st.success("🎉 O endpoint `_primes.json` respondeu!")
                    try:
                        st.json(res_primes.json())
                    except Exception as e:
                        st.error(f"Erro ao converter JSON: {e}")
                        st.code(res_primes.text[:500])
                else:
                    st.warning(
                        "O endpoint `_primes.json` não devolveu 200. A inspecionar o `_view.json`:"
                    )

                    if "data" in data_json and len(data_json["data"]) > 0:
                        primeiro_ciclista = data_json["data"][0]

                        chaves_interessantes = {
                            k: v
                            for k, v in primeiro_ciclista.items()
                            if any(
                                x in k.lower()
                                for x in [
                                    "prime",
                                    "sprint",
                                    "lap",
                                    "pts",
                                    "point",
                                    "seg",
                                    "mfl",
                                ]
                            )
                        }

                        st.write(
                            "**Campos de sprints/pontos no 1º ciclista:**"
                        )
                        st.json(chaves_interessantes)

                        with st.expander("👁️ Ver TODAS as chaves de um ciclista"):
                            st.json(list(primeiro_ciclista.keys()))

        else:
            st.error(
                "Não foi possível obter a resposta do ZwiftPower. Verifica se o Cookie nos Secrets ainda está válido."
            )

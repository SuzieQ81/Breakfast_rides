import requests
import streamlit as st

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Breakfast Rides Dashboard",
    page_icon="🚴",
    layout="wide"
)

st.title("🚴 Breakfast Rides - Live Dashboard")


def fetch_zwiftpower_data(event_id):
    """Procura os dados de um evento no ZwiftPower usando cookies e headers autenticados."""
    # Obter o cookie configurado nos Secrets do Streamlit
    cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")

    # Headers exatos para passar a validação do CloudFront e AJAX
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


# Barra Lateral - Controlo de Input
st.sidebar.header("Configuração do Evento")
event_id_input = st.sidebar.text_input("ID do Evento ZwiftPower", value="5644967")

if st.sidebar.button("Carregar Dados") or event_id_input:
    with st.spinner("A carregar dados do ZwiftPower..."):
        response = fetch_zwiftpower_data(event_id_input)

        if response and response.status_code == 200:
            try:
                data = response.json()
                st.success("Dados do ZwiftPower carregados com sucesso!")

                # Exibir informação bruta do evento ou processar os resultados
                if "data" in data:
                    results = data["data"]
                    st.metric("Total de Atletas Processados", len(results))

                    # Tabela rápida com os resultados
                    st.subheader("Resultados do Evento")
                    st.dataframe(results)
                else:
                    st.json(data)

            except ValueError:
                st.error("Erro ao converter a resposta da API em JSON.")
        elif response:
            st.error(
                f"Erro ao ligar ao ZwiftPower (Código {response.status_code})."
                " Verifica se o Cookie nos Secrets ainda é válido."
            )

# --- TAB 2: PRIMES / SPRINTS ---
with tab_primes:
    st.subheader("🔍 Raio-X dos Primes")

    # 1. Testar o endpoint _primes.json com o timestamp que descobriste
    timestamp = int(time.time() * 1000)
    cookie_str = st.secrets.get("ZWIFTPOWER_COOKIE", "")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie_str,
    }

    url_primes = f"https://zwiftpower.com/cache3/results/{event_id_input}_primes.json?_={timestamp}"
    res_primes = requests.get(url_primes, headers=headers)

    st.write(f"**Status HTTP de `_primes.json`:** `{res_primes.status_code}`")

    if res_primes.status_code == 200:
        st.success("🎉 O endpoint `_primes.json` respondeu!")
        try:
            primes_json = res_primes.json()
            st.json(primes_json)
        except Exception as e:
            st.error(f"Erro ao converter JSON: {e}")
            st.code(res_primes.text[:500])
    else:
        st.warning(
            "O endpoint `_primes.json` não devolveu 200. Vamos ver se os sprints estão dentro do ciclista no `_view.json`:"
        )

        if "data" in data_json and len(data_json["data"]) > 0:
            primeiro_ciclista = data_json["data"][0]

            # Filtrar chaves do primeiro ciclista para ver se há alguma relacionada com sprints/primes/laps
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
                "**Campos relacionados com sprints/pontos no 1º ciclista:**"
            )
            st.json(chaves_interessantes)

            with st.expander("👁️ Ver TODAS as chaves de um ciclista"):
                st.json(list(primeiro_ciclista.keys()))

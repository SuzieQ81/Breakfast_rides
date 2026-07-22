def fetch_primes_html(session, event_id):
    """Procura os dados de primes tentando os endpoints de API e scraping das tabelas HTML."""
    
    # 1. Primeira tentativa: Endpoint de dados brutos dos Primes
    timestamp = int(time.time() * 1000)
    json_url = f"https://zwiftpower.com/cache3/results/{event_id}_primes.json?_={timestamp}"
    
    try:
        res = session.get(json_url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", data) if isinstance(data, dict) else data
            if isinstance(items, list) and len(items) > 0:
                return pd.DataFrame(items)
    except Exception:
        pass

    # 2. Segunda tentativa: Scraping da vista de eventos com o parâmetro de ação do ZwiftPower
    html_urls = [
        f"https://zwiftpower.com/api.php?do=event_primes&zid={event_id}",
        f"https://zwiftpower.com/events.php?zid={event_id}&tab=primes",
        f"https://zwiftpower.com/events.php?zid={event_id}"
    ]

    for url in html_urls:
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Procura qualquer tabela no HTML retornado
                tables = soup.find_all("table")
                for table in tables:
                    rows = []
                    for tr in table.find_all("tr"):
                        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                        if cells:
                            rows.append(cells)
                    
                    if len(rows) > 1:
                        # Se encontrar uma tabela com colunas relevantes
                        header = rows[0]
                        if any(col.lower() in ["banner", "lap", "1st", "2nd", "sprint"] for col in header):
                            return pd.DataFrame(rows[1:], columns=header)
        except Exception:
            continue
            
    return None

import httpx

async def get_market_data():
    async with httpx.AsyncClient() as client:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        res = await client.get(url)
        data = res.json()

        return {
            "bitcoin_price": data.get("bitcoin", {}).get("usd", "N/A")
        }

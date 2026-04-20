import asyncio
import httpx
from sqlalchemy import select
from db import AsyncSessionLocal
from models import Sales

# ================== OLLAMA ==================
async def call_ollama(prompt):
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False
            }
        )
        return res.json().get("response", "").strip()


# ================== DB DATA ==================
async def get_sales_data():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Sales).order_by(Sales.id.desc()).limit(5)
        )
        rows = result.scalars().all()

        return [
            {
                "revenue": r.revenue,
                "growth": r.growth,
                "period": r.period
            }
            for r in rows
        ]


# ================== REAL MARKET DATA ==================
async def get_market_data():
    async with httpx.AsyncClient() as client:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        res = await client.get(url)

        data = res.json()

        return {
            "bitcoin_price": data.get("bitcoin", {}).get("usd", "N/A")
        }


# ================== AGGREGATION ==================
async def aggregate_data():
    sales, market = await asyncio.gather(
        get_sales_data(),
        get_market_data()
    )

    return {
        "sales": sales,
        "market": market
    }


# ================== STRUCTURED SUMMARY ==================
def summarize_structured(data):
    if not data:
        return "No data available."

    latest = data[0]

    return f"""
Summary:
Revenue: ${latest.get('revenue')}
Growth: {latest.get('growth')}
Period: {latest.get('period')}
""".strip()


# ================== LLM SUMMARY ==================
async def summarize_llm(data, market):
    latest = data[0] if data else {}

    prompt = f"""
You are a business analyst.

Write ONE short sentence including:
- revenue
- growth
- period
- market context (bitcoin price)

Revenue: {latest.get('revenue')}
Growth: {latest.get('growth')}
Period: {latest.get('period')}
Bitcoin Price: {market.get('bitcoin_price')}

Rules:
- One line
- Include all values
- Natural sentence

Example:
Revenue is $18,000 with 10% growth over 2 weeks, supported by strong market conditions with Bitcoin at $65,000.

Answer:
"""
    return await call_ollama(prompt)


# ================== MAIN WORKFLOW ==================
async def run_workflow(user_input):
    logs = []

    # 1. Fetch data
    data = await aggregate_data()
    logs.append("OK fetched DB + market data")

    sales = data["sales"]
    market = data["market"]

    # 2. Structured summary
    structured = summarize_structured(sales)
    logs.append("OK structured summary ready")

    # 3. LLM summary
    llm_summary = await summarize_llm(sales, market)
    logs.append("OK LLM summary ready")

    # 4. Format logs safely
    log_text = "\n".join(f"- {l}" for l in logs)

    return f"""
LOGS:
{log_text}

STRUCTURED:
{structured}

ONE-LINE:
{llm_summary}
""".strip()
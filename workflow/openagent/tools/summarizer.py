from openagent.services.llm_service import call_llm

def structured_summary(data):
    latest = data[0] if data else {}

    return f"""
Summary:
Revenue: ${latest.get('revenue')}
Growth: {latest.get('growth')}
Period: {latest.get('period')}
""".strip()

async def llm_summary(data, market):
    latest = data[0] if data else {}

    prompt = f"""
Write ONE line summary with:
- revenue
- growth
- period
- bitcoin price

Revenue: {latest.get('revenue')}
Growth: {latest.get('growth')}
Period: {latest.get('period')}
Bitcoin: {market.get('bitcoin_price')}
"""

    return await call_llm(prompt)

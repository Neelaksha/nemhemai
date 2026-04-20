    #!/bin/bash

echo "🚀 Creating modular project structure..."

# Create folders
mkdir -p openagent/{workflows,services,tools,router,utils}

cd openagent

# Create files
touch api.py
touch workflows/chat_workflow.py
touch workflows/insights_workflow.py
touch services/llm_service.py
touch services/db_service.py
touch services/market_service.py
touch tools/summarizer.py
touch tools/emailer.py
touch router/workflow_router.py
touch utils/formatter.py

# ---------------- API ----------------
cat > api.py << 'EOF'
from fastapi import FastAPI
from router.workflow_router import choose_workflow

from workflows.insights_workflow import run_workflow as insights_workflow
from workflows.chat_workflow import run_workflow as chat_workflow

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat(req: dict):
    user_msg = req["messages"][-1]["content"]

    workflow = choose_workflow(user_msg)

    if workflow == "insights":
        result = await insights_workflow(user_msg)
    else:
        result = await chat_workflow(user_msg)

    return {
        "choices": [
            {"message": {"role": "assistant", "content": result}}
        ]
    }
EOF

# ---------------- ROUTER ----------------
cat > router/workflow_router.py << 'EOF'
def choose_workflow(user_msg: str):
    msg = user_msg.lower()

    if any(k in msg for k in ["insight", "trend", "analysis", "report"]):
        return "insights"

    return "chat"
EOF

# ---------------- LLM SERVICE ----------------
cat > services/llm_service.py << 'EOF'
import httpx

async def call_llm(prompt: str) -> str:
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
EOF

# ---------------- DB SERVICE ----------------
cat > services/db_service.py << 'EOF'
from sqlalchemy import select
from db import AsyncSessionLocal
from models import Sales

async def get_sales_data(limit=5):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Sales).order_by(Sales.id.desc()).limit(limit)
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
EOF

# ---------------- MARKET SERVICE ----------------
cat > services/market_service.py << 'EOF'
import httpx

async def get_market_data():
    async with httpx.AsyncClient() as client:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        res = await client.get(url)
        data = res.json()

        return {
            "bitcoin_price": data.get("bitcoin", {}).get("usd", "N/A")
        }
EOF

# ---------------- SUMMARIZER ----------------
cat > tools/summarizer.py << 'EOF'
from services.llm_service import call_llm

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
EOF

# ---------------- INSIGHTS WORKFLOW ----------------
cat > workflows/insights_workflow.py << 'EOF'
import asyncio
from services.db_service import get_sales_data
from services.market_service import get_market_data
from tools.summarizer import structured_summary, llm_summary

async def run_workflow(user_input):
    logs = []

    sales, market = await asyncio.gather(
        get_sales_data(),
        get_market_data()
    )
    logs.append("OK fetched data")

    structured = structured_summary(sales)
    logs.append("OK structured")

    llm = await llm_summary(sales, market)
    logs.append("OK llm")

    log_text = "\\n".join(f"- {l}" for l in logs)

    return f"""
LOGS:
{log_text}

STRUCTURED:
{structured}

ONE-LINE:
{llm}
""".strip()
EOF

# ---------------- CHAT WORKFLOW ----------------
cat > workflows/chat_workflow.py << 'EOF'
async def run_workflow(user_input):
    return f"Echo: {user_input}"
EOF

echo "✅ Setup complete!"
echo "👉 Run: uvicorn api:app --reload"
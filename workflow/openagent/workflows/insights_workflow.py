# Insights Workflow


import asyncio
from openagent.services.db_service import get_sales_data
from openagent.services.market_service import get_market_data
from openagent.tools.summarizer import structured_summary, llm_summary
from openagent.tools.emailer import send_email


async def run_workflow(user_input):
    logs = []

    # 🔹 Fetch data
    sales, market = await asyncio.gather(
        get_sales_data(),
        get_market_data()
    )
    logs.append("OK fetched data")

    # 🔹 Structured summary
    structured = structured_summary(sales)
    logs.append("OK structured")

    # 🔹 LLM summary
    llm = await llm_summary(sales, market)
    logs.append("OK llm")

    # 🔥 EMAIL LOGIC (MOVE INSIDE FUNCTION)
    email_result = ""

    if "email" in user_input.lower():
        email_result = send_email(
            to_email="test@example.com",
            subject="Sales Insights",
            body=f"{structured}\n\n{llm}"
        )
        logs.append("OK email sent")

    # 🔹 Logs formatting
    log_text = "\n".join(f"- {l}" for l in logs)

    return f"""
LOGS:
{log_text}

STRUCTURED:
{structured}

ONE-LINE:
{llm}

EMAIL:
{email_result}
""".strip()
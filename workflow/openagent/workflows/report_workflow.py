import asyncio
import json

from openagent.services.db_service import get_sales_data
from openagent.services.llm_service import call_llm
from openagent.tools.emailer import send_email


def safe_parse(text: str):
    try:
        return json.loads(text)
    except:
        return {}


async def run_workflow(user_input):
    logs = []

    # 🔹 Parse request (LLM)
    parsed_raw = await call_llm(f"""
    Extract:
    - start_date
    - end_date
    - report_type

    Return JSON only.

    Input: {user_input}
    """)

    parsed = safe_parse(parsed_raw)
    logs.append("OK parsed request")

    # fallback dates (important)
    start_date = parsed.get("start_date", "2024-01-01")
    end_date = parsed.get("end_date", "2024-12-31")

    # 🔹 Fetch data
    #sales = await get_sales_data(start_date, end_date)
    sales = await get_sales_data(
        limit=100,
        start_date=start_date,
        end_date=end_date
    )
    logs.append("OK fetched sales")

    # 🔹 Process data (deterministic)
    total_revenue = sum(x["revenue"] for x in sales)
    total_orders = sum(x["orders"] for x in sales)

    processed = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "avg_order_value": total_revenue / total_orders if total_orders else 0
    }

    logs.append("OK processed metrics")

    # 🔹 LLM Insights
    insights = await call_llm(f"""
    Data:
    {processed}

    Write:
    - 3 key insights
    - 1 anomaly
    - 1 recommendation
    """)

    logs.append("OK insights generated")

    # 🔹 Email (optional trigger)
    email_result = ""

    if "email" in user_input.lower():
        email_result = send_email(
            to_email="test@example.com",
            subject="Automated Report",
            body=f"{processed}\n\n{insights}"
        )
        logs.append("OK email sent")

    # 🔹 Logs formatting
    log_text = "\n".join(f"- {l}" for l in logs)

    return f"""
📊 Sales Report

Total Revenue: {processed['total_revenue']}
Total Orders: {processed['total_orders']}
Avg Order Value: {processed['avg_order_value']}

Insights:
{insights}

{f"📧 Email sent: {email_result}" if email_result else ""}
""".strip()
#     return f"""
# REPORT WORKFLOW

# LOGS:
# {log_text}

# METRICS:
# {processed}

# INSIGHTS:
# {insights}

# EMAIL:
# {email_result}
# """.strip()
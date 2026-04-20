# orchestrator.py

import json
from agents import planner
from tools import get_sales_data, summarize_sales, send_email


def safe_parse_json(text):
    try:
        return json.loads(text)
    except:
        # fallback: try to extract JSON
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
        raise ValueError("Invalid JSON")


def run_workflow(user_input: str):
    plan_response = planner(user_input)

    try:
        steps = safe_parse_json(plan_response.content)
    except Exception as e:
        return f"❌ Plan parsing failed:\n{plan_response.content}"

    context = {}
    logs = []

    for step in steps:
        action = step.get("step")

        if action == "get_sales_data":
            context["data"] = get_sales_data()
            logs.append("✔ Got sales data")

        elif action == "summarize_sales":
            context["summary"] = summarize_sales(context.get("data", {}))
            logs.append("✔ Summarized data")

        elif action == "send_email":
            logs.append(send_email(context.get("summary", "")))

        else:
            logs.append(f"⚠ Unknown step: {action}")

    return "\n".join(logs + ["\n---\n", context.get("summary", "")])
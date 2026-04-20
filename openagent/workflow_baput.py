import asyncio
import json
import requests
from agentscope.agent import AgentBase
from agentscope.message import Msg


# =========================
# OLLAMA CALL
# =========================
def call_ollama(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


# =========================
# TOOLS (REAL WORLD ACTIONS)
# =========================
def db_query():
    return {
        "orders": 128,
        "revenue": 15400,
        "status": "healthy"
    }


def fetch_files():
    return "📁 File: quarterly_report.pdf | 12 pages | confidential"


def send_message(content: str):
    print("\n📨 Sending Message...\n")
    print(content)
    return "✅ Message sent"


def format_report(data):
    return f"""
📊 SYSTEM REPORT
Orders: {data.get('orders')}
Revenue: {data.get('revenue')}
Status: {data.get('status')}
"""


# =========================
# PLANNER AGENT
# =========================
class PlannerAgent(AgentBase):

    def __init__(self):
        super().__init__()
        self.name = "Planner"

    async def reply(self, msg: Msg = None):

        prompt = f"""
You are a workflow planner.

Convert user request into STRICT JSON steps.

ONLY output JSON array:

[
  {{"step": "db_query"}},
  {{"step": "format_report"}},
  {{"step": "fetch_files"}},
  {{"step": "send_message"}}
]

Available steps:
- db_query
- format_report
- fetch_files
- send_message

RULES:
- No explanation
- No extra text
- Only JSON

User Request:
{msg.content}
"""

        output = call_ollama(prompt)

        return Msg(
            name=self.name,
            content=output,
            role="assistant"
        )


# =========================
# EXECUTOR AGENT
# =========================
class ExecutorAgent(AgentBase):

    def __init__(self):
        super().__init__()
        self.name = "Executor"

    async def run(self, steps):

        context = {}
        logs = []

        for step in steps:
            action = step.get("step")

            # ---- DB QUERY ----
            if action == "db_query":
                context["db"] = db_query()
                logs.append("✔ DB queried")

            # ---- FORMAT REPORT ----
            elif action == "format_report":
                context["report"] = format_report(context.get("db", {}))
                logs.append("✔ report formatted")

            # ---- FETCH FILES ----
            elif action == "fetch_files":
                context["file"] = fetch_files()
                logs.append("✔ file fetched")

            # ---- SEND MESSAGE ----
            elif action == "send_message":
                msg = context.get("report", "") + "\n" + context.get("file", "")
                logs.append(send_message(msg))

            else:
                logs.append(f"⚠ unknown step: {action}")

        return logs, context


# =========================
# SAFE JSON PARSER
# =========================
def safe_parse(text: str):
    try:
        return json.loads(text)
    except:
        start = text.find("[")
        end = text.rfind("]")
        return json.loads(text[start:end+1])


# =========================
# ORCHESTRATOR (BRAIN)
# =========================
async def run_workflow(user_input: str):

    planner = PlannerAgent()
    executor = ExecutorAgent()

    msg = Msg(name="user", content=user_input, role="user")

    # STEP 1: PLAN
    plan = await planner.reply(msg)

    try:
        steps = safe_parse(plan.content)
    except:
        return f"❌ Failed to parse plan:\n{plan.content}"

    # STEP 2: EXECUTE
    logs, context = await executor.run(steps)

    return "\n".join(
        logs +
        ["\n===== FINAL OUTPUT =====\n"] +
        [context.get("report", "")]
    )


# =========================
# RUN TEST
# =========================
if __name__ == "__main__":

    test_input = """
    Get system data from DB, generate report,
    fetch related files and send message.
    """

    result = asyncio.run(run_workflow(test_input))

    print("\n=====================\n")
    print(result)
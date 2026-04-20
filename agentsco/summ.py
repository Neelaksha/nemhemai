# summ.py

import asyncio
import requests
from agentscope.agent import AgentBase
from agentscope.message import Msg


# ------------------ OLLAMA CALL ------------------
def call_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


# ------------------ CUSTOM AGENT ------------------
class EmailAgent(AgentBase):

    def __init__(self):
        super().__init__()
        self.name = "EmailSummarizer"

    async def reply(self, x: Msg = None):   # ✅ async
        email_content = x.content

        prompt = f"""
You are an expert email analyst.

Extract EXACTLY:

1. Summary (max 2 lines)
2. Key Points (bullet points)
3. Action Items (VERY IMPORTANT)

Rules for Action Items:
- Convert responsibilities into tasks
- ALWAYS include owner if mentioned
- Even implicit responsibilities = action items
- Never say "None" unless absolutely no task exists

Format strictly:

Summary:
- ...

Key Points:
- ...

Action Items:
- <person>: <task>

Email:
{email_content}
"""

        output = call_ollama(prompt)

        return Msg(
            name=self.name,
            content=output,
            role="assistant"
        )


# ------------------ EMAIL ------------------
def fetch_email():
    return """
Subject: Project Deadline Update

The deadline is moved to next Friday.
John will handle deployment.
Sarah will finalize UI.
"""


# ------------------ MAIN ------------------
async def main():
    agent = EmailAgent()

    msg = Msg(
        name="user",
        content=fetch_email(),
        role="user"
    )

    response = await agent.reply(msg)   # ✅ await

    print("\n===== RESULT =====\n")
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())   # ✅ required
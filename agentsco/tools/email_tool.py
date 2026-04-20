from agentscope.message import Msg
from summ import EmailAgent

agent = EmailAgent()

async def email_summarizer(email_text: str) -> str:
    msg = Msg(name="user", content=email_text, role="user")
    response = await agent.reply(msg)
    return response.content
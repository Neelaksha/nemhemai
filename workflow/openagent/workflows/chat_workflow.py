from openagent.services.llm_service import call_llm


async def run_workflow(user_input: str):

    prompt = f"""
You are a helpful AI assistant.

Answer clearly and concisely.

User: {user_input}
Assistant:
"""

    response = await call_llm(prompt)

    if not response or len(response.strip()) == 0:
        return "Sorry, I couldn't generate a response."

    return response.strip()
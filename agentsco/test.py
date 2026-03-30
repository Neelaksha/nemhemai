import asyncio

from agentscope.agent import ReActAgent, UserAgent
from agentscope.models.ollama_model import OllamaChatModel
from agentscope.formatter._ollama_formatter import OllamaChatFormatter
from agentscope.message import Msg

async def main():
    # 1) Create the Ollama model wrapper
    ollama_model = OllamaChatModel(
        model_name="llama3",               # Your local model name
        formatter=OllamaChatFormatter(),   # Use Ollama formatter
        stream=False
    )

    # 2) Build the agent
    agent = ReActAgent(
        name="OllamaAgent",
        sys_prompt="You are a helpful assistant.",
        model=ollama_model
    )

    # 3) Start simple chat loop
    last_msg = None
    while True:
        # Generate response
        last_msg = await agent(last_msg)
        print(f"Agent: {last_msg.get_text_content()}")

        # Get user input
        user_text = input("You: ")
        if user_text.lower() in {"quit", "exit"}:
            break

        # Convert to agent message and feed into loop
        last_msg = Msg(name="user", content=user_text, role="user")

asyncio.run(main())
# # agents.py

# from agentscope.agent import ReActAgent, UserAgent
# from agentscope.model import OllamaChatModel
# from agentscope.formatter._ollama_formatter import OllamaChatFormatter
# from agentscope.message import Msg

# # Initialize model
# setup_model()

# planner = DialogAgent(
#     name="planner",
#     model_config_name="ollama_llama3",
#     sys_prompt="""
# You are a planner agent.

# Break user requests into steps.

# Return ONLY valid JSON:
# [
#   {"step": "get_sales_data"},
#   {"step": "summarize_sales"},
#   {"step": "send_email"}
# ]
# """
# )

# executor = DialogAgent(
#     name="executor",
#     model_config_name="ollama_llama3",
#     sys_prompt="""
# You execute tasks using tools.
# Be concise.
# """
# )
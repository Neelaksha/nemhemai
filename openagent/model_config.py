# model_config.py

from agentscope import init
from agentscope.models import OllamaChatModel


def setup_model():
    init(
        model_configs=[
            {
                "config_name": "ollama_llama3",
                "model_type": "ollama_chat",
                "model_name": "llama3",
                "api_base": "http://localhost:11434",
            }
        ]
    )
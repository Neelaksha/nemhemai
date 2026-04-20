from email_tool import email_summarizer

tools = [
    {
        "name": "email_summarizer",
        "description": "Summarize emails and extract action items",
        "parameters": {
            "type": "object",
            "properties": {
                "email_text": {"type": "string"}
            },
            "required": ["email_text"]
        },
        "function": email_summarizer
    }
]
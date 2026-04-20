from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from workflow_baput import run_workflow

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============== SCHEMAS ===============
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


# =============== REQUIRED BY OPEN WEBUI ===============
@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [
            {
                "id": "baput-workflow",
                "object": "model",
                "owned_by": "local"
            }
        ]
    }


# =============== CHAT ENDPOINT ===============
@app.post("/v1/chat/completions")
async def chat(req: ChatRequest):

    user_input = req.messages[-1].content

    result = await run_workflow(user_input)

    return {
        "id": "baput",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result
                }
            }
        ]
    }
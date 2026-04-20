# app.py

from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator import run_workflow

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    return {"response": run_workflow(req.message)}
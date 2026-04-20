# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from orchestrator import run_workflow

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ REQUIRED for OpenWebUI
# @app.get("/v1/models")
# async def get_models():
#     return {
#         "object": "list",
#         "data": [
#             {
#                 "id": "agent-model",
#                 "object": "model",
#                 "owned_by": "custom"
#             }
#         ]
#     }

# # ✅ Chat endpoint
# @app.post("/v1/chat/completions")
# async def chat(req: dict):
#     user_msg = req["messages"][-1]["content"]

#     result = await run_workflow(user_msg)

#     print("RESULT SENT TO UI:\n", result)  # ✅ debug

#     return {
#         "id": "chatcmpl-123",
#         "object": "chat.completion",
#         "created": 1710000000,
#         "model": "agent-model",
#         "choices": [
#             {
#                 "index": 0,
#                 "message": {
#                     "role": "assistant",
#                     "content": str(result)  # ✅ ensure string
#                 },
#                 "finish_reason": "stop"
#             }
#         ],
#         "usage": {
#             "prompt_tokens": 0,
#             "completion_tokens": 0,
#             "total_tokens": 0
#         }
#     }




# ##Working
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import StreamingResponse
# import json
# import asyncio

# from orchestrator import run_workflow

# #from orchestrator_insights import run_workflow

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/v1/models")
# async def get_models():
#     return {
#         "object": "list",
#         "data": [{"id": "agent-model", "object": "model"}]
#     }


# @app.post("/v1/chat/completions")
# async def chat(req: dict):

#     user_msg = req["messages"][-1]["content"]

#     # 🔥 run your agent
#     result = await run_workflow(user_msg)

#     print("FINAL RESULT:\n", result)

#     async def stream():
#         for char in str(result):
#             chunk = {
#                 "choices": [
#                     {
#                         "delta": {"content": char},
#                         "index": 0,
#                         "finish_reason": None
#                     }
#                 ]
#             }
#             yield f"data: {json.dumps(chunk)}\n\n"
#             await asyncio.sleep(0.01)

#         yield "data: [DONE]\n\n"

#     if req.get("stream"):
#         return StreamingResponse(stream(), media_type="text/event-stream")

#     return {
#         "id": "chatcmpl-123",
#         "object": "chat.completion",
#         "model": "agent-model",
#         "choices": [
#             {
#                 "message": {
#                     "role": "assistant",
#                     "content": str(result)
#                 }
#             }
#         ]
#     }



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio

# import BOTH workflows
from orchestrator import run_workflow as chat_workflow
from orchestrator_insights import run_workflow as insights_workflow

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/models")
async def get_models():
    return {
        "object": "list",
        "data": [
            {"id": "agent-model", "object": "model"},
            {"id": "insights-model", "object": "model"},
        ]
    }


# ================== ROUTER ==================
def choose_workflow(user_msg: str):
    msg = user_msg.lower()

    # simple rules (you can improve later)
    if any(k in msg for k in ["insight", "trend", "analysis", "report"]):
        return "insights"

    return "chat"


# ================== CHAT ENDPOINT ==================
@app.post("/v1/chat/completions")
async def chat(req: dict):

    user_msg = req["messages"][-1]["content"]

    # 🔥 choose workflow
    workflow_type = choose_workflow(user_msg)

    if workflow_type == "insights":
        result = await insights_workflow(user_msg)
        model_used = "insights-model"
    else:
        result = await chat_workflow(user_msg)
        model_used = "agent-model"

    print(f"WORKFLOW: {workflow_type}")
    print("FINAL RESULT:\n", result)

    # ================== STREAM ==================
    async def stream():
        text = str(result)
        chunk_size = 25

        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]

            chunk = {
                "choices": [
                    {
                        "delta": {"content": chunk_text},
                        "index": 0,
                        "finish_reason": None
                    }
                ]
            }

            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)

        yield "data: [DONE]\n\n"

    if req.get("stream"):
        return StreamingResponse(stream(), media_type="text/event-stream")

    # ================== NORMAL RESPONSE ==================
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "model": model_used,
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": str(result)
                }
            }
        ]
    }
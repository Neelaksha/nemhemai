# """
# cashclaw_pipeline.py — OpenWebUI Pipeline Server
# Runs as a separate FastAPI server on port 9099.
# OpenWebUI connects to it and can trigger it automatically.

# Start with:
#   python cashclaw_pipeline.py

# Then connect in OpenWebUI:
#   Admin Panel → Settings → Pipelines → http://localhost:9099
# """

# from typing import Iterator
# from fastapi import FastAPI, Request
# from fastapi.responses import StreamingResponse, JSONResponse
# import psycopg2
# import os
# import json
# import requests
# from datetime import datetime
# from dotenv import load_dotenv
# import uvicorn

# # ── Load env ──────────────────────────────────────────────
# _DIR     = os.path.dirname(os.path.abspath(__file__))
# _BOT_DIR = os.path.dirname(_DIR)  # one level up from pipelines/
# load_dotenv(os.path.join(_BOT_DIR, ".env"))

# DB_CONFIG = {
#     "dbname":   os.getenv("DB_NAME",     "freelance_bot"),
#     "user":     os.getenv("DB_USER",     "postgres"),
#     "password": os.getenv("DB_PASSWORD", "sql@234"),
#     "host":     os.getenv("DB_HOST",     "localhost"),
#     "port":     os.getenv("DB_PORT",     "5433"),
# }

# OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# FAST_MODEL  = os.getenv("FAST_MODEL",      "qwen2.5-coder:3b")
# PASS_SCORE  = 50

# app = FastAPI(title="CashClaw Pipeline")


# # ══════════════════════════════════════════════════════════
# # DB HELPERS
# # ══════════════════════════════════════════════════════════

# def get_conn():
#     return psycopg2.connect(**DB_CONFIG)


# def get_db_summary() -> dict:
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("SELECT COUNT(*) FROM jobs")
#             total = cur.fetchone()[0]

#             cur.execute("SELECT COUNT(*) FROM jobs WHERE analyzed_at IS NULL")
#             unanalyzed = cur.fetchone()[0]

#             cur.execute("SELECT COUNT(*) FROM jobs WHERE decided_at IS NOT NULL")
#             decided = cur.fetchone()[0]

#             cur.execute(f"""
#                 SELECT COUNT(*) FROM jobs
#                 WHERE decided_at IS NOT NULL
#                   AND feasibility_score >= {PASS_SCORE}
#             """)
#             ready = cur.fetchone()[0]

#             cur.execute("""
#                 SELECT COUNT(*) FROM jobs
#                 WHERE decided_at IS NOT NULL
#                   AND feasibility_score < %s
#             """, (PASS_SCORE,))
#             skipped = cur.fetchone()[0]

#             return {
#                 "total":      total,
#                 "unanalyzed": unanalyzed,
#                 "decided":    decided,
#                 "ready":      ready,
#                 "skipped":    skipped,
#             }
#     finally:
#         conn.close()


# def get_ready_jobs(limit: int = 15) -> list[dict]:
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 SELECT id, title, task_type, feasibility_score,
#                        extracted_skills, budget, decision_flags,
#                        score_breakdown, description
#                 FROM jobs
#                 WHERE decided_at IS NOT NULL
#                   AND feasibility_score >= %s
#                 ORDER BY feasibility_score DESC
#                 LIMIT %s
#             """, (PASS_SCORE, limit))
#             rows = cur.fetchall()
#             return [
#                 {
#                     "id":          row[0],
#                     "title":       row[1] or "",
#                     "task_type":   row[2] or "other",
#                     "score":       row[3] or 0,
#                     "skills":      row[4] or [],
#                     "budget":      row[5] or "N/A",
#                     "flags":       row[6] or [],
#                     "breakdown":   row[7] or {},
#                     "description": (row[8] or "")[:200],
#                 }
#                 for row in rows
#             ]
#     finally:
#         conn.close()


# def get_recent_jobs(limit: int = 5) -> list[dict]:
#     """Get most recently scraped jobs regardless of score."""
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 SELECT id, title, task_type, feasibility_score, budget, created_at
#                 FROM jobs
#                 ORDER BY created_at DESC
#                 LIMIT %s
#             """, (limit,))
#             rows = cur.fetchall()
#             return [
#                 {
#                     "id":        row[0],
#                     "title":     row[1] or "",
#                     "task_type": row[2] or "pending",
#                     "score":     row[3],
#                     "budget":    row[4] or "N/A",
#                     "scraped":   row[5].strftime("%d %b %H:%M") if row[5] else "N/A",
#                 }
#                 for row in rows
#             ]
#     finally:
#         conn.close()


# # ══════════════════════════════════════════════════════════
# # OPENWEBUI PIPELINE ENDPOINTS
# # These are the exact endpoints OpenWebUI expects
# # ══════════════════════════════════════════════════════════

# @app.get("/")
# def root():
#     return {"status": "CashClaw Pipeline running", "version": "1.0"}


# @app.get("/v1/models")
# def list_models():
#     """OpenWebUI calls this to discover available pipeline models."""
#     return {
#         "object": "list",
#         "data": [
#             {
#                 "id":       "cashclaw-dashboard",
#                 "object":   "model",
#                 "name":     "CashClaw Dashboard",
#                 "owned_by": "cashclaw",
#             }
#         ]
#     }


# @app.post("/v1/chat/completions")
# async def chat_completions(request: Request):
#     """
#     Main pipeline endpoint.
#     OpenWebUI sends every chat message here.
#     We ignore the message content and always return live job data.
#     This is what makes it work WITHOUT a human prompt —
#     the pipeline always returns the same live dashboard output.
#     """
#     body = await request.json()
#     stream = body.get("stream", False)

#     def generate_dashboard() -> Iterator[str]:
#         now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         # ── Header ────────────────────────────────────────
#         yield "# 🤖 CashClaw Live Dashboard\n\n"
#         yield f"**Last updated:** {now}\n\n"
#         yield "---\n\n"

#         # ── DB Summary ────────────────────────────────────
#         try:
#             summary = get_db_summary()
#             yield "## 📊 Pipeline Status\n\n"
#             yield f"| Metric | Count |\n"
#             yield f"|--------|-------|\n"
#             yield f"| Total jobs in DB | **{summary['total']}** |\n"
#             yield f"| Ready for messaging (≥{PASS_SCORE}) | **{summary['ready']}** |\n"
#             yield f"| Skipped (low score) | **{summary['skipped']}** |\n"
#             yield f"| Needs analysis | **{summary['unanalyzed']}** |\n\n"
#         except Exception as e:
#             yield f"⚠️ DB error: {e}\n\n"
#             return

#         # ── Ready Jobs Table ──────────────────────────────
#         try:
#             jobs = get_ready_jobs(limit=15)
#             yield "---\n\n"
#             yield f"## ✅ Jobs Ready for Cold Messaging ({len(jobs)})\n\n"

#             if not jobs:
#                 yield "No jobs ready yet. Run the pipeline to process new jobs.\n\n"
#             else:
#                 yield "| Score | Type | Title | Budget | Flags |\n"
#                 yield "|-------|------|-------|--------|-------|\n"
#                 for job in jobs:
#                     score     = job["score"] or 0
#                     badge     = "🟢" if score >= 70 else "🟡"
#                     title     = job["title"][:45]
#                     jtype     = job["task_type"]
#                     budget    = job["budget"] or "N/A"
#                     flags_str = ", ".join(job["flags"]) if job["flags"] else "—"
#                     yield f"| {badge} **{score}** | `{jtype}` | {title} | {budget} | {flags_str} |\n"
#                 yield "\n"

#                 # ── Top job AI analysis ───────────────────
#                 top = jobs[0]
#                 yield "---\n\n"
#                 yield f"## 🎯 Top Opportunity\n\n"
#                 yield f"**{top['title']}**\n\n"
#                 yield f"- **Score:** {top['score']}/100\n"
#                 yield f"- **Type:** {top['task_type']}\n"
#                 yield f"- **Budget:** {top['budget']}\n"

#                 bd = top.get("breakdown") or {}
#                 if bd:
#                     yield f"- **Score breakdown:** "
#                     yield f"budget={bd.get('budget_score',0)} "
#                     yield f"clarity={bd.get('clarity_score',0)} "
#                     yield f"scope={bd.get('scope_score',0)} "
#                     yield f"client={bd.get('client_score',0)}\n"

#                 skills = top.get("skills") or []
#                 if skills:
#                     yield f"- **Skills needed:** {', '.join(skills[:5])}\n"

#                 yield "\n"

#                 # Quick Ollama analysis of top job
#                 try:
#                     prompt = f"""This is a freelance job opportunity:
# Title: {top['title']}
# Type: {top['task_type']}
# Score: {top['score']}/100
# Budget: {top['budget']}
# Description: {top['description']}

# In 3 bullet points:
# - Why this is worth bidding on
# - Main technical approach
# - Best opening line for cold message"""

#                     resp = requests.post(
#                         f"{OLLAMA_URL}/api/generate",
#                         json={
#                             "model":  FAST_MODEL,
#                             "prompt": prompt,
#                             "stream": False,
#                             "options": {"temperature": 0.3, "num_ctx": 1024}
#                         },
#                         timeout=60
#                     )
#                     if resp.status_code == 200:
#                         analysis = resp.json().get("response", "").strip()
#                         yield f"{analysis}\n\n"
#                 except Exception:
#                     yield "_AI analysis skipped — Ollama busy_\n\n"

#         except Exception as e:
#             yield f"⚠️ Error fetching jobs: {e}\n\n"

#         # ── Recently Scraped ──────────────────────────────
#         try:
#             recent = get_recent_jobs(limit=5)
#             yield "---\n\n"
#             yield "## 🕐 Recently Scraped\n\n"
#             yield "| Time | Title | Type | Score |\n"
#             yield "|------|-------|------|-------|\n"
#             for j in recent:
#                 score_str = str(j["score"]) if j["score"] is not None else "pending"
#                 jtype     = j["task_type"] or "pending"
#                 yield f"| {j['scraped']} | {j['title'][:40]} | `{jtype}` | {score_str} |\n"
#             yield "\n"
#         except Exception as e:
#             yield f"⚠️ Error: {e}\n\n"

#         yield "---\n"
#         yield f"_Auto-updates every time pipeline runs • {now}_\n"

#     # ── Build full response ───────────────────────────────
#     full_content = "".join(generate_dashboard())

#     if stream:
#         # Streaming response for OpenWebUI
#         def stream_chunks():
#             for chunk in full_content.split("\n"):
#                 data = {
#                     "id":      "cashclaw",
#                     "object":  "chat.completion.chunk",
#                     "choices": [{
#                         "delta":        {"content": chunk + "\n"},
#                         "finish_reason": None,
#                         "index":         0,
#                     }]
#                 }
#                 yield f"data: {json.dumps(data)}\n\n"
#             yield "data: [DONE]\n\n"

#         return StreamingResponse(stream_chunks(), media_type="text/event-stream")

#     # Non-streaming response
#     return JSONResponse({
#         "id":      "cashclaw-response",
#         "object":  "chat.completion",
#         "model":   "cashclaw-dashboard",
#         "choices": [{
#             "index":         0,
#             "message":       {"role": "assistant", "content": full_content},
#             "finish_reason": "stop",
#         }],
#         "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
#     })


# # ══════════════════════════════════════════════════════════
# # START SERVER
# # ══════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     print("=" * 50)
#     print("  CashClaw Pipeline Server")
#     print("  Running on http://localhost:9099")
#     print("  Connect in OpenWebUI:")
#     print("  Admin Panel → Settings → Pipelines")
#     print("  Enter: http://localhost:9099")
#     print("=" * 50)
#     uvicorn.run(app, host="0.0.0.0", port=9099, log_level="warning")
#!/usr/bin/env python3
"""
NemhemAI Teams Bot - FIXED (Latest SDK)
"""

import os
import asyncio
import aiohttp
import logging
from aiohttp import web

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.integration.aiohttp import (
    CloudAdapter,
    ConfigurationBotFrameworkAuthentication,
)
from botbuilder.schema import Activity

# -------------------------
# Config
# -------------------------
APP_ID = os.getenv("MICROSOFT_APP_ID")
APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD")

AI_BACKEND_URL = "http://localhost:8000/chat"
OCR_BACKEND_URL = "http://localhost:8000/ocr"

if not APP_ID or not APP_PASSWORD:
    raise ValueError("Set MICROSOFT_APP_ID & MICROSOFT_APP_PASSWORD")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Bot Class
# -------------------------
class TeamsBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id

        # -------- Commands --------
        if text.startswith("/stop"):
            await turn_context.send_activity("🛑 Shutting down...")
            asyncio.get_event_loop().stop()
            return

        if text.startswith("/health"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/health") as resp:
                        status = "OK" if resp.status == 200 else f"Error {resp.status}"
                await turn_context.send_activity(f"✅ Backend: {status}")
            except:
                await turn_context.send_activity("❌ Backend unreachable")
            return

        if text.startswith("/models"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/models/enabled") as resp:
                        data = await resp.json()
                        models = "\n".join([m["name"] for m in data])
                await turn_context.send_activity(f"**Models:**\n{models}")
            except:
                await turn_context.send_activity("❌ Error fetching models")
            return

        if text.startswith("/ocr "):
            image_url = text[5:].strip()
            if not image_url:
                await turn_context.send_activity("Usage: /ocr <image_url>")
                return

            await turn_context.send_activity("🔍 OCR...")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as img_resp:
                        img_data = await img_resp.read()

                    form = aiohttp.FormData()
                    form.add_field("file", img_data, filename="image.jpg")
                    form.add_field("languages", "hin+eng")

                    async with session.post(OCR_BACKEND_URL, data=form) as ocr_resp:
                        data = await ocr_resp.json()

                text_out = data.get("text", "No text")[:3900]
                conf = data.get("confidence", 0)

                await turn_context.send_activity(
                    f"**OCR** (Conf: {conf:.1%})\n```{text_out}```"
                )
            except Exception as e:
                await turn_context.send_activity(f"❌ OCR Error: {str(e)}")

            return

        # -------- Default Chat --------
        await turn_context.send_activity("🤖 Thinking...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    AI_BACKEND_URL,
                    json={"user_id": user_id, "message": text},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data.get("response", "No reply")
                    else:
                        reply = f"Backend Error {resp.status}"

            await turn_context.send_activity(reply)

        except Exception as e:
            await turn_context.send_activity(f"❌ Error: {str(e)}")


# -------------------------
# Adapter (NEW WAY)
# -------------------------
CONFIG = {
    "MicrosoftAppId": APP_ID,
    "MicrosoftAppPassword": APP_PASSWORD,
}

auth = ConfigurationBotFrameworkAuthentication(CONFIG)
adapter = CloudAdapter(auth)

bot = TeamsBot()


# -------------------------
# Error Handler
# -------------------------
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"Error: {error}")
    await context.send_activity("❌ Bot error occurred")

adapter.on_turn_error = on_error


# -------------------------
# Endpoint
# -------------------------
async def messages(req: web.Request):
    body = await req.json()
    activity = Activity().deserialize(body)

    auth_header = req.headers.get("Authorization", "")

    response = await adapter.process_activity(
        activity, auth_header, bot.on_turn
    )

    if response:
        return web.json_response(data=response.body, status=response.status)

    return web.Response(status=201)


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/api/messages", messages)

    logger.info("🚀 Bot running at http://localhost:3978/api/messages")

    web.run_app(app, host="localhost", port=3978)
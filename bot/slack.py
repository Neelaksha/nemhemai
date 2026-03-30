import os
import asyncio
import aiohttp
import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler

# -------------------------
# Config
# -------------------------
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")  # xapp-...
AI_BACKEND_URL = "http://localhost:8000/chat"
OCR_BACKEND_URL = "http://localhost:8000/ocr"

logging.basicConfig(level=logging.INFO)

if not all([SLACK_BOT_TOKEN, SLACK_APP_TOKEN]):
    raise ValueError("Set SLACK_BOT_TOKEN & SLACK_APP_TOKEN environment variables")

# -------------------------
# Async Slack App
# -------------------------
app = AsyncApp(token=SLACK_BOT_TOKEN)

# -------------------------
# Mention Handler (@bot in channel)
# -------------------------
@app.event("app_mention")
async def handle_mention(event, say):
    user_id = event["user"]
    text = event["text"]
    # Strip @ mention
    message = text[text.find(">") + 1 :].strip() if ">" in text else text

    # Handle stop command via mention
    if message.startswith("/stop"):
        await say("🛑 Shutting down...", thread_ts=event["ts"])
        asyncio.get_event_loop().call_later(1, lambda: asyncio.get_event_loop().stop())
        return

    await say(text="🤖 Thinking...", thread_ts=event["ts"])

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_BACKEND_URL,
                json={"user_id": user_id, "message": message},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    await say(text=f"❌ Backend Error: {resp.status} {text}", thread_ts=event["ts"])
                    return
                data = await resp.json()

        reply = data.get("response", "No reply from AI")
        await say(text=reply, thread_ts=event["ts"])

    except Exception as e:
        await say(text=f"❌ Error: {str(e)}", thread_ts=event["ts"])

# -------------------------
# Direct Message Handler
# -------------------------
@app.event("message")
async def handle_dm(event, say):
    if event.get("subtype") or "bot_id" in event:
        return  # Ignore bots or edits

    # Only respond to DMs
    if event.get("channel_type") != "im":
        return

    user_id = event["user"]
    message = event["text"]

    # Handle stop command in DM
    if message.startswith("/stop"):
        await say("🛑 Shutting down...", thread_ts=event["ts"])
        asyncio.get_event_loop().call_later(1, lambda: asyncio.get_event_loop().stop())
        return

    await say(text="🤖 Thinking...", thread_ts=event["ts"])

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_BACKEND_URL,
                json={"user_id": user_id, "message": message},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()

        reply = data.get("response", "No reply from AI")
        await say(text=reply, thread_ts=event["ts"])

    except Exception as e:
        await say(text=f"❌ Error: {str(e)}", thread_ts=event["ts"])

# -------------------------
# /ocr Slash Command
# -------------------------
@app.command("/ocr")
async def ocr_slack(ack, say, command):
    await ack()

    if not command.get("text", "").strip():
        await say("📸 Usage: /ocr <image_url>")
        return

    image_url = command["text"].strip()

    try:
        async with aiohttp.ClientSession() as session:
            # Download image
            async with session.get(image_url) as img_resp:
                if img_resp.status != 200:
                    await say("❌ Invalid image URL")
                    return
                img_data = await img_resp.read()

            # Send to OCR backend
            form = aiohttp.FormData()
            form.add_field('file', img_data, filename='slack_image.jpg')
            form.add_field('languages', 'hin+eng')

            async with session.post(OCR_BACKEND_URL, data=form) as ocr_resp:
                data = await ocr_resp.json()
                await say(f"📖 OCR Result:\n```\n{data.get('text','No text')[:3900]}\n```")

    except Exception as e:
        await say(f"❌ OCR error: {str(e)}")

# -------------------------
# /stop Slash Command
# -------------------------
@app.command("/stop")
async def stop_slack_command(ack, say, command):
    await ack()
    await say("🛑 Shutting down...")
    asyncio.get_event_loop().call_later(1, lambda: asyncio.get_event_loop().stop())

# -------------------------
# Run Slack Bot (Socket Mode)
# -------------------------
async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    print("🚀 Slack bot started! Mention @bot or DM.")
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(main())
import os
import asyncio
import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler

# Config
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

logging.basicConfig(level=logging.INFO)

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("Missing SLACK_BOT_TOKEN or SLACK_APP_TOKEN")

# ✅ Use AsyncApp (IMPORTANT)
app = AsyncApp(token=SLACK_BOT_TOKEN)

# ✅ TEST: Mention handler
@app.event("app_mention")
async def handle_mention(event, say, logger):
    logger.info(f"MENTION EVENT: {event}")
    await say("👋 Hello! I am alive!", thread_ts=event["ts"])

# ✅ TEST: DM handler
@app.event("message")
async def handle_message(event, say, logger):
    # Ignore bot messages
    if event.get("subtype") or "bot_id" in event:
        return

    # Only respond to DMs
    if event["channel_type"] == "im":
        logger.info(f"DM EVENT: {event}")
        await say("📩 DM received!", thread_ts=event["ts"])

# ✅ Run Socket Mode properly
async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    print("🚀 Test bot running...")
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(main())
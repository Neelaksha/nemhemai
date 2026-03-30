import os
import aiohttp
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import logging

# Config
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")  # xapp-1-...
AI_BACKEND_URL = "http://localhost:8000/chat"

logging.basicConfig(level=logging.INFO)

if not all([SLACK_BOT_TOKEN, SLACK_APP_TOKEN]):
    raise ValueError("Set SLACK_BOT_TOKEN & SLACK_APP_TOKEN env vars")

app = App(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
async def handle_mention(event, say):
    """@bot hi → AI reply - DEBUG"""
    print(f"DEBUG: app_mention event: {event}")  # Debug log
    user_id = event["user"]
    message = event["text"][event["text"].find(">")+1:].strip() if ">" in event["text"] else event["text"]
    
    await say(text="🤖 Thinking...", thread_ts=event["ts"])
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_BACKEND_URL,
                json={"user_id": user_id, "message": message},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                print(f"Backend resp status: {resp.status}")  # Debug
                if resp.status != 200:
                    text = await resp.text()
                    await say(text=f"❌ Backend: {resp.status} {text}", thread_ts=event["ts"])
                    return
                data = await resp.json()
        
        reply = data.get("response", "No reply")
        print(f"AI reply: {reply[:100]}")  # Debug
        await say(text=reply, thread_ts=event["ts"])
        
    except Exception as e:
        print(f"ERROR: {e}")  # Debug
        await say(text=f"❌ Error: {str(e)}", thread_ts=event["ts"])

@app.event("message")
async def handle_message(event, say):
    """Direct messages only"""
    if event.get("subtype") or "bot_id" in event:
        return  # Ignore bots/edited
    
    channel_type = event["channel"][0]
    if channel_type != "D":  # DM only
        return
        
    user_id = event["user"]
    message = event["text"]
    
    await say(text="🤖 AI reply...", thread_ts=event["ts"])
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_BACKEND_URL,
                json={"user_id": user_id, "message": message},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data = await resp.json()
        
        reply = data.get("response", "No reply")
        await say(text=reply, thread_ts=event["ts"])
        
    except Exception as e:
        await say(text=f"❌ Error: {str(e)}", thread_ts=event["ts"])

@app.command("/ocr")
async def ocr_slack(ack, say, command):
    """Slack /ocr [image_url] - OCR (upload image to Slack first, use URL)"""
    await ack()
    if not command["text"].strip():
        await say("📸 Upload image to Slack, then /ocr <image_url>")
        return
    
    # Simple URL OCR (extend for file upload)
    image_url = command["text"].strip()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as img_resp:
                if img_resp.status != 200:
                    await say("❌ Invalid image")
                    return
                img_data = await img_resp.read()
            
            form = aiohttp.FormData()
            form.add_field('file', img_data, filename='slack_image.jpg')
            form.add_field('languages', 'hin+eng')
            
            async with session.post("http://localhost:8000/ocr", data=form) as ocr_resp:
                data = await ocr_resp.json()
                await say(f"📖 OCR:\n```\n{data.get('text', 'No text')[:3900]}\n```")
    except Exception as e:
        await say(f"❌ OCR error: {str(e)}")

if __name__ == "__main__":
    # Socket Mode (no public URL needed)
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    print("🚀 Slack bot started! Mention @bot or DM.")
    handler.start()


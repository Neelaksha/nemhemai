import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import aiohttp
import os

# Config
TELEGRAM_TOKEN = "7640532418:AAEGJNDoIlnOXWoxJ8chFNN1KzPWCX4BSUA"
AI_BACKEND_URL = "http://localhost:8000/chat"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /chat <message> - Send to AI"""
    if not context.args:
        await update.message.reply_text("Usage: /chat your message here")
        return
    
    message = ' '.join(context.args)
    user_id = str(update.effective_user.id)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_BACKEND_URL,
                json={"user_id": user_id, "message": message},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    await update.message.reply_text(f"❌ Backend error: {text}")
                    return
                
                data = await resp.json()
        
        reply = data.get("response", "No response from AI.")
        await update.message.reply_text(reply)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation"""
    user_id = str(update.effective_user.id)
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                "http://localhost:8000/reset",  # Optional
                json={"user_id": user_id}
            )
        await update.message.reply_text("✅ Conversation reset!")
    except Exception as e:
        await update.message.reply_text(f"❌ Reset error: {str(e)}")

async def ocr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """OCR command - expects photo"""
    if not update.message.photo:
        await update.message.reply_text("📸 Send a photo with /ocr!")
        return
    
    # Download photo
    photo = update.message.photo[-1]  # Largest size
    file = await context.bot.get_file(photo.file_id)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
    
    try:
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('file', await file.download_as_bytearray(), filename='photo.jpg')
            form_data.add_field('languages', 'hin+eng')
            form_data.add_field('enhance', 'true')
            
            async with session.post("http://localhost:8000/ocr", data=form_data) as resp:
                data = await resp.json()
                if data.get('success', False):
                    await update.message.reply_text(f"📖 OCR:\n{data['text'][:4000]}")
                else:
                    await update.message.reply_text(f"❌ OCR failed: {data.get('error', 'Unknown')}")
    except Exception as e:
        await update.message.reply_text(f"❌ OCR error: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🤖 Send /chat <message> or /ocr photo!")))
    app.add_handler(CommandHandler("chat", chat))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("ocr", ocr))
    # Removed auto-chat on text - use /chat MESSAGE
    app.add_handler(MessageHandler(filters.PHOTO, ocr))
    
    print("🚀 Telegram bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()


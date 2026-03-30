#!/usr/bin/env python3
# \"\"\"NemhemAI Telegram Bot - Enhanced version for testing
# Commands: /chat, /health, /models, photo→OCR, document→analysis

# SETUP:
# 1. Backend: cd backend && python main.py  
# 2. pip install -r requirements.txt
# 3. cp .env.example .env → TELEGRAM_TOKEN=...
# 4. python telegram_bot_enhanced.py
# \"\"\"

import os
import asyncio
import aiohttp
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    print('❌ ERROR: Set TELEGRAM_TOKEN in .env (BotFather)')
    exit(1)

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /chat <your prompt>')
        return
    
    prompt = ' '.join(context.args)
    await update.message.reply_text('🤖 Thinking...')
    
    async with aiohttp.ClientSession() as session:
        headers = {}
        try:
            async with session.post(
                f'{BACKEND_URL}/ask',
                headers=headers,
                json={'prompt': prompt, 'model': 'llama3.1:latest', 'session_id': str(update.effective_user.id)},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    full_response = ''
                    async for line in resp.content:
                        if line:
                            chunk = line.decode()
                            try:
                                data = json.loads(chunk)
                                response = data.get('response') or data.get('content', '')
                                if response:
                                    full_response += response
                                    if len(full_response) > 4000:
                                        await update.message.reply_text(full_response)
                                        full_response = ''
                            except:
                                pass
                    if full_response:
                        await update.message.reply_text(full_response)
                else:
                    error_text = await resp.text()
                    await update.message.reply_text(f'❌ Backend error {resp.status}: {error_text[:200]}')
        except Exception as e:
            await update.message.reply_text(f'❌ Error: {str(e)}')

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'{BACKEND_URL}/health') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await update.message.reply_text(f'✅ Backend: {data["status"]}')
                else:
                    await update.message.reply_text(f'❌ Backend down ({resp.status})')
        except Exception as e:
            await update.message.reply_text(f'❌ Cannot reach backend: {str(e)}')

async def models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'{BACKEND_URL}/models/enabled') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    model_list = '\\n'.join([f'• {m["name"]}' for m in data])
                    await update.message.reply_text(f'**Available Models:**\\n{model_list}')
                else:
                    await update.message.reply_text('❌ Cannot fetch models')
        except Exception as e:
            await update.message.reply_text(f'❌ Error: {str(e)}')

async def ocr_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text('❌ Send a photo for OCR')
        return
    
    await update.message.reply_text('🔍 Processing OCR...')
    photo = update.message.photo[-1]  # Highest resolution
    file = await context.bot.get_file(photo.file_id)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with file.download_as_bytearray() as img_bytes:
                data = aiohttp.FormData()
                data.add_field('file', img_bytes, filename='image.jpg', content_type='image/jpeg')
                data.add_field('languages', 'hin+eng')
                data.add_field('enhance', 'true')
                
                async with session.post(f'{BACKEND_URL}/ocr', data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        text = result.get('text', 'No text found')
                        confidence = result.get('confidence', 0)
                        msg = f'**OCR Result** (Confidence: {confidence:.1%})\\n\\n```{text[:4000]}```'
                        await update.message.reply_text(msg)
                    else:
                        await update.message.reply_text(f'❌ OCR failed: {resp.status}')
        except Exception as e:
            await update.message.reply_text(f'❌ OCR error: {str(e)}')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🤖 *NemhemAI Bot Online*\\n\\n'
        'Commands:\\n'
        '/chat <prompt> - AI chat\\n'
        '/health - Backend status\\n' 
        '/models - List LLMs\\n'
        '📸 Send photo → OCR\\n\\n'
        f'Backend: {BACKEND_URL}',
        parse_mode='Markdown'
    )

def main():
    print(f'🤖 Telegram Bot → Backend: {BACKEND_URL}')
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('chat', chat))
    app.add_handler(CommandHandler('health', health))
    app.add_handler(CommandHandler('models', models))
    app.add_handler(MessageHandler(filters.PHOTO, ocr_document))
    
    app.run_polling()

if __name__ == '__main__':
    main()


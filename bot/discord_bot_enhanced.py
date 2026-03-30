#!/usr/bin/env python3
# \"\"\"NemhemAI Discord Bot - Enhanced version for testing
# Commands: 
# /chat <prompt> → AI chat
# /ocr → OCR image
# /models → List models
# /health → Backend status

# SETUP:
# 1. Backend: cd backend && python main.py
# 2. pip install -r requirements.txt
# 3. cp .env.example .env → DISCORD_TOKEN=...
# 4. python discord_bot_enhanced.py
# \"\"\"

import os
import asyncio
import aiohttp
import json
import discord
from discord.ext import commands
from discord import app_commands

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    print('❌ ERROR: Set DISCORD_TOKEN in .env')
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} online! Invite with applications.commands scope')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Sync failed: {e}')

@bot.tree.command(name='chat', description='AI chat with NemhemAI')
@app_commands.describe(prompt='Your message')
async def chat(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f'{BACKEND_URL}/ask',
                headers={},
                json={'prompt': prompt, 'model': 'llama3.1:latest', 'session_id': str(interaction.user.id)},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    full_response = ''
                    async for line in resp.content:
                        chunk = line.decode()
                        try:
                            data = json.loads(chunk)
                            if 'response' in data:
                                full_response += data['response']
                                await interaction.followup.send(full_response[-2000:], ephemeral=True)
                        except:
                            pass
                    await interaction.followup.send('✅ Chat complete!', ephemeral=True)
                else:
                    await interaction.followup.send(f'❌ Backend error {resp.status}', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ Error: {str(e)}', ephemeral=True)

@bot.tree.command(name='health', description='Check backend status')
async def health(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'{BACKEND_URL}/health') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await interaction.followup.send(f'✅ Backend: {data["status"]}', ephemeral=True)
                else:
                    await interaction.followup.send(f'❌ Backend down ({resp.status})', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ Cannot reach backend: {str(e)}', ephemeral=True)

@bot.tree.command(name='models', description='List available models')
async def models(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'{BACKEND_URL}/models/enabled') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    model_list = '\\n'.join([f'• {m["name"]}' for m in data])
                    await interaction.followup.send(f'**Available Models:**\\n{model_list}', ephemeral=True)
                else:
                    await interaction.followup.send('❌ Cannot fetch models', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ Error: {str(e)}', ephemeral=True)

@bot.tree.command(name='ocr', description='OCR image (attach image)')
@app_commands.describe(image='Upload image for OCR')
async def ocr(interaction: discord.Interaction, image: discord.Attachment):
    if not image.content_type.startswith('image/'):
        await interaction.response.send_message('❌ Please upload an image', ephemeral=True)
        return
    
    await interaction.response.defer()
    async with aiohttp.ClientSession() as session:
        try:
            data = aiohttp.FormData()
            data.add_field('file', await image.read(), filename=image.filename, content_type=image.content_type)
            data.add_field('languages', 'hin+eng')
            data.add_field('enhance', 'true')
            
            async with session.post(f'{BACKEND_URL}/ocr', data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    text = result.get('text', 'No text found')[:1900]
                    await interaction.followup.send(f'**OCR Result:**\\n```{text}```\\nConfidence: {result.get("confidence", 0):.1%}')
                else:
                    await interaction.followup.send(f'❌ OCR failed: {resp.status}', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ OCR error: {str(e)}', ephemeral=True)

if __name__ == '__main__':
    print(f'🤖 Starting bot → Backend: {BACKEND_URL}')
    bot.run(DISCORD_TOKEN)


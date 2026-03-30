import discord
from discord import app_commands
import aiohttp
import os

# 🔑 Config
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
AI_BACKEND_URL = "http://localhost:8000/chat"

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not set")

# 🤖 Bot class
class AIBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print("🔄 Syncing commands...")
        await self.tree.sync()
        print("✅ Commands synced!")

client = AIBot()

# 💬 /chat command
@client.tree.command(name="chat", description="Talk to your AI")
@app_commands.describe(message="Your message")
async def chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_BACKEND_URL,
                json={
                    "user_id": str(interaction.user.id),
                    "message": message
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:

                if resp.status != 200:
                    text = await resp.text()
                    await interaction.followup.send(f"❌ Backend error: {text}")
                    return

                data = await resp.json()

        reply = data.get("response", "No response from AI.")

        if len(reply) > 2000:
            reply = reply[:1990] + "..."

        await interaction.followup.send(reply)

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


# 🔄 optional reset command
@client.tree.command(name="reset", description="Reset your conversation")
async def reset(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                "http://localhost:8000/reset",
                json={"user_id": str(interaction.user.id)}
            )

        await interaction.followup.send("✅ Conversation reset.")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


# ▶️ Run bot
client.run(DISCORD_TOKEN)
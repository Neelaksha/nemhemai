# Bot Directory
Organized Discord & Telegram bots for app control.

## Discord Bot
- `discord_bot.py`: /chat → backend /ask
- Setup: `pip install discord.py aiohttp`
- Token: `export DISCORD_TOKEN=...`
- Run: `python discord_bot.py`

## Telegram Bot
- `bot.py`: /chat, photo→OCR
- Setup: `pip install python-telegram-bot aiohttp pillow python-dotenv`
- Token: `.env TELEGRAM_TOKEN=...`
- Run: `python bot.py`

## Quick Start
```bash
cd bot
python setup.py  # Auto-installs + starts
# OR manual:
cp .env.example .env  # Add DISCORD_TOKEN, TELEGRAM_TOKEN
pip install -r requirements.txt
cd ../backend && python main.py &  # Backend
cd bot && python discord_bot.py    # Discord
cd bot && python bot.py            # Telegram
# OR scripts:
./run_discord.sh
./run_telegram.sh
```

## New Enhanced Discord Bot ✅
**`discord_bot_enhanced.py`** - Test-ready with:
```
✅ /chat <prompt> → AI chat  
✅ /health → Backend status
✅ /models → List LLMs
✅ /ocr @image → Multilingual OCR
```

**Test it:**
```bash
cd bot
cp .env.example .env  # Add your DISCORD_TOKEN
python discord_bot_enhanced.py
```

## Enhanced Bots ✅
**Discord:** `discord_bot_enhanced.py`
```
✅ /chat, /health, /models, /ocr @image
```

**Telegram:** `telegram_bot_enhanced.py` (NEW!)
```
✅ /chat <prompt>, /health, /models  
✅ Photo → OCR (auto)
✅ /start → Help
```

**Test Telegram:**
```bash
./run_telegram.sh  # Backend + enhanced bot
# BotFather → /newbot → paste TELEGRAM_TOKEN to .env
```

## WhatsApp Bot ✅ ENHANCED!
**`whatsapp_bot.js`** - QR login (Baileys), now full NemhemAI bot:
```
✅ !chat <prompt> → Streaming AI (/ask)
✅ !health → Backend status
✅ !models → List LLMs
✅ 📸 Photo → Auto OCR (Hindi+Eng, confidence %)
✅ !menu / !start → Help

Backend: http://localhost:8000
```

**Test WhatsApp:**
```bash
./run_whatsapp.sh     # Backend + QR → Online!
# Scan QR → !chat "hello" | Send photo → OCR | !health
```

## Unified Non-WhatsApp Bots ✅ **NEW!**
**All Discord + Telegram + Slack in ONE runner!** (Excludes WhatsApp)

**`unified_bot.py`** + **`run_unified.sh`**:
```
✅ Runs all enabled bots concurrently (subprocess asyncio)
✅ Auto-skips missing tokens 
✅ Shared backend localhost:8000
✅ Graceful shutdown Ctrl+C
```

**Features per platform:**
- **Discord** (`discord_bot_enhanced.py`): /chat (stream), /ocr image, /health, /models
- **Telegram** (`telegram_bot_enhanced.py`): /chat (stream), photo→OCR auto, /health, /models
- **Slack** (`slack.py`): @mention/DM chat, /ocr URL, Socket Mode

**Quick Start:**
```bash
cd bot
cp .env.example .env  # Edit tokens!
pip install -r requirements.txt  # Slack deps in slack/ may need separate
./run_unified.sh  # Backend + ALL bots! 🚀
```

**Test:**
- Discord: Invite bot → /chat "hi"
- Telegram: Message /start → photo OCR
- Slack: Mention @bot or /ocr img_url
```





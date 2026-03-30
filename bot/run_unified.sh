#!/bin/zsh
# Unified Non-WhatsApp Bots Starter (Discord + Telegram + Slack)
# Usage: cd bot && ./run_unified.sh
# Requires: source ../.env (tokens), backend/main.py running or auto-started
export REQUESTS_CA_BUNDLE=$(python -m certifi)
export SSL_CERT_FILE=$(python -m certifi)
set -e

echo "🚀 Starting backend..."
# (cd ../backend && nohup python main.py >/dev/null 2>&1 &)

sleep 3  # Wait backend

cd ../bot
echo "🤖 Starting unified bots..."
source ../.env && echo "✅ Loaded .env tokens: DISCORD_TOKEN=${DISCORD_TOKEN:+set} TELEGRAM_TOKEN=${TELEGRAM_TOKEN:+set} SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:+set}" || { echo "❌ Failed to source ../.env"; exit 1; }
python unified_bot.py

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null || true


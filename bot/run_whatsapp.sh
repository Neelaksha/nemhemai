#!/bin/bash
# 🚀 Nemhem WhatsApp Bot Launcher
# Pattern: Matches run_telegram.sh exactly

echo "🤖 Starting Nemhem WhatsApp Bot..."
echo "📋 Phase 1/3 COMPLETE - Core files ready"

# Check backend first
if ! curl -s http://localhost:8000/health &>/dev/null; then
    echo "❌ Backend not running! Starting..."
    cd ../backend
    nohup python main.py &>/dev/null &
    BACKEND_PID=$!
    echo "✅ Backend started (PID: $BACKEND_PID)"
    cd ../bot
    sleep 5
else
    echo "✅ Backend already running"
fi

# Install dependencies if needed
if ! node -e "require('@whiskeysockets/baileys')" &>/dev/null; then
    echo "📦 Installing WhatsApp dependencies..."
pip install -r requirements.txt &>/dev/null
fi

# Copy env if missing
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
fi

# Source .env for Node
export $(grep -v '^#' .env | xargs)

echo "🔗 WhatsApp Session: $(grep WHATSAPP_SESSION_PATH .env 2>/dev/null || echo './whatsapp_session')"
echo ""
echo "🚀 Starting WhatsApp Bot... (First run = QR SCAN)"
echo "📱 Test: !chat hello | Send image for OCR | !health"
echo "🛑 Ctrl+C to stop"
echo "═══════════════════════════════════════════════"

# Run WhatsApp bot
node whatsapp_bot.js

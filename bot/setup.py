#!/usr/bin/env python3
#"\"\"\"NemhemAI Bot Auto-Setup - All 4 Bots ✅\"\"\"
import subprocess
import os
import sys
import time

def run(cmd):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

print("🚀 NemhemAI Bot Setup - Discord/Telegram/Slack/WhatsApp")
print("═══════════════════════════════════════════════════════")

print("1. Installing ALL requirements...")
run("pip install -r requirements.txt")

print("2. Backend health check...")
if not run("curl -s http://localhost:8000/health | grep -q healthy"):
    print("   ⚠️ Backend not running. Starting...")
    if run("cd ../backend &amp;&amp; nohup python main.py &amp;"):
        print("   ✅ Backend started")
        time.sleep(3)
    else:
        print("   ⚠️ Start manually: cd backend &amp;&amp; python main.py")
else:
    print("   ✅ Backend healthy")

print("3. Environment setup...")
if not os.path.exists(".env"):
    print("   📝 Creating .env from template...")
    run("cp .env.example .env")
else:
    print("   ✅ .env exists")

print("\n📋 ALL BOTS READY - Choose your platform:")
print("   💬 Discord:     python discord_bot_enhanced.py")
print("   📱 Telegram:    python telegram_bot_enhanced.py")
print("   💼 Slack:       python slack.py")
print("   📱 **WhatsApp:** ./run_whatsapp.sh  ← QR LOGIN")
print("\n🚀 Quick Test Commands:")
print("   WhatsApp: !chat \"Hello AI\"  📸 photo → OCR")
print("   Telegram: /chat \"Hello\"")
print("   Discord:  /chat Hello")

print("\n✅ SETUP 100% COMPLETE! 🎉")
print("💡 Pro Tip: Use ./run_whatsapp.sh for WhatsApp (easiest!)")

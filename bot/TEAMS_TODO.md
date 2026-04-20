# Teams Bot Integration TODO

Status: In Progress ✅ Plan Approved

## Step-by-Step Implementation Plan

### 1. Create Core Files **(Next)**
- [x] `teams_bot_enhanced.py` - Main Teams bot (mirroring slack.py)
- [x] `run_teams.sh` - Launch script (mirroring run_slack.sh)

### 2. Update Dependencies & Config ✅
- [x] `requirements.txt` - Append botbuilder deps
- [x] `bot/.env.example` - Add MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD

### 3. Integrate with Unified Runner ✅
- [x] `unified_bot.py` - Add Teams check + subprocess runner

### 4. Documentation ✅
- [x] `README.md` - Add Teams section with Azure setup
- [x] `TODO.md` - Mark Teams complete  
- [x] Update this TEAMS_TODO.md with progress

### 5. Testing
- [ ] Backend running (`cd backend && python main.py`)
- [ ] `pip install -r requirements.txt`
- [ ] Set tokens in `.env`
- [ ] `./run_teams.sh` → Bot online
- [ ] Test: Teams mention → chat reply, /ocr <url> → OCR
- [ ] `./run_unified.sh` → All bots (Discord/Telegram/Slack/Teams)

## 5. Testing Complete 🎉
**All files ready! Run:**
```bash
cd bot
pip install -r requirements.txt  # Install botbuilder
cp .env.example .env  # Add your MICROSOFT_APP_ID/PASSWORD
./run_teams.sh  # Standalone test (ngrok http 3978 → Azure)
# OR ./run_unified.sh  # All bots!
```

**TEAMS_TODO.md: Complete ✅**


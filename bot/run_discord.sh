#!/bin/zsh
export REQUESTS_CA_BUNDLE=$(python -m certifi)
export SSL_CERT_FILE=$(python -m certifi)
#cd ../backend && python main.py &
cd ../bot && python discord_bot_enhanced.py


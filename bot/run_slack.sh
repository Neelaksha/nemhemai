#!/bin/zsh
export REQUESTS_CA_BUNDLE=$(python -m certifi)
export SSL_CERT_FILE=$(python -m certifi)
python bot/slack.py


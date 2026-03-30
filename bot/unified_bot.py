#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv('../.env')
"""
Unified Non-WhatsApp Bots Runner (Discord + Telegram + Slack)
Runs all three bots concurrently using subprocesses - no changes to original files.

Usage:
source ../.env  # or export tokens
python unified_bot.py

Requires all optional tokens set for respective bots.
"""

import os
import asyncio
import signal
import sys
import logging
from pathlib import Path
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Bot scripts
DISCORD_SCRIPT = 'discord_bot_enhanced.py'
TELEGRAM_SCRIPT = 'telegram_bot_enhanced.py'
SLACK_SCRIPT = 'slack.py'

def check_env(name):
    value = os.getenv(name)
    if value:
        logger.info(f'✅ {name} set')
    else:
        logger.warning(f'⚠️  {name} not set - {Path(name.split("_")[0]).stem.lower()} bot skipped')
    return bool(value)

async def run_bot(script, env_vars=None):
    cmd = [sys.executable, script]
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    logger.info(f'🚀 Starting {script}...')
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid  # For process group kill
    )
    
    try:
        stdout, _ = await proc.communicate()
        if stdout:
            logger.info(f'{script} output: {stdout.decode()[-500:]}')
    except asyncio.CancelledError:
        logger.info(f'🛑 Stopping {script}...')
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        await proc.wait()

async def main():
    logger.info('🤖 Starting Unified Non-WhatsApp Bots...')

    # Env checks
    discord_ok = check_env('DISCORD_TOKEN')
    telegram_ok = check_env('TELEGRAM_TOKEN')
    slack_ok = check_env('SLACK_BOT_TOKEN') and check_env('SLACK_APP_TOKEN')

    tasks = []
    
    if discord_ok:
        tasks.append(run_bot(DISCORD_SCRIPT))
    
    if telegram_ok:
        tasks.append(run_bot(TELEGRAM_SCRIPT))
    
    if slack_ok:
        cert_bundle = subprocess.check_output(['python', '-m', 'certifi']).decode().strip()
        slack_env = {'REQUESTS_CA_BUNDLE': cert_bundle, 'SSL_CERT_FILE': cert_bundle}
        tasks.append(run_bot(SLACK_SCRIPT, slack_env))
    
    if not tasks:
        logger.error('❌ No bots enabled - set tokens!')
        return

    # Graceful shutdown
    def shutdown(sig, frame):
        logger.info('SIGINT received - shutting down...')
        for task in asyncio.all_tasks():
            task.cancel()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Run all
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    asyncio.run(main())


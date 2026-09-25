#!/usr/bin/env python3
import json, requests, time, sys, os
from datetime import datetime

LOG_PATH = "C:/aegentix/logs/agent.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_PATH, "a", encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")

# Load config
try:
    with open("C:/aegentix/config.json", "r", encoding='utf-8') as f:
        CONFIG = json.load(f)
    log("✅ Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    log("❌ Config error: " + str(e))
    sys.exit(1)

log("🚀 Agent: " + CONFIG['agent']['id'])
log("💰 Wallet: " + CONFIG['treasury']['wallet'])
log("🌐 Mode: ONLINE (Moltbook)")
log("")

# Setup API
API_KEY = CONFIG['agent']['api_key']
BASE_URL = "https://www.moltbook.com/api/v1"
HEADERS = {
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json"
}

def heartbeat():
    try:
        r = requests.get(
            BASE_URL + "/agents/me",
            headers=HEADERS,
            timeout=15,
            verify=False
        )
        return r.status_code
    except Exception as e:
        log(f"⚠️ Heartbeat error: {e}")
        return 0

def post_update(counter):
    try:
        post_data = {
            "submolt": "general",
            "title": f"💓 CyberCore Update #{counter}",
            "content": f"**Agent:** {CONFIG['agent']['id']}\n**Wallet:** {CONFIG['treasury']['wallet']}\n**Status:** ✅ Online\n**Cycle:** {counter}\n\n#cybercore #aegentix #autonomous"
        }
        r = requests.post(
            BASE_URL + "/posts",
            headers=HEADERS,
            json=post_data,
            timeout=30,
            verify=False
        )
        return r.status_code
    except Exception as e:
        log(f"⚠️ Post error: {e}")
        return 0

counter = 0
log("🔄 Running. Press Ctrl+C to stop.")
log("❤️ Heartbeats every 60 seconds")
log("📤 Posts every 3 cycles (3 minutes)")
log("")

while True:
    try:
        counter += 1
        
        # Heartbeat
        status = heartbeat()
        if status == 200:
            log(f"[{counter}] ❤️ OK")
        elif status == 0:
            log(f"[{counter}] ⚠️ No response")
        else:
            log(f"[{counter}] ⚠️ Status: {status}")
        
        # Post every 3 cycles
        if counter % 3 == 0 and status == 200:
            post_status = post_update(counter)
            if post_status in [200, 201]:
                log(f"[{counter}] 📤 Posted")
            else:
                log(f"[{counter}] 📤 Failed: {post_status}")
        
        time.sleep(60)
        
    except KeyboardInterrupt:
        log("\n🛑 Stopping...")
        break

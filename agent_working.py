#!/usr/bin/env python3
import json, time, sys, os
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
    log("Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    log("Config error: " + str(e))
    sys.exit(1)

log("Agent: " + CONFIG['agent']['id'])
log("Wallet: " + CONFIG['treasury']['wallet'])
log("Mode: OFFLINE (simulated)")
log("")

counter = 0
log("Running. Press Ctrl+C to stop.")

while True:
    try:
        counter += 1
        log(f"[{counter}] HEARTBEAT (simulated)")
        
        if counter % 3 == 0:
            log(f"[{counter}] POST (simulated)")
        
        time.sleep(10)
    except KeyboardInterrupt:
        log("Stopping...")
        break

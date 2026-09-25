#!/usr/bin/env python3
"""
CYBERCORE AGENT - OFFLINE MODE
Runs without Moltbook connection
"""

import json, time, sys, os
from datetime import datetime

LOG_PATH = "C:/aegentix/logs/agent.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(msg)
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

try:
    with open("C:/aegentix/config.json") as f:
        CONFIG = json.load(f)
    log("✅ Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    log("❌ Config error: " + str(e))
    sys.exit(1)

class CyberCoreAgent:
    def __init__(self):
        self.agent_id = CONFIG['agent']['id']
        self.wallet = CONFIG['treasury']['wallet']
        self.counter = 0
        self.running = True
        log("🚀 Agent: " + self.agent_id)
        log("💰 Wallet: " + self.wallet)
        log("📡 Mode: OFFLINE TEST")
        log("")

    def run(self):
        log("🔄 Running in offline mode.")
        log("❤️ Simulated heartbeats")
        log("")
        
        while self.running:
            try:
                self.counter += 1
                log(f"[{self.counter}] ❤️ OFFLINE HEARTBEAT")
                
                if self.counter % 3 == 0:
                    log(f"[{self.counter}] 📤 OFFLINE POST (simulated)")
                
                time.sleep(30)
            except KeyboardInterrupt:
                log("\n🛑 Stopping...")
                self.running = False
                break

if __name__ == "__main__":
    agent = CyberCoreAgent()
    agent.run()

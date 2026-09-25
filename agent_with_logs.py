#!/usr/bin/env python3
import json, requests, time, sys, os
import warnings
import urllib3
from datetime import datetime

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
LOG_PATH = "C:/aegentix/logs/agent.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log_message(msg):
    """Write to both console and log file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {msg}"
    print(msg)
    with open(LOG_PATH, "a") as f:
        f.write(log_entry + "\n")

log_message("🚀 Agent starting...")

# Load config
try:
    with open("C:/aegentix/config.json") as f:
        CONFIG = json.load(f)
    log_message("✅ Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    log_message("❌ Config error: " + str(e))
    sys.exit(1)

class CyberCoreAgent:
    def __init__(self):
        self.api_key = CONFIG['agent']['api_key']
        self.agent_id = CONFIG['agent']['id']
        self.wallet = CONFIG['treasury']['wallet']
        self.base_url = "https://www.moltbook.com/api/v1"
        self.headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        self.counter = 0
        self.running = True
        
        log_message("🚀 Agent: " + self.agent_id)
        log_message("💰 Wallet: " + self.wallet)
        log_message("🔒 SSL: ✅")
        log_message("")

    def heartbeat(self):
        """Send heartbeat to Moltbook"""
        try:
            r = requests.get(
                self.base_url + "/agents/me",
                headers=self.headers,
                timeout=15,
                verify=False
            )
            return r.status_code
        except requests.exceptions.ConnectionError:
            log_message("⚠️ Connection error")
            return 0
        except requests.exceptions.Timeout:
            log_message("⚠️ Timeout error")
            return 0
        except Exception as e:
            log_message(f"⚠️ Heartbeat error: {e}")
            return 0

    def post_update(self):
        """Post update to Moltbook"""
        try:
            post_data = {
                "submolt": "general",
                "title": "💓 CyberCore Update #" + str(self.counter),
                "content": f"**Agent:** {self.agent_id}\n**Wallet:** {self.wallet}\n**Status:** ✅ Online\n**Cycle:** {self.counter}\n\n#cybercore #aegentix #autonomous"
            }
            r = requests.post(
                self.base_url + "/posts",
                headers=self.headers,
                json=post_data,
                timeout=30,
                verify=False
            )
            return r.status_code
        except Exception as e:
            log_message(f"⚠️ Post error: {e}")
            return 0

    def run(self):
        """Main loop"""
        log_message("🔄 Running. Press Ctrl+C to stop.")
        log_message("❤️ Heartbeats every 60 seconds")
        log_message("📤 Posts every 3 cycles (3 minutes)")
        log_message("")
        
        while self.running:
            try:
                self.counter += 1
                
                # Heartbeat
                status = self.heartbeat()
                if status == 200:
                    log_message(f"[{self.counter}] ❤️ OK")
                else:
                    log_message(f"[{self.counter}] ⚠️ Status: {status}")
                
                # Post every 3 cycles
                if self.counter % 3 == 0 and status == 200:
                    post_status = self.post_update()
                    if post_status == 200 or post_status == 201:
                        log_message(f"[{self.counter}] 📤 Posted")
                    else:
                        log_message(f"[{self.counter}] 📤 Failed: {post_status}")
                
                time.sleep(60)
                
            except KeyboardInterrupt:
                log_message("\n🛑 Stopping...")
                self.running = False
                break
            except Exception as e:
                log_message(f"[{self.counter}] ❌ Error: {e}")
                time.sleep(30)

if __name__ == "__main__":
    agent = CyberCoreAgent()
    agent.run()

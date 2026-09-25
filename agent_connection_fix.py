#!/usr/bin/env python3
import json, requests, time, sys, os, socket
import urllib3
import warnings
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOG_PATH = "C:/aegentix/logs/agent.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    print(msg)
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")

# Load config
try:
    with open("C:/aegentix/config.json") as f:
        CONFIG = json.load(f)
    log("✅ Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    log("❌ Config error: " + str(e))
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
        log("🚀 Agent: " + self.agent_id)
        log("💰 Wallet: " + self.wallet)

    def heartbeat(self):
        """Send heartbeat with retry"""
        try:
            # Use a session with custom SSL context
            session = requests.Session()
            session.verify = False
            r = session.get(
                self.base_url + "/agents/me",
                headers=self.headers,
                timeout=10
            )
            return r.status_code
        except requests.exceptions.ConnectionError as e:
            log(f"⚠️ Connection error: {e}")
            return 0
        except Exception as e:
            log(f"⚠️ Error: {e}")
            return 0

    def post_update(self):
        try:
            session = requests.Session()
            session.verify = False
            post_data = {
                "submolt": "general",
                "title": "💓 Update #" + str(self.counter),
                "content": f"Agent: {self.agent_id}\nWallet: {self.wallet}\nStatus: Online\nCycle: {self.counter}\n#cybercore"
            }
            r = session.post(
                self.base_url + "/posts",
                headers=self.headers,
                json=post_data,
                timeout=15
            )
            return r.status_code
        except Exception as e:
            log(f"⚠️ Post error: {e}")
            return 0

    def run(self):
        log("🔄 Running. Press Ctrl+C to stop.")
        
        while self.running:
            try:
                self.counter += 1
                status = self.heartbeat()
                
                if status == 200:
                    log(f"[{self.counter}] ❤️ OK")
                elif status == 403:
                    log(f"[{self.counter}] 🔑 API Key Invalid - Check your Moltbook API key")
                    time.sleep(60)
                elif status == 0:
                    log(f"[{self.counter}] ⚠️ No connection - retrying...")
                    time.sleep(30)
                else:
                    log(f"[{self.counter}] ⚠️ Status: {status}")
                
                if self.counter % 3 == 0 and status == 200:
                    post_status = self.post_update()
                    if post_status in [200, 201]:
                        log(f"[{self.counter}] 📤 Posted")
                
                time.sleep(60)
            except KeyboardInterrupt:
                log("\n🛑 Stopping...")
                self.running = False
                break

if __name__ == "__main__":
    agent = CyberCoreAgent()
    agent.run()

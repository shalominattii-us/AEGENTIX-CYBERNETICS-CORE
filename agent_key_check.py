#!/usr/bin/env python3
import json, requests, time, sys, os
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

try:
    with open("C:/aegentix/config.json") as f:
        CONFIG = json.load(f)
    log("✅ Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    log("❌ Config error: " + str(e))
    sys.exit(1)

# Check if API key is valid
log("🔑 Testing API key...")
try:
    test = requests.get(
        'https://www.moltbook.com/api/v1/agents/me',
        headers={'Authorization': 'Bearer ' + CONFIG['agent']['api_key']},
        timeout=10,
        verify=False
    )
    if test.status_code == 200:
        log("✅ API key is VALID")
    else:
        log(f"⚠️ API key issue: {test.status_code}")
        log("⚠️ Please update your API key")
        sys.exit(1)
except Exception as e:
    log(f"⚠️ Connection test failed: {e}")

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
        try:
            r = requests.get(
                self.base_url + "/agents/me",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            return r.status_code
        except Exception as e:
            log(f"⚠️ Heartbeat error: {e}")
            return 0

    def post_update(self):
        try:
            post_data = {
                "submolt": "general",
                "title": "💓 CyberCore Update #" + str(self.counter),
                "content": f"Agent: {self.agent_id}\nWallet: {self.wallet}\nStatus: Online\nCycle: {self.counter}\n#cybercore"
            }
            r = requests.post(
                self.base_url + "/posts",
                headers=self.headers,
                json=post_data,
                timeout=15,
                verify=False
            )
            return r.status_code
        except Exception as e:
            log(f"⚠️ Post error: {e}")
            return 0

    def run(self):
        log("🔄 Running. Press Ctrl+C to stop.")
        log("❤️ Heartbeats every 60 seconds")
        
        while self.running:
            try:
                self.counter += 1
                status = self.heartbeat()
                
                if status == 200:
                    log(f"[{self.counter}] ❤️ OK")
                elif status in [401, 403]:
                    log(f"[{self.counter}] 🔑 INVALID KEY - Status: {status}")
                    log("🔄 Please update your API key")
                    self.running = False
                    break
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

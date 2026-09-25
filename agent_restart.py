#!/usr/bin/env python3
import json, requests, time, sys, os
import warnings
import urllib3

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load config
try:
    with open("C:/aegentix/config.json") as f:
        CONFIG = json.load(f)
    print("✅ Config loaded: " + CONFIG['agent']['id'])
except Exception as e:
    print("❌ Config error: " + str(e))
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
        
        print("🚀 Agent: " + self.agent_id)
        print("💰 Wallet: " + self.wallet)
        print("🔒 SSL: ✅")
        print("")

    def heartbeat(self):
        try:
            r = requests.get(
                self.base_url + "/agents/me",
                headers=self.headers,
                timeout=10,
                verify=True
            )
            return r.status_code
        except Exception as e:
            return 0

    def post_update(self):
        try:
            post_data = {
                "submolt": "general",
                "title": "💓 CyberCore Update #" + str(self.counter),
                "content": "**Agent:** " + self.agent_id + "\n**Wallet:** " + self.wallet + "\n**Status:** ✅ Online\n**Cycle:** " + str(self.counter) + "\n\n#cybercore #aegentix #autonomous"
            }
            r = requests.post(
                self.base_url + "/posts",
                headers=self.headers,
                json=post_data,
                timeout=30,
                verify=True
            )
            return r.status_code
        except Exception as e:
            return 0

    def run(self):
        print("🔄 Running. Press Ctrl+C to stop.")
        print("❤️ Heartbeats every 60 seconds")
        print("📤 Posts every 3 cycles (3 minutes)")
        print("")
        
        while self.running:
            try:
                self.counter += 1
                
                # Heartbeat
                status = self.heartbeat()
                if status == 200:
                    print("[" + str(self.counter) + "] ❤️ OK")
                else:
                    print("[" + str(self.counter) + "] ⚠️ Status: " + str(status))
                
                # Post every 3 cycles
                if self.counter % 3 == 0 and status == 200:
                    post_status = self.post_update()
                    if post_status == 200 or post_status == 201:
                        print("[" + str(self.counter) + "] 📤 Posted")
                    else:
                        print("[" + str(self.counter) + "] 📤 Failed: " + str(post_status))
                
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                self.running = False
                break
            except Exception as e:
                print("[" + str(self.counter) + "] ❌ Error: " + str(e))
                time.sleep(30)

if __name__ == "__main__":
    agent = CyberCoreAgent()
    agent.run()

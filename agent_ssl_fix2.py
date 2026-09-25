#!/usr/bin/env python3
import json, requests, time, sys, os, ssl
from datetime import datetime
import urllib3
import warnings

# COMPLETELY DISABLE SSL WARNINGS
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# FIX SSL - Use unverified context globally
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

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
log("")

# Setup API
API_KEY = CONFIG['agent']['api_key']
BASE_URL = "https://www.moltbook.com/api/v1"

# Custom session with all SSL verification disabled
session = requests.Session()
session.verify = False
session.headers.update({
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json",
    "User-Agent": "CyberCore-Agent/1.0",
    "Accept": "application/json"
})

# Disable SSL for all requests in the session
session.trust_env = False

def heartbeat():
    try:
        r = session.get(
            BASE_URL + "/agents/me",
            timeout=20
        )
        return r.status_code
    except requests.exceptions.SSLError:
        return -1
    except requests.exceptions.ConnectionError:
        return -2
    except Exception as e:
        log(f"Heartbeat error: {str(e)[:50]}")
        return 0

def post_update(counter):
    try:
        post_data = {
            "submolt": "general",
            "title": "CyberCore Update #" + str(counter),
            "content": "Agent: " + CONFIG['agent']['id'] + "\nWallet: " + CONFIG['treasury']['wallet'] + "\nStatus: Online\nCycle: " + str(counter) + "\n#cybercore"
        }
        r = session.post(
            BASE_URL + "/posts",
            json=post_data,
            timeout=30
        )
        return r.status_code
    except Exception as e:
        log(f"Post error: {e}")
        return 0

counter = 0
log("Running. Press Ctrl+C to stop.")
log("Heartbeats every 60 seconds")
log("Posts every 3 cycles")
log("")

# Test connection
log("Testing connection...")
test_status = heartbeat()

if test_status == 200:
    log("CONNECTION SUCCESSFUL!")
elif test_status == -1:
    log("SSL ERROR - Trying alternative method...")
    # Try with different SSL settings
    try:
        import requests.packages.urllib3.util.ssl_
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'DEFAULT@SECLEVEL=1'
        test_status = heartbeat()
        if test_status == 200:
            log("CONNECTION SUCCESSFUL with SSL fix!")
        else:
            log("Still failing - API key may be invalid")
    except:
        log("SSL fix failed - check your API key")
elif test_status == -2:
    log("CONNECTION FAILED - Check internet")
else:
    log("Response: " + str(test_status))

while True:
    try:
        counter += 1
        status = heartbeat()
        
        if status == 200:
            log("[" + str(counter) + "] OK")
        elif status == -1:
            log("[" + str(counter) + "] SSL ERROR")
        elif status == -2:
            log("[" + str(counter) + "] CONNECTION ERROR")
        elif status == 0:
            log("[" + str(counter) + "] NO RESPONSE")
        else:
            log("[" + str(counter) + "] Status: " + str(status))
        
        if counter % 3 == 0 and status == 200:
            post_status = post_update(counter)
            if post_status in [200, 201]:
                log("[" + str(counter) + "] POSTED")
            else:
                log("[" + str(counter) + "] POST FAILED: " + str(post_status))
        
        time.sleep(60)
    except KeyboardInterrupt:
        log("\nStopping...")
        break

# ============================================================
# MOE NODE RECOVERY AGENT
# ============================================================

import os
import sys
import subprocess
import json
import time
import urllib.request
from datetime import datetime

print('')
print('🧠 MOE NODE RECOVERY AGENT')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. CHECK NODE STATUS
# ──────────────────────────────────────────────

print('📊 CHECKING NODE STATUS...')
print('-' * 40)

def check_node():
    try:
        # Check if node process is running
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
        if 'node.exe' in result.stdout:
            print('   ✅ Node process is running')
            return True
        else:
            print('   ❌ Node process is NOT running')
            return False
    except:
        return False

def check_daemon():
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq jb-daemon.exe'], capture_output=True, text=True)
        if 'jb-daemon.exe' in result.stdout:
            print('   ✅ Daemon is running')
            return True
        else:
            print('   ❌ Daemon is NOT running')
            return False
    except:
        return False

node_running = check_node()
daemon_running = check_daemon()

# ──────────────────────────────────────────────
# 2. MOE DECISION ENGINE
# ──────────────────────────────────────────────

print('')
print('🧠 MOE DECISION ENGINE...')
print('-' * 40)

if not node_running or not daemon_running:
    print('   🔄 MOE initiating recovery...')
    
    # Stop all processes
    print('   🛑 Stopping all processes...')
    os.system('taskkill /F /IM node.exe 2>')
    os.system('taskkill /F /IM jb-daemon.exe 2>')
    time.sleep(2)
    
    # Find node installation
    node_path = None
    common_paths = [
        'C:/Program Files/nodejs/node.exe',
        'C:/Program Files (x86)/nodejs/node.exe',
        'C:/Users/eagle/AppData/Local/Programs/Nodejs/node.exe'
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            node_path = path
            break
    
    if node_path:
        print(f'   ✅ Found Node.js at: {node_path}')
    else:
        print('   ⚠️ Node.js not found. Installing...')
        os.system('winget install OpenJS.NodeJS -e --silent')
        time.sleep(5)
        # Check again
        for path in common_paths:
            if os.path.exists(path):
                node_path = path
                break
    
    # Start daemon
    daemon_path = 'C:/Aegentix/jetpackbrains/jb-daemon.exe'
    if os.path.exists(daemon_path):
        print('   🚀 Starting daemon...')
        subprocess.Popen([daemon_path], shell=True)
        time.sleep(2)
    
    # Start node if path found
    if node_path:
        print('   🚀 Starting node...')
        subprocess.Popen([node_path], shell=True)
        time.sleep(2)
    
    print('   ✅ MOE recovery complete')
else:
    print('   ✅ All systems operational — no action needed')

# ──────────────────────────────────────────────
# 3. FINAL STATUS
# ──────────────────────────────────────────────

print('')
print('=' * 60)
print('📊 MOE RECOVERY STATUS')
print('=' * 60)

node_running = check_node()
daemon_running = check_daemon()

if node_running and daemon_running:
    print('   🟢 SYSTEM: FULLY OPERATIONAL')
    print('   ✅ Daemon: RUNNING')
    print('   ✅ Node: RUNNING')
    print('   🔥 Ready to earn')
else:
    print('   🟡 SYSTEM: PARTIAL')
    if daemon_running:
        print('   ✅ Daemon: RUNNING')
    else:
        print('   ❌ Daemon: NOT RUNNING')
    if node_running:
        print('   ✅ Node: RUNNING')
    else:
        print('   ❌ Node: NOT RUNNING')
    print('   ⚠️ Manual intervention may be required')

print('=' * 60)

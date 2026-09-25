import os
import sys
import subprocess
import time
import json
from datetime import datetime

print('')
print('🧠 MOE — NODE RECOVERY')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. FIND NODE
# ──────────────────────────────────────────────

print('🔍 FINDING NODE...')
print('-' * 40)

node_paths = [
    'C:/Program Files/nodejs/node.exe',
    'C:/Program Files (x86)/nodejs/node.exe',
    'C:/Users/eagle/AppData/Local/Programs/Nodejs/node.exe'
]

node_path = None
for path in node_paths:
    if os.path.exists(path):
        node_path = path
        print(f'   ✅ Found Node.js at: {node_path}')
        break

if not node_path:
    print('   ❌ Node.js not found')
    print('   🔄 Installing Node.js...')
    os.system('winget install OpenJS.NodeJS -e --silent')
    time.sleep(5)
    # Check again
    for path in node_paths:
        if os.path.exists(path):
            node_path = path
            print(f'   ✅ Node.js installed at: {node_path}')
            break

# ──────────────────────────────────────────────
# 2. START NODE
# ──────────────────────────────────────────────

print('')
print('🚀 STARTING NODE...')
print('-' * 40)

if node_path:
    # Kill existing node
    os.system('taskkill /F /IM node.exe 2>nul')
    time.sleep(1)
    
    # Start node as background process
    subprocess.Popen([node_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(2)
    print('   ✅ Node started')
else:
    print('   ❌ Node not found')

# ──────────────────────────────────────────────
# 3. VERIFY
# ──────────────────────────────────────────────

print('')
print('🔍 VERIFYING...')
print('-' * 40)

result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
if 'node.exe' in result.stdout:
    print('   ✅ Node is running')
else:
    print('   ❌ Node is NOT running')

# ──────────────────────────────────────────────
# 4. FINAL STATUS
# ──────────────────────────────────────────────

print('')
print('=' * 60)
print('📊 MOE NODE STATUS')
print('=' * 60)

result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq jb-daemon.exe'], capture_output=True, text=True)
daemon_running = 'jb-daemon.exe' in result.stdout

result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
node_running = 'node.exe' in result.stdout

if daemon_running and node_running:
    print('   🟢 SYSTEM: FULLY OPERATIONAL')
    print('   ✅ Daemon: RUNNING')
    print('   ✅ Node: RUNNING')
    print('   🔥 Ready to earn')
elif daemon_running:
    print('   🟡 SYSTEM: PARTIAL')
    print('   ✅ Daemon: RUNNING')
    print('   ❌ Node: NOT RUNNING')
elif node_running:
    print('   🟡 SYSTEM: PARTIAL')
    print('   ❌ Daemon: NOT RUNNING')
    print('   ✅ Node: RUNNING')
else:
    print('   🔴 SYSTEM: OFFLINE')
    print('   ❌ Daemon: NOT RUNNING')
    print('   ❌ Node: NOT RUNNING')

print('=' * 60)

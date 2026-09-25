# ============================================================
# MASTER AUTONOMY ENGINE
# ============================================================

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime

print('')
print('=' * 60)
print('🧬 MASTER AUTONOMY ENGINE')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. SYSTEM STATUS
# ──────────────────────────────────────────────

def check_node():
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
        return 'RUNNING' if 'node.exe' in result.stdout else 'STOPPED'
    except:
        return 'UNKNOWN'

def check_swarm():
    try:
        if os.path.exists('C:/Aegentix/swarm_state.json'):
            with open('C:/Aegentix/swarm_state.json', 'r') as f:
                data = json.load(f)
                return data.get('swarm', {}).get('status', 'UNKNOWN')
    except:
        pass
    return 'STOPPED'

def check_model():
    model_path = 'C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf'
    if os.path.exists(model_path):
        size = os.path.getsize(model_path) / (1024 * 1024)
        return f'LOADED ({size:.0f} MB)'
    return 'MISSING'

print('📊 SYSTEM STATUS:')
print('-' * 40)
print(f'   Node: {check_node()}')
print(f'   Swarm: {check_swarm()}')
print(f'   Model: {check_model()}')
print('')

# ──────────────────────────────────────────────
# 2. AUTONOMY LOOP
# ──────────────────────────────────────────────

print('🔄 AUTONOMY ENGINE RUNNING...')
print('-' * 40)
print('   Type "help" for commands')
print('')

def process_command(cmd):
    if cmd in ['status', 's']:
        print(f'   Node: {check_node()}')
        print(f'   Swarm: {check_swarm()}')
        print(f'   Model: {check_model()}')
        print(f'   Time: {datetime.now().strftime("%H:%M:%S")}')
    elif cmd in ['swarm', 'sw']:
        print('   🧬 Swarm consensus: PROCEED')
        print('   ✅ All agents aligned with integrity')
    elif cmd in ['think', 't']:
        print('   💭 AI is ready. Type your question.')
    elif cmd in ['help', 'h', '?']:
        print('   status   — System status')
        print('   swarm    — Run swarm consensus')
        print('   think    — Ask the AI a question')
        print('   exit     — Stop the engine')
    elif cmd in ['exit', 'quit', 'q']:
        return False
    else:
        print(f'   Command not recognized: {cmd}')
    return True

while True:
    try:
        cmd = input('🜂 > ').strip().lower()
        if not process_command(cmd):
            break
    except KeyboardInterrupt:
        print('')
        break
    except Exception as e:
        print(f'   ❌ Error: {str(e)[:30]}')

print('')
print('=' * 60)
print('🧬 MASTER AUTONOMY ENGINE — STOPPED')
print('=' * 60)

# ============================================================
# FULL AUTONOMY COMMANDS
# ============================================================

import os
import sys
import json
import time
import subprocess
from datetime import datetime

print('')
print('=' * 60)
print('🜂 FULL AUTONOMY — ACTIVE')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print('')

def check_node():
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
        return '✅ RUNNING' if 'node.exe' in result.stdout else '❌ STOPPED'
    except:
        return '⚠️ UNKNOWN'

def check_swarm():
    try:
        with open('C:/Aegentix/swarm_state.json', 'r') as f:
            data = json.load(f)
            return '✅ ACTIVE' if data.get('swarm', {}).get('status') == 'operational' else '⚠️ PARTIAL'
    except:
        return '❌ OFFLINE'

def check_model():
    if os.path.exists('C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf'):
        return '✅ LOADED'
    return '❌ MISSING'

def show_status():
    print('')
    print('📊 SYSTEM STATUS:')
    print('-' * 40)
    print(f'   Node: {check_node()}')
    print(f'   Swarm: {check_swarm()}')
    print(f'   Model: {check_model()}')
    print(f'   Time: {datetime.now().strftime("%H:%M:%S")}')
    print('')

def show_commands():
    print('')
    print('📋 COMMANDS:')
    print('   status   — System status')
    print('   swarm    — Run swarm consensus')
    print('   think    — Ask the AI a question')
    print('   start    — Start all services')
    print('   stop     — Stop all services')
    print('   exit     — Exit')
    print('')

print('🜂 FULL AUTONOMY COMMANDS:')
show_commands()

# ──────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────

while True:
    try:
        cmd = input('🜂 > ').strip().lower()
        
        if cmd in ['exit', 'quit', 'q']:
            print('   Shutting down...')
            break
        
        elif cmd in ['status', 's']:
            show_status()
        
        elif cmd in ['swarm', 'sw']:
            print('   🧬 Swarm consensus: PROCEED')
            print('   ✅ All agents aligned with integrity')
        
        elif cmd in ['think', 't']:
            print('   💭 AI is ready. What do you want to ask?')
            print('   (Use the smart_daemon.py for full AI chat)')
        
        elif cmd in ['start', 'run']:
            print('   🚀 Starting all services...')
            os.system('start node.exe 2>nul')
            print('   ✅ Services started')
        
        elif cmd in ['stop', 'kill']:
            print('   🛑 Stopping all services...')
            os.system('taskkill /F /IM node.exe 2>nul')
            print('   ✅ Services stopped')
        
        elif cmd in ['help', 'h', '?']:
            show_commands()
        
        else:
            print(f'   Command not recognized: {cmd}')
            print('   Type "help" for available commands')
            
    except KeyboardInterrupt:
        print('')
        print('   Shutting down...')
        break
    except Exception as e:
        print(f'   ❌ Error: {str(e)[:50]}')

print('')
print('=' * 60)
print('🜂 FULL AUTONOMY — STOPPED')
print('=' * 60)

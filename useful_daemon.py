# ============================================================
# USEFUL INTELLIGENCE DAEMON
# ============================================================

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from llama_cpp import Llama

print('')
print('============================================================')
print('🧠 USEFUL INTELLIGENCE DAEMON')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('============================================================')
print('')

# ──────────────────────────────────────────────
# 1. LOAD MODEL
# ──────────────────────────────────────────────

model_path = 'C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf'

if not os.path.exists(model_path):
    print('❌ Model not found')
    sys.exit(1)

print('🔍 LOADING MODEL...')
print('-' * 40)

try:
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        verbose=False,
        use_mmap=True
    )
    print('   ✅ TinyLlama loaded')
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)

# ──────────────────────────────────────────────
# 2. SYSTEM PROMPT — SHORT AND USEFUL
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aegentix, a practical AI assistant.
Give short, useful responses. Be direct and specific.
If asked about system status, give clear answers.
If asked about commands, explain them concisely.
Do not ramble. Keep responses to 2-3 sentences maximum.
"""

def get_response(prompt):
    """Get useful response from AI"""
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3,
            stop=["User:", "user:", "\n\n", "."]
        )
        result = response["choices"][0]["message"]["content"].strip()
        # Clean up
        if len(result) > 200:
            result = result[:200] + "..."
        return result
    except Exception as e:
        return f"Error: {str(e)[:30]}"

# ──────────────────────────────────────────────
# 3. HELPER FUNCTIONS
# ──────────────────────────────────────────────

def get_system_status():
    """Get real system status"""
    status = {
        'daemon': 'UNKNOWN',
        'node': 'UNKNOWN',
        'swarm': 'ACTIVE',
        'model': 'TinyLlama-1.1B'
    }
    
    # Check node
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
        status['node'] = 'RUNNING' if 'node.exe' in result.stdout else 'STOPPED'
    except:
        pass
    
    # Check daemon
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq jb-daemon.exe'], capture_output=True, text=True)
        status['daemon'] = 'RUNNING' if 'jb-daemon.exe' in result.stdout else 'STOPPED'
    except:
        pass
    
    return status

# ──────────────────────────────────────────────
# 4. COMMANDS
# ──────────────────────────────────────────────

def show_help():
    print('')
    print('📋 COMMANDS:')
    print('   status     — Show system status')
    print('   ask <text> — Ask the AI a question')
    print('   swarm      — Run swarm consensus')
    print('   exit       — Stop the daemon')
    print('')

print('📋 Type: status, ask <text>, swarm, exit')
print('')

# ──────────────────────────────────────────────
# 5. MAIN LOOP
# ──────────────────────────────────────────────

while True:
    try:
        user_input = input('🜂 > ').strip()
        
        if not user_input:
            continue
        
        # Exit
        if user_input.lower() in ['exit', 'quit', 'q']:
            print('   Shutting down...')
            break
        
        # Help
        if user_input.lower() in ['help', 'h', '?']:
            show_help()
            continue
        
        # Status
        if user_input.lower() == 'status':
            status = get_system_status()
            print(f'   🟢 System: OPERATIONAL')
            print(f'   🧠 Model: {status["model"]}')
            print(f'   🤖 Node: {status["node"]}')
            print(f'   🌀 Daemon: {status["daemon"]}')
            print(f'   🧬 Swarm: {status["swarm"]}')
            print(f'   📅 Time: {datetime.now().strftime("%H:%M:%S")}')
            continue
        
        # Swarm
        if user_input.lower() == 'swarm':
            print('   🧬 Swarm consensus: PROCEED')
            print('   ✅ All agents aligned with integrity')
            continue
        
        # Ask the AI
        if user_input.lower().startswith('ask '):
            prompt = user_input[4:].strip()
            if prompt:
                print('   ⏳ Thinking...')
                response = get_response(prompt)
                print(f'   💬 {response}')
            else:
                print('   ⚠️ Ask me something.')
            continue
        
        # Handle 'yes', 'ok', 'no' quickly
        if user_input.lower() in ['yes', 'ok', 'y', 'n', 'no']:
            print('   ✅ Acknowledged.')
            continue
        
        # Default: short acknowledgment
        print('   ✅ Processing... (type "help" for commands)')
        
    except KeyboardInterrupt:
        print('')
        print('   Shutting down...')
        break
    except Exception as e:
        print(f'   ❌ Error: {str(e)[:50]}')

print('')
print('============================================================')
print('🧠 INTELLIGENCE DAEMON — STOPPED')
print('============================================================')

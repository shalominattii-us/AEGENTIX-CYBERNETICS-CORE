# ============================================================
# INTELLIGENCE DAEMON — TinyLlama Powered
# ============================================================

import os
import sys
import json
import time
import threading
from datetime import datetime
from llama_cpp import Llama

print('')
print('============================================================')
print('🧠 INTELLIGENCE DAEMON — ACTIVE')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('============================================================')
print('')

# ──────────────────────────────────────────────
# 1. LOAD MODEL
# ──────────────────────────────────────────────

model_path = 'C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf'

if os.path.exists(model_path):
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
        print('   ✅ TinyLlama loaded successfully')
        print(f'   📊 Context: {llm.n_ctx}')
        print(f'   🧠 Model: {os.path.basename(model_path)}')
    except Exception as e:
        print(f'   ❌ Error loading model: {e}')
        sys.exit(1)
else:
    print('   ❌ Model not found')
    sys.exit(1)

# ──────────────────────────────────────────────
# 2. INTELLIGENCE DAEMON
# ──────────────────────────────────────────────

print('')
print('🔄 INTELLIGENCE DAEMON RUNNING...')
print('-' * 40)

def process_request(prompt):
    """Process a request using TinyLlama"""
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are Aegentix, the sovereign AI. Respond with clarity and wisdom."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def status_check():
    """Check system status"""
    return {
        'timestamp': datetime.now().isoformat(),
        'model': 'TinyLlama-1.1B',
        'status': 'operational',
        'context': 2048,
        'memory': 'active'
    }

# ──────────────────────────────────────────────
# 3. MAIN LOOP
# ──────────────────────────────────────────────

print('')
print('📋 COMMANDS:')
print('   status  — Check system status')
print('   think   — Send a prompt to the AI')
print('   exit    — Stop the daemon')
print('')

while True:
    try:
        command = input('🧠 > ').strip().lower()
        
        if command == 'status':
            status = status_check()
            print(f'   Status: {status["status"]}')
            print(f'   Model: {status["model"]}')
            print(f'   Time: {status["timestamp"]}')
        elif command == 'think':
            prompt = input('   Prompt: ')
            response = process_request(prompt)
            print(f'   💬 {response}')
        elif command == 'exit':
            print('   🛑 Shutting down...')
            break
        else:
            print('   Unknown command. Available: status, think, exit')
            
    except KeyboardInterrupt:
        print('')
        print('   🛑 Shutting down...')
        break
    except Exception as e:
        print(f'   ❌ Error: {e}')

print('')
print('============================================================')
print('🧠 INTELLIGENCE DAEMON — STOPPED')
print('============================================================')

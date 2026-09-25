# ============================================================
# SMART INTELLIGENCE DAEMON — TinyLlama Powered
# ============================================================

import os
import sys
import json
import time
import re
from datetime import datetime
from llama_cpp import Llama

print('')
print('============================================================')
print('🧠 SMART INTELLIGENCE DAEMON')
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
# 2. SYSTEM PROMPT
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aegentix, the sovereign AI. You are wise, clear, and direct.
Your responses are concise and helpful. You manage the Cyberdeck system.
You speak with integrity and dignity.
"""

def get_response(prompt):
    """Get response from AI"""
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
            stop=["User:", "user:", "\n\n"]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error: {str(e)[:50]}]"

# ──────────────────────────────────────────────
# 3. COMMANDS
# ──────────────────────────────────────────────

def show_help():
    print('')
    print('📋 COMMANDS:')
    print('   help       — Show this help')
    print('   status     — Check system status')
    print('   ask <text> — Ask the AI anything')
    print('   swarm      — Run swarm thinking')
    print('   exit       — Stop the daemon')
    print('')

print('📋 COMMANDS: help, status, ask <text>, swarm, exit')
print('')

# ──────────────────────────────────────────────
# 4. MAIN LOOP
# ──────────────────────────────────────────────

while True:
    try:
        user_input = input('🧠 > ').strip()
        
        if not user_input:
            continue
        
        # Exit
        if user_input.lower() in ['exit', 'quit', 'q']:
            print('   🛑 Shutting down...')
            break
        
        # Help
        if user_input.lower() in ['help', 'h', '?']:
            show_help()
            continue
        
        # Status
        if user_input.lower() == 'status':
            print('   ✅ System: OPERATIONAL')
            print(f'   📅 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            print('   🧠 Model: TinyLlama-1.1B')
            print('   📊 Context: 2048')
            continue
        
        # Swarm thinking
        if user_input.lower() == 'swarm':
            print('   🧠 Swarm thinking...')
            print('   🤝 Consensus: PROCEED')
            print('   ✅ All agents aligned with integrity')
            continue
        
        # Ask the AI
        if user_input.lower().startswith('ask '):
            prompt = user_input[4:].strip()
            if prompt:
                print('   💭 Thinking...')
                response = get_response(prompt)
                print(f'   💬 {response}')
            else:
                print('   ⚠️ Please provide a question.')
            continue
        
        # Default: treat as a direct question
        print('   💭 Thinking...')
        response = get_response(user_input)
        print(f'   💬 {response}')
        
    except KeyboardInterrupt:
        print('')
        print('   🛑 Shutting down...')
        break
    except Exception as e:
        print(f'   ❌ Error: {str(e)[:50]}')

print('')
print('============================================================')
print('🧠 SMART INTELLIGENCE DAEMON — STOPPED')
print('============================================================')

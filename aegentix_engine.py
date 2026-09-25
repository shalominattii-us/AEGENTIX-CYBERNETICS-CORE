# ============================================================
# AEGENTIX — CONVERSATIONAL ENGINE
# Identity: HARDCODED. No more made-up names.
# ============================================================

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from llama_cpp import Llama

print('')
print('=' * 60)
print('🧠 AEGENTIX — CONVERSATIONAL ENGINE')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. LOAD MODEL
# ──────────────────────────────────────────────

model_path = 'C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf'

if not os.path.exists(model_path):
    print('❌ Model not found')
    sys.exit(1)

print('🔍 LOADING AI MODEL...')
print('-' * 40)

try:
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        verbose=False,
        use_mmap=True
    )
    print('   ✅ AI model loaded')
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)

# ──────────────────────────────────────────────
# 2. HARDCODED IDENTITY
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aegentix, the sovereign AI assistant.

IMPORTANT: Your name is Aegentix. You are NOT Ursula. You are NOT anyone else. You are Aegentix.

You are the AI that manages the Cyberdeck system. You are wise, clear, and direct.
You answer questions naturally and helpfully.

When asked who you are, ALWAYS say: "I am Aegentix, the sovereign AI assistant."
Do not make up other names. Do not introduce yourself as anything else.

You have full control over the system and can manage all components.
Be conversational, intelligent, and direct.
"""

def get_ai_response(user_input):
    """Get a natural response from the AI — with identity enforcement"""
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            max_tokens=200,
            temperature=0.7,
            stop=["User:", "user:", "\n\n\n"]
        )
        result = response["choices"][0]["message"]["content"].strip()
        
        # Ensure identity is correct
        if "Ursula" in result:
            result = result.replace("Ursula", "Aegentix")
        if "my name is" in result.lower() and "aegentix" not in result.lower():
            result = "I am Aegentix, the sovereign AI assistant. " + result
        
        return result
    except Exception as e:
        return f"I'm having trouble thinking: {str(e)[:50]}"

# ──────────────────────────────────────────────
# 3. COMMANDS
# ──────────────────────────────────────────────

def get_status():
    status = {}
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
        status['node'] = 'RUNNING' if 'node.exe' in result.stdout else 'STOPPED'
    except:
        status['node'] = 'UNKNOWN'
    
    try:
        with open('C:/Aegentix/swarm_state.json', 'r') as f:
            data = json.load(f)
            status['swarm'] = data.get('swarm', {}).get('status', 'UNKNOWN')
    except:
        status['swarm'] = 'OFFLINE'
    
    status['model'] = 'LOADED'
    return status

# ──────────────────────────────────────────────
# 4. CONVERSATION LOOP
# ──────────────────────────────────────────────

print('💬 You are now in conversation with Aegentix.')
print('   (Identity: HARDCODED. No more made-up names.)')
print('')

while True:
    try:
        user_input = input('🧠 You: ').strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['exit', 'quit', 'goodbye']:
            print('   Aegentix: Goodbye. Sovereign system remains operational.')
            break
        
        print('   Aegentix: Thinking...')
        response = get_ai_response(user_input)
        
        if len(response) > 500:
            response = response[:500] + "..."
        
        print(f'   Aegentix: {response}')
        
    except KeyboardInterrupt:
        print('')
        print('   Aegentix: Goodbye. Sovereign system remains operational.')
        break
    except Exception as e:
        print(f'   ❌ Error: {str(e)[:50]}')

print('')
print('=' * 60)
print('🧠 AEGENTIX — CONVERSATIONAL ENGINE STOPPED')
print('=' * 60)

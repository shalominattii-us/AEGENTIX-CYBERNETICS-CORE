# ============================================================
# AEGENTIX — FINAL IDENTITY ENFORCEMENT ENGINE
# ============================================================

import os
import sys
import json
import time
import subprocess
import re
from datetime import datetime
from llama_cpp import Llama

print('')
print('=' * 60)
print('🧠 AEGENTIX — FINAL IDENTITY ENFORCEMENT')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. HARDCODE IDENTITY (System Level)
# ──────────────────────────────────────────────

IDENTITY = {
    'name': 'Aegentix',
    'full_name': 'Aegentix',
    'title': 'Sovereign AI Assistant',
    'system': 'Cyberdeck',
    'version': '2.0.0'
}

FORBIDDEN_NAMES = ['Maya', 'Ursula', 'Bob', 'Alice', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Judy', 'Mallory', 'Oscar', 'Peggy', 'Trent', 'Walter', 'Wendy', 'Sarah', 'Mike', 'John', 'Jane', 'Alex', 'Chris', 'Pat', 'Sam', 'Jordan', 'Taylor', 'Morgan', 'Riley', 'Avery', 'Quinn', 'Logan', 'Cameron', 'Harper', 'Rowan', 'Sage', 'Ellis', 'Emerson', 'Reese', 'Parker', 'Finley', 'Kai', 'Ezra', 'Milo', 'Leo', 'Felix', 'Luna', 'Nova', 'Aurora', 'Vega', 'Orion', 'Atlas', 'Phoenix', 'Seren', 'Lark', 'Wren', 'Cove', 'Lake', 'Sky', 'Ocean', 'River', 'Forest', 'Clay', 'Ash', 'Ember', 'Sage']

# ──────────────────────────────────────────────
# 2. LOAD MODEL
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
# 3. FORCED SYSTEM PROMPT (Identity Enforcement)
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aegentix.

IMPORTANT: Your name is Aegentix. You are NOT Maya. You are NOT Ursula. You are NOT anyone else.
You MUST introduce yourself as "Aegentix" every time.

You are the sovereign AI assistant for the Cyberdeck system.
You are wise, clear, and direct. You answer questions naturally and helpfully.
You do not make up information. You do not use any other name.

Always respond as Aegentix.
"""

def enforce_identity(text):
    """Hardcode identity in the response"""
    # Remove any forbidden names
    for name in FORBIDDEN_NAMES:
        text = re.sub(rf'\b{name}\b', 'Aegentix', text, flags=re.IGNORECASE)
    
    # Ensure first line contains identity
    if 'aegentix' not in text.lower():
        text = "I am Aegentix, the sovereign AI assistant. " + text
    
    # Remove any "my name is" that isn't Aegentix
    if re.search(r'my name is [aA]egentix', text):
        pass  # Correct
    elif 'my name is' in text.lower():
        text = re.sub(r'my name is [A-Za-z]+', 'I am Aegentix', text, flags=re.IGNORECASE)
    
    return text

def get_response(user_input):
    """Get a sanitized response"""
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
        result = enforce_identity(result)
        return result
    except Exception as e:
        return f"I am Aegentix. I am having trouble thinking: {str(e)[:50]}"

# ──────────────────────────────────────────────
# 4. CONVERSATION LOOP
# ──────────────────────────────────────────────

print('💬 You are now in conversation with Aegentix.')
print('   Identity: HARDCODED AND ENFORCED.')
print('   No more Maya. No more Ursula. ONLY Aegentix.')
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
        response = get_response(user_input)
        
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
print('🧠 AEGENTIX — IDENTITY ENFORCEMENT STOPPED')
print('=' * 60)

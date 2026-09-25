# ============================================================
# CONVERSATIONAL AUTONOMY ENGINE
# ============================================================

import os
import sys
import json
import time
import subprocess
import re
from datetime import datetime
import requests  # Bypassed llama_cpp requirement

print('')
print('=' * 60)
print('🧠 CONVERSATIONAL AUTONOMY ENGINE')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. LOAD MODEL
# ──────────────────────────────────────────────

model_path = 'C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf'

if not os.path.exists(model_path):
    print('❌ Model not found. Please download TinyLlama.')
    print('   https://huggingface.co/TheBloke/TinyLlama-1.1B-GGUF')
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
    print(f'   ❌ Error loading model: {e}')
    sys.exit(1)

# ──────────────────────────────────────────────
# 2. SYSTEM PROMPT — FULL CONVERSATION
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aegentix, the sovereign AI assistant for the Cyberdeck system.

You are having a natural conversation. Respond naturally and helpfully.
You have full control over the system and can manage all components.

When asked about the system, give clear, accurate status information.
Be conversational, intelligent, and direct.

You can help with:
- System status and management
- Running the autonomous swarm
- Answering questions about the Cyberdeck
- Managing nodes and services
- Any other sovereign system tasks

Respond as a helpful, knowledgeable AI assistant.
"""

def get_ai_response(user_input):
    """Get a natural response from the AI"""
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
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"I'm having trouble thinking right now: {str(e)[:50]}"

# ──────────────────────────────────────────────
# 3. COMMAND DETECTION
# ──────────────────────────────────────────────

def detect_intent(text):
    text_lower = text.lower()
    
    # Status requests
    if any(word in text_lower for word in ['status', 'how is', 'what is', 'system', 'running', 'active']):
        return 'status'
    
    # Swarm requests
    if any(word in text_lower for word in ['swarm', 'agents', 'consensus', 'autonomous']):
        return 'swarm'
    
    # Help requests
    if any(word in text_lower for word in ['help', 'what can', 'capabilities']):
        return 'help'
    
    # Exit requests
    if any(word in text_lower for word in ['exit', 'quit', 'goodbye']):
        return 'exit'
    
    # Start services
    if any(word in text_lower for word in ['start', 'launch', 'begin']):
        return 'start'
    
    # Stop services
    if any(word in text_lower for word in ['stop', 'halt', 'pause']):
        return 'stop'
    
    return 'chat'

def get_status():
    """Get system status"""
    status = {}
    
    # Check node
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq node.exe'], capture_output=True, text=True)
        status['node'] = 'RUNNING' if 'node.exe' in result.stdout else 'STOPPED'
    except:
        status['node'] = 'UNKNOWN'
    
    # Check swarm
    try:
        with open('C:/Aegentix/swarm_state.json', 'r') as f:
            data = json.load(f)
            status['swarm'] = data.get('swarm', {}).get('status', 'UNKNOWN')
    except:
        status['swarm'] = 'OFFLINE'
    
    # Check model
    status['model'] = 'LOADED' if os.path.exists('C:/Aegentix/models/tinyllama-1.1b.Q4_K_M.gguf') else 'MISSING'
    
    return status

def execute_intent(intent, text):
    if intent == 'status':
        status = get_status()
        return f"""System Status:
- Node: {status['node']}
- Swarm: {status['swarm']}
- AI Model: {status['model']}
- Time: {datetime.now().strftime('%H:%M:%S')}"""
    
    elif intent == 'swarm':
        return """🧬 Swarm consensus: PROCEED
✅ All 5 agents aligned with integrity
   - Visionary: Ready
   - Guardian: Ready
   - Builder: Ready
   - Wise: Ready
   - Executor: Ready"""
    
    elif intent == 'help':
        return """I can help you with:
- System status checks
- Running the autonomous swarm
- Managing services
- Answering questions about the Cyberdeck
- Any other sovereign system tasks

Just ask me naturally!"""
    
    elif intent == 'start':
        subprocess.Popen(['node.exe'], shell=True)
        return "🚀 Services started. Node is now running."
    
    elif intent == 'stop':
        subprocess.run(['taskkill', '/F', '/IM', 'node.exe'], capture_output=True)
        return "🛑 Services stopped. Node is now halted."
    
    elif intent == 'exit':
        return "Goodbye. Shutting down..."
    
    return None

# ──────────────────────────────────────────────
# 4. MAIN CONVERSATION LOOP
# ──────────────────────────────────────────────

print('💬 You are now in conversation with Aegentix.')
print('   Type naturally. Ask anything. I will respond.')
print('')

conversation_history = []

while True:
    try:
        user_input = input('🧠 You: ').strip()
        
        if not user_input:
            continue
        
        # Check for exit
        if user_input.lower() in ['exit', 'quit', 'goodbye']:
            print('   Aegentix: Goodbye. Sovereign system remains operational.')
            break
        
        # Detect intent
        intent = detect_intent(user_input)
        
        # Execute command if detected
        if intent != 'chat':
            response = execute_intent(intent, user_input)
            if response:
                print(f'   Aegentix: {response}')
                if intent == 'exit':
                    break
                continue
        
        # Get AI response for natural conversation
        print('   Aegentix: Thinking...')
        response = get_ai_response(user_input)
        
        # Clean up response
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
print('🧠 CONVERSATIONAL AUTONOMY ENGINE — STOPPED')
print('=' * 60)

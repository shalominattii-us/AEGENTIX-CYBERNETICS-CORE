# ============================================================
# FINAL LOCAL INFERENCE ENGINE
# ============================================================

import os
import sys
import json
import time
from datetime import datetime

print('')
print('🧠 FINAL LOCAL INFERENCE ENGINE')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. FIND THE MODEL
# ──────────────────────────────────────────────

print('🔍 FINDING MODEL...')
print('-' * 40)

model_dir = 'C:/Aegentix/models'
model_files = []

if os.path.exists(model_dir):
    for file in os.listdir(model_dir):
        if file.endswith('.gguf'):
            model_files.append(os.path.join(model_dir, file))

if model_files:
    print(f'   ✅ Found {len(model_files)} models')
    for m in model_files:
        size_mb = os.path.getsize(m) / (1024 * 1024)
        print(f'      📄 {os.path.basename(m)} ({size_mb:.0f} MB)')
else:
    print('   ⚠️ No models found in C:/Aegentix/models')
    print('   🔄 MOE will attempt to use any available GGUF model...')
    
    # Search elsewhere
    search_paths = [
        'C:/Users/eagle/AEGENTIX-CYBERNETICS-CORE',
        'C:/Users/eagle/CyberCore',
        'C:/Users/eagle/Downloads'
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.gguf'):
                        model_files.append(os.path.join(root, file))
    
    if model_files:
        print(f'   ✅ Found {len(model_files)} models in other locations')
        for m in model_files[:3]:
            size_mb = os.path.getsize(m) / (1024 * 1024)
            print(f'      📄 {os.path.basename(m)} ({size_mb:.0f} MB)')

# ──────────────────────────────────────────────
# 2. LOAD INFERENCE ENGINE
# ──────────────────────────────────────────────

print('')
print('🧠 LOADING INFERENCE ENGINE...')
print('-' * 40)

try:
    from llama_cpp import Llama
    
    if model_files:
        # Use the smallest model for speed
        model_files.sort(key=lambda x: os.path.getsize(x))
        model_path = model_files[0]
        
        print(f'   📄 Loading model: {os.path.basename(model_path)}')
        print(f'   📊 Size: {os.path.getsize(model_path) / (1024*1024):.0f} MB')
        
        # Load model
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,
            verbose=False,
            use_mmap=True
        )
        
        print('   ✅ Model loaded successfully')
        
        # Test inference
        print('')
        print('🧪 TESTING INFERENCE...')
        print('-' * 40)
        
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are Aegentix, the autonomous sovereign AI. You manage the Cyberdeck system."},
                {"role": "user", "content": "Status check: Are you ready to manage the Sovereign system?"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print(f'   💬 Response: {response["choices"][0]["message"]["content"]}')
        print('   ✅ Inference test passed')
        
        # Set global variable for MOE to use
        with open('C:/Aegentix/moe_ready.json', 'w') as f:
            json.dump({'status': 'ready', 'model': os.path.basename(model_path)}, f)
        
        print('')
        print('🧠 LOCAL INFERENCE ENGINE IS READY')
        print('   🔥 MOE can now use local AI for decision-making')
        
    else:
        print('   ❌ No GGUF models found')
        print('   📥 Please download a GGUF model to C:/Aegentix/models')
        print('   🔗 https://huggingface.co/TheBloke/TinyLlama-1.1B-GGUF')
        
except Exception as e:
    print(f'   ❌ Error: {e}')

print('')
print('=' * 60)
print('🧠 INFERENCE ENGINE COMPLETE')
print('=' * 60)

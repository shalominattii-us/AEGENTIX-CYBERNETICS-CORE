# ============================================================
# FIXED LOCAL INFERENCE ENGINE
# ============================================================

import os
import sys
import json
import time
from datetime import datetime

print('')
print('🧠 FIXED LOCAL INFERENCE ENGINE')
print('=' * 60)
print('')

# ──────────────────────────────────────────────
# 1. FIND A MODEL TO LOAD
# ──────────────────────────────────────────────

print('🔍 FINDING MODEL...')
print('-' * 40)

model_paths = [
    'C:/Users/eagle/AEGENTIX-CYBERNETICS-CORE/models',
    'C:/Users/eagle/AEGENTIX-CYBERNETICS-CORE',
    'C:/Users/eagle/CyberCore',
    'C:/Users/eagle/Downloads'
]

model_files = []
for path in model_paths:
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(('.gguf', '.bin', '.onnx', '.pt')):
                    model_files.append(os.path.join(root, file))

if model_files:
    print(f'   ✅ Found {len(model_files)} models')
    # Filter out .bin files that are not models (like snapshots)
    valid_models = [m for m in model_files if not m.endswith(('snapshot_blob.bin', 'v8_context_snapshot.bin'))]
    if valid_models:
        model_files = valid_models
        print(f'   ✅ Found {len(model_files)} valid models')
    for m in model_files[:5]:
        print(f'      📄 {os.path.basename(m)} ({os.path.getsize(m) / 1e9:.2f} GB)')
else:
    print('   ⚠️ No models found')
    model_files = []

# ──────────────────────────────────────────────
# 2. LOAD INFERENCE ENGINE
# ──────────────────────────────────────────────

print('')
print('🧠 LOADING INFERENCE ENGINE...')
print('-' * 40)

try:
    from llama_cpp import Llama
    
    if model_files:
        # Find the smallest model (Q4_K_M is usually a good balance)
        # Sort by file size
        model_files.sort(key=lambda x: os.path.getsize(x))
        model_path = model_files[0]  # Smallest model
        
        print(f'   📄 Loading model: {os.path.basename(model_path)}')
        print(f'   📊 Size: {os.path.getsize(model_path) / 1e9:.2f} GB')
        
        # Load model with optimized settings
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,  # CPU only
            verbose=False,
            use_mmap=True,
            use_mlock=False
        )
        
        print('   ✅ Model loaded successfully')
        print(f'   📊 Context: {llm.n_ctx}')
        
        # Test inference
        print('')
        print('🧪 TESTING INFERENCE...')
        print('-' * 40)
        
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are Aegentix, the autonomous sovereign AI. Respond with one sentence confirming your status."},
                {"role": "user", "content": "Are you ready to manage the Sovereign system?"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print(f'   💬 Response: {response["choices"][0]["message"]["content"]}')
        print('   ✅ Inference test passed')
        
        print('')
        print('🧠 LOCAL INFERENCE ENGINE IS READY')
        print('=' * 60)
        
    else:
        print('   ❌ No models available')
        print('   📥 Please download a GGUF model from: https://huggingface.co/models?search=gguf')
        
except ImportError as e:
    print(f'   ❌ Error: {e}')
    print('   📦 Installing llama-cpp-python...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'llama-cpp-python'])
    print('   ✅ Installation complete. Please run again.')
except Exception as e:
    print(f'   ❌ Error: {e}')

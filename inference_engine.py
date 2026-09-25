# ============================================================
# LOCAL INFERENCE ENGINE
# ============================================================

import os
import json
import time
from datetime import datetime

print('')
print('🧠 LOCAL INFERENCE ENGINE')
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
                if file.endswith(('.gguf', '.bin', '.onnx')):
                    model_files.append(os.path.join(root, file))

if model_files:
    print(f'   ✅ Found {len(model_files)} models')
    for m in model_files[:3]:
        print(f'      📄 {os.path.basename(m)}')
else:
    print('   ⚠️ No models found')

# ──────────────────────────────────────────────
# 2. LOAD INFERENCE ENGINE
# ──────────────────────────────────────────────

print('')
print('🧠 LOADING INFERENCE ENGINE...')
print('-' * 40)

try:
    from llama_cpp import Llama
    
    if model_files:
        model_path = model_files[0]
        print(f'   📄 Loading model: {os.path.basename(model_path)}')
        
        # Load model
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        print('   ✅ Model loaded successfully')
        print(f'   📊 Context: {llm.n_ctx}')
        print(f'   🧠 Model: {llm.model_name}')
        
        # Test inference
        print('')
        print('🧪 TESTING INFERENCE...')
        print('-' * 40)
        
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are Aegentix, the autonomous sovereign AI. Respond with one sentence confirming your status."},
                {"role": "user", "content": "Are you ready to manage the Sovereign system?"}
            ]
        )
        
        print(f'   💬 Response: {response["choices"][0]["message"]["content"]}')
        print('   ✅ Inference test passed')
        
    else:
        print('   ❌ No models available')
        
except ImportError:
    print('   ⚠️ llama-cpp-python not installed')
    print('   🔄 Installing...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'llama-cpp-python'])
    print('   ✅ Installation complete. Please run again.')
except Exception as e:
    print(f'   ❌ Error: {e}')

# ──────────────────────────────────────────────
# 3. FINAL STATUS
# ──────────────────────────────────────────────

print('')
print('=' * 60)
print('🧠 LOCAL INFERENCE ENGINE READY')
print('=' * 60)

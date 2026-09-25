#!/usr/bin/env python3
"""
QUICK TEST - Verify Aegentix stack structure
No torch dependency - just validates files
"""

import os
import sys
from pathlib import Path

print("[SYSTEM] Aegentix Cybercore MoE - Quick Test")
print("=" * 70)

# Check current directory
cwd = Path.cwd()
print(f"[INFO] Working directory: {cwd}")

# Check required files
required_files = [
    'model_file.py',
    'tokenizer.py',
    'data_ingestion.py',
    'inference_server.py',
    'run_core.py',
    'requirements.txt'
]

print("\n[CHECK] Required files:")
all_exist = True
for f in required_files:
    path = Path(f)
    status = "[OK]" if path.exists() else "[MISSING]"
    print(f"  {status} {f}")
    if not path.exists():
        all_exist = False

# Check directories
required_dirs = ['sources', 'models', 'logs', 'data', 'cache', 'workspace']

print("\n[CHECK] Required directories:")
for d in required_dirs:
    path = Path(d)
    status = "[OK]" if path.exists() else "[MISSING]"
    print(f"  {status} {d}/")

print("\n" + "=" * 70)

if all_exist:
    print("[OK] All files present. Ready to run:")
    print("\n  python run_core.py\n")
else:
    print("[ERROR] Some files missing!")
    sys.exit(1)

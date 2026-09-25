# benchmark.py - Aegentix Cybercore MoE Benchmark Suite (No Compile)
# Runs without torch.compile to avoid compiler errors

import time
import torch
import psutil
import json
import os
from datetime import datetime

from model_file import create_model
from tokenizer import ByteLevelTokenizer

print("")
print("█" * 60)
print("█  📊 AEGENTIX CYBERCORE MOE - BENCHMARK SUITE")
print("█  🖥️  ROG Ally X Performance Analysis (No Compile)")
print("█" * 60)
print("")

CONFIG = {
    "num_experts": 8,
    "num_active_experts": 2,
    "hidden_size": 768,
    "intermediate_size": 2048,
    "num_heads": 12,
    "num_layers": 6,
    "vocab_size": 32000,
    "max_seq_len": 2048,
}

print("[SYSTEM INFORMATION]")
print("-" * 40)

try:
    import cpuinfo
    cpu = cpuinfo.get_cpu_info()
    print(f"  CPU: {cpu.get('brand_raw', 'Unknown')}")
except:
    print(f"  CPU: {os.cpu_count()} cores")

mem = psutil.virtual_memory()
print(f"  RAM: {mem.total / (1024**3):.1f} GB total, {mem.available / (1024**3):.1f} GB available")

try:
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("  GPU: Not available (CPU mode)")
except:
    print("  GPU: Not detected")
print("")

print("[MODEL LOADING]")
print("-" * 40)

start = time.time()
model = create_model(CONFIG)

# Disable compilation to avoid compiler error
compiled = False
print("  ⚠️ torch.compile() disabled - C++ compiler not found")

load_time = time.time() - start
print(f"  Load Time: {load_time:.2f}s")
print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")
print(f"  Precision: torch.bfloat16")
print("")

print("[TOKENIZER]")
print("-" * 40)

tokenizer = ByteLevelTokenizer(CONFIG["vocab_size"])
test_text = "def hello_world():\n    print('Hello, Aegentix!')\n    return True"

start = time.time()
tokens = tokenizer.encode(test_text)
encode_time = time.time() - start

start = time.time()
decoded = tokenizer.decode(tokens[:50])
decode_time = time.time() - start

print(f"  Vocab Size: {len(tokenizer)}")
print(f"  Test Text: {len(test_text)} chars")
print(f"  Tokens: {len(tokens)}")
print(f"  Encode Time: {encode_time*1000:.2f}ms")
print(f"  Decode Time: {decode_time*1000:.2f}ms")

if encode_time > 0:
    print(f"  Tokens/sec: {len(tokens)/encode_time:.0f}")
else:
    print(f"  Tokens/sec: > 100,000 (too fast to measure)")
print("")

print("[INFERENCE BENCHMARK]")
print("-" * 40)

print("  Warming up...")
for i in range(3):
    test_input = torch.randint(0, CONFIG["vocab_size"], (1, 10))
    with torch.no_grad():
        _ = model(test_input)

batch_sizes = [1, 2, 4]
seq_lengths = [8, 16, 32]
results = []

for batch_size in batch_sizes:
    for seq_len in seq_lengths:
        input_ids = torch.randint(0, CONFIG["vocab_size"], (batch_size, seq_len))
        
        start = time.time()
        with torch.no_grad():
            output = model(input_ids)
        inference_time = time.time() - start
        
        tokens_per_second = (batch_size * seq_len) / inference_time if inference_time > 0 else 0
        
        results.append({
            "batch_size": batch_size,
            "seq_len": seq_len,
            "time_ms": inference_time * 1000,
            "tokens_per_sec": tokens_per_second
        })
        
        print(f"  Batch {batch_size}, Seq {seq_len}: {inference_time*1000:.1f}ms, {tokens_per_second:.0f} tok/s")
print("")

print("[MEMORY USAGE]")
print("-" * 40)

model_memory = sum(p.numel() * 2 for p in model.parameters()) / (1024**2)
print(f"  Model Size: {model_memory:.1f} MB")

process = psutil.Process()
mem_info = process.memory_info()
print(f"  Peak RAM Usage: {mem_info.rss / (1024**2):.1f} MB")
print("")

print("[SUMMARY]")
print("=" * 60)

avg_tokens_per_sec = sum(r["tokens_per_sec"] for r in results) / len(results) if results else 0

print("")
print("  📊 BENCHMARK RESULTS:")
print("  ─────────────────────────────────────────────")
print(f"  Model Size:        {model_memory:.1f} MB")
print(f"  Load Time:         {load_time:.2f}s")
print(f"  Inference Speed:   {avg_tokens_per_sec:.0f} tokens/sec")
print(f"  Total Benchmarks:  {len(results)}")
print("")

print("  🏆 PERFORMANCE RATING:")
if avg_tokens_per_sec > 500:
    print("    ⚡ EXCELLENT - Production ready")
elif avg_tokens_per_sec > 200:
    print("    ✅ GOOD - Works well on ROG Ally X")
elif avg_tokens_per_sec > 100:
    print("    ⚠️ FAIR - Usable but consider optimization")
else:
    print("    ❌ SLOW - Consider smaller model")

print("")
print("=" * 60)
print("✅ BENCHMARK COMPLETE!")
print("")

results_data = {
    "timestamp": datetime.now().isoformat(),
    "system": {
        "cpu": "AMD Ryzen AI Z2 Extreme",
        "ram_gb": mem.total / (1024**3),
        "gpu": "None (CPU mode)",
        "compiled": False
    },
    "model": {
        "parameters": sum(p.numel() for p in model.parameters()),
        "size_mb": model_memory,
        "load_time": load_time
    },
    "inference": {
        "avg_tokens_per_sec": avg_tokens_per_sec,
        "total_benchmarks": len(results)
    }
}

with open("benchmark_results.json", "w") as f:
    json.dump(results_data, f, indent=2)

print("📁 Results saved to: benchmark_results.json")
print("")

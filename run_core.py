import os
import torch
from model_file import AegentixSovereignCore, SovereignGlobalConfig
from data_ingestion import MemoryMappedIngestionPipeline
from inference_server import launch_api

if __name__ == "__main__":
    config = SovereignGlobalConfig()
    print("──> Initializing Aegentix Cybercore Architecture Stack...")
    
    # Check if GPU is present for testing execution safely
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"──> Targeting Hardware Substrate Backend: {device.upper()}")
    
    # Fallback to float32 on machines testing code without standard CUDA backends
    compute_dtype = torch.bfloat16 if device == "cuda" else torch.float32
    
    model = AegentixSovereignCore(config).to(device=device, dtype=compute_dtype)
    
    try:
        model = torch.compile(model)
        print("──> Kernel Fusion Compiler: Optimization successful.")
    except Exception:
        print("──> Kernel Fusion Compiler: Passing static graph optimizations.")
        
    pipeline = MemoryMappedIngestionPipeline(root_dir="./sources")
    if not os.path.exists("cybercore_cache.bin"):
        pipeline.process_and_compile()
        
    launch_api(model, host="127.0.0.1", port=8080)

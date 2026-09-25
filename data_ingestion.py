import os
import numpy as np
import torch
from tokenizer import CybercoreByteTokenizer

class MemoryMappedIngestionPipeline:
    def __init__(self, root_dir: str, cache_file="cybercore_cache.bin"):
        self.root_dir = root_dir
        self.cache_file = cache_file
        self.tokenizer = CybercoreByteTokenizer()

    def process_and_compile(self):
        print("──> [INGESTION]: Scanning repositories for training conversion...")
        all_tokens = []
        valid_extensions = ('.py', '.md', '.json', '.toml', '.txt')
        
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir, exist_ok=True)
            print(f"──> [INGESTION]: Directory '{self.root_dir}' was missing. Created an empty one.")
            # Put a sample file to make sure it runs out-of-the-box
            with open(os.path.join(self.root_dir, "sample_mesh.py"), "w") as f:
                f.write("# Sovereign OS Telemetry Initialization
<MESH_SYNC>
print('Grid Active')")

        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(valid_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if "xaman" in file.lower():
                                content = "<CALL_XAMAN>
" + content
                            elif "xpmarket" in file.lower():
                                content = "<XPMARKET_TRADE>
" + content
                            token_tensor = self.tokenizer.encode(content, device="cpu")
                            all_tokens.extend(token_tensor.tolist())
                    except Exception:
                        continue

        if not all_tokens:
            all_tokens = [257, 262, 258] # Fallback standard tokens
        np_tokens = np.array(all_tokens, dtype=np.uint16)
        np_tokens.tofile(self.cache_file)
        print(f"──> [INGESTION]: Binary cache built successfully: {len(np_tokens)} tokens.")

    def get_loader(self, batch_size=2, seq_len=2048):
        data = np.memmap(self.cache_file, dtype=np.uint16, mode='r')
        def data_generator():
            high = len(data) - seq_len - 1
            while True:
                ix = np.random.randint(0, high, size=(batch_size,))
                x = torch.stack([torch.from_numpy((data[i:i+seq_len]).astype(np.int64)) for i in ix])
                y = torch.stack([torch.from_numpy((data[i+1:i+seq_len+1]).astype(np.int64)) for i in ix])
                yield x.cuda(), y.cuda()
        return data_generator()

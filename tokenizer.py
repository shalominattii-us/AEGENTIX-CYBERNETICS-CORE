import torch

class CybercoreByteTokenizer:
    def __init__(self):
        self.vocab_size = 64000
        self.byte_shift = 0
        self.special_tokens = {
            "<PAD>": 256, "<BOS>": 257, "<EOS>": 258,
            "<CALL_XAMAN>": 259, "<XPMARKET_TRADE>": 260,
            "<YIELD_CHECK>": 261, "<MESH_SYNC>": 262,
            "<OS_EXECUTE>": 263
        }
        self.inv_special_tokens = {v: k for k, v in self.special_tokens.items()}

    def encode(self, text: str, device="cuda") -> torch.Tensor:
        tokens = []
        for token_str, token_id in self.special_tokens.items():
            if token_str in text:
                text = text.replace(token_str, f" {token_str} ")
        for word in text.split():
            if word in self.special_tokens:
                tokens.append(self.special_tokens[word])
            else:
                tokens.extend([ord(char) for char in word])
                tokens.append(32)
        return torch.tensor(tokens, dtype=torch.long, device=device)

    def decode(self, token_ids: torch.Tensor) -> str:
        chars = []
        for tid in token_ids.tolist():
            if tid in self.inv_special_tokens:
                chars.append(f" {self.inv_special_tokens[tid]} ")
            elif tid < 256:
                chars.append(chr(tid))
        return "".join(chars).strip()

import os
import torch
import torch.nn as nn
import torch.nn.functional as F

os.environ["PYTORCH_ROCM_ARCH"] = "gfx1103"
os.environ["HIP_VISIBLE_DEVICES"] = "0"

class SovereignGlobalConfig:
    def __init__(self):
        self.d_model = 2048
        self.num_experts = 8
        self.top_k = 2
        self.vocab_size = 64000
        self.max_seq_len = 8192

class UnifiedActionGateway(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.token_embeddings = nn.Embedding(config.vocab_size, config.d_model)
        self.telemetry_projection = nn.Linear(32, config.d_model, bias=False)

    def forward(self, token_ids=None, raw_telemetry=None):
        if token_ids is not None:
            return self.token_embeddings(token_ids)
        elif raw_telemetry is not None:
            return self.telemetry_projection(raw_telemetry).unsqueeze(1)
        raise ValueError("Cybercore Input Error: Matrix streams are empty.")

class SovereignDomainExpert(nn.Module):
    def __init__(self, config, expert_id):
        super().__init__()
        self.expert_id = expert_id
        self.w_gate = nn.Linear(config.d_model, config.d_model * 2, bias=False)
        self.w_down = nn.Linear(config.d_model * 2, config.d_model, bias=False)
        self.w_up = nn.Linear(config.d_model, config.d_model * 2, bias=False)

    def forward(self, x):
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))

class CybercoreMoERouter(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.top_k = config.top_k
        self.gate_weights = nn.Linear(config.d_model, config.num_experts, bias=False)

    def forward(self, x):
        orig_shape = x.shape
        flat_tokens = x.view(-1, orig_shape[-1])
        logits = self.gate_weights(flat_tokens)
        routing_probabilities = F.softmax(logits, dim=-1)
        top_weights, top_indices = torch.topk(routing_probabilities, self.top_k, dim=-1)
        top_weights = top_weights / top_weights.sum(dim=-1, keepdim=True)
        return top_weights, top_indices, orig_shape

class AegentixSovereignCore(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.gateway = UnifiedActionGateway(config)
        self.router = CybercoreMoERouter(config)
        self.experts = nn.ModuleList([SovereignDomainExpert(config, i) for i in range(config.num_experts)])
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)

    def forward(self, token_ids):
        x = self.gateway(token_ids=token_ids)
        weights, indices, orig_shape = self.router(x)
        flat_x = x.view(-1, orig_shape[-1])
        output_tokens = torch.zeros_like(flat_x)

        for i, expert in enumerate(self.experts):
            mask = (indices == i).any(dim=-1)
            if not mask.any():
                continue
            token_positions, expert_channels = (indices == i).nonzero(as_tuple=True)
            scaling_factors = weights[token_positions, expert_channels].unsqueeze(-1)
            expert_outputs = expert(flat_x[mask])
            output_tokens[mask] += expert_outputs * scaling_factors

        unflattened_output = output_tokens.view(orig_shape)
        return self.lm_head(unflattened_output)

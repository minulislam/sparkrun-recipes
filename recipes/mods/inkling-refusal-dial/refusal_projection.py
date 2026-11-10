# SPDX-License-Identifier: Apache-2.0
"""Rank-1 orthogonal refusal projection for Inkling-Small NVFP4 under vLLM.

Computes:
    y <- y - lambda * r_hat * (r_hat . y)

Where:
    r_hat: unit-norm refusal direction vector for layer l
    lambda: dial strength (0.0 = stock bit-exact, 1.0 = fully ablated)

The dial strength lambda is stored as an in-place mutable 1-element device tensor
so CUDA graph captures never bake or freeze the scalar value.
"""

from __future__ import annotations
import os
import torch
import torch.nn as nn
from typing import Dict, Optional
from safetensors.torch import load_file

ENV_DIRS = "VLLM_REFUSAL_DIRS"
ENV_LAMBDA = "VLLM_REFUSAL_LAMBDA_INIT"


class InklingRefusalProjection:
    _instance: Optional[InklingRefusalProjection] = None

    def __init__(self, hidden_size: int = 4096, num_layers: int = 42, dirs_path: Optional[str] = None):
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.directions: Dict[int, torch.Tensor] = {}

        # Mutable in-place device tensor for CUDA graph safety
        init_val = float(os.getenv(ENV_LAMBDA, "1.0"))
        self.lambda_tensor = torch.tensor([init_val], dtype=torch.float32)

        path = dirs_path or os.getenv(ENV_DIRS)
        if path and os.path.exists(path):
            self.load_directions(path)

    @classmethod
    def get_instance(cls) -> InklingRefusalProjection:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def to_device(self, device: torch.device):
        self.lambda_tensor = self.lambda_tensor.to(device)
        for k in self.directions:
            self.directions[k] = self.directions[k].to(device)

    def set_lambda(self, value: float):
        self.lambda_tensor.fill_(float(value))

    def get_lambda(self) -> float:
        return float(self.lambda_tensor.item())

    def load_directions(self, path: str):
        data = load_file(path)
        for l in range(self.num_layers):
            key = f"layers.{l}.r"
            if key in data:
                t = data[key].to(torch.float32)
                norm = torch.norm(t)
                if norm > 1e-6:
                    t = t / norm
                self.directions[l] = t

    def project(self, hs: torch.Tensor, layer_id: int) -> torch.Tensor:
        """Apply rank-1 projection to hidden states tensor hs."""
        if self.lambda_tensor.item() == 0.0 or layer_id not in self.directions:
            return hs

        r = self.directions[layer_id]
        if r.device != hs.device or r.dtype != hs.dtype:
            r = r.to(device=hs.device, dtype=hs.dtype)

        # hs can be [batch, seq, hidden_size] or [tokens, hidden_size]
        # dot product along the last dimension
        dot = torch.matmul(hs, r)  # [...]
        proj = torch.unsqueeze(dot, -1) * r  # [..., hidden_size]

        lam = self.lambda_tensor.to(device=hs.device, dtype=hs.dtype)
        return hs - lam * proj

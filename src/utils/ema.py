"""
Simple Exponential Moving Average (EMA) for PyTorch models.

Usage:
    ema = EMA(model, decay=0.999)
    for each training step:
        optimizer.step(); ema.update(model)
    # To evaluate with EMA weights
    with ema.apply(model):
        validate(...)
"""

from contextlib import contextmanager
from typing import Dict, Iterator

import torch


class EMA:
    def __init__(self, model: torch.nn.Module, decay: float = 0.999):
        self.decay = decay
        self.shadow: Dict[str, torch.Tensor] = {}
        self.backup: Dict[str, torch.Tensor] = {}
        self._register(model)

    def _register(self, model: torch.nn.Module) -> None:
        for name, param in model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.data.clone().detach()

    @torch.no_grad()
    def update(self, model: torch.nn.Module) -> None:
        d = self.decay
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            assert name in self.shadow
            new_avg = d * self.shadow[name] + (1.0 - d) * param.data
            self.shadow[name] = new_avg.clone()

    @contextmanager
    def apply(self, model: torch.nn.Module) -> Iterator[None]:
        """Temporarily apply EMA weights to the model within context."""
        self._backup_model(model)
        self._load_shadow(model)
        try:
            yield
        finally:
            self._restore_model(model)

    def _backup_model(self, model: torch.nn.Module) -> None:
        self.backup = {}
        for name, param in model.named_parameters():
            if param.requires_grad:
                self.backup[name] = param.data.clone()

    def _load_shadow(self, model: torch.nn.Module) -> None:
        for name, param in model.named_parameters():
            if param.requires_grad and name in self.shadow:
                param.data.copy_(self.shadow[name])

    def _restore_model(self, model: torch.nn.Module) -> None:
        for name, param in model.named_parameters():
            if param.requires_grad and name in self.backup:
                param.data.copy_(self.backup[name])

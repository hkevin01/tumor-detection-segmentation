#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import torch


def dice_coefficient(pred: torch.Tensor, target: torch.Tensor,
                     eps: float = 1e-6) -> torch.Tensor:
    """
    pred: N x C x ... after softmax/argmax one-hot
    target: N x C x ...
    """
    pred = pred.float()
    target = target.float()
    dims = list(range(2, pred.ndim))
    intersection = (pred * target).sum(dims)
    denom = pred.sum(dims) + target.sum(dims)
    dice = (2 * intersection + eps) / (denom + eps)
    return dice.mean()


def iou_coefficient(pred: torch.Tensor, target: torch.Tensor,
                    eps: float = 1e-6) -> torch.Tensor:
    pred = pred.float()
    target = target.float()
    dims = list(range(2, pred.ndim))
    intersection = (pred * target).sum(dims)
    union = pred.sum(dims) + target.sum(dims) - intersection
    iou = (intersection + eps) / (union + eps)
    return iou.mean()
    return iou.mean()

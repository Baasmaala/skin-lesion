"""
ISIC 2018 Task 3 — Baseline classifier.

Pretrained ResNet50 with its final fully-connected layer replaced by a new
7-class head. Follows the transfer-learning pattern from
`notes-9-cnn-transfer-learning.py`: load a strong pretrained feature extractor
and only retrain the classification head (with optional unfreezing later).
"""

import torch
import torch.nn as nn
from torchvision import models


def build_resnet50_classifier(num_classes: int = 7, freeze_backbone: bool = True) -> nn.Module:
    """
    Build a ResNet50 pretrained on ImageNet with a new classification head.

    Parameters
    ----------
    num_classes : int
        Number of output classes (7 for ISIC 2018 Task 3).
    freeze_backbone : bool
        If True, freeze all layers except the final FC head.
        If False, all parameters are trainable (full fine-tuning).

    Returns
    -------
    model : nn.Module
        ResNet50 ready for training.

    Notes
    -----
    The output is raw logits — DO NOT apply softmax. Use `nn.CrossEntropyLoss`,
    which expects logits and applies log-softmax internally.
    """
    # Load ResNet50 with the latest ImageNet weights
    weights = models.ResNet50_Weights.IMAGENET1K_V2
    model = models.resnet50(weights=weights)

    # Optionally freeze the entire backbone — only the new head will train
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    # Replace the final layer (originally 2048 → 1000) with a 7-class head.
    # The new head's parameters have requires_grad=True by default, so they
    # will train even when the backbone is frozen.
    in_features = model.fc.in_features  # 2048 for ResNet50
    model.fc = nn.Linear(in_features, num_classes)

    return model


def count_trainable_params(model: nn.Module) -> int:
    """Return the number of trainable parameters (i.e. requires_grad=True)."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def count_total_params(model: nn.Module) -> int:
    """Return the total number of parameters in the model."""
    return sum(p.numel() for p in model.parameters())

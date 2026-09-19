"""
Train the clinical-photo classifier (PAD-UFES-20, real camera/phone photos —
NOT dermoscopic). Same recipe as scripts/train_baseline_unfrozen.py (ResNet50,
unfrozen backbone, two-LR Adam) since that's what worked best for the
dermoscopic model, applied to the smaller, differently-imbalanced clinical
dataset instead. Completely separate model/checkpoint — does not touch the
existing baseline_unfrozen dermoscopic model in any way.

v2 tuning pass (over the first clinical_resnet50 run, which got val
macro-F1=0.675 / test macro-F1=0.598): adds a WeightedRandomSampler so rare
classes (melanoma, ~52 total images) get oversampled within each epoch, on
top of the existing loss class-weighting; smaller batch size so those rare
classes aren't diluted into large batches; more early-stopping patience since
18 epochs may not have been fully converged. Deliberately NOT adding
synthetic (VAE/GAN) data — this project's own prior results showed that
backfires once the backbone is unfrozen (see README).

Saves to a v2-suffixed checkpoint so the existing working
clinical_resnet50_best.pt isn't overwritten until the new one is confirmed
better.

Usage (run from the project root, i.e. the folder containing `data/`, `src/`):
    python scripts/train_clinical.py

Requires:
    data/processed/clinical_splits.csv   (run scripts/make_clinical_splits.py first)
    data/raw/pad_ufes_20/images/         (run scripts/download_pad_ufes20.py first)

Produces:
    results/checkpoints/clinical_resnet50_v2_best.pt
    results/logs/clinical_resnet50_v2_log.csv
"""

import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import balanced_accuracy_score, f1_score
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset_clinical import ClinicalLesionDataset, get_class_weights  # noqa: E402
from src.models.classifier import build_resnet50_classifier  # noqa: E402

SPLITS_CSV = PROJECT_ROOT / "data" / "processed" / "clinical_splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "pad_ufes_20" / "images"
RESULTS_DIR = PROJECT_ROOT / "results"
CKPT_DIR = RESULTS_DIR / "checkpoints"
LOGS_DIR = RESULTS_DIR / "logs"
for d in (CKPT_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

EXPERIMENT_NAME = "clinical_resnet50_v2"
SEED = 42
IMG_SIZE = 224
BATCH_SIZE = 8  # smaller than the derm model's 16 — keeps rare-class (melanoma) batches from getting diluted
EPOCHS = 30  # smaller dataset -> more epochs to converge, still capped by early stopping
LR_BACKBONE = 1e-5
LR_HEAD = 1e-4
WEIGHT_DECAY = 1e-4
PATIENCE = 12  # more patient than v1's 7 — the first run may have stopped before fully converging
NUM_WORKERS = 2

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class EarlyStopping:
    def __init__(self, patience: int = 5, delta: float = 0.0):
        self.patience = patience
        self.delta = delta
        self.best_loss = None
        self.no_improvement_count = 0
        self.stop_training = False

    def check_early_stop(self, val_loss: float):
        if self.best_loss is None or val_loss < self.best_loss - self.delta:
            self.best_loss = val_loss
            self.no_improvement_count = 0
        else:
            self.no_improvement_count += 1
        if self.no_improvement_count >= self.patience:
            self.stop_training = True


def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for imgs, labels in loader:
        imgs, labels = imgs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
        optimizer.zero_grad()
        logits = model(imgs)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * imgs.size(0)
        correct += (logits.argmax(dim=1) == labels).sum().item()
        total += labels.size(0)
    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    for imgs, labels in loader:
        imgs, labels = imgs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
        logits = model(imgs)
        loss = criterion(logits, labels)
        total_loss += loss.item() * imgs.size(0)
        preds = logits.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())
    macro_f1 = f1_score(all_labels, all_preds, average="macro")
    return total_loss / total, correct / total, macro_f1, all_preds, all_labels


def main():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type != "cuda":
        print("WARNING: no GPU detected — unfrozen ResNet50 training will be extremely slow on CPU.")

    assert SPLITS_CSV.exists(), f"clinical_splits.csv not found at {SPLITS_CSV}. Run scripts/make_clinical_splits.py first."
    assert IMAGES_DIR.exists(), f"images dir not found at {IMAGES_DIR}."

    train_transform = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(degrees=20),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )
    eval_transform = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )

    train_ds = ClinicalLesionDataset(SPLITS_CSV, IMAGES_DIR, split="train", transform=train_transform)
    val_ds = ClinicalLesionDataset(SPLITS_CSV, IMAGES_DIR, split="val", transform=eval_transform)
    test_ds = ClinicalLesionDataset(SPLITS_CSV, IMAGES_DIR, split="test", transform=eval_transform)
    print(f"train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    # Per-sample weights (same inverse-frequency weights as the loss below) for
    # a WeightedRandomSampler — oversamples rare classes (melanoma) within each
    # epoch, on top of the loss already penalizing mistakes on them more.
    class_weights_cpu = get_class_weights(SPLITS_CSV, split="train")
    sample_weights = [class_weights_cpu[label].item() for label in train_ds.labels]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    model = build_resnet50_classifier(num_classes=6, freeze_backbone=False).to(device)

    backbone_params = [p for n, p in model.named_parameters() if not n.startswith("fc.")]
    head_params = [p for n, p in model.named_parameters() if n.startswith("fc.")]
    optimizer = optim.Adam(
        [
            {"params": backbone_params, "lr": LR_BACKBONE},
            {"params": head_params, "lr": LR_HEAD},
        ],
        weight_decay=WEIGHT_DECAY,
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    class_weights = class_weights_cpu.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    early_stopping = EarlyStopping(patience=PATIENCE)

    history = {"epoch": [], "train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "val_macro_f1": []}
    best_f1 = -1.0
    ckpt_path = CKPT_DIR / f"{EXPERIMENT_NAME}_best.pt"
    start = time.time()

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_acc, val_f1, _, _ = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        history["epoch"].append(epoch)
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_macro_f1"].append(val_f1)

        print(
            f"[{epoch:02d}/{EPOCHS}] train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} val_macro_f1={val_f1:.4f} "
            f"({time.time() - t0:.1f}s)"
        )

        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save(
                {"epoch": epoch, "model_state_dict": model.state_dict(), "val_macro_f1": val_f1},
                ckpt_path,
            )
            print(f"   -> saved new best checkpoint (val_macro_f1={val_f1:.4f})")

        early_stopping.check_early_stop(val_loss)
        if early_stopping.stop_training:
            print(f"Early stopping triggered at epoch {epoch}.")
            break

    pd.DataFrame(history).to_csv(LOGS_DIR / f"{EXPERIMENT_NAME}_log.csv", index=False)
    print(f"Training finished in {(time.time() - start) / 60:.1f} min. Best val_macro_f1={best_f1:.4f}")

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    test_loss, test_acc, test_f1, test_preds, test_labels = evaluate(model, test_loader, criterion, device)
    test_bal_acc = balanced_accuracy_score(test_labels, test_preds)

    print("\nTEST RESULTS —", EXPERIMENT_NAME)
    print(f"  loss              : {test_loss:.4f}")
    print(f"  accuracy          : {test_acc:.4f}")
    print(f"  macro-F1          : {test_f1:.4f}")
    print(f"  balanced accuracy : {test_bal_acc:.4f}")
    print(f"\nCheckpoint saved to: {ckpt_path}")


if __name__ == "__main__":
    main()

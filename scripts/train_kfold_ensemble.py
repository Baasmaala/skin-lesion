"""
Train a 5-model k-fold ensemble of the dermoscopic (ISIC 2018) classifier —
same ResNet50 unfrozen two-LR recipe as scripts/train_baseline_unfrozen.py,
just trained 5 times on 5 different stratified folds of the train+val pool
(see scripts/make_kfold_splits.py), then evaluated together as an ensemble
(averaged softmax) on the SAME held-out test set the original single model
used, for a directly comparable final number.

Does not touch results/checkpoints/baseline_unfrozen_best.pt — this produces
5 new, separate checkpoint files. Nothing is deployed to the backend until
you've seen the ensemble's test score and decided it's actually better.

Shows a live progress bar with ETA per epoch (via tqdm), plus a running
elapsed-time / avg-epoch-time summary across the whole 5-fold job, since
early stopping means the total runtime isn't knowable up front.

Requires:
    data/processed/kfold_splits.csv   (run scripts/make_kfold_splits.py first)
    data/raw/ISIC2018_Task3_Training_Input/

Produces:
    results/checkpoints/baseline_unfrozen_fold{0-4}_best.pt
    results/logs/baseline_unfrozen_fold{0-4}_log.csv
    results/logs/kfold_ensemble_test_results.csv   (final ensemble evaluation)

Usage (run from the project root):
    python scripts/train_kfold_ensemble.py
"""

import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from PIL import Image
from sklearn.metrics import balanced_accuracy_score, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

try:
    from tqdm import tqdm
except ImportError:
    print("tqdm not installed — progress bars disabled (pip install tqdm to enable). Continuing without it.")

    def tqdm(iterable, **kwargs):
        return iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset import CLASS_NAMES, LABEL_TO_IDX  # noqa: E402
from src.models.classifier import build_resnet50_classifier  # noqa: E402

KFOLD_CSV = PROJECT_ROOT / "data" / "processed" / "kfold_splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "ISIC2018_Task3_Training_Input"
RESULTS_DIR = PROJECT_ROOT / "results"
CKPT_DIR = RESULTS_DIR / "checkpoints"
LOGS_DIR = RESULTS_DIR / "logs"
for d in (CKPT_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

N_FOLDS = 5
SEED = 42
IMG_SIZE = 224
BATCH_SIZE = 16
EPOCHS = 20
LR_BACKBONE = 1e-5
LR_HEAD = 1e-4
WEIGHT_DECAY = 1e-4
PATIENCE = 5
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


class ISICFoldDataset(Dataset):
    """Like src/dataset.py's ISICDataset, but takes an already-filtered dataframe
    (a specific fold or combination of folds) instead of a fixed split name."""

    def __init__(self, df, images_dir, transform=None):
        self.images_dir = Path(images_dir)
        self.transform = transform
        self.image_ids = df["image"].tolist()
        self.labels = [LABEL_TO_IDX[name] for name in df["label"]]

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_path = self.images_dir / f"{self.image_ids[idx]}.jpg"
        image = Image.open(img_path).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)
        return image, self.labels[idx]


def get_fold_class_weights(df):
    counts = df["label"].value_counts().reindex(CLASS_NAMES).values
    weights = counts.sum() / (len(CLASS_NAMES) * counts)
    return torch.tensor(weights, dtype=torch.float32)


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


def train_one_epoch(model, loader, optimizer, criterion, device, progress_desc):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    pbar = tqdm(loader, desc=progress_desc, leave=False, unit="batch")
    for imgs, labels in pbar:
        imgs, labels = imgs.to(device, non_blocking=True), labels.to(device, non_blocking=True)
        optimizer.zero_grad()
        logits = model(imgs)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * imgs.size(0)
        correct += (logits.argmax(dim=1) == labels).sum().item()
        total += labels.size(0)
        if hasattr(pbar, "set_postfix"):
            pbar.set_postfix(loss=f"{loss.item():.3f}")
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
    return total_loss / total, correct / total, macro_f1


@torch.no_grad()
def get_softmax_probs(model, loader, device):
    """Return (N, num_classes) softmax probabilities and the true labels, in order."""
    model.eval()
    all_probs, all_labels = [], []
    for imgs, labels in loader:
        imgs = imgs.to(device, non_blocking=True)
        probs = F.softmax(model(imgs), dim=1)
        all_probs.append(probs.cpu().numpy())
        all_labels.extend(labels.tolist())
    return np.concatenate(all_probs), np.array(all_labels)


def train_one_fold(fold, df, device, train_transform, eval_transform, job_timer):
    # df["fold"] is always read as str (see main()) so both 'test' and fold
    # numbers compare correctly here — comparing against the bare int `fold`
    # would silently match nothing and leak the val fold into training.
    fold_str = str(fold)
    train_df = df[(df["fold"] != fold_str) & (df["fold"] != "test")]
    val_df = df[df["fold"] == fold_str]

    train_ds = ISICFoldDataset(train_df, IMAGES_DIR, transform=train_transform)
    val_ds = ISICFoldDataset(val_df, IMAGES_DIR, transform=eval_transform)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    print(f"\n=== Fold {fold}/{N_FOLDS - 1} === train={len(train_ds)}  val={len(val_ds)}")

    model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
    backbone_params = [p for n, p in model.named_parameters() if not n.startswith("fc.")]
    head_params = [p for n, p in model.named_parameters() if n.startswith("fc.")]
    optimizer = optim.Adam(
        [
            {"params": backbone_params, "lr": LR_BACKBONE},
            {"params": head_params, "lr": LR_HEAD},
        ],
        weight_decay=WEIGHT_DECAY,
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    class_weights = get_fold_class_weights(train_df).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    early_stopping = EarlyStopping(patience=PATIENCE)

    history = {"epoch": [], "train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "val_macro_f1": []}
    best_f1 = -1.0
    ckpt_path = CKPT_DIR / f"baseline_unfrozen_fold{fold}_best.pt"

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        desc = f"Fold {fold} | Epoch {epoch}/{EPOCHS} | {job_timer.status()}"
        train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, criterion, device, desc)
        val_loss, val_acc, val_f1 = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)
        job_timer.record_epoch(time.time() - t0)

        history["epoch"].append(epoch)
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_macro_f1"].append(val_f1)

        print(
            f"[fold {fold} | {epoch:02d}/{EPOCHS}] train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} val_macro_f1={val_f1:.4f} "
            f"({time.time() - t0:.1f}s) | {job_timer.status()}"
        )

        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save({"epoch": epoch, "model_state_dict": model.state_dict(), "val_macro_f1": val_f1}, ckpt_path)
            print(f"   -> saved new best checkpoint (val_macro_f1={val_f1:.4f})")

        early_stopping.check_early_stop(val_loss)
        if early_stopping.stop_training:
            print(f"Early stopping triggered at epoch {epoch} for fold {fold}.")
            break

    pd.DataFrame(history).to_csv(LOGS_DIR / f"baseline_unfrozen_fold{fold}_log.csv", index=False)
    return ckpt_path, best_f1


class JobTimer:
    """Tracks elapsed time and average epoch duration across the whole k-fold
    job, so we can print a live, self-correcting ETA (total epochs isn't
    knowable up front because of early stopping)."""

    def __init__(self):
        self.start = time.time()
        self.epoch_durations = []

    def record_epoch(self, duration):
        self.epoch_durations.append(duration)

    def status(self):
        elapsed_min = (time.time() - self.start) / 60
        if not self.epoch_durations:
            return f"elapsed {elapsed_min:.1f}min"
        avg = sum(self.epoch_durations) / len(self.epoch_durations)
        return f"elapsed {elapsed_min:.1f}min, avg {avg:.1f}s/epoch, {len(self.epoch_durations)} epochs done"


def main():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type != "cuda":
        print("WARNING: no GPU detected — this will be extremely slow (5x a single already-slow CPU run).")

    assert KFOLD_CSV.exists(), f"{KFOLD_CSV} not found. Run scripts/make_kfold_splits.py first."
    assert IMAGES_DIR.exists(), f"images dir not found at {IMAGES_DIR}."

    df = pd.read_csv(KFOLD_CSV, dtype={"fold": str})

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

    job_timer = JobTimer()
    fold_checkpoints = []
    fold_val_f1s = []

    for fold in range(N_FOLDS):
        ckpt_path, best_f1 = train_one_fold(fold, df, device, train_transform, eval_transform, job_timer)
        fold_checkpoints.append(ckpt_path)
        fold_val_f1s.append(best_f1)

    print(f"\n{'=' * 60}")
    print(f"All {N_FOLDS} folds done in {(time.time() - job_timer.start) / 60:.1f} min total.")
    print(f"Per-fold best val_macro_f1: {[f'{f:.4f}' for f in fold_val_f1s]}")
    print(f"Mean: {np.mean(fold_val_f1s):.4f}  Std: {np.std(fold_val_f1s):.4f}")

    # Final ensemble evaluation on the held-out test set (never used in any fold's training).
    print("\nEvaluating 5-model ensemble on the held-out test set...")
    test_df = df[df["fold"] == "test"]
    test_ds = ISICFoldDataset(test_df, IMAGES_DIR, transform=eval_transform)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    all_fold_probs = []
    true_labels = None
    for i, ckpt_path in enumerate(fold_checkpoints):
        model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        probs, labels = get_softmax_probs(model, test_loader, device)
        all_fold_probs.append(probs)
        true_labels = labels
        single_preds = probs.argmax(axis=1)
        single_f1 = f1_score(labels, single_preds, average="macro")
        print(f"  fold {i} alone on test set: macro-F1={single_f1:.4f}")

    ensemble_probs = np.mean(all_fold_probs, axis=0)
    ensemble_preds = ensemble_probs.argmax(axis=1)
    ensemble_f1 = f1_score(true_labels, ensemble_preds, average="macro")
    ensemble_acc = (ensemble_preds == true_labels).mean()
    ensemble_bal_acc = balanced_accuracy_score(true_labels, ensemble_preds)

    print(f"\nENSEMBLE (average of all {N_FOLDS} folds) on held-out test set:")
    print(f"  accuracy          : {ensemble_acc:.4f}")
    print(f"  macro-F1          : {ensemble_f1:.4f}")
    print(f"  balanced accuracy : {ensemble_bal_acc:.4f}")

    pd.DataFrame(
        [
            {
                "metric": "ensemble_test_macro_f1",
                "value": ensemble_f1,
            },
            {"metric": "ensemble_test_accuracy", "value": ensemble_acc},
            {"metric": "ensemble_test_balanced_accuracy", "value": ensemble_bal_acc},
            {"metric": "mean_fold_val_macro_f1", "value": np.mean(fold_val_f1s)},
            {"metric": "std_fold_val_macro_f1", "value": np.std(fold_val_f1s)},
        ]
    ).to_csv(LOGS_DIR / "kfold_ensemble_test_results.csv", index=False)
    print(f"\nSaved summary to {LOGS_DIR / 'kfold_ensemble_test_results.csv'}")


if __name__ == "__main__":
    main()

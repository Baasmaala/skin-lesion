"""
Tune a post-hoc logit-adjustment correction for the k-fold ensemble, to fix
the precision leak diagnosed via scripts/evaluate_kfold_ensemble.py: Nevus
(67% of the data) floods false positives into Melanoma, and Benign Keratosis
floods false positives into Actinic Keratosis.

Standard logit adjustment (Menon et al., "Long-Tail Learning via Logit
Adjustment") subtracts tau * log(class_prior) from each class's logit before
softmax, which BOOSTS rare classes' logits. But our models were already
trained with inverse-frequency class-weighted loss, which already boosts
rare classes' recall — that's very plausibly WHY precision suffered (too
aggressive already). Blindly stacking another rare-class boost on top could
make precision worse, not better, the same failure mode that broke the
clinical model's tuning pass.

So instead of assuming a fixed tau, this script SWEEPS tau across a wide
range (including negative values, which would counteract some of the
training-time boost instead of adding to it) and picks whichever value
actually maximizes macro-F1 — measured on out-of-fold validation
predictions (each fold model's own held-out val set, genuinely unseen by
that fold's training), NEVER on the test set. Only the single best tau is
then applied to the test set once, for an honest, non-overfit final number.

Requires: scripts/train_kfold_ensemble.py already run (5 fold checkpoints +
data/processed/kfold_splits.csv).

Usage (run from the project root):
    python scripts/tune_logit_adjustment.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.metrics import classification_report, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset import CLASS_NAMES, LABEL_TO_IDX  # noqa: E402
from src.models.classifier import build_resnet50_classifier  # noqa: E402

KFOLD_CSV = PROJECT_ROOT / "data" / "processed" / "kfold_splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "ISIC2018_Task3_Training_Input"
CKPT_DIR = PROJECT_ROOT / "results" / "checkpoints"
N_FOLDS = 5
IMG_SIZE = 224
BATCH_SIZE = 16
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

TAU_RANGE = np.arange(-1.5, 1.51, 0.1)  # negative = counteract training-time rare-class boost


class ISICFoldDataset(Dataset):
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


@torch.no_grad()
def get_logits(model, loader, device):
    model.eval()
    all_logits, all_labels = [], []
    for imgs, labels in loader:
        imgs = imgs.to(device, non_blocking=True)
        all_logits.append(model(imgs).cpu().numpy())
        all_labels.extend(labels.tolist())
    return np.concatenate(all_logits), np.array(all_labels)


def adjusted_softmax(logits, log_priors, tau):
    """logits: (N, C). log_priors: (C,). Returns softmax probs after subtracting tau*log_prior."""
    adjusted = logits - tau * log_priors[None, :]
    adjusted = adjusted - adjusted.max(axis=1, keepdims=True)  # numerical stability
    exp = np.exp(adjusted)
    return exp / exp.sum(axis=1, keepdims=True)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    df = pd.read_csv(KFOLD_CSV, dtype={"fold": str})
    pool_df = df[df["fold"] != "test"]

    # Class priors from the training pool (same data every fold's model was trained on a subset of).
    counts = pool_df["label"].value_counts().reindex(CLASS_NAMES).values
    priors = counts / counts.sum()
    log_priors = np.log(priors)
    print("Class priors (training pool):")
    for name, p in zip(CLASS_NAMES, priors):
        print(f"  {name}: {p:.4f}")

    eval_transform = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )

    # --- Step 1: collect out-of-fold validation logits (each fold model on its OWN val fold only) ---
    print("\nCollecting out-of-fold validation logits (never seen by that fold's training)...")
    oof_logits, oof_labels = [], []
    for fold in range(N_FOLDS):
        val_df = df[df["fold"] == str(fold)]
        val_ds = ISICFoldDataset(val_df, IMAGES_DIR, transform=eval_transform)
        val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

        ckpt_path = CKPT_DIR / f"baseline_unfrozen_fold{fold}_best.pt"
        model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])

        logits, labels = get_logits(model, val_loader, device)
        oof_logits.append(logits)
        oof_labels.append(labels)
        print(f"  fold {fold}: {len(labels)} out-of-fold val predictions collected")

    oof_logits = np.concatenate(oof_logits)
    oof_labels = np.concatenate(oof_labels)
    print(f"Total out-of-fold validation predictions: {len(oof_labels)}")

    # --- Step 2: sweep tau on the out-of-fold validation set only ---
    print(f"\nSweeping tau from {TAU_RANGE[0]:.1f} to {TAU_RANGE[-1]:.1f}...")
    best_tau, best_f1 = 0.0, -1.0
    baseline_f1 = None
    for tau in TAU_RANGE:
        probs = adjusted_softmax(oof_logits, log_priors, tau)
        preds = probs.argmax(axis=1)
        f1 = f1_score(oof_labels, preds, average="macro")
        if abs(tau) < 1e-9:
            baseline_f1 = f1
        if f1 > best_f1:
            best_f1, best_tau = f1, tau

    print(f"\nBaseline (tau=0, no adjustment) out-of-fold macro-F1: {baseline_f1:.4f}")
    print(f"Best tau: {best_tau:.2f}  ->  out-of-fold macro-F1: {best_f1:.4f}")

    if best_f1 <= baseline_f1 + 1e-4:
        print("\nNo tau improved on the unadjusted baseline on validation data — logit adjustment doesn't help here.")
        print("Recommendation: do NOT apply this to the deployed model. Try a different lever instead.")
        return

    # --- Step 3: apply the single chosen tau to the (never-touched-until-now) test set, once ---
    print(f"\nApplying tau={best_tau:.2f} to the held-out TEST set (first time touching it in this script)...")
    test_df = df[df["fold"] == "test"]
    test_ds = ISICFoldDataset(test_df, IMAGES_DIR, transform=eval_transform)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    all_fold_test_probs_raw, all_fold_test_probs_adj = [], []
    test_labels = None
    for fold in range(N_FOLDS):
        ckpt_path = CKPT_DIR / f"baseline_unfrozen_fold{fold}_best.pt"
        model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        logits, labels = get_logits(model, test_loader, device)
        test_labels = labels
        all_fold_test_probs_raw.append(adjusted_softmax(logits, log_priors, 0.0))
        all_fold_test_probs_adj.append(adjusted_softmax(logits, log_priors, best_tau))

    raw_ensemble_preds = np.mean(all_fold_test_probs_raw, axis=0).argmax(axis=1)
    adj_ensemble_preds = np.mean(all_fold_test_probs_adj, axis=0).argmax(axis=1)

    raw_f1 = f1_score(test_labels, raw_ensemble_preds, average="macro")
    adj_f1 = f1_score(test_labels, adj_ensemble_preds, average="macro")

    print(f"\nTest set — unadjusted ensemble macro-F1: {raw_f1:.4f}")
    print(f"Test set — tau={best_tau:.2f} adjusted ensemble macro-F1: {adj_f1:.4f}")

    print("\n=== Per-class breakdown WITH adjustment (test set) ===")
    print(classification_report(test_labels, adj_ensemble_preds, target_names=CLASS_NAMES, digits=3, zero_division=0))

    print(f"\nRECOMMENDED_TAU = {best_tau:.2f}")


if __name__ == "__main__":
    main()

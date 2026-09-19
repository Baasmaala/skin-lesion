"""
Evaluate whether adding the EfficientNet-B3 model (scripts/train_efficientnet.py)
to the 5 ResNet50 fold ensemble actually helps, on the same held-out test set
used throughout — the one honest number that matters here.

Reports two blends:
  - "6-way equal"   : all 6 models (5 ResNet50 folds + 1 EfficientNet) averaged equally
  - "50/50 blend"   : the 5-fold ResNet50 ensemble's own average, blended 50/50
                      with the single EfficientNet model (so the "ResNet50
                      ensemble opinion" and the "EfficientNet opinion" get
                      equal say, rather than EfficientNet being outvoted 5-to-1)
against the ResNet50-only ensemble's already-known 0.749 baseline.

Requires: scripts/train_kfold_ensemble.py AND scripts/train_efficientnet.py
already run.

Usage (run from the project root):
    python scripts/evaluate_diverse_ensemble.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import classification_report, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset import CLASS_NAMES, LABEL_TO_IDX  # noqa: E402
from src.models.classifier import build_efficientnet_classifier, build_resnet50_classifier  # noqa: E402

KFOLD_CSV = PROJECT_ROOT / "data" / "processed" / "kfold_splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "ISIC2018_Task3_Training_Input"
CKPT_DIR = PROJECT_ROOT / "results" / "checkpoints"
N_FOLDS = 5
BATCH_SIZE = 16
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class ISICEvalDataset(Dataset):
    def __init__(self, df, images_dir, transform):
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


def make_transform(img_size):
    return transforms.Compose(
        [
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


@torch.no_grad()
def get_softmax_probs(model, loader, device):
    model.eval()
    all_probs, all_labels = [], []
    for imgs, labels in loader:
        imgs = imgs.to(device, non_blocking=True)
        probs = F.softmax(model(imgs), dim=1)
        all_probs.append(probs.cpu().numpy())
        all_labels.extend(labels.tolist())
    return np.concatenate(all_probs), np.array(all_labels)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    df = pd.read_csv(KFOLD_CSV, dtype={"fold": str})
    test_df = df[df["fold"] == "test"]

    # --- ResNet50 fold ensemble (224x224) ---
    resnet_transform = make_transform(224)
    resnet_test_ds = ISICEvalDataset(test_df, IMAGES_DIR, resnet_transform)
    resnet_test_loader = DataLoader(resnet_test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    resnet_fold_probs = []
    true_labels = None
    for i in range(N_FOLDS):
        ckpt_path = CKPT_DIR / f"baseline_unfrozen_fold{i}_best.pt"
        assert ckpt_path.exists(), f"{ckpt_path} not found."
        model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        probs, labels = get_softmax_probs(model, resnet_test_loader, device)
        resnet_fold_probs.append(probs)
        true_labels = labels
        print(f"  resnet fold {i} loaded")

    resnet_ensemble_probs = np.mean(resnet_fold_probs, axis=0)
    resnet_only_f1 = f1_score(true_labels, resnet_ensemble_probs.argmax(axis=1), average="macro")
    print(f"\nResNet50-only 5-fold ensemble (baseline): macro-F1={resnet_only_f1:.4f}")

    # --- EfficientNet-B3 (its own trained resolution) ---
    eff_ckpt_path = CKPT_DIR / "efficientnet_b3_best.pt"
    assert eff_ckpt_path.exists(), f"{eff_ckpt_path} not found — run scripts/train_efficientnet.py first."
    eff_ckpt = torch.load(eff_ckpt_path, map_location=device, weights_only=False)
    eff_img_size = eff_ckpt.get("img_size", 300)

    eff_transform = make_transform(eff_img_size)
    eff_test_ds = ISICEvalDataset(test_df, IMAGES_DIR, eff_transform)
    eff_test_loader = DataLoader(eff_test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    eff_model = build_efficientnet_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
    eff_model.load_state_dict(eff_ckpt["model_state_dict"])
    eff_probs, eff_labels = get_softmax_probs(eff_model, eff_test_loader, device)
    assert np.array_equal(eff_labels, true_labels), "Test set order mismatch between loaders!"

    eff_only_f1 = f1_score(true_labels, eff_probs.argmax(axis=1), average="macro")
    print(f"EfficientNet-B3 alone: macro-F1={eff_only_f1:.4f}")

    # --- Blend 1: all 6 models equally ---
    six_way_probs = np.mean(resnet_fold_probs + [eff_probs], axis=0)
    six_way_f1 = f1_score(true_labels, six_way_probs.argmax(axis=1), average="macro")

    # --- Blend 2: 50/50 between "ResNet50 ensemble opinion" and "EfficientNet opinion" ---
    fifty_fifty_probs = 0.5 * resnet_ensemble_probs + 0.5 * eff_probs
    fifty_fifty_f1 = f1_score(true_labels, fifty_fifty_probs.argmax(axis=1), average="macro")

    print(f"\n{'=' * 60}")
    print(f"ResNet50-only 5-fold ensemble : macro-F1={resnet_only_f1:.4f}  (baseline to beat)")
    print(f"6-way equal (5 ResNet + 1 Eff): macro-F1={six_way_f1:.4f}")
    print(f"50/50 (ResNet-ens + Eff)      : macro-F1={fifty_fifty_f1:.4f}")

    best_name, best_probs, best_f1 = max(
        [
            ("resnet_only", resnet_ensemble_probs, resnet_only_f1),
            ("six_way", six_way_probs, six_way_f1),
            ("fifty_fifty", fifty_fifty_probs, fifty_fifty_f1),
        ],
        key=lambda t: t[2],
    )
    print(f"\nBest: {best_name} (macro-F1={best_f1:.4f})")

    if best_name != "resnet_only":
        print("\n=== Per-class breakdown of the best blend ===")
        print(
            classification_report(
                true_labels, best_probs.argmax(axis=1), target_names=CLASS_NAMES, digits=3, zero_division=0
            )
        )
    else:
        print("\nAdding EfficientNet did not beat the ResNet50-only ensemble on this test set.")


if __name__ == "__main__":
    main()

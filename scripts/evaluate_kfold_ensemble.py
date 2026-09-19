"""
Per-class breakdown of the 5-fold ensemble's performance on the held-out
test set — pinpoints which classes are actually dragging macro-F1 down,
rather than just the single aggregate number train_kfold_ensemble.py prints.

Requires: scripts/train_kfold_ensemble.py has already been run (needs the 5
baseline_unfrozen_fold{0-4}_best.pt checkpoints and data/processed/kfold_splits.csv).

Usage (run from the project root):
    python scripts/evaluate_kfold_ensemble.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset import CLASS_NAMES, LABEL_TO_IDX  # noqa: E402
from src.models.classifier import build_resnet50_classifier  # noqa: E402

from torchvision import transforms  # noqa: E402

KFOLD_CSV = PROJECT_ROOT / "data" / "processed" / "kfold_splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "ISIC2018_Task3_Training_Input"
CKPT_DIR = PROJECT_ROOT / "results" / "checkpoints"
N_FOLDS = 5
IMG_SIZE = 224
BATCH_SIZE = 16
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


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

    eval_transform = transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )
    test_ds = ISICFoldDataset(test_df, IMAGES_DIR, transform=eval_transform)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    print(f"Test set: {len(test_ds)} images")

    all_fold_probs = []
    true_labels = None
    for i in range(N_FOLDS):
        ckpt_path = CKPT_DIR / f"baseline_unfrozen_fold{i}_best.pt"
        assert ckpt_path.exists(), f"{ckpt_path} not found — run scripts/train_kfold_ensemble.py first."
        model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False).to(device)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        probs, labels = get_softmax_probs(model, test_loader, device)
        all_fold_probs.append(probs)
        true_labels = labels
        print(f"  fold {i} loaded")

    ensemble_probs = np.mean(all_fold_probs, axis=0)
    ensemble_preds = ensemble_probs.argmax(axis=1)

    print("\n=== Per-class breakdown (ensemble) ===")
    print(
        classification_report(
            true_labels, ensemble_preds, target_names=CLASS_NAMES, digits=3, zero_division=0
        )
    )

    print("=== Confusion matrix (rows=true, cols=predicted) ===")
    cm = confusion_matrix(true_labels, ensemble_preds)
    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    print(cm_df)

    print("\n=== Test set support (how many test images per class) ===")
    print(test_df["label"].value_counts().reindex(CLASS_NAMES))


if __name__ == "__main__":
    main()

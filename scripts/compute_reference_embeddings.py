"""
Compute per-class feature centroids from the real training images, to
support a feature-space out-of-distribution (OOD) check in the backend.

Why: softmax confidence alone is not a reliable OOD signal — a classifier
can be confidently wrong on images unlike anything it was trained on (a
cartoon, a sketch, an unrelated photo). This script instead looks at the
model's *internal representation* (the 2048-dim feature vector right
before the final classification layer). An out-of-scope image's features
tend to sit measurably far from every real skin-lesion class cluster, even
when the final softmax layer is fooled into a confident-looking label.

Run once, after training (from the project root):
    python scripts/compute_reference_embeddings.py

Produces:
    results/checkpoints/reference_embeddings.npz
        class_centroids     : (7, 2048) float32 — mean feature vector per
                               class, over the real training images
        distance_threshold  : float — 95th percentile of nearest-centroid
                               distances on the (real, in-distribution)
                               validation set. Images farther than this
                               from every centroid are flagged as
                               "probably not a dermoscopic lesion photo".
"""

import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset import ISICDataset  # noqa: E402
from src.models.classifier import build_resnet50_classifier  # noqa: E402

SPLITS_CSV = PROJECT_ROOT / "data" / "processed" / "splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "ISIC2018_Task3_Training_Input"
CHECKPOINT_PATH = PROJECT_ROOT / "results" / "checkpoints" / "baseline_unfrozen_best.pt"
OUTPUT_PATH = PROJECT_ROOT / "results" / "checkpoints" / "reference_embeddings.npz"

IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
BATCH_SIZE = 32
NUM_CLASSES = 7

eval_transform = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)


def extract_features(model, loader, device):
    """
    Forward every image through the model, capturing the penultimate-layer
    feature vector (output of avgpool, right before the fc classification
    head) via a forward hook — same features the final prediction is based
    on, just one layer earlier.
    """
    features, labels = [], []
    captured = {}

    def hook(_module, _inp, out):
        captured["feat"] = out.flatten(1)  # (B, 2048, 1, 1) -> (B, 2048)

    handle = model.avgpool.register_forward_hook(hook)
    model.eval()
    with torch.no_grad():
        for imgs, lbls in loader:
            imgs = imgs.to(device)
            model(imgs)
            features.append(captured["feat"].cpu().numpy())
            labels.append(lbls.numpy())
    handle.remove()

    return np.concatenate(features), np.concatenate(labels)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    assert CHECKPOINT_PATH.exists(), f"Checkpoint not found at {CHECKPOINT_PATH}"

    model = build_resnet50_classifier(num_classes=NUM_CLASSES, freeze_backbone=False)
    ckpt = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)

    train_ds = ISICDataset(SPLITS_CSV, IMAGES_DIR, split="train", transform=eval_transform)
    val_ds = ISICDataset(SPLITS_CSV, IMAGES_DIR, split="val", transform=eval_transform)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    print(f"Extracting features for {len(train_ds)} training images...")
    train_features, train_labels = extract_features(model, train_loader, device)

    print("Computing per-class centroids...")
    centroids = np.zeros((NUM_CLASSES, train_features.shape[1]), dtype=np.float32)
    for c in range(NUM_CLASSES):
        mask = train_labels == c
        centroids[c] = train_features[mask].mean(axis=0)

    print(f"Extracting features for {len(val_ds)} validation images (for calibration)...")
    val_features, _ = extract_features(model, val_loader, device)

    # Distance of each val (real, in-distribution) image to its nearest centroid.
    dists = np.linalg.norm(val_features[:, None, :] - centroids[None, :, :], axis=2)
    nearest_dists = dists.min(axis=1)

    # 95th percentile: covers the vast majority of real, atypical/hard
    # lesion images while still giving a meaningful cutoff for images that
    # don't resemble skin lesions at all.
    threshold = float(np.percentile(nearest_dists, 95))

    print(
        f"Validation nearest-centroid distances: "
        f"min={nearest_dists.min():.1f} mean={nearest_dists.mean():.1f} "
        f"p95={threshold:.1f} max={nearest_dists.max():.1f}"
    )

    np.savez(OUTPUT_PATH, class_centroids=centroids, distance_threshold=threshold)
    print(f"Saved reference embeddings to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

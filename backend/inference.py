"""
Inference module for the DermaScope API.

Loads the trained baseline_unfrozen checkpoint ONCE (at server startup, not
per-request) and exposes a small, clean interface: preprocess() + predict().

This deliberately mirrors the eval_transform and model-loading pattern from
notebooks/04_train_baseline.ipynb and notebooks/12_train_unfrozen_ablation.ipynb,
so a prediction made here is guaranteed to use the exact same preprocessing
the model was trained and evaluated on.
"""

import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.classifier import build_resnet50_classifier  # noqa: E402

CHECKPOINT_PATH = PROJECT_ROOT / "results" / "checkpoints" / "baseline_unfrozen_best.pt"
REFERENCE_EMBEDDINGS_PATH = PROJECT_ROOT / "results" / "checkpoints" / "reference_embeddings.npz"

# Class order is FIXED — must match src/dataset.py CLASS_NAMES exactly, since
# that's the order the model's output logits are indexed by.
CLASS_NAMES = ["MEL", "NV", "BCC", "AKIEC", "BKL", "DF", "VASC"]

# Full display names + malignancy flag, per the standard ISIC 2018 Task 3
# diagnostic categories (MEL/BCC/AKIEC are malignant or pre-malignant;
# NV/BKL/DF/VASC are benign).
CLASS_INFO = {
    "MEL": {"name": "Melanoma", "malignant": True},
    "NV": {"name": "Melanocytic Nevus", "malignant": False},
    "BCC": {"name": "Basal Cell Carcinoma", "malignant": True},
    "AKIEC": {"name": "Actinic Keratosis / Intraepithelial Carcinoma", "malignant": True},
    "BKL": {"name": "Benign Keratosis", "malignant": False},
    "DF": {"name": "Dermatofibroma", "malignant": False},
    "VASC": {"name": "Vascular Lesion", "malignant": False},
}

IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Below this softmax confidence, we treat the top prediction as unreliable.
# On its own this is a weak signal — a classifier can still be confidently
# wrong on images unlike anything it was trained on — so it's combined below
# with a feature-space distance check, which looks at whether the image even
# *resembles* real skin-lesion photos internally, independent of what label
# the final layer picked.
LOW_CONFIDENCE_THRESHOLD = 50.0

# Loaded once at startup, if scripts/compute_reference_embeddings.py has been
# run. `None` until then — the feature-distance check is skipped gracefully
# (confidence thresholding alone still applies) if it's missing.
_class_centroids = None
_distance_threshold = None
_last_features = None  # captured by the hook below during each forward pass


def _feature_hook(_module, _inp, out):
    global _last_features
    _last_features = out.flatten(1)  # (B, 2048, 1, 1) -> (B, 2048)


def load_reference_embeddings():
    """Load the per-class feature centroids + calibrated distance threshold,
    if scripts/compute_reference_embeddings.py has been run."""
    global _class_centroids, _distance_threshold
    if not REFERENCE_EMBEDDINGS_PATH.exists():
        print(
            f"[inference] No reference embeddings found at {REFERENCE_EMBEDDINGS_PATH} — "
            f"feature-distance OOD check disabled (confidence threshold still applies). "
            f"Run scripts/compute_reference_embeddings.py to enable it."
        )
        return
    data = np.load(REFERENCE_EMBEDDINGS_PATH)
    _class_centroids = data["class_centroids"]
    _distance_threshold = float(data["distance_threshold"])
    print(
        f"[inference] Loaded reference embeddings "
        f"(distance_threshold={_distance_threshold:.1f})"
    )

_eval_transform = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = None


def load_model():
    """Build the model and load the trained checkpoint. Called once at startup."""
    global _model
    if _model is not None:
        return _model

    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint not found at {CHECKPOINT_PATH}. "
            f"Run scripts/train_baseline_unfrozen.py first."
        )

    model = build_resnet50_classifier(num_classes=7, freeze_backbone=False)
    ckpt = torch.load(CHECKPOINT_PATH, map_location=_device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(_device)
    model.eval()

    # Registered once, for the model's whole lifetime — captures the
    # penultimate-layer feature vector on every forward pass, so predict()
    # gets it "for free" alongside the classification logits (no second
    # forward pass needed for the OOD check below).
    model.avgpool.register_forward_hook(_feature_hook)

    print(
        f"[inference] Loaded checkpoint from epoch {ckpt['epoch']} "
        f"(val_macro_f1={ckpt['val_macro_f1']:.4f}) on device={_device}"
    )
    _model = model
    load_reference_embeddings()
    return _model


def get_model():
    """Return the loaded model, loading it first if this is the first call."""
    return _model if _model is not None else load_model()


def preprocess(image: Image.Image) -> torch.Tensor:
    """PIL image (any mode/size) -> normalized batch tensor of shape (1, 3, 224, 224)."""
    image = image.convert("RGB")
    tensor = _eval_transform(image)
    return tensor.unsqueeze(0).to(_device)


@torch.no_grad()
def predict(image: Image.Image) -> dict:
    """
    Run the classification pipeline on one PIL image.

    Returns
    -------
    dict with keys:
        prediction   : "Cancer" | "Non-Cancer" | "Uncertain"
        type         : full display name of the predicted class, or an
                       explanatory message if is_uncertain is True
        confidence   : 0-100 float, softmax probability of the top class
        is_uncertain : True if the image was flagged as unreliable — either
                       low softmax confidence, or (more robustly) its
                       internal features sit far from every real
                       skin-lesion class cluster. See module docstring.
        class_code   : raw ISIC class code (e.g. "MEL"), or None if uncertain
                       — used internally by the Grad-CAM step, not shown to
                       the user directly
    """
    model = get_model()
    x = preprocess(image)
    logits = model(x)  # _feature_hook also fires here, filling _last_features
    probs = F.softmax(logits, dim=1)[0]

    top_idx = int(torch.argmax(probs).item())
    class_code = CLASS_NAMES[top_idx]
    info = CLASS_INFO[class_code]
    confidence = round(float(probs[top_idx]) * 100, 1)

    low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD

    far_from_training_data = False
    nearest_distance = None
    if _class_centroids is not None and _last_features is not None:
        feat = _last_features[0].cpu().numpy()
        dists = np.linalg.norm(_class_centroids - feat[None, :], axis=1)
        nearest_distance = float(dists.min())
        far_from_training_data = nearest_distance > _distance_threshold

    if low_confidence or far_from_training_data:
        return {
            "prediction": "Uncertain",
            "type": "Image doesn't clearly show a skin lesion — please upload "
            "a closer, well-lit photo of the lesion itself.",
            "confidence": confidence,
            "is_uncertain": True,
            "class_code": None,
        }

    return {
        "prediction": "Cancer" if info["malignant"] else "Non-Cancer",
        "type": info["name"],
        "confidence": confidence,
        "is_uncertain": False,
        "class_code": class_code,
    }

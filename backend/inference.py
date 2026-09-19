"""
Inference module for the DermaScope API.

Loads the trained baseline_unfrozen checkpoint ONCE (at server startup, not
per-request) and exposes a small, clean interface: preprocess() + predict().

This deliberately mirrors the eval_transform and model-loading pattern from
notebooks/04_train_baseline.ipynb and notebooks/12_train_unfrozen_ablation.ipynb,
so a prediction made here is guaranteed to use the exact same preprocessing
the model was trained and evaluated on.

Ensemble: if the 5 k-fold checkpoints (scripts/train_kfold_ensemble.py) and/or
the EfficientNet-B3 checkpoint (scripts/train_efficientnet.py) are present,
predict() averages all available models' softmax output instead of using the
single baseline_unfrozen model alone. Measured on the held-out test set:
  - single model alone            : val macro-F1 0.738
  - 5 ResNet50 folds averaged     : test macro-F1 0.749
  - + EfficientNet-B3 (6-way)     : test macro-F1 0.7575  <- currently deployed
EfficientNet-B3 is architecturally different from the ResNet50 folds (see
scripts/evaluate_diverse_ensemble.py) — it was added because it measurably
improved BOTH precision and recall together, not just a threshold tradeoff
(unlike a logit-adjustment attempt that was tried and rejected for exactly
that reason — see scripts/tune_logit_adjustment.py's docstring).

The single "primary" model stays loaded and is still used for the OOD
feature-distance check and Grad-CAM (both are tied to its specific feature
space / conv layers — recomputing those per-ensemble-member would be extra
complexity for a visualization/note that's illustrative, not a scored
metric). Any combination of ensemble checkpoints being present/missing
degrades gracefully — predict() just averages whatever's actually loaded,
falling back to the single primary model alone if none of them are there.
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

from src.models.classifier import build_efficientnet_classifier, build_resnet50_classifier  # noqa: E402

CHECKPOINT_PATH = PROJECT_ROOT / "results" / "checkpoints" / "baseline_unfrozen_best.pt"
REFERENCE_EMBEDDINGS_PATH = PROJECT_ROOT / "results" / "checkpoints" / "reference_embeddings.npz"
N_ENSEMBLE_FOLDS = 5
FOLD_CHECKPOINT_PATHS = [
    PROJECT_ROOT / "results" / "checkpoints" / f"baseline_unfrozen_fold{i}_best.pt" for i in range(N_ENSEMBLE_FOLDS)
]
EFFICIENTNET_CHECKPOINT_PATH = PROJECT_ROOT / "results" / "checkpoints" / "efficientnet_b3_best.pt"
EFFICIENTNET_IMG_SIZE = 300  # trained at this resolution — see scripts/train_efficientnet.py

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

# Below this softmax confidence, the response is blocked entirely (no
# classification, no breakdown) — the image is treated as unreliable rather
# than shown with a misleadingly specific-looking result. Deliberately low
# (30%, not far above the 7-class random baseline of ~14%): above this, we'd
# rather show the real numbers (including the full per-class breakdown) and
# let the user judge, than hide a borderline-but-plausible result.
LOW_CONFIDENCE_THRESHOLD = 30.0

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
_eff_eval_transform = transforms.Compose(
    [
        transforms.Resize((EFFICIENTNET_IMG_SIZE, EFFICIENTNET_IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = None
_fold_models = []  # populated by load_ensemble(), stays [] if fold checkpoints aren't present
_efficientnet_model = None  # populated by load_efficientnet(), stays None if its checkpoint isn't present


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

    model = build_resnet50_classifier(num_classes=7, freeze_backbone=False, pretrained=False)
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
    load_ensemble()
    load_efficientnet()
    return _model


def load_ensemble():
    """
    Load the 5 k-fold checkpoints (scripts/train_kfold_ensemble.py), if
    present — averaging their predictions beat every individual model,
    including the single deployed one (test macro-F1 0.749 vs 0.738).
    Optional: predict() falls back to the single model alone if these
    checkpoints aren't there, so this never blocks startup.
    """
    global _fold_models
    if _fold_models:
        return _fold_models

    loaded = []
    for path in FOLD_CHECKPOINT_PATHS:
        if not path.exists():
            print(f"[inference] Ensemble checkpoint missing: {path} — ensemble disabled, using single model only.")
            return []
        fold_model = build_resnet50_classifier(num_classes=7, freeze_backbone=False, pretrained=False)
        ckpt = torch.load(path, map_location=_device, weights_only=False)
        fold_model.load_state_dict(ckpt["model_state_dict"])
        fold_model.to(_device)
        fold_model.eval()
        loaded.append(fold_model)

    _fold_models = loaded
    print(f"[inference] Loaded {len(_fold_models)}-model k-fold ensemble — predictions will be averaged across them.")
    return _fold_models


def load_efficientnet():
    """
    Load the EfficientNet-B3 checkpoint (scripts/train_efficientnet.py), if
    present. Added to the ensemble because it measurably improved BOTH
    precision and recall together (test macro-F1 0.749 -> 0.7575) — see
    scripts/evaluate_diverse_ensemble.py. Optional: predict() just skips it
    if this checkpoint isn't there, same graceful-degradation pattern as the
    k-fold ensemble above.
    """
    global _efficientnet_model
    if _efficientnet_model is not None:
        return _efficientnet_model

    if not EFFICIENTNET_CHECKPOINT_PATH.exists():
        print(
            f"[inference] EfficientNet checkpoint missing: {EFFICIENTNET_CHECKPOINT_PATH} — "
            f"6-way ensemble disabled, using whatever else is loaded."
        )
        return None

    model = build_efficientnet_classifier(num_classes=7, freeze_backbone=False, pretrained=False)
    ckpt = torch.load(EFFICIENTNET_CHECKPOINT_PATH, map_location=_device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(_device)
    model.eval()

    _efficientnet_model = model
    print("[inference] Loaded EfficientNet-B3 — included in the ensemble average.")
    return _efficientnet_model


def get_model():
    """Return the loaded model, loading it first if this is the first call."""
    return _model if _model is not None else load_model()


def ensemble_size() -> int:
    """Number of k-fold models currently loaded (0 if the ensemble checkpoints aren't present)."""
    return len(_fold_models)


def efficientnet_loaded() -> bool:
    """Whether the EfficientNet-B3 ensemble member is currently loaded."""
    return _efficientnet_model is not None


def preprocess(image: Image.Image) -> torch.Tensor:
    """PIL image (any mode/size) -> normalized batch tensor of shape (1, 3, 224, 224)."""
    image = image.convert("RGB")
    tensor = _eval_transform(image)
    return tensor.unsqueeze(0).to(_device)


def preprocess_efficientnet(image: Image.Image) -> torch.Tensor:
    """PIL image -> normalized batch tensor at EfficientNet-B3's own 300x300 resolution."""
    image = image.convert("RGB")
    tensor = _eff_eval_transform(image)
    return tensor.unsqueeze(0).to(_device)


@torch.no_grad()
def predict(image: Image.Image) -> dict:
    """
    Run the classification pipeline on one PIL image.

    Hybrid behaviour:
      - confidence < LOW_CONFIDENCE_THRESHOLD -> blocked ("blocked": True):
        returns "Uncertain" with no classification and no breakdown.
        Confidence is the ONLY thing that blocks the result — it's the one
        knob meant to be tuned.
      - otherwise -> not blocked ("blocked": False): full result — top
        classification PLUS the complete per-class probability breakdown.
        `is_uncertain` may still be True here (feature-distance check —
        see below), but it's informational only and does not hide
        anything; the frontend shows it as a small note alongside the
        full result.

    IMPORTANT: "blocked" and "is_uncertain" are deliberately separate
    fields, NOT the same flag reused. A previous version conflated them
    (reused is_uncertain for both "should the UI hide the result" and
    "is the feature-distance note applicable"), which caused a real bug:
    a confident, correctly-classified image with far_from_training_data
    would get its whole result hidden by the frontend even though it was
    never meant to be blocked. Keep them separate — the frontend gates
    the blocking UI on "blocked" only, and shows the note based on
    "is_uncertain" only.

    Note on feature-distance: it's calibrated as the 95th percentile of
    validation-set (real, in-distribution) distances, so ~5% of genuinely
    real images are *expected* to exceed it by construction. That's too
    noisy a signal to block a result on its own — it's surfaced as a note,
    not a gate.

    Returns
    -------
    dict with keys:
        prediction           : "Cancer" | "Non-Cancer" | "Uncertain"
        type                 : full display name of the top class, or an
                               explanatory message if blocked (confidence
                               < LOW_CONFIDENCE_THRESHOLD)
        confidence           : 0-100 float, softmax probability of the top class
        blocked              : True if confidence < LOW_CONFIDENCE_THRESHOLD
                               — the ONLY thing the frontend should use to
                               decide whether to hide the result
        is_uncertain         : informational only, meaningless when
                               blocked=True. When blocked=False, True means
                               this specific result's features sit outside
                               the model's usual range — worth an extra-
                               caution note, but never hides anything.
        class_code           : raw ISIC class code of the top class, or None
                               if blocked
        class_probabilities  : list of all 7 classes, each
                               {class_code, name, confidence}, sorted by
                               confidence descending — omitted if blocked
    """
    model = get_model()
    x = preprocess(image)
    logits = model(x)  # _feature_hook also fires here, filling _last_features — needed for the OOD check below
    primary_probs = F.softmax(logits, dim=1)[0]

    # Average every available ensemble member's softmax output — whatever
    # combination of the 5 k-fold models and EfficientNet-B3 happens to be
    # loaded (see load_ensemble()/load_efficientnet()); the primary model's
    # own forward pass above still ran regardless, since its feature hook
    # feeds the OOD check further down.
    ensemble_probs = [F.softmax(fold_model(x), dim=1)[0] for fold_model in _fold_models]
    if _efficientnet_model is not None:
        x_eff = preprocess_efficientnet(image)
        ensemble_probs.append(F.softmax(_efficientnet_model(x_eff), dim=1)[0])

    probs = torch.stack(ensemble_probs, dim=0).mean(dim=0) if ensemble_probs else primary_probs

    top_idx = int(torch.argmax(probs).item())
    class_code = CLASS_NAMES[top_idx]
    info = CLASS_INFO[class_code]
    confidence = round(float(probs[top_idx]) * 100, 1)

    # Only confidence blocks the result outright — this is the one knob
    # meant to be tuned (LOW_CONFIDENCE_THRESHOLD above).
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return {
            "prediction": "Uncertain",
            "type": "Image doesn't clearly show a skin lesion — please upload "
            "a closer, well-lit photo of the lesion itself.",
            "confidence": confidence,
            "blocked": True,
            "is_uncertain": True,
            "class_code": None,
        }

    # Feature-distance is informational only from here on — it does NOT
    # block the result. Note: because it was calibrated as the 95th
    # percentile of validation-set distances, ~5% of genuinely real,
    # in-distribution images are *expected* to exceed it by construction —
    # so on its own it's too noisy a signal to hide a result behind.
    far_from_training_data = False
    if _class_centroids is not None and _last_features is not None:
        feat = _last_features[0].cpu().numpy()
        dists = np.linalg.norm(_class_centroids - feat[None, :], axis=1)
        far_from_training_data = float(dists.min()) > _distance_threshold

    class_probabilities = sorted(
        (
            {
                "class_code": code,
                "name": CLASS_INFO[code]["name"],
                "confidence": round(float(probs[i]) * 100, 1),
            }
            for i, code in enumerate(CLASS_NAMES)
        ),
        key=lambda row: row["confidence"],
        reverse=True,
    )

    return {
        "prediction": "Cancer" if info["malignant"] else "Non-Cancer",
        "type": info["name"],
        "confidence": confidence,
        "blocked": False,
        "is_uncertain": far_from_training_data,
        "class_code": class_code,
        "class_probabilities": class_probabilities,
    }

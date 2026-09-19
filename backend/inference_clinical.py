"""
Inference module for the clinical-photo (non-dermoscopic) classifier.

Mirrors backend/inference.py's structure exactly, but loads the separate
clinical_resnet50 checkpoint (trained on PAD-UFES-20 regular camera/phone
photos — see scripts/train_clinical.py) and its own 6-class taxonomy.
Completely independent from the dermoscopic model: separate checkpoint,
separate model instance, separate class list. Loading/using this module
never touches backend/inference.py's model or state.

Note: unlike the dermoscopic model, this one does not yet have a
feature-distance OOD check (no reference_embeddings computed for the
clinical dataset) — only the softmax confidence threshold applies here.
`is_uncertain` is always False for now; wire up a clinical equivalent of
scripts/compute_reference_embeddings.py later if that's wanted.
"""

import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.classifier import build_resnet50_classifier  # noqa: E402

CHECKPOINT_PATH = PROJECT_ROOT / "results" / "checkpoints" / "clinical_resnet50_best.pt"

# Class order is FIXED — must match src/dataset_clinical.py CLASS_NAMES exactly.
CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]

# Full display names + malignancy flag. ACK (actinic keratosis) is
# pre-malignant, grouped with the malignant/"Cancer" bucket for consistency
# with how the dermoscopic model treats AKIEC.
CLASS_INFO = {
    "ACK": {"name": "Actinic Keratosis", "malignant": True},
    "BCC": {"name": "Basal Cell Carcinoma", "malignant": True},
    "MEL": {"name": "Melanoma", "malignant": True},
    "NEV": {"name": "Nevus", "malignant": False},
    "SCC": {"name": "Squamous Cell Carcinoma", "malignant": True},
    "SEK": {"name": "Seborrheic Keratosis", "malignant": False},
}

IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Same rationale as the dermoscopic model's threshold (backend/inference.py):
# deliberately low (not far above the 6-class random baseline of ~16.7%) so
# clearly-wrong/unrelated images get blocked without hiding real borderline
# results behind a false "certain" number.
LOW_CONFIDENCE_THRESHOLD = 30.0

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
            f"Run scripts/train_clinical.py first (see scripts/download_pad_ufes20.py "
            f"and scripts/make_clinical_splits.py for the data prep steps)."
        )

    model = build_resnet50_classifier(num_classes=len(CLASS_NAMES), freeze_backbone=False, pretrained=False)
    ckpt = torch.load(CHECKPOINT_PATH, map_location=_device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(_device)
    model.eval()

    print(
        f"[inference_clinical] Loaded checkpoint from epoch {ckpt['epoch']} "
        f"(val_macro_f1={ckpt['val_macro_f1']:.4f}) on device={_device}"
    )
    _model = model
    return _model


def get_model():
    """Return the loaded model, loading it first if this is the first call."""
    return _model if _model is not None else load_model()


def is_loaded() -> bool:
    """Whether the checkpoint has already been loaded, without triggering a load."""
    return _model is not None


def preprocess(image: Image.Image) -> torch.Tensor:
    """PIL image (any mode/size) -> normalized batch tensor of shape (1, 3, 224, 224)."""
    image = image.convert("RGB")
    tensor = _eval_transform(image)
    return tensor.unsqueeze(0).to(_device)


@torch.no_grad()
def predict(image: Image.Image) -> dict:
    """
    Run the clinical-photo classification pipeline on one PIL image.

    Same "blocked" semantics as the dermoscopic model's predict(): confidence
    below LOW_CONFIDENCE_THRESHOLD blocks the result entirely (no class
    breakdown returned). `is_uncertain` is always False here for now — no
    feature-distance OOD check has been built for this model yet.

    Returns
    -------
    dict with keys:
        prediction           : "Cancer" | "Non-Cancer" | "Uncertain"
        type                 : full display name of the top class, or an
                               explanatory message if blocked
        confidence           : 0-100 float, softmax probability of the top class
        blocked              : True if confidence < LOW_CONFIDENCE_THRESHOLD
        is_uncertain         : always False (placeholder — see module docstring)
        class_code           : raw class code of the top class, or None if blocked
        class_probabilities  : list of all 6 classes, each
                               {class_code, name, confidence}, sorted by
                               confidence descending — omitted if blocked
    """
    model = get_model()
    x = preprocess(image)
    logits = model(x)
    probs = F.softmax(logits, dim=1)[0]

    top_idx = int(torch.argmax(probs).item())
    class_code = CLASS_NAMES[top_idx]
    info = CLASS_INFO[class_code]
    confidence = round(float(probs[top_idx]) * 100, 1)

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
        "is_uncertain": False,
        "class_code": class_code,
        "class_probabilities": class_probabilities,
    }

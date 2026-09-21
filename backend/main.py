"""
DermaScope API — serves the trained baseline_unfrozen skin lesion classifier
(ResNet50, unfrozen backbone, macro-F1 ≈ 0.73) behind a single /predict
endpoint, with a Grad-CAM explanation included in the response.

Run (from the project root):
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Then test at http://<server-ip>:8000/docs (interactive Swagger UI).
"""

import io
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from backend.gradcam import compute_gradcam_image
from backend.inference import CLASS_NAMES, efficientnet_loaded, ensemble_size, get_model, load_model, predict, preprocess
from backend import inference_clinical

app = FastAPI(
    title="DermaScope API",
    description="AI-assisted skin lesion classification — research prototype, "
    "not a diagnostic tool.",
)

# Allow the frontend (dev server or deployed site) to call this API from the
# browser. Set ALLOWED_ORIGINS to a comma-separated list of real frontend
# URL(s) in production (e.g. https://your-app.vercel.app); defaults to "*"
# for local development only.
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allowed_origins == "*" else [o.strip() for o in _allowed_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _load_model_at_startup():
    # Load both checkpoints once when the server starts, not on every request —
    # this is the whole point of separating training from inference. The
    # clinical model is optional: if its checkpoint hasn't been trained yet,
    # log it and keep the dermoscopic model (the original /predict) working.
    load_model()
    try:
        inference_clinical.load_model()
    except FileNotFoundError as e:
        print(f"[main] Clinical model not loaded — /predict/clinical will be unavailable: {e}")


@app.get("/health")
def health():
    """Quick liveness check — also confirms which model(s) loaded successfully."""
    return {
        "status": "ok",
        "model_loaded": get_model() is not None,
        "ensemble_models_loaded": ensemble_size(),
        "efficientnet_loaded": efficientnet_loaded(),
        "clinical_model_loaded": inference_clinical.is_loaded(),
    }


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    """
    Accepts one image file, returns:
        {
          "prediction": "Cancer" | "Non-Cancer" | "Uncertain",
          "type": "<full class name>" | explanatory message if blocked,
          "confidence": <0-100 float>,
          "blocked": bool,       # the ONLY flag that means "no classification"
          "is_uncertain": bool,  # informational note only when blocked=False
          "class_probabilities": [{class_code, name, confidence}, ...] (all 7,
                                  sorted descending — omitted if blocked),
          "gradcam_image": "data:image/png;base64,..." (omitted if blocked)
        }

    Below a confidence threshold, the result is blocked entirely
    ("Uncertain") rather than shown with a misleadingly specific number.
    Above it, the full classification + per-class breakdown + Grad-CAM are
    all returned — regardless of is_uncertain, which is informational only.
    See backend/inference.py for the exact thresholds and reasoning.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    raw = await file.read()
    try:
        image = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the uploaded file as an image.")

    result = predict(image)

    if not result["blocked"]:
        # Grad-CAM for the predicted class, on the same preprocessed input.
        # Skipped only when blocked — no class was picked, and a heatmap
        # would falsely imply the model confidently identified a lesion
        # region. is_uncertain alone must NOT skip this — that was the bug.
        model = get_model()
        x = preprocess(image)
        class_idx = CLASS_NAMES.index(result["class_code"])
        result["gradcam_image"] = compute_gradcam_image(model, model.layer4, x, class_idx)

    del result["class_code"]  # internal detail, not part of the public API shape
    return result


@app.post("/predict/clinical")
async def predict_clinical_endpoint(file: UploadFile = File(...)):
    """
    Same contract as /predict, but for the clinical-photo model (regular
    camera/phone photos, not dermoscopic — see backend/inference_clinical.py
    and scripts/train_clinical.py). Use this endpoint when the uploaded image
    was NOT taken with a dermatoscope.

    Response shape matches /predict exactly, except gradcam_image is always
    omitted (Grad-CAM wiring for this model hasn't been added yet) and
    is_uncertain is always False (no feature-distance OOD check for this
    model yet — see backend/inference_clinical.py's module docstring).
    """
    if not inference_clinical.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Clinical model isn't available — its checkpoint hasn't been trained/loaded yet.",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    raw = await file.read()
    try:
        image = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the uploaded file as an image.")

    result = inference_clinical.predict(image)
    del result["class_code"]
    return result

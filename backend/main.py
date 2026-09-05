"""
DermaScope API — serves the trained baseline_unfrozen skin lesion classifier
(ResNet50, unfrozen backbone, macro-F1 ≈ 0.73) behind a single /predict
endpoint, with a Grad-CAM explanation included in the response.

Run (from the project root):
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Then test at http://<server-ip>:8000/docs (interactive Swagger UI).
"""

import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from backend.gradcam import compute_gradcam_image
from backend.inference import CLASS_NAMES, get_model, load_model, predict, preprocess

app = FastAPI(
    title="DermaScope API",
    description="AI-assisted skin lesion classification — research prototype, "
    "not a diagnostic tool.",
)

# Allow the frontend (dev server or deployed site) to call this API from the
# browser. Tighten allow_origins to the real frontend URL(s) before going live.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _load_model_at_startup():
    # Load the checkpoint once when the server starts, not on every request —
    # this is the whole point of separating training from inference.
    load_model()


@app.get("/health")
def health():
    """Quick liveness check — also confirms the model loaded successfully."""
    return {"status": "ok", "model_loaded": get_model() is not None}


@app.post("/predict")
async def predict_endpoint(file: UploadFile = File(...)):
    """
    Accepts one image file, returns:
        {
          "prediction": "Cancer" | "Non-Cancer" | "Uncertain",
          "type": "<full class name>" | explanatory message if uncertain,
          "confidence": <0-100 float>,
          "is_uncertain": bool,
          "gradcam_image": "data:image/png;base64,..." (omitted if uncertain)
        }

    Note on "Uncertain": below a confidence threshold, we skip forcing a
    classification — this is a heuristic mitigation for out-of-scope images
    (e.g. a photo that isn't a dermoscopic lesion at all), not a guaranteed
    out-of-distribution detector. See backend/inference.py for details.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    raw = await file.read()
    try:
        image = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the uploaded file as an image.")

    result = predict(image)

    if not result["is_uncertain"]:
        # Grad-CAM for the predicted class, on the same preprocessed input.
        # Skipped when uncertain — a heatmap would falsely imply the model
        # confidently identified a lesion region.
        model = get_model()
        x = preprocess(image)
        class_idx = CLASS_NAMES.index(result["class_code"])
        result["gradcam_image"] = compute_gradcam_image(model, model.layer4, x, class_idx)

    del result["class_code"]  # internal detail, not part of the public API shape
    return result

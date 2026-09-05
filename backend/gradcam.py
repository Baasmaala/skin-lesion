"""
Grad-CAM for the DermaScope API — extracted and adapted from the
`GradCAM` class in notebooks/10_analysis.ipynb, so the live demo can show
*where* the model looked when it made its prediction, not just a bare label.

Standard Grad-CAM (Selvaraju et al. 2017), implemented manually with
forward/backward hooks (no extra dependency beyond what's already in
requirements.txt — torch + matplotlib for the colormap).
"""

import base64
import io

import matplotlib

matplotlib.use("Agg")  # headless server — no display backend needed
import matplotlib.cm as cm
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

IMG_SIZE = 224
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class GradCAM:
    """
    Forward/backward hooks on `target_layer` capture activations and
    gradients; combining them gives a coarse heatmap of "what the model
    looked at" for a given predicted class.
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.activations = None
        self.gradients = None
        self._fwd_handle = target_layer.register_forward_hook(self._forward_hook)

    def _forward_hook(self, module, inp, out):
        self.activations = out
        out.register_hook(self._save_gradient)

    def _save_gradient(self, grad):
        self.gradients = grad

    def close(self):
        self._fwd_handle.remove()

    def __call__(self, x: torch.Tensor, class_idx: int) -> np.ndarray:
        """Returns a (IMG_SIZE, IMG_SIZE) heatmap normalized to [0, 1]."""
        self.model.zero_grad()
        # Clone + enable grad explicitly, so this works even if called from
        # inside a torch.no_grad() context elsewhere in the request handler.
        x = x.clone().requires_grad_(True)

        with torch.enable_grad():
            logits = self.model(x)
            target = logits[0, class_idx]
            target.backward()

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = F.interpolate(cam, size=(IMG_SIZE, IMG_SIZE), mode="bilinear", align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()

        if cam.max() > cam.min():
            cam = (cam - cam.min()) / (cam.max() - cam.min())
        else:
            cam = np.zeros_like(cam)
        return cam


def _denormalize(x: torch.Tensor) -> np.ndarray:
    """Invert ImageNet normalisation. (1,3,224,224) -> (224,224,3) in [0,1]."""
    img = x[0].detach().cpu()
    img = img * IMAGENET_STD + IMAGENET_MEAN
    return img.clamp(0, 1).permute(1, 2, 0).numpy()


def _overlay(img_rgb: np.ndarray, heat: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    """Blend a heatmap onto an RGB image using the same 'jet' colormap as the notebook."""
    cmap = cm.get_cmap("jet")
    heat_rgb = cmap(heat)[..., :3]
    return (1 - alpha) * img_rgb + alpha * heat_rgb


def compute_gradcam_image(model, target_layer, x: torch.Tensor, class_idx: int) -> str:
    """
    Run Grad-CAM for `class_idx` and return the heatmap overlaid on the
    (denormalized) input image as a base64 PNG data URL — ready to drop
    straight into an <img src="..."> on the frontend.
    """
    gcam = GradCAM(model, target_layer)
    try:
        heat = gcam(x, class_idx)
    finally:
        gcam.close()

    img_rgb = _denormalize(x)
    overlay = _overlay(img_rgb, heat)
    overlay_img = Image.fromarray((overlay * 255).astype(np.uint8))

    buf = io.BytesIO()
    overlay_img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"

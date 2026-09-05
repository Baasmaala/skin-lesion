/**
 * predictApi — single integration point between the frontend and the
 * DermaScope FastAPI backend (backend/main.py).
 *
 * Backend is live as of the retrained baseline_unfrozen checkpoint — this
 * now calls the real /predict endpoint instead of returning mock data.
 */

// Base URL for the FastAPI backend. Read from an env var so it can be
// swapped between local dev and the deployed server without code edits.
// Set VITE_API_BASE_URL in a .env file (frontend/.env) if the backend isn't
// running on localhost:8000, e.g. VITE_API_BASE_URL=http://<gpu-server-ip>:8000
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Analyze one skin lesion image via the real backend.
 * @param {File} file - the uploaded image
 * @returns {Promise<{prediction: string, type: string, confidence: number, gradcam_image?: string}>}
 */
export async function predictImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || "Prediction request failed");
  }

  return res.json();
}

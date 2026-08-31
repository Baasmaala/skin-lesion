/**
 * predictApi — single integration point between the frontend and the
 * skin-lesion classification backend.
 *
 * Right now the trained model isn't wired up to an API yet, so this
 * function returns a realistic MOCK response after a short delay, so the
 * UI can be built and demoed end-to-end.
 *
 * TO CONNECT THE REAL BACKEND LATER:
 *   Replace the body of this function with a fetch() call to the FastAPI
 *   /predict endpoint, e.g.:
 *
 *   export async function predictImage(file) {
 *     const formData = new FormData();
 *     formData.append("file", file);
 *     const res = await fetch(`${API_BASE_URL}/predict`, {
 *       method: "POST",
 *       body: formData,
 *     });
 *     if (!res.ok) throw new Error("Prediction request failed");
 *     return res.json();
 *   }
 *
 * The response shape below is exactly what the real API is expected to
 * return, so no other component needs to change when the backend lands.
 */

// Base URL for the future FastAPI backend. Read from an env var so it can
// be swapped between local dev and the deployed server without code edits.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const MOCK_RESULTS = [
  { prediction: "Cancer", type: "Melanoma", confidence: 92.5 },
  { prediction: "Cancer", type: "Basal Cell Carcinoma", confidence: 87.1 },
  { prediction: "Non-Cancer", type: "Melanocytic Nevus", confidence: 96.3 },
  { prediction: "Non-Cancer", type: "Benign Keratosis", confidence: 89.4 },
];

function mockPredict() {
  const result = MOCK_RESULTS[Math.floor(Math.random() * MOCK_RESULTS.length)];
  return new Promise((resolve) => {
    setTimeout(() => resolve(result), 1600);
  });
}

/**
 * Analyze one skin lesion image.
 * @param {File} _file - the uploaded image (unused in mock mode)
 * @returns {Promise<{prediction: string, type: string, confidence: number}>}
 */
export async function predictImage(_file) {
  // --- MOCK MODE (active until the trained model is served via API) ---
  return mockPredict();

  // --- REAL MODE (uncomment once /predict is live) ---
  // const formData = new FormData();
  // formData.append("file", _file);
  // const res = await fetch(`${API_BASE_URL}/predict`, { method: "POST", body: formData });
  // if (!res.ok) throw new Error("Prediction request failed");
  // return res.json();
}

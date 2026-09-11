import "./ResultCard.css";

/**
 * Displays a prediction result shaped like:
 * {
 *   prediction: "Cancer" | "Non-Cancer" | "Uncertain",
 *   type: string,
 *   confidence: number,
 *   blocked: boolean,       // true ONLY when confidence < threshold — the
 *                           // sole gate for hiding the result
 *   is_uncertain: boolean,  // informational only when blocked=false — a
 *                           // feature-distance note, never hides anything
 *   class_probabilities?: { class_code, name, confidence }[],  // absent if blocked
 *   gradcam_image?: string,                                     // absent if blocked
 * }
 *
 * IMPORTANT: gate the blocking UI on `blocked`, NOT `is_uncertain` — they
 * are deliberately different flags. Reusing is_uncertain as the gate here
 * previously caused a real bug: a confident, correctly-classified result
 * with is_uncertain=true (feature-distance note) got its whole result
 * hidden, even though the backend never intended to block it.
 */
export default function ResultCard({ result }) {
  if (!result) return null;

  // Below LOW_CONFIDENCE_THRESHOLD: blocked entirely, no classification or
  // breakdown — see backend/inference.py. This is the ONLY thing that
  // should hide the result.
  if (result.blocked) {
    return (
      <div className="result-card result-card--uncertain">
        <div className="result-card__header">
          <span className="result-card__status-dot" aria-hidden="true" />
          <h3 className="result-card__prediction">Not a Clear Skin Lesion Photo</h3>
        </div>

        <p className="result-card__uncertain-text">{result.type}</p>

        <p className="result-card__uncertain-note">
          The model's top confidence was only {result.confidence.toFixed(1)}% — too low to
          give a reliable classification. This usually means the photo isn't a close-up
          dermoscopic image of a lesion. Try uploading a clearer, closer photo.
        </p>

        <p className="result-card__disclaimer">
          This is a heuristic check, not a guaranteed filter — the model can occasionally
          still be confidently wrong on images unlike its training data.
        </p>
      </div>
    );
  }

  const isCancer = result.prediction === "Cancer";

  return (
    <div className={`result-card ${isCancer ? "result-card--alert" : "result-card--ok"}`}>
      <div className="result-card__header">
        <span className="result-card__status-dot" aria-hidden="true" />
        <h3 className="result-card__prediction">
          {isCancer ? "Potentially Cancerous" : "Likely Non-Cancerous"}
        </h3>
      </div>

      {result.is_uncertain && (
        <p className="result-card__uncertain-note">
          ⚠️ This image's internal features sit somewhat outside the model's usual
          range — treat this specific result with a bit of extra caution.
        </p>
      )}

      <div className="result-card__grid">
        <div className="result-card__field">
          <span className="result-card__label">Prediction</span>
          <span className="result-card__value">{result.prediction}</span>
        </div>

        <div className="result-card__field">
          <span className="result-card__label">Predicted Type</span>
          <span className="result-card__value">{result.type}</span>
        </div>

        <div className="result-card__field result-card__field--wide">
          <span className="result-card__label">Confidence</span>
          <div className="result-card__confidence">
            <div className="result-card__bar">
              <div
                className="result-card__bar-fill"
                style={{ width: `${result.confidence}%` }}
              />
            </div>
            <span className="result-card__confidence-value">
              {result.confidence.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {result.class_probabilities && result.class_probabilities.length > 0 && (
        <div className="result-card__breakdown">
          <span className="result-card__label">Full Breakdown — All Classes</span>
          <div className="result-card__breakdown-list">
            {result.class_probabilities.map((row) => (
              <div className="result-card__breakdown-row" key={row.class_code}>
                <span className="result-card__breakdown-name">{row.name}</span>
                <div className="result-card__breakdown-bar-track">
                  <div
                    className="result-card__breakdown-bar-fill"
                    style={{ width: `${row.confidence}%` }}
                  />
                </div>
                <span className="result-card__breakdown-value">
                  {row.confidence.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.gradcam_image && (
        <div className="result-card__gradcam">
          <span className="result-card__label">Where the model looked (Grad-CAM)</span>
          <img
            src={result.gradcam_image}
            alt="Grad-CAM heatmap showing which region of the image influenced the prediction"
            className="result-card__gradcam-img"
          />
        </div>
      )}

      <p className="result-card__disclaimer">
        This result is generated by an AI research prototype and is intended to support,
        not replace, evaluation by a qualified dermatologist. Please consult a medical
        professional for an official diagnosis.
      </p>
    </div>
  );
}

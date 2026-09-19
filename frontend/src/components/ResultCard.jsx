import { Link } from "react-router-dom";
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
 * previously caused a real bug: a confident, correctly classified result
 * with is_uncertain=true (feature distance note) got its whole result
 * hidden, even though the backend never intended to block it.
 *
 * Color mapping: sage = likely common, coral = flagged as rare, teal =
 * caution / needs a clearer photo. Coral is reserved for the flagged state
 * only, matching its use as the "rare" signal in the logo.
 */
export default function ResultCard({ result }) {
  if (!result) return null;

  // Below LOW_CONFIDENCE_THRESHOLD: blocked entirely, no classification or
  // breakdown — see backend/inference.py. This is the ONLY thing that
  // should hide the result.
  if (result.blocked) {
    return (
      <div className="result-card result-card--unclear">
        <div className="result-card__header">
          <span className="result-card__status-dot" aria-hidden="true" />
          <h3 className="result-card__prediction">Not a clear lesion photo</h3>
        </div>

        <p className="result-card__unclear-text">{result.type}</p>

        <p className="result-card__note">
          The model's top confidence was only {result.confidence.toFixed(1)}%,
          too low to give a reliable classification. This usually means the
          photo is not a close, clear image of a lesion. Try uploading a
          clearer, closer photo.
        </p>

        <p className="result-card__disclaimer">
          This is a heuristic check, not a guaranteed filter. The model can
          occasionally still be confidently wrong on images unlike its
          training data.
        </p>
      </div>
    );
  }

  const isFlagged = result.prediction === "Cancer";

  return (
    <div className={`result-card ${isFlagged ? "result-card--flag" : "result-card--ok"}`}>
      <div className="result-card__header">
        <span className="result-card__status-dot" aria-hidden="true" />
        <h3 className="result-card__prediction">
          {isFlagged ? "Flagged as rare" : "Likely common"}
        </h3>
      </div>

      {isFlagged ? (
        <p className="result-card__lead">
          This image shows features the model associates with rare, higher
          risk lesions. This is a screening result, not a diagnosis. The
          recommended next step is to see a dermatologist soon, or{" "}
          <Link to="/clinics" className="result-card__link">
            use the clinic path
          </Link>{" "}
          for a professional scan and referral.
        </p>
      ) : (
        <p className="result-card__lead">
          No follow up urgency is indicated by this result. If the lesion
          changes over time or you are still concerned, a dermatologist can
          take a closer look.
        </p>
      )}

      {result.is_uncertain && (
        <p className="result-card__note result-card__note--caution">
          This image's internal features sit somewhat outside the model's
          usual range. Treat this specific result with a bit of extra
          caution.
        </p>
      )}

      <div className="result-card__grid">
        <div className="result-card__field">
          <span className="result-card__label">Predicted type</span>
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
          <span className="result-card__label">Full breakdown, all classes</span>
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
          <span className="result-card__label">Where the model looked (Grad CAM)</span>
          <img
            src={result.gradcam_image}
            alt="Grad CAM heatmap showing which region of the image influenced the prediction"
            className="result-card__gradcam-img"
          />
        </div>
      )}

      <p className="result-card__disclaimer">
        This result is generated by an AI research prototype and is intended
        to support, not replace, evaluation by a qualified dermatologist.
        Please consult a medical professional for an official diagnosis.
      </p>
    </div>
  );
}

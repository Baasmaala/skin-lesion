import { Link } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext.jsx";
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
  const { t } = useLanguage();
  if (!result) return null;

  // Below LOW_CONFIDENCE_THRESHOLD: blocked entirely, no classification or
  // breakdown — see backend/inference.py. This is the ONLY thing that
  // should hide the result.
  if (result.blocked) {
    return (
      <div className="result-card result-card--unclear">
        <div className="result-card__header">
          <span className="result-card__status-dot" aria-hidden="true" />
          <h3 className="result-card__prediction">{t("resultCard.unclearTitle")}</h3>
        </div>

        <p className="result-card__unclear-text">{result.type}</p>

        <p className="result-card__note">
          {t("resultCard.unclearNote").replace("{confidence}", result.confidence.toFixed(1))}
        </p>

        <p className="result-card__disclaimer">{t("resultCard.unclearDisclaimer")}</p>
      </div>
    );
  }

  const isFlagged = result.prediction === "Cancer";

  return (
    <div className={`result-card ${isFlagged ? "result-card--flag" : "result-card--ok"}`}>
      <div className="result-card__header">
        <span className="result-card__status-dot" aria-hidden="true" />
        <h3 className="result-card__prediction">
          {isFlagged ? t("resultCard.flaggedTitle") : t("resultCard.commonTitle")}
        </h3>
      </div>

      {isFlagged ? (
        <p className="result-card__lead">
          {t("resultCard.flaggedLeadBefore")}{" "}
          <Link to="/clinics" className="result-card__link">
            {t("resultCard.flaggedLeadLink")}
          </Link>{" "}
          {t("resultCard.flaggedLeadAfter")}
        </p>
      ) : (
        <p className="result-card__lead">{t("resultCard.commonLead")}</p>
      )}

      {result.is_uncertain && (
        <p className="result-card__note result-card__note--caution">
          {t("resultCard.uncertainNote")}
        </p>
      )}

      <div className="result-card__grid">
        <div className="result-card__field">
          <span className="result-card__label">{t("resultCard.predictedTypeLabel")}</span>
          <span className="result-card__value">{result.type}</span>
        </div>

        <div className="result-card__field result-card__field--wide">
          <span className="result-card__label">{t("resultCard.confidenceLabel")}</span>
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
          <span className="result-card__label">{t("resultCard.breakdownLabel")}</span>
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
          <span className="result-card__label">{t("resultCard.gradcamLabel")}</span>
          <img
            src={result.gradcam_image}
            alt={t("resultCard.gradcamAlt")}
            className="result-card__gradcam-img"
          />
        </div>
      )}

      <p className="result-card__disclaimer">{t("resultCard.disclaimer")}</p>
    </div>
  );
}

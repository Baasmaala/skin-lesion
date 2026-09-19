import { Fragment } from "react";
import "./AnalyzeStepper.css";

const STEPS = [
  { id: 1, label: "Upload" },
  { id: 2, label: "Analyzing" },
  { id: 3, label: "Result" },
];

/**
 * Horizontal 1-2-3 timeline for the upload -> analyze -> result flow.
 * currentStep is derived from the panel's status, not tracked separately,
 * so the stepper always reflects what is actually on screen.
 *
 * Click rules (see AnalyzePanel for the reasoning):
 *  - Step 1 is always clickable and starts a fresh upload.
 *  - Step 2 is only clickable once a file exists; clicking it while a
 *    result already exists just returns to step 1, since there is no
 *    "analyzing" screen to show once the image has been analyzed.
 *  - Step 3 is only clickable once a result exists.
 */
export default function AnalyzeStepper({ currentStep, canGoToStep2, canGoToStep3, onStepClick }) {
  const isEnabled = (id) => {
    if (id === 1) return true;
    if (id === 2) return canGoToStep2;
    return canGoToStep3;
  };

  return (
    <div className="stepper" role="tablist" aria-label="Analysis progress">
      {STEPS.map((step, i) => {
        const enabled = isEnabled(step.id);
        const isCurrent = currentStep === step.id;
        const isDone = currentStep > step.id;

        return (
          <Fragment key={step.id}>
            {i > 0 && (
              <div className={`stepper__connector ${currentStep > i ? "stepper__connector--done" : ""}`} />
            )}
            <button
              type="button"
              role="tab"
              aria-selected={isCurrent}
              className={`stepper__step ${isCurrent ? "stepper__step--current" : ""} ${
                isDone ? "stepper__step--done" : ""
              }`}
              disabled={!enabled}
              onClick={() => enabled && onStepClick(step.id)}
            >
              <span className="stepper__circle">{isDone ? "✓" : step.id}</span>
              <span className="stepper__label">{step.label}</span>
            </button>
          </Fragment>
        );
      })}
    </div>
  );
}

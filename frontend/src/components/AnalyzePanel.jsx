import { useEffect, useRef, useState } from "react";
import UploadArea from "./UploadArea.jsx";
import ResultCard from "./ResultCard.jsx";
import Button from "./Button.jsx";
import AnalyzeStepper from "./AnalyzeStepper.jsx";
import { predictImage } from "../api/predictApi.js";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./AnalyzePanel.css";

/**
 * The upload -> analyze -> result flow, shared by the Analyze page and the
 * Clinics page. Clinics has no real partner integrations yet, so it reuses
 * this same panel to show what a clinic visit would offer, rather than
 * leaving that page purely informational.
 *
 * The two pages now call two different trained models via `predictFn`: the
 * phone path uses predictClinicalImage (backend/inference_clinical.py,
 * trained on ordinary camera photos), and the clinic path uses predictImage
 * (backend/inference.py, trained on dermatoscope images) — see each page's
 * `tips` and `predictFn` props below.
 *
 * Presented as a single 1-2-3 timeline instead of two side-by-side boxes,
 * so only one thing is on screen at a time: upload, then analyzing, then
 * the result. See AnalyzeStepper for the step-click rules.
 */
export default function AnalyzePanel({
  showTips = true,
  tipsTitle,
  tips,
  predictFn = predictImage,
  allowCamera = true,
}) {
  const { t } = useLanguage();
  const resolvedTipsTitle = tipsTitle ?? t("analyzePanel.defaultTipsTitle");
  const resolvedTips = tips ?? t("analyzePanel.defaultTips");
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const objectUrlRef = useRef(null);

  // Revoke the previous object URL whenever it's replaced or the panel
  // unmounts, so we don't leak memory across repeated uploads.
  useEffect(() => {
    return () => {
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, []);

  const handleFileSelected = (selected) => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    const url = URL.createObjectURL(selected);
    objectUrlRef.current = url;

    setFile(selected);
    setPreviewUrl(url);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
  };

  const handleClear = () => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    objectUrlRef.current = null;
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setStatus("idle");
    setErrorMsg("");
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setStatus("loading");
    setErrorMsg("");
    try {
      const response = await predictFn(file);
      setResult(response);
      setStatus("done");
    } catch (err) {
      setErrorMsg(t("analyzePanel.errorMsg"));
      setStatus("error");
    }
  };

  // The stepper's current step is derived from status, never tracked on
  // its own, so the indicator always matches what is actually rendered.
  const currentStep = status === "loading" ? 2 : status === "done" ? 3 : 1;
  const canGoToStep2 = Boolean(file);
  const canGoToStep3 = status === "done";

  const handleStepClick = (stepId) => {
    if (stepId === 1) {
      handleClear();
      return;
    }
    if (stepId === 2) {
      // Analysis is a transient, automatic step. If a result already
      // exists there is nothing left to show at "analyzing", so this
      // just starts over. Otherwise, a file is waiting and clicking
      // "Analyzing" kicks it off.
      if (status === "done") {
        handleClear();
      } else if (file && status !== "loading") {
        handleAnalyze();
      }
      return;
    }
    // Step 3 is only ever clickable once a result exists, and that is
    // already the current view, so there is nothing further to do.
  };

  return (
    <div className="analyze-panel">
      <AnalyzeStepper
        currentStep={currentStep}
        canGoToStep2={canGoToStep2}
        canGoToStep3={canGoToStep3}
        onStepClick={handleStepClick}
      />

      <div className="analyze-panel__stage">
        {currentStep === 1 && (
          <>
            <UploadArea
              file={file}
              previewUrl={previewUrl}
              onFileSelected={handleFileSelected}
              onClear={handleClear}
              allowCamera={allowCamera}
            />

            {showTips && !file && (
              <div className="analyze-panel__tips">
                <h2>{resolvedTipsTitle}</h2>
                <ul>
                  {resolvedTips.map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}

            {file && (
              <Button
                variant="primary"
                size="md"
                className="analyze-panel__btn"
                onClick={handleAnalyze}
              >
                {t("analyzePanel.analyzeButton")}
              </Button>
            )}

            {status === "error" && <p className="analyze-panel__error">{errorMsg}</p>}
          </>
        )}

        {currentStep === 2 && (
          <div className="analyze-panel__placeholder">
            <span className="analyze-panel__spinner" aria-hidden="true" />
            <p>{t("analyzePanel.analyzingText")}</p>
          </div>
        )}

        {currentStep === 3 && result && <ResultCard result={result} />}
      </div>
    </div>
  );
}

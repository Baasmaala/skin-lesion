import { useEffect, useRef, useState } from "react";
import UploadArea from "../components/UploadArea.jsx";
import ResultCard from "../components/ResultCard.jsx";
import Button from "../components/Button.jsx";
import { predictImage } from "../api/predictApi.js";
import "./Analyze.css";

export default function Analyze() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const objectUrlRef = useRef(null);

  // Revoke the previous object URL whenever it's replaced or the page unmounts,
  // so we don't leak memory across repeated uploads.
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
      const response = await predictImage(file);
      setResult(response);
      setStatus("done");
    } catch (err) {
      setErrorMsg("Something went wrong while analyzing the image. Please try again.");
      setStatus("error");
    }
  };

  return (
    <section className="section analyze">
      <div className="container analyze__inner">
        <div className="analyze__header">
          <span className="eyebrow">AI Analysis</span>
          <h1 className="analyze__title">Analyze Your Skin Lesion</h1>
          <p className="analyze__subtitle">
            Upload a clear, well-lit photo of the lesion. For best results, keep the lesion
            centered and in focus.
          </p>
        </div>

        <div className="analyze__grid">
          <div className="analyze__panel">
            <UploadArea
              file={file}
              previewUrl={previewUrl}
              onFileSelected={handleFileSelected}
              onClear={handleClear}
            />

            <Button
              variant="primary"
              size="md"
              className="analyze__btn"
              disabled={!file || status === "loading"}
              onClick={handleAnalyze}
            >
              {status === "loading" ? "Analyzing…" : "Analyze Image"}
            </Button>

            {status === "error" && <p className="analyze__error">{errorMsg}</p>}
          </div>

          <div className="analyze__panel analyze__result-panel">
            {status === "idle" && !result && (
              <div className="analyze__placeholder">
                <span className="analyze__placeholder-icon" aria-hidden="true">
                  🔬
                </span>
                <p>Your result will appear here once the image is analyzed.</p>
              </div>
            )}

            {status === "loading" && (
              <div className="analyze__placeholder">
                <span className="analyze__spinner" aria-hidden="true" />
                <p>Analyzing image with the AI model…</p>
              </div>
            )}

            {status === "done" && result && <ResultCard result={result} />}
          </div>
        </div>
      </div>
    </section>
  );
}

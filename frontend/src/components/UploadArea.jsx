import { useCallback, useRef, useState } from "react";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./UploadArea.css";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

/**
 * Drag-and-drop + click-to-browse image upload area with preview.
 *
 * props:
 *   file: File | null           — currently selected file (controlled)
 *   previewUrl: string | null   — object URL for the preview image
 *   onFileSelected: (file) => void
 *   onClear: () => void
 *   allowCamera: bool — hide the "Take a photo" option when the source
 *     image must come from dedicated hardware (a clinic's dermatoscope)
 *     rather than the device's own camera. Defaults to true (the phone path).
 */
export default function UploadArea({ file, previewUrl, onFileSelected, onClear, allowCamera = true }) {
  const { t } = useLanguage();
  const inputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");

  const validateAndEmit = useCallback(
    (candidate) => {
      if (!candidate) return;
      if (!ACCEPTED_TYPES.includes(candidate.type)) {
        setError(t("uploadArea.invalidType"));
        return;
      }
      setError("");
      onFileSelected(candidate);
    },
    [onFileSelected, t]
  );

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    validateAndEmit(dropped);
  };

  const handleBrowse = (e) => {
    const chosen = e.target.files?.[0];
    validateAndEmit(chosen);
  };

  if (file && previewUrl) {
    return (
      <div className="upload upload--preview">
        <img src={previewUrl} alt={t("uploadArea.previewAlt")} className="upload__preview-img" />
        <div className="upload__preview-meta">
          <span className="upload__filename" title={file.name}>
            {file.name}
          </span>
          <button type="button" className="upload__clear" onClick={onClear}>
            {t("uploadArea.removeButton")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`upload ${dragActive ? "upload--active" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        onChange={handleBrowse}
        hidden
      />
      {allowCamera && (
        <input
          ref={cameraInputRef}
          type="file"
          accept={ACCEPTED_TYPES.join(",")}
          capture="environment"
          onChange={handleBrowse}
          hidden
        />
      )}

      <div className="upload__icon" aria-hidden="true">
        <svg width="46" height="46" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 16V4M12 4L7 9M12 4l5 5"
            stroke="var(--ink)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
            stroke="var(--teal)"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      <p className="upload__title">{t("uploadArea.dragTitle")}</p>
      <p className="upload__subtitle">{t("uploadArea.or")}</p>

      <div className="upload__actions">
        {allowCamera && (
          <button
            type="button"
            className="upload__browse-btn"
            onClick={(e) => {
              e.stopPropagation();
              cameraInputRef.current?.click();
            }}
          >
            {t("uploadArea.takePhoto")}
          </button>
        )}
        <button
          type="button"
          className={`upload__browse-btn ${allowCamera ? "upload__browse-btn--ghost" : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            inputRef.current?.click();
          }}
        >
          {t("uploadArea.browseFiles")}
        </button>
      </div>

      <p className="upload__hint">{t("uploadArea.hint")}</p>

      {error && <p className="upload__error">{error}</p>}
    </div>
  );
}

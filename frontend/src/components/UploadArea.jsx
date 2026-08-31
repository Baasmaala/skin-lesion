import { useCallback, useRef, useState } from "react";
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
 */
export default function UploadArea({ file, previewUrl, onFileSelected, onClear }) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");

  const validateAndEmit = useCallback(
    (candidate) => {
      if (!candidate) return;
      if (!ACCEPTED_TYPES.includes(candidate.type)) {
        setError("Please upload a JPG, PNG, or WEBP image.");
        return;
      }
      setError("");
      onFileSelected(candidate);
    },
    [onFileSelected]
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
        <img src={previewUrl} alt="Selected skin lesion" className="upload__preview-img" />
        <div className="upload__preview-meta">
          <span className="upload__filename" title={file.name}>
            {file.name}
          </span>
          <button type="button" className="upload__clear" onClick={onClear}>
            Remove & choose another image
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

      <div className="upload__icon" aria-hidden="true">
        <svg width="46" height="46" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 16V4M12 4L7 9M12 4l5 5"
            stroke="#1b4b91"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
            stroke="#14b8a6"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      <p className="upload__title">Drag & drop your image here</p>
      <p className="upload__subtitle">or</p>

      <button
        type="button"
        className="upload__browse-btn"
        onClick={(e) => {
          e.stopPropagation();
          inputRef.current?.click();
        }}
      >
        Browse Files
      </button>

      <p className="upload__hint">Supports JPG, PNG, WEBP</p>

      {error && <p className="upload__error">{error}</p>}
    </div>
  );
}

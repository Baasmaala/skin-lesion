import { useEffect, useRef, useState } from "react";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Learn.css";

const MALIGNANT_BY_CODE = {
  MEL: true,
  NV: false,
  BCC: true,
  AKIEC: true,
  BKL: false,
  DF: false,
  VASC: false,
};

const IMAGE_BY_CODE = {
  MEL: "/lesion-examples/MEL.jpg",
  NV: "/lesion-examples/NV.jpg",
  BCC: "/lesion-examples/BCC.jpg",
  AKIEC: "/lesion-examples/AKIEC.jpg",
  BKL: "/lesion-examples/BKL.jpg",
  DF: "/lesion-examples/DF.jpg",
  VASC: "/lesion-examples/VASC.jpg",
};

export default function Learn() {
  const { t } = useLanguage();
  const lesionTypes = t("learn.types").map((item) => ({
    ...item,
    malignant: MALIGNANT_BY_CODE[item.code],
    image: IMAGE_BY_CODE[item.code],
  }));

  const [index, setIndex] = useState(0);
  const total = lesionTypes.length;
  const current = lesionTypes[index];
  const touchStartX = useRef(null);

  const goNext = () => setIndex((i) => (i + 1) % total);
  const goPrev = () => setIndex((i) => (i - 1 + total) % total);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "ArrowRight") goNext();
      if (e.key === "ArrowLeft") goPrev();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e) => {
    if (touchStartX.current === null) return;
    const delta = e.changedTouches[0].clientX - touchStartX.current;
    if (delta > 50) goPrev();
    else if (delta < -50) goNext();
    touchStartX.current = null;
  };

  return (
    <section className="section learn">
      <div className="container">
        <div className="learn__header">
          <h1 className="learn__title">{t("learn.title")}</h1>
          <p className="learn__subtitle">{t("learn.subtitle")}</p>
        </div>

        <div className="learn__carousel">
          <button
            type="button"
            className="learn__arrow"
            onClick={goPrev}
            aria-label={t("learn.prevAria")}
          >
            ‹
          </button>

          <div
            className="learn__card"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
          >
            <div className="learn__card-head">
              <span
                className={`learn__badge ${
                  current.malignant ? "learn__badge--flag" : "learn__badge--ok"
                }`}
              >
                {current.malignant ? t("learn.malignantBadge") : t("learn.benignBadge")}
              </span>
              <h2>{current.name}</h2>
              <p>{current.text}</p>
            </div>
            <img
              className="learn__card-visual"
              src={current.image}
              alt={t("learn.imageAlt").replace("{name}", current.name)}
            />
          </div>

          <button
            type="button"
            className="learn__arrow"
            onClick={goNext}
            aria-label={t("learn.nextAria")}
          >
            ›
          </button>
        </div>

        <div className="learn__dots" role="tablist" aria-label={t("learn.dotsAria")}>
          {lesionTypes.map((item, i) => (
            <button
              key={item.code}
              type="button"
              role="tab"
              aria-selected={i === index}
              aria-label={item.name}
              className={`learn__dot ${i === index ? "learn__dot--active" : ""}`}
              onClick={() => setIndex(i)}
            />
          ))}
        </div>

        <p className="learn__credit">
          {t("learn.creditBefore")}{" "}
          <a href="https://www.isic-archive.com/" target="_blank" rel="noreferrer">
            {t("learn.creditLinkText")}
          </a>
          {t("learn.creditAfter")}
        </p>
      </div>
    </section>
  );
}

import { useEffect, useRef, useState } from "react";
import "./Learn.css";

const LESION_TYPES = [
  {
    code: "MEL",
    name: "Melanoma",
    malignant: true,
    text: "The most serious form of skin cancer. It develops in the pigment producing cells and can spread to other parts of the body if not caught early. Often shows up as a new mole, or an existing one that changes in size, shape, or color. Early detection makes a real difference in outcomes.",
    image: "/lesion-examples/MEL.jpg",
  },
  {
    code: "NV",
    name: "Melanocytic Nevus",
    malignant: false,
    text: "Commonly known as a mole. Almost everyone has several, and the vast majority stay harmless for life. Still worth keeping an eye on if one changes noticeably over time.",
    image: "/lesion-examples/NV.jpg",
  },
  {
    code: "BCC",
    name: "Basal Cell Carcinoma",
    malignant: true,
    text: "The most common form of skin cancer. It grows slowly and rarely spreads beyond the skin, but can damage surrounding tissue if left untreated. Often looks like a pearly or waxy bump, or a flat patch that will not heal.",
    image: "/lesion-examples/BCC.jpg",
  },
  {
    code: "AKIEC",
    name: "Actinic Keratosis / Intraepithelial Carcinoma",
    malignant: true,
    text: "A rough, scaly patch caused by years of sun exposure, sometimes described as precancerous. A small number of cases progress into a more serious skin cancer if left untreated, so these are usually monitored or removed.",
    image: "/lesion-examples/AKIEC.jpg",
  },
  {
    code: "BKL",
    name: "Benign Keratosis",
    malignant: false,
    text: "A group of harmless growths that become more common with age. They often look waxy, scaly, or stuck on the skin, and do not need treatment unless they become irritated.",
    image: "/lesion-examples/BKL.jpg",
  },
  {
    code: "DF",
    name: "Dermatofibroma",
    malignant: false,
    text: "A small, firm, harmless nodule, often found on the legs. It is sometimes linked to a minor injury such as an insect bite, and does not require treatment.",
    image: "/lesion-examples/DF.jpg",
  },
  {
    code: "VASC",
    name: "Vascular Lesion",
    malignant: false,
    text: "A group of harmless lesions made up of blood vessels, appearing as red or purple marks on the skin. Most are present from birth or develop naturally and are not a health concern.",
    image: "/lesion-examples/VASC.jpg",
  },
];

export default function Learn() {
  const [index, setIndex] = useState(0);
  const total = LESION_TYPES.length;
  const current = LESION_TYPES[index];
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
          <h1 className="learn__title">The seven types we screen for</h1>
          <p className="learn__subtitle">
            Rareflect classifies a lesion into one of seven categories,
            three of them cancerous or precancerous and four of them
            benign. This is general information, not medical advice. A
            dermatologist should always confirm any diagnosis.
          </p>
        </div>

        <div className="learn__carousel">
          <button
            type="button"
            className="learn__arrow"
            onClick={goPrev}
            aria-label="Previous lesion type"
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
                {current.malignant ? "Cancerous or precancerous" : "Usually benign"}
              </span>
              <h2>{current.name}</h2>
              <p>{current.text}</p>
            </div>
            <img
              className="learn__card-visual"
              src={current.image}
              alt={`Dermoscopic example of ${current.name}`}
            />
          </div>

          <button
            type="button"
            className="learn__arrow"
            onClick={goNext}
            aria-label="Next lesion type"
          >
            ›
          </button>
        </div>

        <div className="learn__dots" role="tablist" aria-label="Lesion type">
          {LESION_TYPES.map((item, i) => (
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
          Example images from the{" "}
          <a href="https://www.isic-archive.com/" target="_blank" rel="noreferrer">
            ISIC Archive
          </a>
          , released under CC0.
        </p>
      </div>
    </section>
  );
}

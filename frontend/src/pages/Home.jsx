import { Link } from "react-router-dom";
import Button from "../components/Button.jsx";
import "./Home.css";

const STEPS = [
  {
    number: "01",
    title: "Upload an image",
    text: "Upload a clear photo of a skin lesion — from a dermoscopic device or a regular camera.",
  },
  {
    number: "02",
    title: "AI model analyzes it",
    text: "A fine-tuned deep learning model (ResNet50) processes the image and evaluates lesion patterns.",
  },
  {
    number: "03",
    title: "Get your result",
    text: "See the prediction, the likely category, and a confidence score in a clear, easy-to-read report.",
  },
];

const BENEFITS = [
  {
    title: "Fast, preliminary insight",
    text: "Get an AI-generated read on a skin lesion in seconds, to help you decide on next steps.",
  },
  {
    title: "Built on real research",
    text: "Trained on the ISIC 2018 dermoscopy dataset, with class-imbalance-aware evaluation.",
  },
  {
    title: "Explainable by design",
    text: "Designed to support clear, transparent AI-assisted screening — not a black box.",
  },
];

export default function Home() {
  return (
    <>
      {/* ---------------- Hero ---------------- */}
      <section className="hero">
        <div className="container hero__inner">
          <div className="hero__copy">
            <span className="eyebrow">AI-Powered Dermatology</span>
            <h1 className="hero__title">
              AI-Powered Skin Lesion Analysis, <span>In Seconds</span>
            </h1>
            <p className="hero__subtitle">
              DermaScope uses artificial intelligence to analyze photos of skin lesions and
              provide a preliminary assessment — helping you understand what you're looking
              at, faster.
            </p>
            <div className="hero__actions">
              <Button as={Link} to="/analyze" variant="primary" size="md">
                Analyze Your Skin
              </Button>
              <Button as={Link} to="/analyze" variant="outline" size="md">
                Upload Image
              </Button>
            </div>
            <p className="hero__note">
              🔒 Images are processed for analysis only and are not stored or shared.
            </p>
          </div>

          <div className="hero__visual" aria-hidden="true">
            <div className="hero__visual-card">
              <div className="hero__visual-scan" />
              <svg viewBox="0 0 200 200" width="100%" height="100%">
                <circle cx="100" cy="100" r="92" fill="#eaf2fb" />
                <circle cx="100" cy="100" r="60" fill="#ffffff" stroke="#1b4b91" strokeWidth="2" />
                <circle cx="100" cy="100" r="34" fill="#1b4b91" opacity="0.85" />
                <circle cx="100" cy="100" r="12" fill="#14b8a6" />
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="section section-alt">
        <div className="container">
          <span className="eyebrow">How It Works</span>
          <h2 className="section-heading">Three simple steps</h2>
          <p className="section-subtext">
            From photo to result, DermaScope keeps the process quick and transparent.
          </p>

          <div className="steps">
            {STEPS.map((step) => (
              <div className="steps__item" key={step.number}>
                <span className="steps__number">{step.number}</span>
                <h3 className="steps__title">{step.title}</h3>
                <p className="steps__text">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- Benefits ---------------- */}
      <section className="section">
        <div className="container">
          <span className="eyebrow">Why DermaScope</span>
          <h2 className="section-heading">Purpose &amp; benefits</h2>
          <p className="section-subtext">
            Built as an AI research project to explore how deep learning can support early
            skin lesion screening.
          </p>

          <div className="benefits">
            {BENEFITS.map((b) => (
              <div className="benefits__item" key={b.title}>
                <div className="benefits__icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 12.5l4.5 4.5L19 7"
                      stroke="#14b8a6"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <h3 className="benefits__title">{b.title}</h3>
                <p className="benefits__text">{b.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- Disclaimer ---------------- */}
      <section className="section section-alt">
        <div className="container">
          <div className="disclaimer-box">
            <span className="disclaimer-box__icon" aria-hidden="true">
              ⚠️
            </span>
            <p>
              <strong>Medical disclaimer:</strong> DermaScope is a research and educational
              prototype. Its AI-generated results are intended to support analysis and
              awareness — they are <strong>not</strong> a medical diagnosis and should never
              replace consultation with a qualified dermatologist.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------- Closing CTA ---------------- */}
      <section className="section cta">
        <div className="container cta__inner">
          <h2 className="cta__title">Ready to try it?</h2>
          <p className="cta__text">Upload a skin lesion image and get an instant AI-assisted read.</p>
          <Button as={Link} to="/analyze" variant="secondary" size="md">
            Start Analysis
          </Button>
        </div>
      </section>
    </>
  );
}

import { Link } from "react-router-dom";
import Button from "../components/Button.jsx";
import "./Home.css";

const STEPS = [
  {
    number: "01",
    title: "Take or upload a photo",
    text: "Take a clear photo of a lesion yourself, or have one captured at a partner clinic.",
  },
  {
    number: "02",
    title: "The model analyzes it",
    text: "A model trained on dermatologist graded images evaluates the lesion's features.",
  },
  {
    number: "03",
    title: "Get a clear result",
    text: "See whether it looks common, uncertain, or flagged as rare, plus a clear next step.",
  },
];

const BENEFITS = [
  {
    title: "Fast, private screening",
    text: "Get a read on a lesion in under a minute, with no appointment needed to start.",
  },
  {
    title: "Built on real research",
    text: "Trained on dermatologist graded dermoscopy images, evaluated with attention to rare classes.",
  },
  {
    title: "A clear next step, always",
    text: "Every result names what to do next, whether that is nothing, a follow up, or a dermatologist visit.",
  },
];

export default function Home() {
  return (
    <>
      {/* ---------------- Hero ---------------- */}
      <section className="hero">
        <div className="container">
          <h1 className="hero__title">Check a lesion your way.</h1>
          <p className="hero__subtitle">
            Rareflect screens skin lesions with a model trained on images
            graded by dermatologists. Start from your phone in seconds, or
            visit a partner clinic for a more detailed scan and a direct path
            to a dermatologist if something needs a closer look.
          </p>
        </div>
      </section>

      {/* ---------------- Two paths ---------------- */}
      <section className="paths-section">
        <div className="container">
          <div className="paths">
            <div className="path-card path-card--primary">
              <svg className="path-card__icon" viewBox="0 0 40 40" fill="none" stroke="var(--teal-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="11" y="4" width="18" height="32" rx="3" />
                <circle cx="20" cy="30" r="1.6" fill="var(--teal-text)" stroke="none" />
                <path d="M15 9h10" strokeWidth="1.6" />
              </svg>
              <h3>Use your phone</h3>
              <p>
                Take a photo at home and get a screening result in under a
                minute. It is private, free to start, and needs no
                appointment.
              </p>
              <Button as={Link} to="/analyze" variant="primary" size="md" className="path-card__cta">
                Analyze a photo
              </Button>
            </div>

            <div className="path-card">
              <svg className="path-card__icon" viewBox="0 0 40 40" fill="none" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="14" width="28" height="21" rx="2" />
                <path d="M14 35v-9h12v9" />
                <path d="M20 14v-6M17 11h6" strokeWidth="2" />
                <path d="M6 22h28" strokeWidth="1.4" opacity="0.5" />
              </svg>
              <h3>Visit a clinic</h3>
              <p>
                Partner clinics capture a dermatoscope scan, read by a model
                trained specifically on that kind of image, then connect you
                straight to a dermatologist if a result is flagged.
              </p>
              <Button as={Link} to="/clinics" variant="outline" size="md" className="path-card__cta">
                Find a clinic
              </Button>
            </div>
          </div>

          <p className="paths__fine-print">
            Rareflect is a screening aid, not a diagnosis. Results flagged as
            rare should always be reviewed by a dermatologist. The clinic
            path connects you to one directly.
          </p>
        </div>
      </section>

      {/* ---------------- Fun fact ---------------- */}
      <section className="section-alt fun-fact-section">
        <div className="container">
          <div className="fun-fact">
            <svg viewBox="0 0 28 28" fill="none" stroke="var(--teal-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="14" cy="14" r="11" />
              <path d="M14 9v6" />
              <circle cx="14" cy="19" r="0.6" fill="var(--teal-text)" stroke="none" />
            </svg>
            <div>
              <h4>Why early checks matter</h4>
              <p>
                Melanoma is far less common than other skin cancers, but it
                causes most skin cancer deaths. Caught early, about 99% of
                cases are treated successfully. Catching it early is exactly
                what a quick phone photo can help with.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="section">
        <div className="container">
          <h2 className="section-heading">Three simple steps</h2>
          <p className="section-subtext">
            From photo to result, Rareflect keeps the process quick and
            transparent.
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
      <section className="section section-alt">
        <div className="container">
          <h2 className="section-heading">Purpose and benefits</h2>
          <p className="section-subtext">
            Built as an AI research project to explore how deep learning can
            support early skin lesion screening.
          </p>

          <div className="benefits">
            {BENEFITS.map((b) => (
              <div className="benefits__item" key={b.title}>
                <div className="benefits__icon" aria-hidden="true">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 12.5l4.5 4.5L19 7"
                      stroke="var(--teal-text)"
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
      <section className="section">
        <div className="container">
          <div className="disclaimer-box">
            <p>
              <strong>Medical disclaimer.</strong> Rareflect is a research
              and educational prototype. Its results are a screening aid, not
              a medical diagnosis, and should never replace evaluation by a
              qualified dermatologist.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------- Closing CTA ---------------- */}
      <section className="section cta">
        <div className="container cta__inner">
          <h2 className="cta__title">Ready to try it?</h2>
          <p className="cta__text">
            Upload a skin lesion photo and get a screening result right away.
          </p>
          <Button as={Link} to="/analyze" variant="primary" size="md">
            Analyze a photo
          </Button>
        </div>
      </section>
    </>
  );
}

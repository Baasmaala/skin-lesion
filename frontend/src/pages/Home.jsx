import { Link } from "react-router-dom";
import Button from "../components/Button.jsx";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Home.css";

export default function Home() {
  const { t } = useLanguage();
  const steps = t("home.steps.items");
  const benefits = t("home.benefits.items");

  return (
    <>
      {/* ---------------- Hero ---------------- */}
      <section className="hero">
        <div className="container">
          <h1 className="hero__title">{t("home.hero.title")}</h1>
          <p className="hero__subtitle">{t("home.hero.subtitle")}</p>
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
              <h3>{t("home.phonePath.title")}</h3>
              <p>{t("home.phonePath.text")}</p>
              <Button as={Link} to="/analyze" variant="primary" size="md" className="path-card__cta">
                {t("home.phonePath.cta")}
              </Button>
            </div>

            <div className="path-card">
              <svg className="path-card__icon" viewBox="0 0 40 40" fill="none" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="14" width="28" height="21" rx="2" />
                <path d="M14 35v-9h12v9" />
                <path d="M20 14v-6M17 11h6" strokeWidth="2" />
                <path d="M6 22h28" strokeWidth="1.4" opacity="0.5" />
              </svg>
              <h3>{t("home.clinicPath.title")}</h3>
              <p>{t("home.clinicPath.text")}</p>
              <Button as={Link} to="/clinics" variant="outline" size="md" className="path-card__cta">
                {t("home.clinicPath.cta")}
              </Button>
            </div>
          </div>

          <p className="paths__fine-print">{t("home.finePrint")}</p>
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
              <h4>{t("home.funFact.title")}</h4>
              <p>{t("home.funFact.text")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="section">
        <div className="container">
          <h2 className="section-heading">{t("home.steps.heading")}</h2>
          <p className="section-subtext">{t("home.steps.subtext")}</p>

          <div className="steps">
            {steps.map((step) => (
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
          <h2 className="section-heading">{t("home.benefits.heading")}</h2>
          <p className="section-subtext">{t("home.benefits.subtext")}</p>

          <div className="benefits">
            {benefits.map((b) => (
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
              <strong>{t("home.disclaimer.label")}</strong> {t("home.disclaimer.text")}
            </p>
          </div>
        </div>
      </section>

      {/* ---------------- Closing CTA ---------------- */}
      <section className="section cta">
        <div className="container cta__inner">
          <h2 className="cta__title">{t("home.cta.title")}</h2>
          <p className="cta__text">{t("home.cta.text")}</p>
          <Button as={Link} to="/analyze" variant="primary" size="md">
            {t("home.cta.button")}
          </Button>
        </div>
      </section>
    </>
  );
}

import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Navbar.css";

const THEME_KEY = "rareflect-theme";

function getInitialTheme() {
  try {
    return localStorage.getItem(THEME_KEY) || "system";
  } catch {
    return "system";
  }
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState(getInitialTheme);
  const { lang, setLang, t } = useLanguage();

  useEffect(() => {
    if (theme === "system") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // localStorage unavailable, theme just won't persist across visits
    }
  }, [theme]);

  const themeLabels = {
    light: t("nav.themeLight"),
    dark: t("nav.themeDark"),
    system: t("nav.themeSystem"),
  };

  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <NavLink to="/" className="navbar__brand" onClick={() => setOpen(false)}>
          <span className="navbar__logo" aria-hidden="true">
            <span className="navbar__logo-r navbar__logo-r--ghost">R</span>
            <span className="navbar__logo-r">R</span>
            <span className="navbar__logo-dot" />
          </span>
          <span className="navbar__name">
            Rarefle<span className="navbar__name-mirror">c</span>t
          </span>
        </NavLink>

        <button
          className="navbar__toggle"
          aria-label={t("nav.toggleMenu")}
          onClick={() => setOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>

        <nav className={`navbar__links ${open ? "navbar__links--open" : ""}`}>
          <NavLink to="/" end className="navbar__link" onClick={() => setOpen(false)}>
            {t("nav.home")}
          </NavLink>
          <NavLink to="/analyze" className="navbar__link" onClick={() => setOpen(false)}>
            {t("nav.analyze")}
          </NavLink>
          <NavLink to="/clinics" className="navbar__link" onClick={() => setOpen(false)}>
            {t("nav.clinics")}
          </NavLink>
          <NavLink to="/learn" className="navbar__link" onClick={() => setOpen(false)}>
            {t("nav.learn")}
          </NavLink>

          <div className="navbar__theme" role="group" aria-label={t("nav.themeGroup")}>
            {["light", "dark", "system"].map((mode) => (
              <button
                key={mode}
                type="button"
                className={`navbar__theme-btn ${theme === mode ? "navbar__theme-btn--active" : ""}`}
                onClick={() => setTheme(mode)}
              >
                {themeLabels[mode]}
              </button>
            ))}
          </div>

          <div className="navbar__theme" role="group" aria-label={t("nav.languageGroup")}>
            {["en", "ar"].map((code) => (
              <button
                key={code}
                type="button"
                className={`navbar__theme-btn ${lang === code ? "navbar__theme-btn--active" : ""}`}
                onClick={() => setLang(code)}
              >
                {code === "en" ? "EN" : "عربي"}
              </button>
            ))}
          </div>

          <NavLink to="/analyze" className="navbar__cta" onClick={() => setOpen(false)}>
            {t("nav.cta")}
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

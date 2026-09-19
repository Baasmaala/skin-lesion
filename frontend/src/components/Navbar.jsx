import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
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
          aria-label="Toggle navigation menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>

        <nav className={`navbar__links ${open ? "navbar__links--open" : ""}`}>
          <NavLink to="/" end className="navbar__link" onClick={() => setOpen(false)}>
            Home
          </NavLink>
          <NavLink to="/analyze" className="navbar__link" onClick={() => setOpen(false)}>
            Analyze
          </NavLink>
          <NavLink to="/clinics" className="navbar__link" onClick={() => setOpen(false)}>
            Clinics
          </NavLink>
          <NavLink to="/learn" className="navbar__link" onClick={() => setOpen(false)}>
            Learn
          </NavLink>

          <div className="navbar__theme" role="group" aria-label="Theme">
            {["light", "dark", "system"].map((mode) => (
              <button
                key={mode}
                type="button"
                className={`navbar__theme-btn ${theme === mode ? "navbar__theme-btn--active" : ""}`}
                onClick={() => setTheme(mode)}
              >
                {mode}
              </button>
            ))}
          </div>

          <NavLink to="/analyze" className="navbar__cta" onClick={() => setOpen(false)}>
            Analyze a photo
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

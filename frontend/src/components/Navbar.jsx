import { useState } from "react";
import { NavLink } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <NavLink to="/" className="navbar__brand" onClick={() => setOpen(false)}>
          <span className="navbar__logo" aria-hidden="true">
            <svg viewBox="0 0 32 32" width="30" height="30">
              <circle cx="16" cy="16" r="16" fill="#1b4b91" />
              <path
                d="M16 7c-4.5 3-7 6.7-7 10.4C9 21.6 12.2 25 16 25s7-3.4 7-7.6C23 13.7 20.5 10 16 7z"
                fill="#fff"
                opacity="0.95"
              />
              <circle cx="16" cy="18" r="2.4" fill="#14b8a6" />
            </svg>
          </span>
          <span className="navbar__name">DermaScope</span>
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
          <NavLink to="/analyze" className="navbar__cta" onClick={() => setOpen(false)}>
            Start Analysis
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

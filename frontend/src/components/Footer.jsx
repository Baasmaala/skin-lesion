import { Link } from "react-router-dom";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <span className="footer__name-wrap">
            <span className="footer__name">
              Rarefle<span className="footer__name-mirror">c</span>t
            </span>
            <span className="footer__name footer__name--reflection" aria-hidden="true">
              Rarefle<span className="footer__name-mirror">c</span>t
            </span>
          </span>
          <p className="footer__tagline">
            AI assisted skin lesion screening, built as an academic deep
            learning research project.
          </p>
        </div>

        <nav className="footer__links">
          <Link to="/">Home</Link>
          <Link to="/analyze">Analyze a photo</Link>
          <Link to="/clinics">Clinics</Link>
          <Link to="/learn">Learn</Link>
        </nav>

        <p className="footer__disclaimer">
          Rareflect is a research and educational tool. Its predictions are
          intended to support, not replace, evaluation by a qualified medical
          professional. Always consult a dermatologist for diagnosis and
          treatment decisions.
        </p>
      </div>
    </footer>
  );
}

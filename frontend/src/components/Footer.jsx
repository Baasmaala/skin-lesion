import { Link } from "react-router-dom";
import "./Footer.css";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <span className="footer__name">DermaScope</span>
          <p className="footer__tagline">
            AI-assisted skin lesion analysis — a research prototype built as part of an
            academic AI/Deep Learning graduation project.
          </p>
        </div>

        <nav className="footer__links">
          <Link to="/">Home</Link>
          <Link to="/analyze">Analyze Image</Link>
        </nav>

        <p className="footer__disclaimer">
          DermaScope is a research and educational tool. Its predictions are intended to
          support — not replace — evaluation by a qualified medical professional. Always
          consult a dermatologist for diagnosis and treatment decisions.
        </p>

        <p className="footer__copy">© {new Date().getFullYear()} DermaScope. Academic project.</p>
      </div>
    </footer>
  );
}

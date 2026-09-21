import { Link } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Footer.css";

export default function Footer() {
  const { t } = useLanguage();

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
          <p className="footer__tagline">{t("footer.tagline")}</p>
        </div>

        <nav className="footer__links">
          <Link to="/">{t("nav.home")}</Link>
          <Link to="/analyze">{t("nav.cta")}</Link>
          <Link to="/clinics">{t("nav.clinics")}</Link>
          <Link to="/learn">{t("nav.learn")}</Link>
        </nav>

        <p className="footer__disclaimer">{t("footer.disclaimer")}</p>
      </div>
    </footer>
  );
}

import AnalyzePanel from "../components/AnalyzePanel.jsx";
import { predictClinicalImage } from "../api/predictApi.js";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Analyze.css";

export default function Analyze() {
  const { t } = useLanguage();

  return (
    <section className="section analyze">
      <div className="container analyze__inner">
        <div className="analyze__header">
          <h1 className="analyze__title">{t("analyze.title")}</h1>
          <p className="analyze__subtitle">{t("analyze.subtitle")}</p>
        </div>

        <AnalyzePanel
          tipsTitle={t("analyze.tipsTitle")}
          tips={t("analyze.tips")}
          predictFn={predictClinicalImage}
        />
      </div>
    </section>
  );
}

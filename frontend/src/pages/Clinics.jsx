import AnalyzePanel from "../components/AnalyzePanel.jsx";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Clinics.css";

export default function Clinics() {
  const { t } = useLanguage();

  return (
    <section className="section clinics">
      <div className="container">
        <div className="clinics__header">
          <h1 className="clinics__title">{t("clinics.title")}</h1>
          <p className="clinics__subtitle">{t("clinics.subtitle")}</p>

          <div className="clinics__notice">
            <h2>{t("clinics.noticeTitle")}</h2>
            <p>{t("clinics.noticeText")}</p>
          </div>
        </div>

        <AnalyzePanel
          tipsTitle={t("clinics.tipsTitle")}
          tips={t("clinics.tips")}
          allowCamera={false}
        />
      </div>
    </section>
  );
}

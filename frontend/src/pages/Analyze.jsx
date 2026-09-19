import AnalyzePanel from "../components/AnalyzePanel.jsx";
import { predictClinicalImage } from "../api/predictApi.js";
import "./Analyze.css";

const PHONE_TIPS = [
  "Use bright, natural light and avoid harsh shadows or glare.",
  "Hold the phone steady and roughly level with the skin, not at a sharp angle.",
  "Get close enough that the lesion fills a good part of the frame, but keep it in focus.",
  "Avoid using flash directly on the skin. It can wash out color and texture.",
];

export default function Analyze() {
  return (
    <section className="section analyze">
      <div className="container analyze__inner">
        <div className="analyze__header">
          <h1 className="analyze__title">Analyze a skin lesion</h1>
          <p className="analyze__subtitle">
            Upload a clear, well lit photo of the lesion. For best results,
            keep the lesion centered and in focus.
          </p>
        </div>

        <AnalyzePanel
          tipsTitle="How to get the best phone photo"
          tips={PHONE_TIPS}
          predictFn={predictClinicalImage}
        />
      </div>
    </section>
  );
}

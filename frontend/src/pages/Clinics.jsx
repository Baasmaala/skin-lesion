import AnalyzePanel from "../components/AnalyzePanel.jsx";
import "./Clinics.css";

const CLINIC_TIPS = [
  "This preview is trained on dermatoscope images: close, magnified, and evenly lit.",
  "Upload an image captured with a dermatoscope, not a regular phone photo.",
  "The lesion should already fill almost the entire frame, centered and in sharp focus.",
  "Even, diffuse lighting with no shadows, hair, or reflections gives the most accurate read.",
];

export default function Clinics() {
  return (
    <section className="section clinics">
      <div className="container">
        <div className="clinics__header">
          <h1 className="clinics__title">Visit a partner clinic</h1>
          <p className="clinics__subtitle">
            Partner clinics will capture a dermatoscope scan and connect you
            straight to a dermatologist if a result is flagged.
          </p>

          <div className="clinics__notice">
            <h2>Partner clinic listings are coming soon</h2>
            <p>
              We are onboarding the first partner clinics now. In the
              meantime, this page previews the dermatoscope trained side of
              Rareflect: the more detailed scan a clinic visit would offer,
              as opposed to the phone model built for ordinary camera photos.
            </p>
          </div>
        </div>

        <AnalyzePanel
          tipsTitle="How to get the closest clinic preview"
          tips={CLINIC_TIPS}
          allowCamera={false}
        />
      </div>
    </section>
  );
}

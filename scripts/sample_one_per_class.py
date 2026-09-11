"""
Sample ONE real test-set image per class, for manual testing of the live
demo against known ground-truth labels.

Uses the 'test' split specifically — images the model never saw during
training, so this is a clean, honest test (not cherry-picked from data
the model already memorized).

Run (from the project root, on the GPU server):
    python scripts/sample_one_per_class.py

Produces:
    results/test_samples/<CLASS>_<original_filename>.jpg   (7 images)
    results/test_samples/labels.txt                          (a plain
                                                               text summary)
"""

import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset import CLASS_NAMES  # noqa: E402

SPLITS_CSV = PROJECT_ROOT / "data" / "processed" / "splits.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "raw" / "ISIC2018_Task3_Training_Input"
OUTPUT_DIR = PROJECT_ROOT / "results" / "test_samples"

# Full display names, matching backend/inference.py, so the printout is
# immediately readable (not just the 4-5 letter ISIC codes).
FULL_NAMES = {
    "MEL": "Melanoma",
    "NV": "Melanocytic Nevus",
    "BCC": "Basal Cell Carcinoma",
    "AKIEC": "Actinic Keratosis / Intraepithelial Carcinoma",
    "BKL": "Benign Keratosis",
    "DF": "Dermatofibroma",
    "VASC": "Vascular Lesion",
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(SPLITS_CSV)
    test_df = df[df["split"] == "test"].reset_index(drop=True)

    summary_lines = []
    print(f"{'Class':<8}{'Full name':<48}{'Image file'}")
    print("-" * 90)

    for cls in CLASS_NAMES:
        rows = test_df[test_df["label"] == cls]
        if rows.empty:
            print(f"{cls:<8}(no test images found for this class)")
            continue

        # First test image for this class — deterministic, no randomness,
        # so this list stays the same every time the script is re-run.
        image_id = rows.iloc[0]["image"]
        src_path = IMAGES_DIR / f"{image_id}.jpg"
        dst_name = f"{cls}_{image_id}.jpg"
        dst_path = OUTPUT_DIR / dst_name

        if not src_path.exists():
            print(f"{cls:<8}WARNING: source image not found at {src_path}")
            continue

        shutil.copy(src_path, dst_path)

        line = f"{cls:<8}{FULL_NAMES[cls]:<48}{dst_name}"
        print(line)
        summary_lines.append(
            f"{dst_name}  ->  true class: {cls} ({FULL_NAMES[cls]})"
        )

    (OUTPUT_DIR / "labels.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nSaved {len(summary_lines)} images + labels.txt to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

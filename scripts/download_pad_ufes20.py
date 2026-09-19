"""
Download the PAD-UFES-20 clinical (non-dermoscopic) skin lesion dataset via
the ISIC Archive API (collection 406 — PAD-UFES-20 is mirrored there under
ISIC's own metadata schema, no Mendeley login/scraping needed).

This is a SEPARATE dataset from the ISIC 2018 dermoscopic images used by the
existing baseline_unfrozen model — it powers a second, independent "clinical
photo" model. Nothing here touches data/raw/ISIC2018_Task3_Training_Input/.

Produces:
    data/raw/pad_ufes_20/images/<isic_id>.jpg   (~2,298 clinical photos)
    data/raw/pad_ufes_20/metadata.csv           (isic_id, label, rollup)

Usage (run from the project root):
    python scripts/download_pad_ufes20.py
"""

import csv
import json
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "data" / "raw" / "pad_ufes_20"
IMAGES_DIR = OUT_DIR / "images"
METADATA_CSV = OUT_DIR / "metadata.csv"

COLLECTION_ID = 406  # PAD-UFES-20 on the ISIC Archive
API_URL = f"https://api.isic-archive.com/api/v2/images/search/?collections={COLLECTION_ID}&limit=200"

# Full diagnosis name (diagnosis_3, as returned by the API) -> short class code.
# Matches the original PAD-UFES-20 paper's 6 diagnostic categories.
LABEL_MAP = {
    "Basal cell carcinoma": "BCC",
    "Solar or actinic keratosis": "ACK",
    "Nevus": "NEV",
    "Seborrheic keratosis": "SEK",
    "Squamous cell carcinoma, NOS": "SCC",
    "Melanoma, NOS": "MEL",
}

MALIGNANT_CODES = {"BCC", "SCC", "MEL"}  # ACK is pre-malignant, kept separate; NEV/SEK are benign


def fetch_all_metadata():
    """Page through the ISIC API, keeping only images with a recognized label."""
    records = []
    skipped = 0
    url = API_URL
    page = 0
    while url:
        page += 1
        with urllib.request.urlopen(url) as resp:
            data = json.load(resp)
        for r in data["results"]:
            clinical = r["metadata"].get("clinical", {})
            diagnosis = clinical.get("diagnosis_3") or clinical.get("diagnosis_2")
            code = LABEL_MAP.get(diagnosis)
            if code is None:
                skipped += 1
                continue
            records.append(
                {
                    "isic_id": r["isic_id"],
                    "url": r["files"]["full"]["url"],
                    "label": code,
                    "malignant": code in MALIGNANT_CODES,
                }
            )
        url = data.get("next")
        print(f"  page {page}: {len(records)} labeled so far ({skipped} skipped/unlabeled)")
    return records


def download_images(records):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for i, rec in enumerate(records, 1):
        dest = IMAGES_DIR / f"{rec['isic_id']}.jpg"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        for attempt in range(3):
            try:
                urllib.request.urlretrieve(rec["url"], dest)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"  FAILED {rec['isic_id']}: {e}")
                time.sleep(1)
        if i % 200 == 0:
            print(f"  downloaded {i}/{len(records)}")


def write_metadata_csv(records):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(METADATA_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["isic_id", "label", "malignant"])
        writer.writeheader()
        for rec in records:
            writer.writerow({"isic_id": rec["isic_id"], "label": rec["label"], "malignant": rec["malignant"]})
    print(f"Saved metadata for {len(records)} images to {METADATA_CSV}")


def main():
    print("Fetching metadata from ISIC Archive API...")
    records = fetch_all_metadata()
    print(f"\nTotal labeled images: {len(records)}")

    from collections import Counter

    counts = Counter(r["label"] for r in records)
    for code, n in counts.most_common():
        print(f"  {code}: {n}")

    print("\nDownloading images (skips files that already exist)...")
    download_images(records)

    write_metadata_csv(records)
    print("Done.")


if __name__ == "__main__":
    main()

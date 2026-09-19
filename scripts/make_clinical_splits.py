"""
Stratified 70/15/15 train/val/test split for the PAD-UFES-20 clinical
dataset — mirrors notebooks/02_split.ipynb (same seed, same ratios) so the
two models' evaluation methodology stays comparable, applied to
data/raw/pad_ufes_20/metadata.csv instead of the ISIC 2018 labels.

Requires: scripts/download_pad_ufes20.py has been run first.

Usage (run from the project root):
    python scripts/make_clinical_splits.py
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METADATA_CSV = PROJECT_ROOT / "data" / "raw" / "pad_ufes_20" / "metadata.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "clinical_splits.csv"


def main():
    assert METADATA_CSV.exists(), f"{METADATA_CSV} not found — run scripts/download_pad_ufes20.py first."
    df = pd.read_csv(METADATA_CSV)

    df_trainval, df_test = train_test_split(
        df, test_size=0.15, stratify=df["label"], random_state=SEED
    )
    val_relative = 0.15 / 0.85
    df_train, df_val = train_test_split(
        df_trainval, test_size=val_relative, stratify=df_trainval["label"], random_state=SEED
    )

    df_train = df_train.assign(split="train")
    df_val = df_val.assign(split="val")
    df_test = df_test.assign(split="test")
    splits_df = pd.concat([df_train, df_val, df_test], ignore_index=True)

    assert len(splits_df) == len(df)
    assert splits_df["isic_id"].is_unique

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    splits_df.to_csv(OUTPUT_CSV, index=False)

    print(f"Train: {len(df_train):>5}  ({len(df_train)/len(df):.1%})")
    print(f"Val:   {len(df_val):>5}  ({len(df_val)/len(df):.1%})")
    print(f"Test:  {len(df_test):>5}  ({len(df_test)/len(df):.1%})")
    print(f"\nSaved {len(splits_df)} rows to {OUTPUT_CSV}")

    print("\nClass counts per split:")
    print(splits_df.groupby("split")["label"].value_counts().unstack().fillna(0).astype(int))


if __name__ == "__main__":
    main()

"""
Build 5-fold stratified splits for k-fold ensemble training of the
dermoscopic (ISIC 2018) model — reuses the EXISTING held-out test set from
data/processed/splits.csv (produced by notebooks/02_split.ipynb) so the
final ensemble's test score stays directly comparable to the original single
baseline_unfrozen model's test score. Only the train+val pool (85% of the
data) gets re-split into 5 folds; the test 15% is never touched by any fold.

Requires: data/processed/splits.csv already exists (it does on this machine
from the original training run).

Produces:
    data/processed/kfold_splits.csv
        columns: image, label, fold
        fold is an int 0-4 for every image that was originally 'train' or
        'val' (assigned via fresh stratified 5-fold over that combined pool),
        or the string 'test' for the original held-out test images.

Usage (run from the project root):
    python scripts/make_kfold_splits.py
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedKFold

SEED = 42
N_FOLDS = 5
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPLITS_CSV = PROJECT_ROOT / "data" / "processed" / "splits.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "kfold_splits.csv"


def main():
    assert SPLITS_CSV.exists(), f"{SPLITS_CSV} not found — this should already exist from the original training run."
    df = pd.read_csv(SPLITS_CSV)

    test_df = df[df["split"] == "test"].copy()
    pool_df = df[df["split"] != "test"].reset_index(drop=True)  # original train+val, 85% of the data

    print(f"Held-out test set (untouched by any fold): {len(test_df)} images")
    print(f"Train+val pool to be re-split into {N_FOLDS} folds: {len(pool_df)} images")

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    pool_df["fold"] = -1
    for fold_idx, (_, val_idx) in enumerate(skf.split(pool_df["image"], pool_df["label"])):
        pool_df.loc[val_idx, "fold"] = fold_idx

    assert (pool_df["fold"] >= 0).all()

    test_df["fold"] = "test"
    out_df = pd.concat([pool_df[["image", "label", "fold"]], test_df[["image", "label", "fold"]]], ignore_index=True)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {len(out_df)} rows to {OUTPUT_CSV}")

    print("\nPer-fold class counts (each fold's images, used as that fold's val set):")
    print(pool_df.groupby("fold")["label"].value_counts().unstack().fillna(0).astype(int))


if __name__ == "__main__":
    main()

"""
PAD-UFES-20 clinical (non-dermoscopic) skin lesion — PyTorch Dataset.

Separate from src/dataset.py (the ISIC 2018 dermoscopic dataset). This one
powers a second, independent classifier for regular camera/phone photos —
see scripts/download_pad_ufes20.py and scripts/train_clinical.py.

Loads images using data/raw/pad_ufes_20/metadata.csv, produced by
scripts/download_pad_ufes20.py. Returns (image_tensor, label_int) pairs.
"""

from pathlib import Path
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset

# Class name -> integer index. Order is FIXED — don't change it once models
# are trained, or saved checkpoints will silently predict the wrong class.
# Matches the 6 diagnostic categories in the original PAD-UFES-20 paper.
CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]
LABEL_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}
IDX_TO_LABEL = {idx: name for idx, name in enumerate(CLASS_NAMES)}


class ClinicalLesionDataset(Dataset):
    """
    PyTorch Dataset for PAD-UFES-20 clinical skin lesion images.

    Parameters
    ----------
    metadata_csv : str or Path
        Path to data/raw/pad_ufes_20/metadata.csv (created by
        scripts/download_pad_ufes20.py), OR to a split CSV produced by a
        make_clinical_splits.py script with the same columns plus 'split'.
    images_dir : str or Path
        Path to the folder of .jpg images (data/raw/pad_ufes_20/images/).
    split : {'train', 'val', 'test'}, optional
        Which subset to load. If the CSV has no 'split' column (e.g. the raw
        metadata.csv before splitting), this must be None and all rows are used.
    transform : callable, optional
        torchvision transform applied to each image. If None, returns a raw PIL Image.
    """

    def __init__(self, metadata_csv, images_dir, split=None, transform=None):
        self.images_dir = Path(images_dir)
        self.transform = transform

        df = pd.read_csv(metadata_csv)
        if split is not None:
            if split not in {"train", "val", "test"}:
                raise ValueError(f"split must be 'train', 'val', or 'test', got {split!r}")
            df = df[df["split"] == split].reset_index(drop=True)

        self.image_ids = df["isic_id"].tolist()
        self.labels = [LABEL_TO_IDX[name] for name in df["label"]]

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_path = self.images_dir / f"{self.image_ids[idx]}.jpg"
        image = Image.open(img_path).convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        label = self.labels[idx]
        return image, label


def get_class_weights(metadata_csv, split="train"):
    """
    Inverse-frequency class weights for nn.CrossEntropyLoss(weight=...).
    Rare classes (MEL has only ~46 samples, far fewer than the others) get
    proportionally higher weight so the loss doesn't ignore them.
    """
    df = pd.read_csv(metadata_csv)
    if "split" in df.columns:
        df = df[df["split"] == split]

    counts = df["label"].value_counts().reindex(CLASS_NAMES).values
    weights = counts.sum() / (len(CLASS_NAMES) * counts)
    return torch.tensor(weights, dtype=torch.float32)

"""
ISIC 2018 Task 3 — PyTorch Dataset.

Loads images using the splits CSV (data/processed/splits.csv) produced by
notebooks/02_split.ipynb. Returns (image_tensor, label_int) pairs.
"""

from pathlib import Path
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset

# Class name → integer index. Order is FIXED — don't change it once models are trained,
# or saved checkpoints will silently predict the wrong class.
CLASS_NAMES = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']
LABEL_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}
IDX_TO_LABEL = {idx: name for idx, name in enumerate(CLASS_NAMES)}


class ISICDataset(Dataset):
    """
    PyTorch Dataset for ISIC 2018 Task 3 skin lesion images.

    Parameters
    ----------
    splits_csv : str or Path
        Path to data/processed/splits.csv (created by 02_split.ipynb).
    images_dir : str or Path
        Path to the folder of .jpg images
        (data/raw/ISIC2018_Task3_Training_Input/).
    split : {'train', 'val', 'test'}
        Which subset to load.
    transform : callable, optional
        torchvision transform applied to each image. If None, returns a raw PIL Image.
    """

    def __init__(self, splits_csv, images_dir, split, transform=None):
        # Validate split name early — typo here is the most common bug
        if split not in {'train', 'val', 'test'}:
            raise ValueError(f"split must be 'train', 'val', or 'test', got {split!r}")

        self.images_dir = Path(images_dir)
        self.transform = transform

        # Load splits CSV and keep only rows for the requested split
        df = pd.read_csv(splits_csv)
        df = df[df['split'] == split].reset_index(drop=True)

        # Store image filenames and integer labels as plain lists (fast indexing)
        self.image_ids = df['image'].tolist()
        self.labels = [LABEL_TO_IDX[name] for name in df['label']]

    def __len__(self):
        """Number of samples in this split."""
        return len(self.image_ids)

    def __getitem__(self, idx):
        """
        Load one (image, label) pair.

        Returns
        -------
        image : Tensor or PIL.Image
            Transformed image if `transform` was provided, else a raw PIL Image.
        label : int
            Integer class index (0–6).
        """
        # Build the image path: <images_dir>/<image_id>.jpg
        img_path = self.images_dir / f"{self.image_ids[idx]}.jpg"

        # Open with PIL and ensure RGB (some images may be RGBA or grayscale)
        image = Image.open(img_path).convert('RGB')

        # Apply transform pipeline (resize, normalize, augment, etc.) if provided
        if self.transform is not None:
            image = self.transform(image)

        label = self.labels[idx]
        return image, label


def get_class_weights(splits_csv, split='train'):
    """
    Compute inverse-frequency class weights for `nn.CrossEntropyLoss(weight=...)`.

    Returns a tensor of shape [num_classes] where rare classes get higher weight.
    Used to combat class imbalance: a misclassified DF sample contributes more
    to the loss than a misclassified NV sample.

    Parameters
    ----------
    splits_csv : str or Path
    split : str
        Which split's distribution to base the weights on (usually 'train').

    Returns
    -------
    weights : torch.Tensor, shape [7]
        Tensor of class weights aligned with CLASS_NAMES order.
    """
    df = pd.read_csv(splits_csv)
    df = df[df['split'] == split]

    counts = df['label'].value_counts().reindex(CLASS_NAMES).values
    weights = counts.sum() / (len(CLASS_NAMES) * counts)
    return torch.tensor(weights, dtype=torch.float32)
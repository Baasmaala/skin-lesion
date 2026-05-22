"""
AugmentedISICDataset — wraps real ISIC train data + Phase 8 synthetic samples
into a single PyTorch Dataset for the Phase 10 main experiment.

Design choices (documented so they can be defended):

  1. **Wrapper, not subclass.** This Dataset reads splits.csv (real) AND
     synthetic_manifest.csv (synthetic) and builds a unified
     (image_path, label, is_synthetic) list. It does NOT inherit from
     ISICDataset -- that would couple it to the original schema and break
     if the real dataset changes. The wrapper just produces the same
     output format ((tensor, label)) that the classifier already expects.

  2. **Per-class source filter.** A `sources_per_class` dict lets the
     caller declare, for each rare class, which generator(s) to use
     ('cvae', 'cgan', 'both', or 'none'). Default: 'both' for any class
     that appears in the manifest. This is the knob Phase 10 turns based
     on Phase 9's FID results.

  3. **Same transform for real and synthetic.** Synthetic PNGs were
     saved in [0, 1] RGB at 224x224 (Phase 8). Real images come in at
     varying sizes. The shared transform (Resize -> ToTensor -> ImageNet
     normalize) handles both. The synthetic Resize is a no-op since
     they're already 224x224.

  4. **Augmentation.** Apply standard train-time augmentation (flip,
     rotation) to BOTH real and synthetic. We don't want the classifier
     to learn "synthetic == always upright" as a shortcut.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset


class AugmentedISICDataset(Dataset):
    """
    Combined real + synthetic dataset for Phase 10.

    Args:
        splits_csv          : path to data/processed/splits.csv (real)
        images_dir          : path to data/raw/ISIC2018_Task3_Training_Input
        synth_manifest_csv  : path to data/synthetic/synthetic_manifest.csv
        project_root        : root used to resolve relative image_paths in the manifest
        split               : which real split to include ('train', 'val', or 'test')
        transform           : torchvision transform applied to every image
        sources_per_class   : dict[class_idx -> 'cvae' | 'cgan' | 'both' | 'none']
                              Controls which synthetic samples are mixed in.
                              Missing keys default to 'both'.
                              IGNORED when split != 'train' -- val/test never include synthetic.

    A row of this dataset yields (image_tensor, label_long). The
    `is_synthetic` flag is stored on the dataset (self.is_synthetic) for
    later inspection but is NOT returned by __getitem__, so it's a
    drop-in replacement for ISICDataset.
    """

    def __init__(
        self,
        splits_csv: Path,
        images_dir: Path,
        synth_manifest_csv: Path,
        project_root: Path,
        split: str = 'train',
        transform=None,
        sources_per_class: Optional[dict] = None,
    ):
        self.transform = transform
        self.split = split

        # ---- Real images (always included) ----
        splits = pd.read_csv(splits_csv)
        real_rows = splits[splits['split'] == split].copy()
        label_col = 'label' if 'label' in real_rows.columns else 'class_idx'
        image_col = 'image_id' if 'image_id' in real_rows.columns else 'filename'

        self.image_paths: list[Path] = []
        self.labels: list[int] = []
        self.is_synthetic: list[bool] = []

        for _, r in real_rows.iterrows():
            img_id = str(r[image_col])
            fname = img_id if img_id.endswith(('.jpg', '.JPG', '.png')) else f'{img_id}.jpg'
            p = Path(images_dir) / fname
            if p.exists():
                self.image_paths.append(p)
                self.labels.append(int(r[label_col]))
                self.is_synthetic.append(False)

        # ---- Synthetic images: only for train split ----
        if split == 'train' and synth_manifest_csv.exists():
            manifest = pd.read_csv(synth_manifest_csv)
            sources_per_class = sources_per_class or {}

            for _, r in manifest.iterrows():
                cls = int(r['label'])
                source = r['source']
                policy = sources_per_class.get(cls, 'both')

                # Apply per-class policy
                if policy == 'none':
                    continue
                if policy in ('cvae', 'cgan') and source != policy:
                    continue
                # 'both' includes everything; specific source matches itself

                p = Path(project_root) / r['image_path']
                if p.exists():
                    self.image_paths.append(p)
                    self.labels.append(cls)
                    self.is_synthetic.append(True)

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        img = Image.open(self.image_paths[idx]).convert('RGB')
        if self.transform is not None:
            img = self.transform(img)
        return img, self.labels[idx]

    # ---- Useful inspection helpers (don't affect training) ----

    def count_by_source_and_class(self) -> pd.DataFrame:
        """Return a (class_idx x [real, synth]) count table for sanity checking."""
        df = pd.DataFrame({
            'label':        self.labels,
            'is_synthetic': self.is_synthetic,
        })
        df['source'] = df['is_synthetic'].map({False: 'real', True: 'synth'})
        return df.groupby(['label', 'source']).size().unstack(fill_value=0)

from __future__ import annotations
from pathlib import Path
from typing import Optional

import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset

CLASS_NAMES = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']
LABEL_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}

class AugmentedISICDataset(Dataset):

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

        self.image_paths = []
        self.labels = []
        self.is_synthetic = []

        # =========================
        # REAL IMAGES
        # =========================
        splits = pd.read_csv(splits_csv)

        real_rows = splits[splits['split'] == split].copy()

        label_col = 'label' if 'label' in real_rows.columns else 'class_idx'
        image_col = 'image_id' if 'image_id' in real_rows.columns else 'image'

        for _, r in real_rows.iterrows():

            img_id = str(r[image_col])

            fname = (
                img_id
                if img_id.endswith(('.jpg', '.JPG', '.png'))
                else f'{img_id}.jpg'
            )

            p = Path(images_dir) / fname

            if p.exists():

                label_value = r[label_col]

                if isinstance(label_value, str):
                    label_value = LABEL_TO_IDX[label_value]

                self.image_paths.append(p)
                self.labels.append(int(label_value))
                self.is_synthetic.append(False)

        # =========================
        # SYNTHETIC IMAGES
        # =========================
        if split == 'train' and Path(synth_manifest_csv).exists():

            manifest = pd.read_csv(synth_manifest_csv)

            image_col = (
                'image_path'
                if 'image_path' in manifest.columns
                else 'image'
            )

            sources_per_class = sources_per_class or {}

            for _, r in manifest.iterrows():

                cls = int(r['label'])
                source = r['source']

                policy = sources_per_class.get(cls, 'both')

                if policy == 'none':
                    continue

                if policy in ('cvae', 'cgan') and source != policy:
                    continue

                p = Path(r[image_col])

                if not p.is_absolute():
                    p = Path(project_root) / p

                if p.exists():
                    self.image_paths.append(p)
                    self.labels.append(cls)
                    self.is_synthetic.append(True)

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):

        img = Image.open(self.image_paths[idx]).convert('RGB')

        if self.transform is not None:
            img = self.transform(img)

        return img, self.labels[idx]

    def count_by_source_and_class(self):

        df = pd.DataFrame({
            'label': self.labels,
            'is_synthetic': self.is_synthetic,
        })

        df['source'] = df['is_synthetic'].map({
            False: 'real',
            True: 'synth'
        })

        return df.groupby(['label', 'source']).size().unstack(fill_value=0)
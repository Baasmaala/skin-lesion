"""
Conditional DCGAN for skin lesion synthesis (ISIC 2018 Task 3).

Goal of Phase 7 (per PROJECT_STATUS.md):
  Train a class-conditioned GAN so Phase 8 can sample synthetic
  minority-class images. The GAN is meant as the "sharp" counterpart
  to the Phase 6 CVAE (which produces blurry but stable samples).

Architecture follows notes13gan.pdf (DCGAN) with three project-specific
adaptations:

  1. Conditional. Same one-hot conditioning pattern as the CVAE for
     consistency:
       - Generator    : concat one-hot(y) to noise z
       - Discriminator: concat one-hot(y) -- spatially broadcast as
                        extra input channels -- to the input image
     (Spatial broadcasting in D is the standard cGAN trick: it lets the
     conv stack "see" the class label everywhere, instead of only at the
     end. Concatenating to flattened features would also work but loses
     the locality.)

  2. Scaled to 224x224 RGB (note uses 32x32 grayscale).
     Generator: latent_dim+7 -> 4x4 -> 7x7 -> 14 -> 28 -> 56 -> 112 -> 224
     This is 6 ConvTranspose layers; the 4->7 step uses a non-standard
     (k=4, s=2, p=2, output_padding=1) configuration to get an odd size.
     Discriminator mirrors it back down to a scalar real/fake score.

  3. Tanh output -> images in [-1, 1].
     This is the DCGAN convention (matches the note). It means the GAN
     training transform must normalise to [-1, 1], NOT [0, 1] like the
     CVAE. The sample_images() helper below renormalises to [0, 1] so
     callers (Phase 8) get the same range as CVAE.sample() from Phase 6.

Stability choices (standard DCGAN tricks from Radford et al. 2016, also
implied by the BN-everywhere pattern in notes13gan.pdf):
  - BatchNorm in both G and D (except first layer of D and last of G).
  - LeakyReLU(0.2) in both networks (the note uses this).
  - Adam with betas=(0.5, 0.999), lr=2e-4 for both nets.
  - Weights initialised from N(0, 0.02) -- DCGAN paper recommendation.

References followed:
  - notes13gan.pdf            : DCGAN architecture and training procedure
  - notes12generativeAI.pdf   : conditioning concept
  - notes-7-code-5-batch-normal__1_.py : BatchNorm pattern (course code)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================
# 0.  DCGAN weight init  (standard, from Radford et al. 2016)
# ============================================================================

def init_dcgan_weights(m: nn.Module) -> None:
    """Apply with model.apply(init_dcgan_weights)."""
    classname = m.__class__.__name__
    if 'Conv' in classname:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif 'BatchNorm' in classname:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


# ============================================================================
# 1.  Generator
# ============================================================================

class Generator(nn.Module):
    """
    Maps (noise z, class y) -> RGB image in [-1, 1].

    Input : z (B, latent_dim)
            y (B,)  long tensor of class indices
    Output: image (B, 3, 224, 224)
    """

    def __init__(self, latent_dim: int = 100, n_classes: int = 7,
                 base_channels: int = 64):
        super().__init__()
        self.latent_dim = latent_dim
        self.n_classes  = n_classes
        self.base_channels = base_channels

        # Project (z, one-hot(y)) -> 8*base_channels feature map of size 4x4
        # 8*64 = 512 channels, matching the note's Generator (which starts
        # at 512 channels too).
        self.fc = nn.Sequential(
            nn.Linear(latent_dim + n_classes, 8 * base_channels * 4 * 4),
            nn.BatchNorm1d(8 * base_channels * 4 * 4),
            nn.LeakyReLU(0.2, inplace=True),
        )

        c = base_channels
        # Upsampling stack: 4 -> 7 -> 14 -> 28 -> 56 -> 112 -> 224
        # Each block: ConvTranspose2d -> BatchNorm -> LeakyReLU
        # Final block uses Tanh and NO BatchNorm (DCGAN convention).
        self.deconv = nn.Sequential(
            # 4 -> 7   (odd target size: use output_padding=1)
            nn.ConvTranspose2d(8 * c, 8 * c, kernel_size=4, stride=2,
                               padding=2, output_padding=1, bias=False),
            nn.BatchNorm2d(8 * c), nn.LeakyReLU(0.2, inplace=True),

            # 7 -> 14
            nn.ConvTranspose2d(8 * c, 4 * c, kernel_size=4, stride=2,
                               padding=1, bias=False),
            nn.BatchNorm2d(4 * c), nn.LeakyReLU(0.2, inplace=True),

            # 14 -> 28
            nn.ConvTranspose2d(4 * c, 2 * c, kernel_size=4, stride=2,
                               padding=1, bias=False),
            nn.BatchNorm2d(2 * c), nn.LeakyReLU(0.2, inplace=True),

            # 28 -> 56
            nn.ConvTranspose2d(2 * c, c, kernel_size=4, stride=2,
                               padding=1, bias=False),
            nn.BatchNorm2d(c), nn.LeakyReLU(0.2, inplace=True),

            # 56 -> 112
            nn.ConvTranspose2d(c, c // 2, kernel_size=4, stride=2,
                               padding=1, bias=False),
            nn.BatchNorm2d(c // 2), nn.LeakyReLU(0.2, inplace=True),

            # 112 -> 224  (final: no BN, Tanh)
            nn.ConvTranspose2d(c // 2, 3, kernel_size=4, stride=2,
                               padding=1, bias=False),
            nn.Tanh(),
        )

    def forward(self, z: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        y_onehot = F.one_hot(y, num_classes=self.n_classes).float()
        h = torch.cat([z, y_onehot], dim=1)              # (B, latent+7)
        h = self.fc(h)                                   # (B, 512*4*4)
        h = h.view(h.size(0), 8 * self.base_channels, 4, 4)
        return self.deconv(h)                            # (B, 3, 224, 224) in [-1,1]


# ============================================================================
# 2.  Discriminator
# ============================================================================

class Discriminator(nn.Module):
    """
    Decides real vs fake, conditioned on the class label.

    Input : x (B, 3, 224, 224) in [-1, 1]
            y (B,)  long tensor of class indices
    Output: score (B, 1) in [0, 1]  (probability of "real")

    Conditioning trick: we one-hot the label and broadcast it spatially to
    7 extra channels matching the image size, then concatenate to x. So
    the first Conv sees 3+7 = 10 input channels.
    """

    def __init__(self, n_classes: int = 7, base_channels: int = 64):
        super().__init__()
        self.n_classes = n_classes
        c = base_channels

        # Downsampling stack with strided convs (DCGAN style).
        # Stride-2 convs reach: 224 -> 112 -> 56 -> 28 -> 14 -> 7.
        # We then AdaptiveAvgPool2d down to exactly 4x4 -- simpler than
        # choreographing odd-sized strided convs to land at 4x4 exactly,
        # and a common pattern for cGANs at non-power-of-two input sizes.
        # First block: NO BatchNorm (DCGAN convention) -- BN here would
        # smear the only direct signal from the real/fake input.
        self.conv = nn.Sequential(
            # 224 -> 112  (input has 3 + n_classes channels)
            nn.Conv2d(3 + n_classes, c, kernel_size=4, stride=2,
                      padding=1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),

            # 112 -> 56
            nn.Conv2d(c, 2 * c, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(2 * c), nn.LeakyReLU(0.2, inplace=True),

            # 56 -> 28
            nn.Conv2d(2 * c, 4 * c, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(4 * c), nn.LeakyReLU(0.2, inplace=True),

            # 28 -> 14
            nn.Conv2d(4 * c, 8 * c, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(8 * c), nn.LeakyReLU(0.2, inplace=True),

            # 14 -> 7
            nn.Conv2d(8 * c, 8 * c, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(8 * c), nn.LeakyReLU(0.2, inplace=True),

            # 7 -> 4  (deterministic via adaptive pooling)
            nn.AdaptiveAvgPool2d((4, 4)),
        )

        # Real/fake head
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(8 * c * 4 * 4, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        # Spatially broadcast one-hot(y) to (B, n_classes, H, W) and concat
        B, _, H, W = x.shape
        y_onehot = F.one_hot(y, num_classes=self.n_classes).float()   # (B, n_classes)
        y_map = y_onehot.view(B, self.n_classes, 1, 1).expand(B, self.n_classes, H, W)
        h = torch.cat([x, y_map], dim=1)                              # (B, 3+n_classes, H, W)
        h = self.conv(h)
        return self.head(h)                                           # (B, 1)


# ============================================================================
# 3.  Convenience: sample helper used by Phase 8
# ============================================================================

@torch.no_grad()
def sample_images(generator: Generator,
                  class_idx: int,
                  n: int = 1,
                  device: str = "cpu") -> torch.Tensor:
    """
    Sample `n` synthetic images of class `class_idx`.

    Returns images in [0, 1] (NOT [-1, 1]) so the interface matches
    CVAE.sample() from Phase 6. Phase 8 can mix VAE and GAN samples
    without worrying about scale.
    """
    generator.eval()
    z = torch.randn(n, generator.latent_dim, device=device)
    y = torch.full((n,), class_idx, dtype=torch.long, device=device)
    imgs = generator(z, y)                       # [-1, 1]
    imgs = (imgs + 1.0) / 2.0                    # -> [0, 1]
    return imgs.clamp(0.0, 1.0)


# ============================================================================
# 4.  Quick sanity check  (style matches src/models/cvae.py)
# ============================================================================
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Sanity check on {device}")

    LATENT_DIM = 100
    N_CLASSES  = 7

    G = Generator(latent_dim=LATENT_DIM, n_classes=N_CLASSES).to(device)
    D = Discriminator(n_classes=N_CLASSES).to(device)
    G.apply(init_dcgan_weights)
    D.apply(init_dcgan_weights)

    print(f"Generator     params: {sum(p.numel() for p in G.parameters()):,}")
    print(f"Discriminator params: {sum(p.numel() for p in D.parameters()):,}")

    # Generator forward
    z = torch.randn(2, LATENT_DIM, device=device)
    y = torch.tensor([0, 5], device=device)        # MEL, DF
    fake = G(z, y)
    print(f"fake  : {tuple(fake.shape)}   "
          f"min={fake.min().item():.3f}  max={fake.max().item():.3f}  "
          f"(expected ~[-1, 1])")

    # Discriminator forward on fake and on a fake "real" batch
    real = torch.rand(2, 3, 224, 224, device=device) * 2 - 1   # pretend real, in [-1,1]
    d_fake = D(fake.detach(), y)
    d_real = D(real, y)
    print(f"D(fake): {tuple(d_fake.shape)}   value={d_fake.flatten().tolist()}")
    print(f"D(real): {tuple(d_real.shape)}   value={d_real.flatten().tolist()}")

    # Sample helper
    s = sample_images(G, class_idx=5, n=4, device=device)
    print(f"sample: {tuple(s.shape)}   "
          f"min={s.min().item():.3f}  max={s.max().item():.3f}  "
          f"(expected ~[0, 1])")

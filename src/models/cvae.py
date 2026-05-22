"""
Conditional VAE for skin lesion synthesis (ISIC 2018 Task 3).

Goal of Phase 6 (per PROJECT_STATUS.md):
  Learn p(image | class) so we can later sample synthetic minority-class
  images (DF, VASC, AKIEC, ...) and use them to augment classifier training
  in Phase 10.

Design (all decisions documented so they can be defended in the report):

  - Input  : (B, 3, 224, 224)  RGB in [0, 1]  (NO ImageNet normalization,
             because the decoder ends in Sigmoid and must produce [0, 1])
  - Label  : integer class index in [0, 7), turned into one-hot (B, 7)

  - Encoder: 4 strided conv layers
        3   x 224 x 224   ->  32 x 112 x 112
        32  x 112 x 112   ->  64 x 56  x 56
        64  x 56  x 56    -> 128 x 28  x 28
        128 x 28  x 28    -> 256 x 14  x 14
     Then concatenate one-hot label to the flattened features, and two
     linear heads produce (z_mean, z_log_var).

  - Sampling: reparameterisation trick (identical to notes-12-vae.py)

  - Decoder: concatenate one-hot label to z, project to 256x14x14, then
     4 transposed-conv layers mirror the encoder back up to 3x224x224,
     ending in Sigmoid so outputs are in [0, 1].

  - Loss   : MSE reconstruction + beta * KL divergence.
     We use MSE (not BCE as in notes-12-vae.py) because BCE is fragile on
     natural RGB images -- it overpenalises grey-area pixel values typical
     of skin photos. MSE is the standard choice for RGB VAEs.
     beta starts small (we use 1.0) because for 224x224 RGB the
     reconstruction term naturally dominates; tune later if KL collapses.

  - latent_dim = 128.  Reference notes-12-vae.py uses 2 for Fashion-MNIST
     visualisation; 224x224 RGB skin lesions need far more capacity.

References followed:
  - notes-12-vae.py            : encoder/decoder pattern, reparameterise,
                                 vae_loss structure, training loop shape
  - notes12generativeAI.pdf    : CVAE concept (condition both encoder and
                                 decoder on the class label)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================
# 1.  Model
# ============================================================================

class CVAEEncoder(nn.Module):
    """
    Convolutional encoder, conditioned on class label.

    Input :  x       (B, 3, 224, 224)  RGB in [0, 1]
             y_onehot (B, n_classes)
    Output:  z_mean, z_log_var   each (B, latent_dim)
    """

    def __init__(self, latent_dim: int = 128, n_classes: int = 7):
        super().__init__()
        self.n_classes = n_classes

        # 4 strided conv layers: 224 -> 112 -> 56 -> 28 -> 14
        # BatchNorm is added (course note 7 covers this) to keep training
        # stable at 224x224 RGB scale -- without BN the loss is noisy.
        self.conv = nn.Sequential(
            nn.Conv2d(3,   32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),  nn.ReLU(inplace=True),

            nn.Conv2d(32,  64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),  nn.ReLU(inplace=True),

            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(inplace=True),

            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(256), nn.ReLU(inplace=True),
        )

        # After conv: 256 * 14 * 14 = 50,176 features
        self.flatten_dim = 256 * 14 * 14

        # Linear heads take the flattened features CONCAT with the class
        # one-hot. This is the "conditional" part of CVAE: the encoder
        # knows which class it's looking at.
        self.fc_mean    = nn.Linear(self.flatten_dim + n_classes, latent_dim)
        self.fc_log_var = nn.Linear(self.flatten_dim + n_classes, latent_dim)

    def forward(self, x: torch.Tensor, y_onehot: torch.Tensor):
        h = self.conv(x)                                # (B, 256, 14, 14)
        h = h.view(h.size(0), -1)                       # (B, 50176)
        h = torch.cat([h, y_onehot], dim=1)             # (B, 50176 + 7)
        z_mean    = self.fc_mean(h)                     # (B, latent_dim)
        z_log_var = self.fc_log_var(h)                  # (B, latent_dim)
        return z_mean, z_log_var


def reparameterise(z_mean: torch.Tensor, z_log_var: torch.Tensor) -> torch.Tensor:
    """
    Reparameterisation trick (identical math to notes-12-vae.py):
        z = z_mean + exp(0.5 * z_log_var) * epsilon,  epsilon ~ N(0, I)
    Lets gradients flow through the sampling step.
    """
    std     = torch.exp(0.5 * z_log_var)
    epsilon = torch.randn_like(std)
    return z_mean + std * epsilon


class CVAEDecoder(nn.Module):
    """
    Transposed-conv decoder, conditioned on class label.

    Input : z        (B, latent_dim)
            y_onehot (B, n_classes)
    Output: reconstruction (B, 3, 224, 224) in [0, 1]
    """

    def __init__(self, latent_dim: int = 128, n_classes: int = 7):
        super().__init__()
        self.n_classes = n_classes
        self.flatten_dim = 256 * 14 * 14

        # Project (z, y_onehot) back to the spatial shape before the convs.
        # Concatenating the label here is the second half of CVAE: the
        # decoder also knows which class it is generating.
        self.fc = nn.Linear(latent_dim + n_classes, self.flatten_dim)

        # Mirror the encoder: 14 -> 28 -> 56 -> 112 -> 224
        self.deconv = nn.Sequential(
            nn.ConvTranspose2d(256, 128, kernel_size=3, stride=2,
                               padding=1, output_padding=1),
            nn.BatchNorm2d(128), nn.ReLU(inplace=True),

            nn.ConvTranspose2d(128, 64,  kernel_size=3, stride=2,
                               padding=1, output_padding=1),
            nn.BatchNorm2d(64),  nn.ReLU(inplace=True),

            nn.ConvTranspose2d(64,  32,  kernel_size=3, stride=2,
                               padding=1, output_padding=1),
            nn.BatchNorm2d(32),  nn.ReLU(inplace=True),

            nn.ConvTranspose2d(32,  3,   kernel_size=3, stride=2,
                               padding=1, output_padding=1),
            nn.Sigmoid(),   # output in [0, 1] to match input scale
        )

    def forward(self, z: torch.Tensor, y_onehot: torch.Tensor):
        h = torch.cat([z, y_onehot], dim=1)             # (B, latent_dim + 7)
        h = self.fc(h)                                  # (B, 50176)
        h = h.view(h.size(0), 256, 14, 14)              # (B, 256, 14, 14)
        x_recon = self.deconv(h)                        # (B, 3, 224, 224)
        return x_recon


class CVAE(nn.Module):
    """
    Full Conditional VAE: wraps encoder + reparameterise + decoder.

    Forward returns (reconstruction, z_mean, z_log_var) -- same signature
    as the unconditional VAE in notes-12-vae.py, so the training loop
    barely changes.
    """

    def __init__(self, latent_dim: int = 128, n_classes: int = 7):
        super().__init__()
        self.latent_dim = latent_dim
        self.n_classes  = n_classes
        self.encoder = CVAEEncoder(latent_dim, n_classes)
        self.decoder = CVAEDecoder(latent_dim, n_classes)

    def forward(self, x: torch.Tensor, y: torch.Tensor):
        """
        x: (B, 3, 224, 224) in [0, 1]
        y: (B,) long tensor of class indices
        """
        y_onehot = F.one_hot(y, num_classes=self.n_classes).float()
        z_mean, z_log_var = self.encoder(x, y_onehot)
        z = reparameterise(z_mean, z_log_var)
        x_recon = self.decoder(z, y_onehot)
        return x_recon, z_mean, z_log_var

    @torch.no_grad()
    def sample(self, class_idx: int, n: int = 1, device: str = "cpu") -> torch.Tensor:
        """
        Sample `n` synthetic images of class `class_idx` from the prior N(0, I).
        Used in Phase 8 to generate synthetic minority-class images.

        Returns: (n, 3, 224, 224) in [0, 1]
        """
        self.eval()
        z = torch.randn(n, self.latent_dim, device=device)
        y = torch.full((n,), class_idx, dtype=torch.long, device=device)
        y_onehot = F.one_hot(y, num_classes=self.n_classes).float()
        return self.decoder(z, y_onehot)


# ============================================================================
# 2.  Loss
# ============================================================================

def cvae_loss(x: torch.Tensor,
              x_recon: torch.Tensor,
              z_mean: torch.Tensor,
              z_log_var: torch.Tensor,
              beta: float = 1.0):
    """
    CVAE loss = reconstruction + beta * KL divergence.

    Reconstruction: MSE summed over pixels, averaged over the batch.
        We chose MSE over BCE (notes-12-vae.py uses BCE on grayscale
        Fashion-MNIST) because BCE is fragile on natural RGB images
        with continuous mid-range pixel values.

    KL divergence (same formula as notes-12-vae.py):
        KL = -0.5 * sum(1 + log_var - mean^2 - exp(log_var))

    beta:
        Controls the trade-off (Beta-VAE idea, slide 58 of notes12).
        beta = 0 -> behaves like an autoencoder (latent space not Gaussian,
                   can't sample from prior, but reconstruction is sharp).
        beta >> 1 -> Gaussian latent space (good for sampling) but blurry
                     reconstruction. For 224x224 RGB images, recon loss is
                     huge in absolute terms so a beta around 1 is a sensible
                     start. Tune by watching whether kl -> 0 (posterior
                     collapse -- too much beta) or kl explodes (too little).
    """
    batch_size = x.size(0)

    # MSE summed over pixels, then averaged over the batch -- consistent
    # with how notes-12-vae.py computes BCE.
    recon_loss = F.mse_loss(x_recon, x, reduction="sum") / batch_size

    # KL divergence per sample, then averaged over the batch.
    kl_loss = -0.5 * torch.mean(
        torch.sum(1 + z_log_var - z_mean.pow(2) - z_log_var.exp(), dim=1)
    )

    total = recon_loss + beta * kl_loss
    return total, recon_loss, kl_loss


# ============================================================================
# 3.  Quick sanity check  (matches the style of src/models/classifier.py)
# ============================================================================
if __name__ == "__main__":
    # Forward-pass dry run -- catches shape bugs without a real dataset.
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Sanity check on {device}")

    model = CVAE(latent_dim=128, n_classes=7).to(device)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {n_params:,}")

    x = torch.rand(2, 3, 224, 224, device=device)        # in [0, 1]
    y = torch.tensor([0, 5], device=device)              # MEL, DF

    x_recon, z_mean, z_log_var = model(x, y)
    print(f"x_recon   : {tuple(x_recon.shape)}   "
          f"min={x_recon.min().item():.3f} max={x_recon.max().item():.3f}")
    print(f"z_mean    : {tuple(z_mean.shape)}")
    print(f"z_log_var : {tuple(z_log_var.shape)}")

    total, recon, kl = cvae_loss(x, x_recon, z_mean, z_log_var, beta=1.0)
    print(f"loss={total.item():.2f}   recon={recon.item():.2f}   kl={kl.item():.4f}")

    # Sample 4 synthetic images of class 5 (DF -- the rarest class)
    synth = model.sample(class_idx=5, n=4, device=device)
    print(f"sampled   : {tuple(synth.shape)}   "
          f"min={synth.min().item():.3f} max={synth.max().item():.3f}")

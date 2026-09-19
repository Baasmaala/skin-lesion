# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# CPU-only torch/torchvision — skips the ~2GB of bundled CUDA libraries,
# which this deployment doesn't use and which would blow past free-tier
# image size limits.
COPY backend/requirements-prod.txt ./backend/requirements-prod.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch torchvision && \
    pip install --no-cache-dir -r backend/requirements-prod.txt huggingface_hub

COPY backend/ backend/
COPY src/ src/

# Checkpoints (~570MB) aren't in git — they're pulled from a Hugging Face
# Hub *model* repo (plain git-lfs storage, unrelated to Spaces/Docker
# billing) at build time. Set HF_CHECKPOINTS_REPO to your own repo id.
# If that repo is private, also pass --build-arg HF_TOKEN=<token>.
ARG HF_CHECKPOINTS_REPO
ARG HF_TOKEN
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download(repo_id='${HF_CHECKPOINTS_REPO}', repo_type='model', local_dir='results/checkpoints', token='${HF_TOKEN}' or None)"

ENV MPLBACKEND=Agg
# Railway/Render/Fly.io inject their own $PORT; this falls back to 7860
# (also what Hugging Face Spaces expects) when nothing sets it.
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

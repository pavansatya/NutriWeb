"""Step 1 — fetch the Open Food Facts parquet from the Hugging Face Hub.

The file is ~7.8 GB. It lands in the shared HF cache rather than the repo, so
re-runs are free and the working tree stays clean. Anonymous access gets
rate-limited (HTTP 429) on a file this size, so we authenticate: `hf auth login`
once, or export HF_TOKEN.

Usage:
    python pipeline/01_download.py
"""

import os
import sys

from huggingface_hub import hf_hub_download

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.config import SOURCE_FILE, SOURCE_REPO  # noqa: E402


def download() -> str:
    """Download food.parquet and return its local path."""
    # hf_transfer gives a large speedup on multi-GB files; harmless if absent.
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

    print(f"Downloading {SOURCE_REPO}/{SOURCE_FILE} (~7.8 GB)...")
    path = hf_hub_download(
        repo_id=SOURCE_REPO,
        filename=SOURCE_FILE,
        repo_type="dataset",
    )
    size_gb = os.path.getsize(path) / 1024**3
    print(f"Done: {path} ({size_gb:.2f} GB)")
    return path


if __name__ == "__main__":
    download()

"""Weight management: download Exp4x checkpoint from Zenodo on first use."""

from __future__ import annotations

import hashlib
import os
import tarfile
from pathlib import Path
from urllib.request import urlretrieve

# To be filled when the Zenodo deposit is published; replace ZENODO_RECORD with
# the actual record ID and set ZENODO_FILE + SHA256_HASH.
ZENODO_RECORD = "PENDING_RECORD_ID"
ZENODO_FILE = "exp4x_for_maia.tar.gz"
ZENODO_URL = f"https://zenodo.org/record/{ZENODO_RECORD}/files/{ZENODO_FILE}"
SHA256_HASH = "PENDING_SHA256"

# Layout inside the tarball:
#   exp4x_for_maia/Dataset932/nnUNetTrainer__nnUNetPlans__3d_fullres/fold_0/
WEIGHTS_ROOT_NAME = "exp4x_for_maia"


def _cache_dir() -> Path:
    if os.environ.get("BREAST_MRI_SEG_CACHE"):
        return Path(os.environ["BREAST_MRI_SEG_CACHE"])
    return Path.home() / ".cache" / "breast_mri_segmentator"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_weights(force_download: bool = False) -> Path:
    """Return the path to the Exp4x weights root (``$nnUNet_results``).

    Downloads from Zenodo on first use and caches under
    ``$BREAST_MRI_SEG_CACHE`` or ``~/.cache/breast_mri_segmentator/``.
    """
    cache = _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    extracted = cache / WEIGHTS_ROOT_NAME

    if extracted.exists() and not force_download:
        return extracted

    archive = cache / ZENODO_FILE
    if not archive.exists() or force_download:
        print(f"Downloading Exp4x weights from {ZENODO_URL} -> {archive}")
        urlretrieve(ZENODO_URL, archive)

    if SHA256_HASH != "PENDING_SHA256":
        digest = _sha256(archive)
        if digest != SHA256_HASH:
            raise RuntimeError(
                f"SHA256 mismatch for {archive}: expected {SHA256_HASH}, got {digest}"
            )

    print(f"Extracting {archive} -> {cache}")
    with tarfile.open(archive, "r:gz") as t:
        # Use the 'data' filter (Python >= 3.12) to reject unsafe members
        # (absolute paths / traversal) when extracting a downloaded archive.
        if hasattr(tarfile, "data_filter"):
            t.extractall(cache, filter="data")
        else:  # pragma: no cover - Python 3.10/3.11 fallback
            t.extractall(cache)

    return extracted

"""Unit tests for breast_mri_segmentator.weights.

These cover the cache-location logic, the SHA256 helper, and the
download/extract/verify flow in ``ensure_weights`` — all with the network
mocked (no real Zenodo access).
"""
from __future__ import annotations

import hashlib
import tarfile
from pathlib import Path

import pytest

from breast_mri_segmentator import weights


def _make_weights_tarball(dst: Path) -> Path:
    """Build a tiny tarball whose top dir is ``WEIGHTS_ROOT_NAME``."""
    root = dst.parent / weights.WEIGHTS_ROOT_NAME
    root.mkdir(parents=True, exist_ok=True)
    (root / "dataset.json").write_text("{}")
    with tarfile.open(dst, "w:gz") as t:
        t.add(root, arcname=weights.WEIGHTS_ROOT_NAME)
    # Remove the staging dir so extraction is what creates the final one.
    (root / "dataset.json").unlink()
    root.rmdir()
    return dst


# --------------------------------------------------------------- _cache_dir ---
def test_cache_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("BREAST_MRI_SEG_CACHE", str(tmp_path / "mycache"))
    assert weights._cache_dir() == tmp_path / "mycache"


def test_cache_dir_default(monkeypatch):
    monkeypatch.delenv("BREAST_MRI_SEG_CACHE", raising=False)
    assert weights._cache_dir() == Path.home() / ".cache" / "breast_mri_segmentator"


# ------------------------------------------------------------------- _sha256 ---
def test_sha256_matches_hashlib(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"breast-mri-segmentator")
    assert weights._sha256(f) == hashlib.sha256(b"breast-mri-segmentator").hexdigest()


# ------------------------------------------------------------ ensure_weights ---
def test_ensure_weights_returns_cached_without_download(tmp_path, monkeypatch):
    monkeypatch.setenv("BREAST_MRI_SEG_CACHE", str(tmp_path))
    extracted = tmp_path / weights.WEIGHTS_ROOT_NAME
    extracted.mkdir()

    def _boom(*_a, **_k):  # urlretrieve must NOT be called
        raise AssertionError("should not download when cache exists")

    monkeypatch.setattr(weights, "urlretrieve", _boom)
    assert weights.ensure_weights() == extracted


def test_ensure_weights_downloads_and_extracts(tmp_path, monkeypatch):
    monkeypatch.setenv("BREAST_MRI_SEG_CACHE", str(tmp_path))
    archive = tmp_path / weights.ZENODO_FILE

    def fake_urlretrieve(url, dest):
        _make_weights_tarball(Path(dest))
        return dest, None

    monkeypatch.setattr(weights, "urlretrieve", fake_urlretrieve)
    monkeypatch.setattr(weights, "SHA256_HASH", "PENDING_SHA256")  # skip check

    extracted = weights.ensure_weights()
    assert extracted == tmp_path / weights.WEIGHTS_ROOT_NAME
    assert (extracted / "dataset.json").exists()
    assert archive.exists()


def test_ensure_weights_sha256_mismatch_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("BREAST_MRI_SEG_CACHE", str(tmp_path))
    archive = tmp_path / weights.ZENODO_FILE
    _make_weights_tarball(archive)  # archive present, no download needed

    monkeypatch.setattr(weights, "SHA256_HASH", "0" * 64)  # deliberately wrong
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        weights.ensure_weights()


def test_ensure_weights_sha256_match_passes(tmp_path, monkeypatch):
    monkeypatch.setenv("BREAST_MRI_SEG_CACHE", str(tmp_path))
    archive = tmp_path / weights.ZENODO_FILE
    _make_weights_tarball(archive)
    good = weights._sha256(archive)

    monkeypatch.setattr(weights, "SHA256_HASH", good)
    extracted = weights.ensure_weights()
    assert (extracted / "dataset.json").exists()

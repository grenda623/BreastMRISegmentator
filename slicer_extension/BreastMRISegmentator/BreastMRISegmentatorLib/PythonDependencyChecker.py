"""Ensure the Python runtime inside Slicer has the inference engine available.

DentalSegmentator checks for ``torch`` + ``nnunetv2`` and downloads weights
from a GitHub release. We instead depend on the pip package
``breast-mri-segmentator`` (which pulls in ``nnunetv2`` -> ``torch``), and let
that package fetch the Exp4x weights from Zenodo on first use. So this checker
only has to guarantee the pip package is importable.

SCAFFOLD: the GPU/torch install path is environment-specific and untested
inside Slicer. ``light-the-torch`` is recommended to pick the right CUDA wheel.
"""
from __future__ import annotations

import logging

#: Pip requirement that provides ``breast_mri_segmentator`` and its deps.
PACKAGE_REQUIREMENT = "breast-mri-segmentator>=0.1.0"


def isPackageInstalled() -> bool:
    try:
        import breast_mri_segmentator  # noqa: F401

        return True
    except ImportError:
        return False


def areDependenciesSatisfied() -> bool:
    """True iff the inference engine and its heavy deps are importable."""
    try:
        import torch  # noqa: F401
        import nnunetv2  # noqa: F401
        import breast_mri_segmentator  # noqa: F401

        return True
    except ImportError:
        return False


def installDependencies(progressCallback=None) -> None:
    """Install ``breast-mri-segmentator`` into Slicer's Python.

    Uses ``slicer.util.pip_install`` when running inside Slicer. Installing a
    CUDA-enabled torch is left to ``light-the-torch`` (``ltt``) because the
    correct wheel depends on the host driver.
    """
    def _log(msg: str) -> None:
        logging.info(msg)
        if progressCallback is not None:
            progressCallback(msg)

    try:
        from slicer.util import pip_install
    except ImportError as exc:  # not inside Slicer
        raise RuntimeError(
            "installDependencies() must be called from within 3D Slicer."
        ) from exc

    # TODO: validate the torch/CUDA path on a real Slicer install. The pattern:
    #   pip_install("light-the-torch")
    #   subprocess ltt install torch     # driver-matched CUDA wheel
    # then install our package without re-resolving torch.
    _log("Installing torch via light-the-torch (driver-matched CUDA wheel)...")
    pip_install("light-the-torch")
    # ltt is invoked as a module; see TODO above for the exact incantation.

    _log(f"Installing {PACKAGE_REQUIREMENT} ...")
    pip_install(PACKAGE_REQUIREMENT)

    if not areDependenciesSatisfied():
        raise RuntimeError(
            "Dependency installation finished but torch/nnunetv2/"
            "breast_mri_segmentator are still not importable. See the Slicer "
            "Python console log."
        )
    _log("Dependencies ready.")

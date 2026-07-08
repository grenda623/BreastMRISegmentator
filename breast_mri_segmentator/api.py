"""High-level Python API.

This module wraps the nnUNetv2_predict CLI as a callable Python function.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from breast_mri_segmentator.io import build_4ch_kinetic, dicom_to_nifti
from breast_mri_segmentator.weights import ensure_weights

PathLike = str | Path


def segment(
    input_dir: PathLike,
    output_dir: PathLike,
    from_dicom: bool = False,
    weights_dir: PathLike | None = None,
    use_tta: bool = False,
    fold: int = 0,
) -> Path:
    """Run breast/FGT/tumor segmentation on a directory of DCE-MRI cases.

    Parameters
    ----------
    input_dir : path
        Either (a) a directory of DICOM series, one sub-directory per case
        (when ``from_dicom=True``), or (b) a directory of per-phase NIfTI
        files named ``<case>_phase{0,1,2,3,4}.nii.gz``.
    output_dir : path
        Where prediction NIfTI volumes (``<case>.nii.gz``) will be written.
        Each output volume has labels ``0=background, 1=breast, 2=FGT, 3=tumor``.
    from_dicom : bool
        If True, treat ``input_dir`` as DICOM and run dcm2niix first.
    weights_dir : path, optional
        Path to a downloaded weights directory (``nnUNet_results`` root). If
        ``None``, the package will fetch from Zenodo into a per-user cache.
    use_tta : bool
        Enable test-time augmentation. Slower (~8x) but yields marginally
        higher Dice.
    fold : int
        Which trained fold to use. Default ``0`` (the deployed Exp4x model
        ships with fold 0 only).

    Returns
    -------
    Path
        ``output_dir`` as a Path.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bmrs_") as tmp:
        tmp = Path(tmp)
        nifti_root = tmp / "nifti"
        kinetic_root = tmp / "kinetic_4ch"

        # 1. DICOM -> NIfTI
        if from_dicom:
            dicom_to_nifti(input_dir, nifti_root)
        else:
            shutil.copytree(input_dir, nifti_root)

        # 2. NIfTI per-phase -> 4-channel kinetic input
        build_4ch_kinetic(nifti_root, kinetic_root)

        # 3. nnUNet inference
        weights_dir = Path(weights_dir) if weights_dir else ensure_weights()

        env = os.environ.copy()
        env.update({
            "nnUNet_results": str(weights_dir),
            "nnUNet_raw": str(tmp / "nnunet_raw_unused"),
            "nnUNet_preprocessed": str(tmp / "nnunet_preprocessed_unused"),
            "nnUNet_compile": "0",
        })
        os.makedirs(env["nnUNet_raw"], exist_ok=True)
        os.makedirs(env["nnUNet_preprocessed"], exist_ok=True)

        cmd = [
            "nnUNetv2_predict",
            "-i", str(kinetic_root),
            "-o", str(output_dir),
            "-d", "932",
            "-c", "3d_fullres",
            "-tr", "nnUNetTrainer",
            "-p", "nnUNetPlans",
            "-f", str(fold),
        ]
        if not use_tta:
            cmd.append("--disable_tta")

        subprocess.run(cmd, check=True, env=env)

    return output_dir

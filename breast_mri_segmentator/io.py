"""Input/output helpers: DICOM->NIfTI conversion + 4-channel kinetic build."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import nibabel as nib
import numpy as np

PathLike = str | Path

# Patterns recognized as DCE phases in dcm2niix-converted filenames.
# Two protocols seen in practice (Siemens TWIST-VIBE + dynaVIEWS).
_TTC_RE = re.compile(r"TTC[=_](\d+\.?\d*)s", re.IGNORECASE)
_DYNAVIEWS_KW = "dynaviews"
_SERIES_RE = re.compile(r"^(\d+)_")


def dicom_to_nifti(src: PathLike, dst: PathLike) -> None:
    """Convert a directory of DICOM cases to NIfTI using dcm2niix.

    Expects ``src`` layout: ``src/<case>/<series dirs>...``. For each case
    sub-directory, all series are converted into ``dst/<case>/*.nii.gz``.
    """
    src, dst = Path(src), Path(dst)
    dst.mkdir(parents=True, exist_ok=True)

    if shutil.which("dcm2niix") is None:
        raise RuntimeError(
            "dcm2niix not found on PATH. Install with `pip install dcm2niix` "
            "or download a binary from https://github.com/rordenlab/dcm2niix."
        )

    for case_dir in sorted(p for p in src.iterdir() if p.is_dir()):
        case_out = dst / case_dir.name
        case_out.mkdir(exist_ok=True)
        subprocess.run(
            ["dcm2niix", "-z", "y", "-f", "%s_%d", "-o", str(case_out), str(case_dir)],
            check=True,
        )


def _gather_dce_phases(case_dir: Path) -> list[tuple[float, Path]]:
    """Return DCE phase files sorted by acquisition time (or series number)."""
    nii_files = [
        f for f in case_dir.glob("*.nii.gz")
        if not f.name.startswith("._")
    ]

    # Strategy A: filenames contain TTC=XX.Xs (Siemens TWIST-VIBE)
    ttc_phases = []
    for f in nii_files:
        m = _TTC_RE.search(f.name)
        if m:
            ttc_phases.append((float(m.group(1)), f))
    if len(ttc_phases) >= 3:
        ttc_phases.sort(key=lambda x: x[0])
        return ttc_phases

    # Strategy B: dynaVIEWS files, sort by series number prefix
    dyna_phases = []
    for f in nii_files:
        if _DYNAVIEWS_KW in f.name.lower():
            m = _SERIES_RE.match(f.name)
            if m:
                dyna_phases.append((float(m.group(1)), f))
    if len(dyna_phases) >= 3:
        dyna_phases.sort(key=lambda x: x[0])
        return dyna_phases

    # Strategy C: pre-named phase files like case_phase0.nii.gz
    phase_re = re.compile(r"_?phase[_-]?(\d+)", re.IGNORECASE)
    named_phases = []
    for f in nii_files:
        m = phase_re.search(f.stem)
        if m:
            named_phases.append((float(m.group(1)), f))
    if len(named_phases) >= 3:
        named_phases.sort(key=lambda x: x[0])
        return named_phases

    return []


def build_4ch_kinetic(src: PathLike, dst: PathLike) -> int:
    """Build 4-channel kinetic nnUNet input from per-phase NIfTI files.

    For each ``src/<case>/*.nii.gz`` group of DCE phases, writes::

        dst/<case>_0000.nii.gz   P0    (pre-contrast)
        dst/<case>_0001.nii.gz   P1    (first post-contrast)
        dst/<case>_0002.nii.gz   d_early = P1 - P0
        dst/<case>_0003.nii.gz   d_late  = P_last - P1

    Returns the number of cases successfully prepared.
    """
    src, dst = Path(src), Path(dst)
    dst.mkdir(parents=True, exist_ok=True)

    ok = 0
    for case_dir in sorted(p for p in src.iterdir() if p.is_dir()):
        cid = case_dir.name
        phases = _gather_dce_phases(case_dir)
        if len(phases) < 3:
            print(f"  [skip] {cid}: only {len(phases)} DCE phase(s) detected")
            continue

        p0_img = nib.load(phases[0][1])
        p0 = p0_img.get_fdata(dtype=np.float32)
        p1 = nib.load(phases[1][1]).get_fdata(dtype=np.float32)
        p_last = nib.load(phases[-1][1]).get_fdata(dtype=np.float32)

        if p1.shape != p0.shape or p_last.shape != p0.shape:
            print(f"  [skip] {cid}: phase shape mismatch")
            continue

        channels = [p0, p1, p1 - p0, p_last - p1]
        aff, hdr = p0_img.affine, p0_img.header
        for ch_idx, arr in enumerate(channels):
            out = dst / f"{cid}_{ch_idx:04d}.nii.gz"
            nib.save(nib.Nifti1Image(arr, aff, hdr), str(out))
        ok += 1

    return ok

"""Unit tests for breast_mri_segmentator.io.

We test the three phase-detection heuristics on synthetic NIfTI fixtures so
that CI does not need any real DICOM or GPU.
"""
from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from breast_mri_segmentator.io import _gather_dce_phases, build_4ch_kinetic


def _write_dummy_nifti(path: Path, shape=(8, 8, 8), value: float = 0.0) -> None:
    """Write a tiny constant-valued NIfTI volume."""
    arr = np.full(shape, value, dtype=np.float32)
    img = nib.Nifti1Image(arr, affine=np.eye(4))
    nib.save(img, str(path))


# -----------------------------------------------------------------------------
# _gather_dce_phases — TTC pattern (Siemens TWIST-VIBE)
# -----------------------------------------------------------------------------
def test_gather_ttc_pattern(tmp_path):
    case = tmp_path / "case01"
    case.mkdir()
    # Four DCE phases with TTC=XX.Xs in the filename, plus distractors
    _write_dummy_nifti(case / "12_t1_vibe_TTC=18.4s_W.nii.gz", value=18.4)
    _write_dummy_nifti(case / "34_t1_vibe_TTC=118.1s_W.nii.gz", value=118.1)
    _write_dummy_nifti(case / "48_t1_vibe_TTC=181.6s_W.nii.gz", value=181.6)
    _write_dummy_nifti(case / "82_t1_vibe_TTC=335.8s_W.nii.gz", value=335.8)
    _write_dummy_nifti(case / "3_tirm_tra.nii.gz", value=999)  # distractor

    phases = _gather_dce_phases(case)
    assert len(phases) == 4
    times = [t for t, _ in phases]
    assert times == sorted(times)
    assert times == [18.4, 118.1, 181.6, 335.8]


# -----------------------------------------------------------------------------
# _gather_dce_phases — dynaVIEWS pattern (no TTC, sort by series number)
# -----------------------------------------------------------------------------
def test_gather_dynaviews_pattern(tmp_path):
    case = tmp_path / "case02"
    case.mkdir()
    _write_dummy_nifti(case / "9_t1_fl3d_tra_dynaVIEWS_spair_1+9.nii.gz")
    _write_dummy_nifti(case / "10_t1_fl3d_tra_dynaVIEWS_spair_1+9.nii.gz")
    _write_dummy_nifti(case / "16_t1_fl3d_tra_dynaVIEWS_spair_1+9.nii.gz")
    _write_dummy_nifti(case / "24_t1_fl3d_tra_dynaVIEWS_spair_1+9.nii.gz")
    _write_dummy_nifti(case / "3_tirm_tra.nii.gz")  # distractor (no dynaviews keyword)

    phases = _gather_dce_phases(case)
    assert len(phases) == 4
    series = [t for t, _ in phases]
    assert series == [9.0, 10.0, 16.0, 24.0]


# -----------------------------------------------------------------------------
# _gather_dce_phases — generic phaseN naming (our canonical convention)
# -----------------------------------------------------------------------------
def test_gather_generic_phase_naming(tmp_path):
    case = tmp_path / "case03"
    case.mkdir()
    for ph in range(5):
        _write_dummy_nifti(case / f"case03_phase{ph}.nii.gz", value=ph)

    phases = _gather_dce_phases(case)
    assert len(phases) == 5
    ordinals = [t for t, _ in phases]
    assert ordinals == [0.0, 1.0, 2.0, 3.0, 4.0]


# -----------------------------------------------------------------------------
# _gather_dce_phases — degenerate case (no DCE files)
# -----------------------------------------------------------------------------
def test_gather_no_phases(tmp_path):
    case = tmp_path / "case04"
    case.mkdir()
    _write_dummy_nifti(case / "3_tirm_tra.nii.gz")
    _write_dummy_nifti(case / "4_ep2d_diff_ADC.nii.gz")

    phases = _gather_dce_phases(case)
    assert phases == []


# -----------------------------------------------------------------------------
# build_4ch_kinetic — end-to-end channel synthesis
# -----------------------------------------------------------------------------
def test_build_4ch_kinetic_writes_expected_channels(tmp_path):
    src = tmp_path / "nifti_root"
    src.mkdir()
    case = src / "case_demo"
    case.mkdir()

    # 4 phases of distinct constant values so we can verify channel arithmetic
    _write_dummy_nifti(case / "case_demo_phase0.nii.gz", value=10.0)
    _write_dummy_nifti(case / "case_demo_phase1.nii.gz", value=30.0)
    _write_dummy_nifti(case / "case_demo_phase2.nii.gz", value=25.0)
    _write_dummy_nifti(case / "case_demo_phase3.nii.gz", value=20.0)

    dst = tmp_path / "kinetic_4ch"
    n = build_4ch_kinetic(src, dst)
    assert n == 1

    # All four channel files must exist
    for ch in range(4):
        out = dst / f"case_demo_{ch:04d}.nii.gz"
        assert out.exists(), f"missing channel {ch}"

    p0 = nib.load(dst / "case_demo_0000.nii.gz").get_fdata()
    p1 = nib.load(dst / "case_demo_0001.nii.gz").get_fdata()
    d_early = nib.load(dst / "case_demo_0002.nii.gz").get_fdata()
    d_late = nib.load(dst / "case_demo_0003.nii.gz").get_fdata()

    assert np.allclose(p0, 10.0)
    assert np.allclose(p1, 30.0)
    assert np.allclose(d_early, 30.0 - 10.0)   # P1 - P0
    assert np.allclose(d_late, 20.0 - 30.0)    # P_last - P1


def test_build_4ch_kinetic_skips_shape_mismatch(tmp_path, capsys):
    src = tmp_path / "nifti_root"
    src.mkdir()
    case = src / "case_bad"
    case.mkdir()
    _write_dummy_nifti(case / "case_bad_phase0.nii.gz", shape=(8, 8, 8))
    _write_dummy_nifti(case / "case_bad_phase1.nii.gz", shape=(8, 8, 10))
    _write_dummy_nifti(case / "case_bad_phase4.nii.gz", shape=(8, 8, 10))

    dst = tmp_path / "kinetic_4ch"
    n = build_4ch_kinetic(src, dst)
    captured = capsys.readouterr()
    assert n == 0
    assert "shape mismatch" in captured.out

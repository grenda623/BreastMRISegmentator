# Usage Guide

BreastMRISegmentator accepts DCE-MRI in several input layouts. This page walks through each one.

The trained model (Exp4x) expects a **4-channel kinetic input**:

| Channel | Content | Meaning |
|---|---|---|
| `_0000` | P0 | Pre-contrast |
| `_0001` | P1 | First post-contrast |
| `_0002` | P1 − P0 | Early uptake (`d_early`) |
| `_0003` | P_last − P1 | Wash-out (`d_late`) |

Output labels: `0 = background, 1 = breast, 2 = FGT, 3 = tumor`.

---

## Layout A — DICOM root

Best when you have raw DICOM series straight from PACS.

```
my_dicom/
├── patient_001/
│   ├── series_pre/
│   │   └── *.dcm
│   ├── series_post1/
│   └── ...
└── patient_002/
    └── ...
```

```bash
breast-mri-segment -i my_dicom/ -o predictions/ --from-dicom
```

Under the hood: `dcm2niix -z y -f '%s_%d'` converts every series to NIfTI, then the next step picks phases automatically.

---

## Layout B — Per-phase NIfTI

If your data is already in NIfTI and follows the canonical `<case>_phase{N}.nii.gz` naming:

```
nifti_root/
├── patient_001/
│   ├── patient_001_phase0.nii.gz
│   ├── patient_001_phase1.nii.gz
│   ├── patient_001_phase2.nii.gz
│   ├── patient_001_phase3.nii.gz
│   └── patient_001_phase4.nii.gz
└── patient_002/
    └── ...
```

```bash
breast-mri-segment -i nifti_root/ -o predictions/
```

If you have only 3 phases (P0, P1, P2), `P_last = P2` is used for `d_late`.

---

## Layout C — dcm2niix output with TTC timestamps

Some Siemens TWIST-VIBE / dynaVIEWS protocols embed acquisition timing in series descriptions. The package recognises them automatically:

| Detected pattern | What we do |
|---|---|
| `..._TTC=18.4s_W.nii.gz` | Sort by the embedded time, oldest = P0 |
| `..._dynaVIEWS_spair_...nii.gz` | Sort by series number prefix (`12_`, `34_`, …) |
| `<case>_phase{N}.nii.gz` | Sort by ordinal N |

If none of the three patterns match, the case is skipped with a `[skip]` message rather than failing the run.

---

## Layout D — Already-built 4-channel kinetic

If you have already constructed the 4-channel kinetic input yourself (e.g. for reproducing thesis results), point the CLI at it directly with `--skip-build` (not yet implemented; for now use the Python API):

```python
from pathlib import Path
import subprocess, os

os.environ["nnUNet_results"] = "/path/to/cached/weights"
os.environ["nnUNet_raw"] = "/tmp/nnUNet_raw"
os.environ["nnUNet_preprocessed"] = "/tmp/nnUNet_preprocessed"

subprocess.run([
    "nnUNetv2_predict",
    "-i", "my_4ch_input/",
    "-o", "predictions/",
    "-d", "932", "-c", "3d_fullres",
    "-tr", "nnUNetTrainer", "-p", "nnUNetPlans",
    "-f", "0", "--disable_tta",
], check=True)
```

---

## CLI reference

```text
breast-mri-segment -i INPUT -o OUTPUT [--from-dicom]
                                      [--weights WEIGHTS]
                                      [--tta]
                                      [--fold N]
```

| Flag | Default | Meaning |
|---|---|---|
| `-i / --input` | (required) | Input directory (DICOM cases or per-phase NIfTI). |
| `-o / --output` | (required) | Output directory for predictions. |
| `--from-dicom` | off | Treat `--input` as DICOM and convert first. |
| `--weights` | auto-download from Zenodo | Local path to the weights root. |
| `--tta` | off | Enable nnUNet test-time augmentation. ~8× slower. |
| `--fold` | `0` | Trained fold to load. The deployed Exp4x is fold 0 only. |

---

## Hardware

| | Minimum | Recommended |
|---|---|---|
| GPU VRAM | 6 GB | 12 GB+ |
| RAM | 16 GB | 32 GB |
| Disk | 5 GB for weights + cache | 50 GB+ if running on many cases |

CPU-only inference works but each volume can take 5–10 minutes (vs. <30 s on GPU with TTA disabled).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `dcm2niix not found on PATH` | Missing converter | `pip install dcm2niix` |
| `phase shape mismatch` skip messages | Vibe high-res pre + dynaVIEWS post mix | Use Layout B with already-aligned NIfTI, or pre-resample |
| Empty tumor predictions on mid-treatment scans | Out-of-distribution input | Expected — the model was trained on baseline (T0) acquisitions only |
| `Background workers died` | nnUNet preprocess OOM | Reduce CPU threads via `nnUNet_n_proc_DA=2` or run on a machine with more RAM |
| Hash mismatch from Zenodo | Corrupted download | Delete `~/.cache/breast_mri_segmentator/exp4x_for_maia.tar.gz` and re-run |

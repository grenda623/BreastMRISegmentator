# BreastMRISegmentator

Open-source automated segmentation of breast, fibroglandular tissue (FGT), and tumor on dynamic contrast-enhanced MRI (DCE-MRI).

The package wraps a pre-trained 3D nnU-Net model (Exp4x) that takes a 4-channel kinetic input — `P0, P1, P1−P0, P4−P1` — and produces a 3-label segmentation in a single command. Trained on 1,280 multi-centre cases (Duke + MAMA-MIA: I-SPY1 / I-SPY2 / NACT / DUKE) and validated on six external cohorts (mean Tumor Dice 0.78).

> **Status**: pre-release, repository scaffold. Weights are hosted on Zenodo (record pending) and downloaded on first use. See `release_plan.md` for the rollout checklist.

---

## Installation

```bash
pip install breast-mri-segmentator
```

Or from source:

```bash
git clone https://github.com/grenda623/BreastMRISegmentator.git
cd BreastMRISegmentator
pip install -e .
```

Dependencies (installed automatically): `nnunetv2`, `nibabel`, `numpy`, `dcm2niix`.

A working CUDA-capable GPU is recommended (~6 GB VRAM minimum for 3D fullres inference).

---

## Quick start

### A. From DICOM directory

```bash
breast-mri-segment -i /path/to/dicom_root -o /path/to/predictions --from-dicom
```

`/path/to/dicom_root` is expected to contain one subdirectory per case, each holding the case's DCE series.

### B. From per-phase NIfTI

If your DCE phases are already in NIfTI (one file per phase per case), arrange them as:

```
nifti_root/
├── case001/
│   ├── case001_phase0.nii.gz   # pre-contrast
│   ├── case001_phase1.nii.gz   # first post-contrast
│   ├── case001_phase2.nii.gz
│   ├── case001_phase3.nii.gz
│   └── case001_phase4.nii.gz   # late post-contrast
└── case002/
    └── ...
```

Then:

```bash
breast-mri-segment -i nifti_root/ -o predictions/
```

### C. Python API

```python
from breast_mri_segmentator import segment

segment(
    input_dir="my_dicom_root/",
    output_dir="my_predictions/",
    from_dicom=True,
)
```

### Output

Each input case yields one volume in the output directory:

```
predictions/case001.nii.gz   # voxel labels: 0=bg, 1=breast, 2=FGT, 3=tumor
```

---

## Performance

External-cohort Tumor Dice (mean) reported in our companion paper:

| Cohort | N | Tumor Dice |
|---|---|---|
| MAMAMIA ISPY1 test | 67 | 0.77 |
| MAMAMIA ISPY2 test | 131 | 0.83 |
| MAMAMIA NACT test  | 17 | 0.78 |
| Yunnan             | 55 | 0.82 |
| BMMR2 (v2 GT)      | 69 | 0.77 |
| French (multi-protocol) | 56 | 0.72 |
| **6-cohort mean**  |    | **0.78** |

Full benchmarks and ablations are in [`docs/results.md`](docs/results.md).

---

## Repository layout

```
BreastMRISegmentator/
├── breast_mri_segmentator/   Python package
│   ├── __init__.py
│   ├── api.py                segment() entry point
│   ├── cli.py                breast-mri-segment CLI
│   ├── io.py                 DICOM → NIfTI + 4-channel kinetic build
│   └── weights.py            Zenodo download / cache
├── scripts/                  Helper scripts (inference wrapper)
├── examples/                 Example pipelines (demo notebook)
├── tests/                    Unit tests (io, cli, weights)
├── slicer_extension/         3D Slicer extension (Phase 2 scaffold)
├── docs/                     Usage, results, training, citation
├── .github/workflows/        CI (ruff + pytest)
├── CITATION.cff              Machine-readable citation
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── pyproject.toml
├── LICENSE
├── README.md
└── release_plan.md
```

---

## Citation

If you use BreastMRISegmentator in your research, please cite (preprint pending):

```bibtex
@article{guo2026breastmrisegmentator,
  title   = {{BreastMRISegmentator}: an open-source deep learning framework for multi-structure segmentation in breast DCE-MRI},
  author  = {Guo, Renda and Moreno, Rodrigo and others},
  year    = {2026},
  journal = {(preprint)},
}
```

---

## Documentation

| Doc | Contents |
|---|---|
| [`docs/usage.md`](docs/usage.md) | All input layouts (DICOM, per-phase NIfTI, TTC/dynaVIEWS, raw 4-channel) and the CLI reference. |
| [`docs/results.md`](docs/results.md) | Cross-cohort benchmark tables and known failure modes. |
| [`docs/training.md`](docs/training.md) | How the Exp4x model was trained and its intended scope. |
| [`docs/zenodo_upload.md`](docs/zenodo_upload.md) | Operator checklist for depositing the weights on Zenodo and wiring in the DOI. |
| [`docs/owner_release_todo.md`](docs/owner_release_todo.md) | Owner-only release action items (accounts, GPU, supervisor sign-off). |
| [`examples/run_on_public_demo_case.ipynb`](examples/run_on_public_demo_case.ipynb) | End-to-end notebook on a synthetic demo case. |
| [`release_plan.md`](release_plan.md) | GitHub + Zenodo + 3D Slicer rollout checklist. |

---

## Acknowledgements

Model training was carried out on the Berzelius cluster (National Supercomputer
Centre, Linköping University) and the MAIA server. We thank the providers of the
public and institutional cohorts used for training and evaluation — Duke Breast
Cancer MRI, the MAMA-MIA collection (I-SPY1 / I-SPY2 / NACT / DUKE), BMMR2
(ACRIN-6698), and the Yunnan and French multi-protocol cohorts.

---

## License

Code: Apache 2.0 (see `LICENSE`).
Pre-trained weights: CC-BY 4.0 (deposited on Zenodo).

This tool is for research use only and is **not** a medical device. It must not be used for clinical decision-making.

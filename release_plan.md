# Release Plan — BreastMRISegmentator v0.1.0

This document describes the rollout for the first public release of **BreastMRISegmentator**, mirroring the pattern used by [DentalSegmentator](https://github.com/gaudot/SlicerDentalSegmentator) (Dot et al., *Journal of Dentistry* 2024).

| Component | Where | Status |
|---|---|---|
| Source code (CLI + Python API) | GitHub (`BreastMRISegmentator`) | ✅ Scaffold complete in this repo (not yet pushed to GitHub) |
| Pre-trained weights (Exp4x, ~220 MB) | **Zenodo** (DOI to be minted) | ☐ Pending upload |
| Clinical / interactive UI | **3D Slicer extension** (`SlicerBreastMRISegmentator`) | ◐ Phase 2 — scaffold in `slicer_extension/` (not validated in Slicer; not in v0.1.0) |
| Package distribution | **PyPI** (`pip install breast-mri-segmentator`) | ☐ Pending account verification |

---

## 1. Pre-release checklist

- [x] Python package skeleton (`breast_mri_segmentator/`)
- [x] CLI (`breast-mri-segment`)
- [x] `pyproject.toml` with declared dependencies
- [x] `README.md`, `LICENSE` (Apache 2.0), `.gitignore`, `CHANGELOG.md`
- [x] `release_plan.md`
- [x] Unit tests covering the IO heuristics (`tests/test_io.py`) — 6 tests, all passing
- [x] One end-to-end example notebook (`examples/run_on_public_demo_case.ipynb`)
- [x] `docs/usage.md` with the four input layouts we support
- [x] Reference results table copied from thesis (mean Tumor Dice on 6 cohorts) — `docs/results.md`
- [x] CI: GitHub Actions running `ruff` + `pytest` on linux + macOS (`.github/workflows/test.yml`)
- [ ] One smoke-test run of `breast-mri-segment` on a single demo case (needs GPU + Zenodo weights)
- [ ] Final cross-platform install test (`pip install -e .` on macOS + Linux)

---

## 2. Weights release (Zenodo)

DentalSegmentator deposited the trained nnU-Net model on Zenodo and cited it via DOI. We do the same.

> **Hands-on, command-level steps:** see [`docs/zenodo_upload.md`](docs/zenodo_upload.md). The section below is the rationale + metadata reference.

### 2.1 What to upload
A single tarball containing only Exp4x assets:

```
exp4x_for_maia.tar.gz
└── exp4x_for_maia/Dataset932/
    ├── dataset.json
    ├── dataset_fingerprint.json
    └── nnUNetTrainer__nnUNetPlans__3d_fullres/
        ├── dataset.json
        ├── plans.json
        ├── dataset_fingerprint.json
        └── fold_0/
            └── checkpoint_final.pth
```

The same archive already exists at `~/renda/weights/exp4x_for_maia.tar.gz` on MAIA (219 MB).

### 2.2 Steps

- [ ] **1.** Create an account at https://zenodo.org and link ORCID.
- [ ] **2.** *New upload* → drop in `exp4x_for_maia.tar.gz`.
- [ ] **3.** Metadata to fill:
   - [ ] **Resource type**: *Software / model*.
   - [ ] **Title**: `Pre-trained nnU-Net weights for BreastMRISegmentator (Exp4x)`.
   - [ ] **Authors**: Renda Guo (ORCID), Rodrigo Moreno (ORCID), …
   - [ ] **Description**: 1-paragraph summary — model, training pool, 6-cohort Dice, intended use, **not for clinical use**.
   - [ ] **Keywords**: breast MRI, DCE-MRI, segmentation, nnU-Net, deep learning, multi-centre.
   - [ ] **License**: CC-BY-4.0 (mirrors Dot et al.).
   - [ ] **Related identifiers**: link to the GitHub repo (`isSupplementTo`).
   - [ ] **Funding** if applicable (KTH BMIP, supervisor's grant).
- [ ] **4.** *Reserve DOI*, copy it into `breast_mri_segmentator/weights.py` (`ZENODO_RECORD = "..."`).
- [ ] **5.** Compute the SHA256 of the tarball and paste it into `weights.py` (`SHA256_HASH = "..."`):
   ```bash
   shasum -a 256 exp4x_for_maia.tar.gz
   ```
- [ ] **6.** *Publish* on Zenodo. (Note: published versions are immutable — bug fixes require a new version + new DOI.)
- [ ] **7.** Update `README.md` / `pyproject.toml` to link the actual DOI URL.

### 2.3 Versioning

Use the same record's *new version* feature for retraining or fold updates. Increment `breast_mri_segmentator.__version__` and update `CHANGELOG.md` in lock-step.

---

## 3. Source release (GitHub)

DentalSegmentator's repo (`gaudot/SlicerDentalSegmentator`) hosts both the Slicer extension and the pre-training code. We host the Python package now; the Slicer extension lives in a parallel repo when ready.

### 3.1 Repository creation

- [ ] **1.** New repo `USER/BreastMRISegmentator`, public, MIT/Apache 2.0 (already set).
- [ ] **2.** Push the contents of `Degree Project/BreastMRISegmentator/`.
- [x] **3.** Add a `CITATION.cff` (added; ORCID list + paper DOI still to fill once minted).
- [x] **4.** Add a `CODE_OF_CONDUCT.md` (Contributor Covenant).
- [x] **5.** Add a one-paragraph "Acknowledgements" section pointing to Berzelius (NSC), MAIA, and the data providers (Duke, MAMA-MIA, BMMR2, …) — in `README.md`.
- [ ] **6.** Pin a release tag `v0.1.0` once Zenodo DOI lands.

### 3.2 GitHub Actions (CI)

- [x] Add the workflow as `.github/workflows/test.yml` (installs lightweight test deps only — `nibabel numpy pytest ruff` — since CI runs no GPU inference):

```yaml
# .github/workflows/test.yml
name: tests
on: [push, pull_request]
jobs:
  pytest:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python: ["3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install -e .[dev]
      - run: pytest -q
```

CI does **not** run nnUNet inference (no GPU on runners); tests cover IO heuristics, manifest parsing, and CLI argparse only.

### 3.3 GitHub release

- [ ] **1.** Tag `v0.1.0`.
- [ ] **2.** *Draft new release*; auto-generate changelog.
- [ ] **3.** Attach a slim asset (`weights_pointer.txt`) that contains the Zenodo DOI — do **not** attach the actual weights here (Zenodo is the canonical store).

---

## 4. PyPI

DentalSegmentator did **not** publish to PyPI (their tool is delivered through 3D Slicer). We do publish so non-Slicer users can `pip install` straight away.

- [ ] **1.** Register `breast-mri-segmentator` on https://pypi.org (after sanity-checking the name is free).
- [ ] **2.** Use [API tokens](https://pypi.org/help/#apitoken) + `twine`, not username/password:
   ```bash
   python -m build
   twine check dist/*
   twine upload dist/*
   ```
- [ ] **3.** Mark v0.1.0 as a **release candidate** (`0.1.0rc1`) first; promote to `0.1.0` after at least one external installation test.

---

## 5. 3D Slicer extension (phase 2)

Dot et al. shipped a Slicer extension under the Slicer Extension Manager. We follow the same template.

### 5.1 Why
A GUI greatly broadens the user base — radiologists rarely run a CLI. The Slicer ecosystem provides DICOM loaders, visualisation, segment editing, and DICOMweb querying for free.

### 5.2 Approach

- [~] **1.** ~~Fork~~ — instead of forking, scaffolded a fresh module in `slicer_extension/` mirroring DentalSegmentator's structure (CMake + ScriptedModule + Lib). See `slicer_extension/README.md`.
- [~] **2.** Inference call: rather than depend on the `NNUNet` Slicer extension (single-channel), the module **delegates to the `breast-mri-segmentator` pip package**, which builds the 4-channel kinetic input and runs nnUNetv2_predict. Stub in `BreastMRISegmentatorLib/SegmentationWidget.py` (needs live-Slicer validation).
- [x] **3.** Label colormap set (1 = breast `#4FB0C6`, 2 = FGT `#E6B84F`, 3 = tumor `#D8654F`) in `BreastMRISegmentatorLib/Utils.py`.
- [ ] **4.** Update README + screenshots — extension README drafted; **screenshots/icons still TODO** (placeholders only).
- [~] **5.** `SlicerBreastMRISegmentator.s4ext` written (USER/commit placeholders); submit to the [Slicer Extension Index](https://github.com/Slicer/ExtensionsIndex) once the standalone repo exists.
- [ ] **6.** Versioning of the Slicer extension is decoupled from the Python package; tie each release to a Slicer-bundled nnU-Net version.

> **Open question #3 resolved:** full pipeline in the GUI, with the
> `breast-mri-segmentator` package as the inference engine (not a thin CLI
> shell, not a reimplementation). DentalSegmentator's single-channel pattern
> does not transfer because Exp4x needs a 4-channel kinetic input.

Effort estimate: ~2 weeks of focused work after v0.1.0. The scaffold is done;
remaining effort is live-Slicer validation, async inference, assets, and the
standalone-repo + Extensions-Index submission.

---

## 6. Documentation set

| File | Purpose | Status |
|---|---|---|
| `README.md` | Marketing entry, install + quickstart. | ✅ |
| `release_plan.md` | This file. | ✅ |
| `CHANGELOG.md` | Version history. | ✅ |
| `docs/usage.md` | All input layouts (DICOM, per-phase NIfTI, raw 5-channel, raw 4-channel). | ✅ |
| `docs/results.md` | Cross-cohort benchmark table (copied from `results_comparison.md`). | ✅ |
| `docs/training.md` | How we trained Exp4x: dataset construction, 1,280-case label fusion, SLURM scripts. Links to `Code/` repo for fully reproducible scripts. | ✅ |
| `docs/citation.bib` | BibTeX entries for the package and the underlying paper. | ✅ (DOIs pending) |
| `CITATION.cff` | Machine-readable citation. | ✅ (ORCID/DOI pending) |

---

## 7. Open questions (need supervisor input)

- [ ] **1. Co-authorship & ORCID list** on Zenodo / CITATION.cff — need supervisor confirmation before minting the DOI.
- [ ] **2. Paper status** — release v0.1.0 simultaneously with paper acceptance, or push as pre-release now and tag stable on acceptance?
- [ ] **3. Slicer extension scope** — full pipeline (DICOM → segmentation) or thin wrapper that delegates everything to the Python CLI?
- [ ] **4. Funding / acknowledgements** statement wording for Zenodo description.
- [ ] **5. Data availability** — only weights are shipped; no training data. Confirm with each cohort PI that this is sufficient (Duke / MAMA-MIA are public; Yunnan / French / BMMR2 v2 may have restrictions on derived assets).

---

## 8. Release-day checklist

- [ ] Tarball uploaded to Zenodo, DOI minted.
- [ ] `weights.py` updated with real `ZENODO_RECORD` + `SHA256_HASH`.
- [ ] GitHub tag `v0.1.0` pushed.
- [ ] PyPI upload (`twine upload`).
- [ ] `pip install breast-mri-segmentator` in a fresh conda env on (a) Linux box and (b) MAIA — both must reach "Done" on a 1-case demo.
- [ ] Announcement: short post in the MAMA-MIA discussion forum + DentalSegmentator-style Twitter/X thread.
- [ ] `BreastMRISegmentator` linked from the paper's *Code availability* section.

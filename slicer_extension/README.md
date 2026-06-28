# SlicerBreastMRISegmentator (Phase 2 — scaffold)

A 3D Slicer extension that runs **BreastMRISegmentator** (breast / FGT / tumor
segmentation on DCE-MRI) from a GUI, modelled on
[SlicerDentalSegmentator](https://github.com/gaudot/SlicerDentalSegmentator)
(Dot et al., *Journal of Dentistry* 2024).

> **Status: scaffold.** None of this has been run inside 3D Slicer yet. Every
> file marked `SCAFFOLD` / `TODO` needs validation against a live Slicer build
> (>= 5.8.0) and a GPU. This directory exists so Phase 2 can start from a
> working skeleton; it is **not** part of the v0.1.0 Python release and will
> eventually move to its own repo (`SlicerBreastMRISegmentator`).

## How it differs from DentalSegmentator

DentalSegmentator feeds a **single CT volume** to a single-channel nnU-Net. Our
Exp4x model needs a **4-channel kinetic input** (P0, P1, P1−P0, P_last−P1) built
from several DCE phases. So instead of depending on the `NNUNet` Slicer
extension (single-channel), this extension **delegates inference to the
`breast-mri-segmentator` pip package**, which already builds the kinetic
channels and runs `nnUNetv2_predict` (Dataset932, fold 0). Weights are fetched
from Zenodo on first use by that package.

This also settles release_plan §7 open question #3: **full pipeline in the GUI,
package as the engine** (not a thin CLI shell, not a reimplementation).

## Pipeline

1. User selects ≥3 DCE phase volumes in acquisition order (pre + post-contrast).
2. Widget exports them to a temp dir as `case/case_phaseN.nii.gz` ("Layout B").
3. Logic calls `breast_mri_segmentator.api.segment(...)`.
4. Output label volume is loaded back; 3 segments are named/colored
   (1 = Breast `#4FB0C6`, 2 = FGT `#E6B84F`, 3 = Tumor `#D8654F`).

## Layout

```
slicer_extension/
├── CMakeLists.txt                       Top-level extension (meta + add_subdirectory)
├── SlicerBreastMRISegmentator.s4ext     Extensions-Index description file
├── README.md                            This file
└── BreastMRISegmentator/
    ├── CMakeLists.txt                    slicerMacroBuildScriptedModule
    ├── BreastMRISegmentator.py           Module metadata + widget delegation
    ├── BreastMRISegmentatorLib/
    │   ├── __init__.py
    │   ├── SegmentationWidget.py          GUI + SegmentationLogic (the core)
    │   ├── PythonDependencyChecker.py     pip-install breast-mri-segmentator
    │   ├── Signal.py                      tiny observer helper
    │   ├── IconPath.py                    icon resource resolver
    │   └── Utils.py                       label palette + node<->NIfTI IO
    ├── Testing/
    │   ├── IntegrationTestCase.py          fast (mocked) + slow (end-to-end) tests
    │   ├── Utils.py                        base case + synthetic phase fixtures
    │   └── conftest.py                     registers the `slow` marker
    └── Resources/Icons/                   (placeholder — add real artwork)
```

## Remaining work (Phase 2 TODO)

- [ ] Create the icon/screenshot assets under `Resources/Icons/` + `Screenshots/`.
- [ ] Run inference in a background process (`slicer.modules.processes` / QProcess)
      so the UI stays responsive; current code runs it synchronously.
- [ ] Validate node ↔ NIfTI export/import orientation (RAS/LPS) against Slicer.
- [ ] Verify the label-value → segment-id mapping in `_styleSegments`.
- [ ] Confirm the torch/CUDA install path via `light-the-torch` inside Slicer.
- [~] `Testing/` scaffold added (`IntegrationTestCase.py` + `Utils.py` + `conftest.py`):
      fast dependency/layout tests (mock `segment`, Slicer-only) and a
      `@pytest.mark.slow` end-to-end case (needs GPU + weights). **Not yet run
      inside Slicer.**
- [ ] Move to a standalone repo and submit the `.s4ext` to the
      [Slicer Extensions Index](https://github.com/Slicer/ExtensionsIndex).

## Research use only

Not a medical device. Must not be used for clinical decision-making.

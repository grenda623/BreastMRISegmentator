# Changelog

All notable changes to BreastMRISegmentator are documented in this file. Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial Python package scaffold (`breast_mri_segmentator/`).
- CLI entry point `breast-mri-segment`.
- DICOM→NIfTI conversion via `dcm2niix`.
- 4-channel kinetic input builder (`P0, P1, P1−P0, P_last−P1`) with three filename heuristics (TTC, dynaVIEWS, generic `phaseN`).
- Zenodo weights downloader (placeholder DOI; record ID to be filled at release).
- `release_plan.md` covering the GitHub + Zenodo + 3D Slicer rollout.
- Apache 2.0 license, baseline `pyproject.toml`, `.gitignore`.
- Unit tests for the IO phase-detection heuristics and 4-channel kinetic builder (`tests/test_io.py`).
- Unit tests for the CLI argparse layer (`tests/test_cli.py`) and the Zenodo weights download/extract/verify flow (`tests/test_weights.py`), all network/inference mocked.
- Hardened tarball extraction in `weights.py` with the `data` filter (Python >= 3.12) to reject unsafe archive members.
- GitHub Actions CI running `ruff` + `pytest` on Linux and macOS (`.github/workflows/test.yml`).
- Usage, results, and training documentation (`docs/usage.md`, `docs/results.md`, `docs/training.md`).
- End-to-end example notebook on a synthetic demo case (`examples/run_on_public_demo_case.ipynb`).
- Machine-readable citation (`CITATION.cff`) and BibTeX entries (`docs/citation.bib`).
- Contributor Covenant `CODE_OF_CONDUCT.md`.
- 3D Slicer extension scaffold under `slicer_extension/` (Phase 2, not validated in Slicer): CMake build files, scripted module, GUI/logic skeleton delegating inference to the `breast-mri-segmentator` package, and a `.s4ext` index descriptor.
- Slicer extension test scaffold (`Testing/`): fast dependency/Layout-B tests with `segment` mocked, plus a `@pytest.mark.slow` end-to-end case; wired into the module self-test via SlicerPythonTestRunner.
- `scripts/run_inference.sh`: convenience wrapper around the `breast-mri-segment` CLI.
- `docs/zenodo_upload.md`: operator checklist for depositing the Exp4x weights on Zenodo and wiring the DOI back into the package.
- `ruff` and `pytest` configuration in `pyproject.toml` so local and CI runs are consistent.

### Changed
- Modernized type hints to PEP 604 syntax (`X | None`, `str | Path`).

## [0.1.0] - PENDING

First public alpha. Tracks the Exp4x model trained on 1,280 multi-centre cases.

# Owner Release TODO

Action items that **only the repository owner can do** (external accounts, GPU,
supervisor input). Everything code-side is done and CI is green; this is the
human-in-the-loop checklist to get from scaffold → published release.

Legend: 🔴 blocks release · 🟢 quick/parallel · 🖥️ needs GPU · 🧩 needs 3D Slicer

Priority order:

```
Part 0 (10 min)  →  Part 1 (ask supervisor — the real blocker)  →  Part 2 (Zenodo)
   →  send me record ID + SHA256 (I wire in the DOI)  →  Part 3 verify
   →  Part 5 tag v0.1.0  →  Part 6 PyPI
Part 4 / Part 7 need GPU / Slicer — parallel or later.
```

---

## Part 0 · Quick wins (browser, ~10 min) 🟢

- [ ] **Revoke the leaked token.** https://github.com/settings/tokens
      (fine-grained: https://github.com/settings/personal-access-tokens ).
      Delete the token that was pasted into chat. The new one with `workflow`
      scope stays.
- [ ] **Set repo Description + Topics.** Repo home → About (gear icon).
  - Description: `Open-source deep-learning toolkit for automatic breast, FGT & tumor segmentation on breast DCE-MRI (nnU-Net).`
  - Topics: `breast-mri dce-mri medical-imaging medical-image-segmentation segmentation tumor-segmentation nnunet deep-learning pytorch radiology`
- [x] **CI green.** https://github.com/grenda623/BreastMRISegmentator/actions
      (ruff + pytest on Linux/macOS × Py 3.10/3.11 — confirmed passing.)

## Part 1 · Supervisor sign-off 🔴

Zenodo deposits are **immutable once published**, so settle these first. Send
the supervisor these four questions:

- [ ] **Authors + ORCID list** — who is credited, in what order, with which ORCIDs
      (at minimum Renda Guo + Rodrigo Moreno). *Blocks the DOI.*
- [ ] **Funding / acknowledgement wording** — KTH BMIP / grant number phrasing.
- [ ] **Data availability** — confirm shipping weights only (no training data) is
      acceptable, especially for Yunnan / French / BMMR2 v2 derived assets.
- [ ] **Release timing** — publish v0.1.0 now, or pre-release now + stable on
      paper acceptance?

## Part 2 · Zenodo weights upload 🔴

Full command-level steps: [`zenodo_upload.md`](zenodo_upload.md). Summary:

- [ ] **Verify archive + compute hash** on MAIA (no GPU):
  ```bash
  cd ~/renda/weights
  tar tzf exp4x_for_maia.tar.gz | head -30     # top dir must be exp4x_for_maia/
  shasum -a 256 exp4x_for_maia.tar.gz          # copy this 64-char hash
  ```
  (If the tarball isn't on your Mac, `scp` it down first — ~220 MB.)
- [ ] Zenodo account + **link ORCID**.
- [ ] New upload → drop in `exp4x_for_maia.tar.gz`.
- [ ] Fill metadata (title/description/keywords/CC-BY-4.0/`isSupplementTo` →
      the GitHub repo) — templates in `zenodo_upload.md`.
- [ ] **Reserve DOI** → note the record ID (trailing number of
      `10.5281/zenodo.<ID>`).
- [ ] **Publish.**
- [ ] **Send me:** the record ID + the SHA256. I then wire the DOI into
      `weights.py`, `pyproject.toml`, `docs/citation.bib`, `CITATION.cff`,
      `README.md`, `CHANGELOG.md` (checklist §5) — **you don't edit code.**

## Part 3 · Verify weights download (no GPU, just network)

- [ ] After I wire in the DOI:
  ```bash
  export BREAST_MRI_SEG_CACHE="$(mktemp -d)"
  python -c "from breast_mri_segmentator.weights import ensure_weights; print(ensure_weights())"
  ```
  Success = prints the extracted path, no `SHA256 mismatch`.

## Part 4 · Real inference smoke test 🖥️ (recommended, not blocking)

- [ ] On a GPU box (MAIA/Berzelius), one real ≥3-phase DCE case:
  ```bash
  pip install -e .        # or pip install breast-mri-segmentator
  breast-mri-segment -i /path/to/one_case_nifti -o /tmp/pred
  # /tmp/pred/<case>.nii.gz labels should include 0/1/2/3 (bg/breast/FGT/tumor)
  ```
  Meets release_plan §8 "1-case demo reaches Done".

## Part 5 · Tag v0.1.0 (only after Parts 2–3) 🔴

- [ ] After DOI is wired in and download verified:
  ```bash
  git tag -a v0.1.0 -m "BreastMRISegmentator v0.1.0"
  git push origin v0.1.0
  ```
  Order matters: tagging before the DOI is live means installers can't fetch
  weights. (I can prepare the local tag; the push needs your credentials.)

## Part 6 · Publish to PyPI (no GPU, can be last)

- [ ] Check the name is free: https://pypi.org/project/breast-mri-segmentator/
- [ ] PyPI account → API token: https://pypi.org/manage/account/token/
- [ ] Build + upload:
  ```bash
  python -m pip install --upgrade build twine
  python -m build
  twine check dist/*
  twine upload dist/*     # username: __token__   password: pypi-...
  ```
- [ ] Recommended: ship `0.1.0rc1` first (bump `version` in `pyproject.toml` —
      I can do this), test-install, then promote to `0.1.0`.

## Part 7 · Slicer extension validation 🧩🖥️ (Phase 2, later)

- [ ] Load `slicer_extension/BreastMRISegmentator/` as a module in 3D Slicer ≥ 5.8.
- [ ] Run the fast tests (no GPU) in Slicer's Python console:
  ```
  pytest slicer_extension/BreastMRISegmentator/Testing -m "not slow"
  ```
- [ ] Clear the `SCAFFOLD/TODO` markers (async inference, RAS/LPS orientation,
      label↔segment mapping, torch/CUDA install path).
- [ ] Add icons + screenshots, move to a standalone repo, submit the `.s4ext`
      to the Slicer Extensions Index.

---

**The single real blocker is Part 1** (supervisor confirming the author/ORCID
list). Once that clears, Part 2 can proceed and I can take over most of the rest.

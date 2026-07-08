# Zenodo Weights Upload — Operator Checklist

Hands-on, command-level steps to deposit the **Exp4x** weights on Zenodo, mint a
DOI, and wire it back into the package. This is the operational companion to
`release_plan.md` §2 (which explains the *why*).

> Do this **before** tagging `v0.1.0` or publishing to PyPI — a released package
> whose `weights.py` still says `PENDING` cannot download weights.

---

## 0. Prerequisites

- [ ] A [Zenodo](https://zenodo.org) account, logged in.
- [ ] ORCID linked (Zenodo → *Account* → *Linked accounts*). Needed for the author metadata.
- [ ] The tarball on hand: `exp4x_for_maia.tar.gz` (~220 MB), at
      `~/renda/weights/exp4x_for_maia.tar.gz` on MAIA.
- [ ] Supervisor sign-off on the **author/ORCID list** (release_plan §7 #1) —
      the deposit is immutable once published.

### 0.1 Verify the archive before uploading

```bash
cd ~/renda/weights            # wherever the tarball is

# (a) Contents must match the expected layout (Dataset932 + fold_0 checkpoint).
tar tzf exp4x_for_maia.tar.gz | head -30

# (b) Compute the SHA256 — copy this value, you need it in step 6.
shasum -a 256 exp4x_for_maia.tar.gz     # macOS
# sha256sum exp4x_for_maia.tar.gz       # Linux
```

Expected top-level layout inside the tarball:

```
exp4x_for_maia/Dataset932/
├── dataset.json
├── dataset_fingerprint.json
└── nnUNetTrainer__nnUNetPlans__3d_fullres/
    ├── dataset.json
    ├── plans.json
    ├── dataset_fingerprint.json
    └── fold_0/checkpoint_final.pth
```

The top directory **must** be `exp4x_for_maia/` — the package extracts and then
looks for `WEIGHTS_ROOT_NAME = "exp4x_for_maia"`.

---

## 1. Create the deposit

- [ ] Zenodo → **New upload**.
- [ ] Drag in `exp4x_for_maia.tar.gz`. Wait for the upload to finish.

## 2. Fill the metadata

| Field | Value |
|---|---|
| **Resource type** | *Software* (or *Model* if offered) |
| **Title** | `Pre-trained nnU-Net weights for BreastMRISegmentator (Exp4x)` |
| **Authors** | Renda Guo (ORCID), Rodrigo Moreno (ORCID), … *(confirm list first)* |
| **Description** | See template below |
| **Keywords** | `breast MRI`, `DCE-MRI`, `segmentation`, `nnU-Net`, `deep learning`, `multi-centre` |
| **License** | **Creative Commons Attribution 4.0 (CC-BY-4.0)** |
| **Related/alternate identifiers** | `https://github.com/grenda623/BreastMRISegmentator` — relation **isSupplementTo** |
| **Funding** | KTH BMIP / supervisor's grant *(if applicable — confirm wording, release_plan §7 #4)* |

**Description template:**

> Pre-trained 3D nnU-Net weights (Exp4x) for the BreastMRISegmentator toolkit.
> The model segments breast, fibroglandular tissue (FGT), and tumor on
> dynamic contrast-enhanced breast MRI from a 4-channel kinetic input
> (P0, P1, P1−P0, P_last−P1). Trained on 1,280 multi-centre cases and validated
> on six external cohorts (mean Tumor Dice ≈ 0.78). **Research use only — not a
> medical device; not for clinical decision-making.** Code and usage:
> https://github.com/grenda623/BreastMRISegmentator

## 3. Reserve the DOI

- [ ] In the deposit, under *Digital Object Identifier*, click **Reserve DOI**.
- [ ] Note the reserved DOI, e.g. `10.5281/zenodo.1234567`.
      The trailing number (`1234567`) is your **record ID** → `ZENODO_RECORD`.

> Zenodo also mints a *concept DOI* (all versions) alongside the *version DOI*.
> For `weights.py` use the **version** record ID (the specific file you upload).
> Cite the concept DOI in papers when you want "latest version".

## 4. Publish

- [ ] Review everything (metadata is editable later, but the **files are not**).
- [ ] Click **Publish**.

---

## 5. Wire the DOI into the package

Edit these files (record ID and hash from steps 3 and 0.1):

### 5.1 `breast_mri_segmentator/weights.py`
```python
ZENODO_RECORD = "1234567"                 # <- reserved record ID
SHA256_HASH   = "<64-hex-from-shasum>"    # <- from step 0.1
```

### 5.2 `pyproject.toml`
```toml
"Weights (Zenodo)" = "https://doi.org/10.5281/zenodo.1234567"
```

### 5.3 `docs/citation.bib` — uncomment/fill the `doi` in `@software{...}`
```bibtex
  doi = {10.5281/zenodo.1234567},
```

### 5.4 `CITATION.cff` — add the weights DOI under `identifiers:` (optional but nice)
```yaml
identifiers:
  - type: doi
    value: "10.5281/zenodo.1234567"
    description: "Pre-trained Exp4x weights"
```

### 5.5 `README.md` — replace the "record pending" note with the real DOI/link.

### 5.6 `CHANGELOG.md` — note the DOI under `[Unreleased]`.

---

## 6. Verify the download works end-to-end

Point the cache at a throwaway dir and let the package fetch + verify the hash:

```bash
export BREAST_MRI_SEG_CACHE="$(mktemp -d)"
python -c "from breast_mri_segmentator.weights import ensure_weights; print(ensure_weights())"
ls -R "$BREAST_MRI_SEG_CACHE" | head
```

- A **SHA256 mismatch** error here means the hash in `weights.py` is wrong
  (re-copy from step 0.1) or the download is corrupt.
- If the URL 404s, confirm the download URL Zenodo actually serves
  (`https://zenodo.org/records/<ID>/files/exp4x_for_maia.tar.gz`) matches the
  `ZENODO_URL` template in `weights.py`; update the template if Zenodo changed
  the `record` vs `records` path form.

Then run the test suite (still all mocked, but confirms nothing broke):

```bash
pytest -q && ruff check breast_mri_segmentator tests
```

---

## 7. Commit, push, then tag

```bash
git add breast_mri_segmentator/weights.py pyproject.toml docs/citation.bib \
        CITATION.cff README.md CHANGELOG.md
git commit -m "Wire in Zenodo weights DOI 10.5281/zenodo.1234567"
git push origin main

# Only now is it safe to tag the release:
git tag -a v0.1.0 -m "BreastMRISegmentator v0.1.0"
git push origin v0.1.0
```

---

## 8. Notes on versioning

- Published Zenodo files are **immutable**. Bug-fixing the weights = Zenodo
  *New version* (new version DOI) + bump `breast_mri_segmentator.__version__`
  + update `CHANGELOG.md` in lock-step.
- Keep using the **same concept DOI** across versions in the paper's
  *Code/Data availability* section.

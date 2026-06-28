# Training Notes — Exp4x

This page documents how the deployed **Exp4x** checkpoint was trained, so that
the result is reproducible and the model's scope is clear. The package ships
only the trained weights; the full training/evaluation code lives in the
parent project's `Code/` repository.

> **Scope** — Exp4x is the default 3D nnU-Net configuration with a 4-channel
> kinetic input. It was selected because, once the input is fixed to 4-channel
> kinetic, the architecture has only a small effect on cross-domain Dice, and
> the default nnU-Net was the strongest single model
> (see [`results.md`](results.md) §3).

---

## 1. Model

| Item | Value |
|---|---|
| Framework | nnU-Net v2 |
| Configuration | `3d_fullres` |
| Trainer | `nnUNetTrainer` (default) |
| Plans | `nnUNetPlans` |
| Dataset id | `932` |
| Folds shipped | `fold_0` only |
| Input channels | 4 (kinetic) |
| Output labels | `0 = background, 1 = breast, 2 = FGT, 3 = tumor` |

The deployed archive (`exp4x_for_maia.tar.gz`, ~220 MB) contains
`dataset.json`, `plans.json`, `dataset_fingerprint.json`, and
`fold_0/checkpoint_final.pth`.

---

## 2. Input construction (4-channel kinetic)

Each case is reduced from its DCE series to four channels:

| Channel | Content | Meaning |
|---|---|---|
| `_0000` | P0 | Pre-contrast |
| `_0001` | P1 | First post-contrast |
| `_0002` | P1 − P0 | Early uptake (`d_early`) |
| `_0003` | P_last − P1 | Wash-out (`d_late`) |

This is exactly what `breast_mri_segmentator.io.build_4ch_kinetic` produces at
inference time, so train- and test-time inputs are identical.

---

## 3. Training pool

1,280 multi-centre cases pooled from public cohorts (baseline / T0 acquisitions
only):

| Source | Role |
|---|---|
| Duke Breast Cancer MRI | Training |
| MAMA-MIA: I-SPY1 | Training |
| MAMA-MIA: I-SPY2 | Training |
| MAMA-MIA: NACT | Training |
| MAMA-MIA: DUKE | Training |

Labels were produced by a label-fusion pipeline over the 1,280 cases (breast,
FGT, tumor). External cohorts (Yunnan, BMMR2 v2, French multi-protocol) were
held out entirely for evaluation and never seen during training — see
[`results.md`](results.md).

---

## 4. Reproducing training

The training is standard nnU-Net v2; nothing in the pipeline is bespoke beyond
the 4-channel kinetic input. At a high level:

```bash
# 1. Build the 4-channel kinetic dataset (Dataset932) — see Code/ repo.
# 2. Plan + preprocess.
nnUNetv2_plan_and_preprocess -d 932 --verify_dataset_integrity

# 3. Train fold 0 of the default 3d_fullres config.
nnUNetv2_train 932 3d_fullres 0
```

SLURM submission scripts (Berzelius / NSC) and the dataset-construction and
label-fusion code are kept in the parent `Code/` repository for full
reproducibility; they are not redistributed in this package because they depend
on cohort-specific raw data with access restrictions.

---

## 5. Intended use and limitations

- **Research use only.** Not a medical device; not for clinical decisions.
- Trained on **baseline (T0)** scans — expect degraded/empty tumor output on
  mid-treatment follow-up scans.
- Needs **≥3 DCE phases**; single-phase acquisitions are out of scope.

Known failure modes are enumerated in [`results.md`](results.md) §5.

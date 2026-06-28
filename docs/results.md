# Benchmark Results

Full evaluation of BreastMRISegmentator on six external cohorts spanning five institutions. All numbers in this page are derived from `Code/results/results_comparison.md` in the parent project; please cite the paper (preprint pending) when reporting them.

The deployed model packaged in this distribution is **Exp4x**: a default 3D nnUNet trained on a 1,280-case multi-centre pool with a 4-channel kinetic input (P0, P1, P1−P0, P4−P1).

---

## 1. Headline (Tumor Dice)

| Cohort | N | Tumor Dice (mean ± std) | Median |
|---|---|---|---|
| MAMA-MIA ISPY1 test | 67  | 0.7719 ± 0.1896 | — |
| MAMA-MIA ISPY2 test | 131 | 0.8326 ± 0.1475 | — |
| MAMA-MIA NACT test  | 17  | 0.7833 ± 0.1749 | — |
| Yunnan              | 55  | 0.8153 ± 0.1189 | — |
| BMMR2 (v2 GT)       | 69  | 0.7691 ± —      | — |
| French (multi-protocol) | 56 | 0.7230 ± 0.2302 | — |
| **6-cohort mean**   |     | **0.7825**      |   |

The 6-cohort mean (0.7825) is the best **single-model** cross-domain Tumor Dice we measured. Inference-time ensembles can push the per-cohort number up by 0.01–0.02 but do not change the ranking.

---

## 2. Internal validation (fold 0)

Held-out 5-fold-style validation on the 1,280-case training pool, fold 0.

| Class | Dice |
|---|---|
| Breast (label 1) | 0.967 |
| FGT (label 2)    | 0.887 |
| Tumor (label 3)  | 0.800 |
| **Foreground mean** | **0.885** |

---

## 3. Cross-domain ranking — all evaluated models

Reproduced verbatim from `results_comparison.md §12`. **Exp4x** is the one shipped in this package.

| Experiment | Description | 6-cohort mean Tumor Dice |
|---|---|---|
| **Exp4x** | default nnUNet, 4ch kinetic | **0.7825** |
| Exp6x | ME-KPINet + KinAug, 4ch | 0.7757 |
| Exp7x | ME-KPINet + Gated, 4ch  | 0.7757 |
| ADCSegNet | Dual-Conv + residual, 4ch — try | 0.7740 |
| Exp5x | ME-KPINet, 4ch | 0.7700 |
| Exp5bx | ME-KPINet + ResEnc, 4ch | 0.7666 |
| Exp1x | default nnUNet, 1ch P1 | 0.7647 |
| Exp9x | default nnUNet, 3ch (P0,P2,P2−P0) | 0.7450 |
| Exp8x | default nnUNet, 3ch (P0,P1,P1−P0) | 0.7344 |
| Exp2x | default nnUNet, 5ch raw | 0.7521 |
| Exp3x | ResEnc + AG + BaseBoost, 5ch | 0.7520 |
| WNet3D_S | two-stream W-shape (PoolFormer mixer) — try | 0.7559 |

> Practical takeaway: once the input is fixed to 4ch kinetic, the choice of architecture has small effect on cross-domain Dice. The default nnUNet (Exp4x) is the strongest single model. This is the reason the package ships only the Exp4x checkpoint.

---

## 4. Per-cohort details (Exp4x)

| Cohort | Acquisition | Why included |
|---|---|---|
| MAMA-MIA ISPY1 (test) | I-SPY1 clinical trial; varied scanners | Multi-centre held-out set |
| MAMA-MIA ISPY2 (test) | I-SPY2 / ACRIN-6698 | Largest single cohort |
| MAMA-MIA NACT (test) | NACT-Pilot | Small, hard cohort |
| Yunnan | Yunnan Cancer Hospital (China) | True international generalisation; 55/100 cases usable |
| BMMR2 (v2 GT) | ACRIN-6698 single-binary tumour annotation, mid-treatment T1 included | Public benchmark with cleaner GT |
| French (MAIA server) | 3 protocols (T1.DYN, dynaVIEWS, GE VIBRANT) | Multi-protocol stress test |

See `Code/results/list_skipped_cases.md` for the complete enumeration of cases excluded from each cohort, including the rationale (single-phase scanner protocol, incomplete acquisitions, lost GT, etc.).

---

## 5. Failure modes (do not run blindly on these)

The Exp4x model has a few known weaknesses, documented for honest deployment:

1. **Mid-treatment (T1-equivalent) scans** — the training pool is baseline (T0) acquisitions only. On post-NAC follow-up scans you may see empty tumour predictions. Five of the eight BMMR2 systematic failures are T1 cases.
2. **Single-phase acquisitions** — by design, this model needs ≥3 DCE phases. Cohorts with single-phase scanners (45 of 100 Yunnan cases) are not segmentable.
3. **Wrong-side breast over-segmentation** — rare. Documented for case `980397_T0` in BMMR2 v2.
4. **Multi-protocol drift** — French cohort drops to 0.72 Dice when multiple acquisition protocols (T1.DYN / dynaVIEWS / GE VIBRANT) are mixed.

See `Code/results/list_skipped_cases.md` for individual case IDs.

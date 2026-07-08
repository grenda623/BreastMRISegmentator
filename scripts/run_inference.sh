#!/usr/bin/env bash
#
# Thin convenience wrapper around the `breast-mri-segment` CLI.
#
# Usage:
#   scripts/run_inference.sh <input_dir> <output_dir> [extra CLI flags...]
#
# Examples:
#   # per-phase NIfTI (Layout B)
#   scripts/run_inference.sh data/nifti_root out/preds
#
#   # DICOM root (Layout A), with test-time augmentation
#   scripts/run_inference.sh data/dicom out/preds --from-dicom --tta
#
# This is just sugar over:
#   breast-mri-segment -i <input_dir> -o <output_dir> [flags]
# Training and evaluation scripts are not shipped here; they live in the
# parent project's `Code/` repository (see docs/training.md).

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "usage: $0 <input_dir> <output_dir> [extra breast-mri-segment flags...]" >&2
    exit 2
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
shift 2

if ! command -v breast-mri-segment >/dev/null 2>&1; then
    echo "error: 'breast-mri-segment' not found on PATH." >&2
    echo "       install the package first: pip install breast-mri-segmentator" >&2
    exit 1
fi

if [[ ! -d "$INPUT_DIR" ]]; then
    echo "error: input directory does not exist: $INPUT_DIR" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo ">> breast-mri-segment -i '$INPUT_DIR' -o '$OUTPUT_DIR' $*"
exec breast-mri-segment -i "$INPUT_DIR" -o "$OUTPUT_DIR" "$@"

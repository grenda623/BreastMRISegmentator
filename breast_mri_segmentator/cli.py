"""CLI entry point for `breast-mri-segment`."""

from __future__ import annotations

import argparse
import sys

from breast_mri_segmentator import __version__
from breast_mri_segmentator.api import segment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="breast-mri-segment",
        description=(
            "Automated breast / FGT / tumor segmentation on DCE-MRI "
            "(model: Exp4x, 4-channel kinetic input, 3D nnUNet)."
        ),
    )
    parser.add_argument("-i", "--input", required=True,
                        help="Input directory (DICOM cases or per-phase NIfTI).")
    parser.add_argument("-o", "--output", required=True,
                        help="Output directory for prediction NIfTI volumes.")
    parser.add_argument("--from-dicom", action="store_true",
                        help="Treat --input as DICOM and run dcm2niix first.")
    parser.add_argument("--weights", default=None,
                        help="Local weights root (skips Zenodo download).")
    parser.add_argument("--tta", action="store_true",
                        help="Enable test-time augmentation (~8x slower).")
    parser.add_argument("--fold", type=int, default=0,
                        help="Trained fold to use (default 0).")
    parser.add_argument("--version", action="version",
                        version=f"breast-mri-segmentator {__version__}")
    args = parser.parse_args(argv)

    out = segment(
        input_dir=args.input,
        output_dir=args.output,
        from_dicom=args.from_dicom,
        weights_dir=args.weights,
        use_tta=args.tta,
        fold=args.fold,
    )
    print(f"\nDone. Predictions written to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

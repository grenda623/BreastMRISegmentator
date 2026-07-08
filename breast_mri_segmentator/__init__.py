"""BreastMRISegmentator — open-source DCE-MRI segmentation toolkit.

Provides automated breast / FGT / tumor segmentation on DCE-MRI volumes using a
4-channel kinetic input (P0, P1, P1-P0, P4-P1) and a pre-trained nnUNet model
(Exp4x, trained on 1,280 multi-centre cases).

Quick start (Python API):
    >>> from breast_mri_segmentator import segment
    >>> segment(input_dir="my_dicom/", output_dir="seg_out/")

Quick start (CLI):
    $ breast-mri-segment -i my_dicom/ -o seg_out/ --from-dicom

See README.md and docs/usage.md for details.
"""

__version__ = "0.1.0"
__author__ = "Renda Guo"
__license__ = "Apache-2.0"

# Re-exports
from breast_mri_segmentator.api import segment  # noqa: F401
from breast_mri_segmentator.io import build_4ch_kinetic, dicom_to_nifti  # noqa: F401

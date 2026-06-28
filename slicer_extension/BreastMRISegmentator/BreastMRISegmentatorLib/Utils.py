"""Small helpers shared by the widget and logic layers."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

# Label map produced by the Exp4x model.
LABELS = ["Breast", "FGT", "Tumor"]
# Distinct, clinically readable colors (breast = teal, FGT = amber, tumor = red).
COLORS_HEX = ["#4FB0C6", "#E6B84F", "#D8654F"]
OPACITIES = [0.4, 0.6, 1.0]


def toRGB(hex_color: str) -> tuple[float, float, float]:
    """'#RRGGBB' -> (r, g, b) floats in [0, 1]."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def exportVolumeToNifti(volumeNode, outPath: Path) -> Path:
    """Save a Slicer scalar volume node to a .nii.gz file.

    SCAFFOLD: thin wrapper around ``slicer.util.exportNode`` /
    ``saveNode``; needs validation inside Slicer.
    """
    import slicer

    outPath = Path(outPath)
    outPath.parent.mkdir(parents=True, exist_ok=True)
    slicer.util.saveNode(volumeNode, str(outPath))
    return outPath


def loadSegmentation(segPath: Path):
    """Load a label NIfTI as a segmentation node. SCAFFOLD."""
    import slicer

    return slicer.util.loadSegmentation(str(segPath))


def assertSamePhaseCount(phaseNodes: Sequence, minimum: int = 3) -> None:
    if len([n for n in phaseNodes if n is not None]) < minimum:
        raise ValueError(
            f"BreastMRISegmentator needs at least {minimum} DCE phase volumes "
            "(pre-contrast + >=2 post-contrast)."
        )

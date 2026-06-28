"""Shared test base class + fixtures for the BreastMRISegmentator extension.

Mirrors DentalSegmentator's ``Testing/Utils.py`` (scene reset + sample-data
helpers). Because there is no public breast-DCE demo case bundled here, the
helpers fabricate *synthetic* DCE phase volumes in the scene, matching the
synthetic case in ``examples/run_on_public_demo_case.ipynb``.

SCAFFOLD: requires the Slicer Python environment to run.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

try:  # available only inside Slicer
    import slicer

    _HAS_SLICER = True
except ImportError:
    slicer = None  # type: ignore[assignment]
    _HAS_SLICER = False


class BreastMRISegmentatorTestCase(unittest.TestCase):
    """Base case: clears the Slicer scene around each test."""

    def setUp(self):
        if not _HAS_SLICER:
            self.skipTest("requires the 3D Slicer Python environment")
        self._clearScene()

    def tearDown(self):
        if _HAS_SLICER:
            slicer.app.processEvents()

    @staticmethod
    def _clearScene():
        slicer.app.processEvents()
        slicer.mrmlScene.Clear()
        slicer.app.processEvents()


def _dataFolderPath() -> Path:
    return Path(__file__).parent / "Data"


def make_synthetic_phase_volumes(n_phases: int = 4, shape=(32, 32, 16)):
    """Create ``n_phases`` synthetic DCE phase volume nodes in the scene.

    Returns the list of ``vtkMRMLScalarVolumeNode`` in acquisition order. A
    small cuboid 'lesion' brightens after contrast then washes out, so the
    kinetic channels are non-degenerate.
    """
    if not _HAS_SLICER:
        raise RuntimeError("make_synthetic_phase_volumes() needs Slicer.")

    rng = np.random.default_rng(0)
    base = rng.normal(100, 10, size=shape).astype(np.float32)
    lesion = np.zeros(shape, dtype=np.float32)
    lesion[12:20, 12:20, 6:10] = 1.0
    phase_gain = [0.0, 80.0, 60.0, 40.0, 30.0]  # P0..P4 enhancement

    nodes = []
    for i in range(n_phases):
        arr = base + phase_gain[i % len(phase_gain)] * lesion
        node = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLScalarVolumeNode", f"phase{i}"
        )
        slicer.util.updateVolumeFromArray(node, arr)
        nodes.append(node)
    return nodes


def count_segmentation_nodes() -> int:
    if not _HAS_SLICER:
        return 0
    return len(slicer.util.getNodesByClass("vtkMRMLSegmentationNode"))

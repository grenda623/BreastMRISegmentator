"""Integration tests for the BreastMRISegmentator Slicer extension.

Mirrors DentalSegmentator's ``Testing/IntegrationTestCase.py``. Two tiers:

* fast tests (default) — exercise the dependency checker and the
  ``SegmentationLogic`` Layout-B construction with ``segment`` mocked, so they
  need Slicer but no GPU / weights.
* ``@pytest.mark.slow`` — the genuine end-to-end run (real Exp4x weights + GPU);
  skipped unless dependencies are present.

SCAFFOLD: none of this has been executed inside Slicer yet. Run via
SlicerPythonTestRunner / pytest from the Slicer Python console.
"""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from BreastMRISegmentatorLib import SegmentationLogic
from BreastMRISegmentatorLib import PythonDependencyChecker as deps

from .Utils import (
    BreastMRISegmentatorTestCase,
    count_segmentation_nodes,
    make_synthetic_phase_volumes,
)


class DependencyCheckerTestCase(BreastMRISegmentatorTestCase):
    """Fast: validate the dependency-checker contract without installing."""

    def test_reports_missing_package_as_unsatisfied(self):
        with mock.patch.object(deps, "isPackageInstalled", return_value=False):
            self.assertFalse(deps.isPackageInstalled())

    def test_install_requires_slicer_pip(self):
        # Outside Slicer's pip_install, installDependencies must raise clearly.
        with mock.patch.dict("sys.modules", {"slicer.util": None}):
            with self.assertRaises(Exception):
                deps.installDependencies()


class LogicLayoutTestCase(BreastMRISegmentatorTestCase):
    """Fast: the logic must lay phases out as Layout B and call segment()."""

    def test_builds_layout_b_and_invokes_segment(self):
        nodes = make_synthetic_phase_volumes(n_phases=4)

        # Export the synthetic phases to NIfTI on disk (real Slicer save).
        import qt
        from BreastMRISegmentatorLib.Utils import exportVolumeToNifti

        tmp = Path(qt.QTemporaryDir().path())
        phase_paths = []
        for i, node in enumerate(nodes):
            p = tmp / "input" / f"phase{i}.nii.gz"
            exportVolumeToNifti(node, p)
            phase_paths.append(p)

        logic = SegmentationLogic()
        finished = []
        logic.finished.connect(finished.append)

        captured = {}

        def fake_segment(input_dir, output_dir, **kwargs):
            # Assert Layout B was produced, then fabricate a label volume.
            case_dir = Path(input_dir) / "case"
            files = sorted(p.name for p in case_dir.glob("*.nii.gz"))
            captured["layout"] = files
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            # Reuse one of the inputs as a stand-in label volume.
            (out / "case.nii.gz").write_bytes(phase_paths[0].read_bytes())
            return out

        with mock.patch(
            "breast_mri_segmentator.api.segment", side_effect=fake_segment
        ):
            label_path = logic.startSegmentation(phase_paths, tmp)

        self.assertEqual(
            captured["layout"],
            ["case_phase0.nii.gz", "case_phase1.nii.gz",
             "case_phase2.nii.gz", "case_phase3.nii.gz"],
        )
        self.assertTrue(label_path.exists())
        self.assertEqual(len(finished), 1)

    def test_rejects_too_few_phases(self):
        from BreastMRISegmentatorLib.Utils import assertSamePhaseCount

        nodes = make_synthetic_phase_volumes(n_phases=2)
        with self.assertRaises(ValueError):
            assertSamePhaseCount(nodes, minimum=3)


@pytest.mark.slow
class IntegrationTestCase(BreastMRISegmentatorTestCase):
    """Slow: full GUI -> Apply -> one segmentation node, real inference."""

    def setUp(self):
        super().setUp()
        if not deps.areDependenciesSatisfied():
            self.skipTest(
                "Exp4x dependencies (torch/nnunetv2/breast_mri_segmentator) "
                "not installed; skipping end-to-end test."
            )

    def test_end_to_end_segmentation_creates_one_node(self):
        import slicer
        from BreastMRISegmentatorLib import SegmentationWidget

        make_synthetic_phase_volumes(n_phases=4)
        widget = SegmentationWidget()

        # Wire the scene's phase nodes into the first selectors.
        phase_nodes = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
        for sel, node in zip(widget._phaseSelectors, phase_nodes):
            sel.setCurrentNode(node)

        widget.applyButton.clicked()
        slicer.app.processEvents()

        # Exactly one segmentation node should have been produced.
        self.assertEqual(count_segmentation_nodes(), 1)
        widget.onClose()

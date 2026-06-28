"""3D Slicer scripted module entry point for BreastMRISegmentator.

Mirrors the structure of gaudot/SlicerDentalSegmentator. The actual GUI and
inference logic live in ``BreastMRISegmentatorLib.SegmentationWidget``; this
file only declares the module metadata and delegates to that widget.

SCAFFOLD: this module has not yet been run inside 3D Slicer. Wiring marked
``TODO`` needs validation against a live Slicer build (>= 5.8.0).
"""
from pathlib import Path

from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
)


class BreastMRISegmentator(ScriptedLoadableModule):
    """Module metadata shown in the Slicer module list."""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "BreastMRISegmentator"
        self.parent.categories = ["Segmentation"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Renda Guo (KTH)",
            "Rodrigo Moreno (KTH)",
        ]
        self.parent.helpText = (
            "Fully automatic segmentation of breast, fibroglandular tissue "
            "(FGT) and tumor on DCE-MRI, using the BreastMRISegmentator "
            "nnU-Net model (Exp4x, 4-channel kinetic input). Select the "
            "pre-contrast and post-contrast phase volumes, then click Apply.\n\n"
            "Research use only. Not a medical device."
        )
        self.parent.acknowledgementText = (
            "Developed at KTH Royal Institute of Technology. Model trained on "
            "the Berzelius cluster (NSC). Built on the nnU-Net framework "
            "(Isensee et al., 2021) and modelled on the DentalSegmentator "
            "Slicer extension (Dot et al., 2024)."
        )


class BreastMRISegmentatorWidget(ScriptedLoadableModuleWidget):
    """Thin wrapper: embeds the SegmentationWidget from the Lib package."""

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Imported lazily so that a missing dependency does not break module
        # discovery at Slicer startup.
        from BreastMRISegmentatorLib import SegmentationWidget

        self.widget = SegmentationWidget()
        self.layout.addWidget(self.widget)
        self.logic = self.widget.logic

    def cleanup(self):
        if getattr(self, "widget", None) is not None:
            self.widget.onClose()
        super().cleanup()


class BreastMRISegmentatorTest:
    """Slicer self-test hook.

    Runs the pytest cases under ``Testing/`` via the SlicerPythonTestRunner
    extension (same pattern as DentalSegmentator). Fast tests need Slicer only;
    the ``@pytest.mark.slow`` end-to-end case needs a GPU + Exp4x weights and is
    deselected here.
    """

    def runTest(self):  # pragma: no cover - requires Slicer runtime
        try:
            from SlicerPythonTestRunnerLib import (
                RunnerLogic,
                RunSettings,
                isRunnerInstalled,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Install the 'SlicerPythonTestRunner' extension to run these "
                "tests, or run pytest manually from the Slicer Python console:\n"
                f"  pytest {Path(__file__).parent / 'Testing'} -m 'not slow'"
            ) from exc

        if not isRunnerInstalled():
            raise RuntimeError("SlicerPythonTestRunner is not properly installed.")

        testDir = Path(__file__).parent / "Testing"
        results = RunnerLogic().runAndWaitFinished(
            testDir,
            RunSettings(extraPytestArgs=["-m", "not slow", "--verbose"]),
        )
        if results.failuresNumber:
            raise AssertionError(f"{results.failuresNumber} test(s) failed.")

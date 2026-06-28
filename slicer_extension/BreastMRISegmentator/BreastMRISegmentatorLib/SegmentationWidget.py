"""GUI + logic for the BreastMRISegmentator Slicer module.

Design (differs from DentalSegmentator):
    DentalSegmentator feeds a *single* CT volume to a single-channel nnU-Net.
    Our Exp4x model needs a *4-channel kinetic* input synthesised from several
    DCE phases (P0, P1, P1-P0, P_last-P1). Rather than re-implement that inside
    Slicer, we delegate to the pip package ``breast_mri_segmentator``:

        1. Widget collects >=3 DCE phase volume nodes (pre + post-contrast).
        2. Logic exports them to a temp dir as ``case/case_phaseN.nii.gz``
           (the package's "Layout B").
        3. Logic calls ``breast_mri_segmentator.api.segment(...)`` which builds
           the 4 kinetic channels and runs nnUNetv2_predict (Exp4x, Dataset932,
           fold 0). Weights are auto-fetched from Zenodo on first use.
        4. The resulting label volume is loaded back and the 3 segments are
           named/colored (1=Breast, 2=FGT, 3=Tumor).

SCAFFOLD: this file has NOT been run inside Slicer. Lines marked ``TODO`` need
validation against a live Slicer build (>= 5.8.0) and a GPU. The threading is
intentionally simplistic — production code should run inference in a
``slicer.modules.processes`` / ``QProcess`` job so the UI stays responsive.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

try:  # available only inside Slicer
    import ctk
    import qt
    import slicer

    _HAS_SLICER = True
except ImportError:  # importable outside Slicer for linting/inspection
    ctk = qt = slicer = None  # type: ignore[assignment]
    _HAS_SLICER = False

from .PythonDependencyChecker import (
    areDependenciesSatisfied,
    installDependencies,
)
from .Signal import Signal
from .Utils import COLORS_HEX, LABELS, OPACITIES, assertSamePhaseCount, toRGB

#: Minimum number of DCE phase selectors shown in the UI.
_MIN_PHASES = 3


class SegmentationLogic:
    """Stateless-ish engine wrapper around ``breast_mri_segmentator``.

    Emits progress/finished/error signals so the widget can stay decoupled.
    """

    def __init__(self):
        self.progress = Signal("str")
        self.finished = Signal("Path")  # path to the output label volume
        self.errored = Signal("str")
        self.useTta = False
        self.fold = 0

    def _emit(self, msg: str) -> None:
        logging.info("[BreastMRISegmentator] %s", msg)
        self.progress.emit(msg)

    def startSegmentation(self, phaseNiftiPaths: list[Path], workdir: Path) -> Path:
        """Run the full pipeline synchronously and return the label path.

        ``phaseNiftiPaths`` are ordered DCE phases already written to disk.
        SCAFFOLD: should be dispatched to a background process in production.
        """
        from breast_mri_segmentator.api import segment

        case_id = "case"
        nifti_root = workdir / "nifti_root"
        case_dir = nifti_root / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Re-name into the package's canonical Layout B.
        for i, src in enumerate(phaseNiftiPaths):
            dst = case_dir / f"{case_id}_phase{i}.nii.gz"
            if Path(src) != dst:
                dst.write_bytes(Path(src).read_bytes())

        out_dir = workdir / "predictions"
        self._emit(f"Running Exp4x inference on {len(phaseNiftiPaths)} phases...")
        segment(
            input_dir=nifti_root,
            output_dir=out_dir,
            from_dicom=False,
            use_tta=self.useTta,
            fold=self.fold,
        )
        label_path = out_dir / f"{case_id}.nii.gz"
        if not label_path.exists():
            raise RuntimeError(
                f"Inference produced no output at {label_path}. The case may "
                "have been skipped (need >=3 valid DCE phases of equal shape)."
            )
        self._emit("Inference complete.")
        self.finished.emit(label_path)
        return label_path


class SegmentationWidget(qt.QWidget if _HAS_SLICER else object):
    """Qt widget: phase selectors, device choice, Apply/Stop, progress log."""

    def __init__(self, parent=None):
        if not _HAS_SLICER:
            raise RuntimeError(
                "SegmentationWidget requires the Slicer Python environment."
            )
        super().__init__(parent)
        self.logic = SegmentationLogic()
        self._workdir: Path | None = None
        self._phaseSelectors: list = []
        self._setupUi()
        self._connectLogic()

    # ------------------------------------------------------------------ UI ---
    def _setupUi(self) -> None:
        layout = qt.QFormLayout(self)

        info = qt.QLabel(
            "Select the DCE phases in acquisition order: phase 0 = pre-contrast, "
            "phase 1 = first post-contrast, last = late post-contrast.\n"
            "Research use only — not a medical device."
        )
        info.setWordWrap(True)
        layout.addRow(info)

        # Phase volume selectors (start with the minimum, allow adding more).
        self._phaseBox = qt.QVBoxLayout()
        for i in range(_MIN_PHASES):
            self._addPhaseSelector(i)
        addBtn = qt.QPushButton("+ Add another phase")
        addBtn.clicked.connect(lambda: self._addPhaseSelector(len(self._phaseSelectors)))
        layout.addRow("DCE phases:", self._phaseBox)
        layout.addRow("", addBtn)

        # Device selection.
        self.deviceComboBox = qt.QComboBox()
        self.deviceComboBox.addItems(["cuda", "cpu", "mps"])
        layout.addRow("Device:", self.deviceComboBox)

        # TTA toggle.
        self.ttaCheckBox = qt.QCheckBox("Enable test-time augmentation (~8x slower)")
        layout.addRow("", self.ttaCheckBox)

        # Apply / Stop.
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.clicked.connect(self.onApplyClicked)
        layout.addRow(self.applyButton)

        # Output segmentation selector.
        self.outputSelector = slicer.qMRMLNodeComboBox()
        self.outputSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.outputSelector.noneEnabled = True
        self.outputSelector.addEnabled = False
        self.outputSelector.setMRMLScene(slicer.mrmlScene)
        layout.addRow("Result:", self.outputSelector)

        # Progress log.
        self.currentInfoTextEdit = qt.QPlainTextEdit()
        self.currentInfoTextEdit.setReadOnly(True)
        self.currentInfoTextEdit.setMaximumHeight(120)
        layout.addRow(self.currentInfoTextEdit)

    def _addPhaseSelector(self, index: int) -> None:
        sel = slicer.qMRMLNodeComboBox()
        sel.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        sel.noneEnabled = index >= _MIN_PHASES
        sel.addEnabled = False
        sel.setMRMLScene(slicer.mrmlScene)
        row = qt.QHBoxLayout()
        row.addWidget(qt.QLabel(f"phase {index}:"))
        row.addWidget(sel)
        self._phaseBox.addLayout(row)
        self._phaseSelectors.append(sel)

    # -------------------------------------------------------------- logic ---
    def _connectLogic(self) -> None:
        self.logic.progress.connect(self._log)
        self.logic.errored.connect(self._log)
        self.logic.finished.connect(self._loadSegmentationResults)

    def _log(self, msg: str) -> None:
        self.currentInfoTextEdit.appendPlainText(msg)
        slicer.app.processEvents()

    def _selectedPhaseNodes(self) -> list:
        return [s.currentNode() for s in self._phaseSelectors if s.currentNode()]

    def onApplyClicked(self) -> None:
        try:
            phaseNodes = self._selectedPhaseNodes()
            assertSamePhaseCount(phaseNodes, _MIN_PHASES)

            if not areDependenciesSatisfied():
                self._log("Installing inference dependencies (first run only)...")
                installDependencies(progressCallback=self._log)

            self.applyButton.setEnabled(False)
            self._workdir = Path(tempfile.mkdtemp(prefix="SlicerBMRS_"))

            from .Utils import exportVolumeToNifti

            phasePaths = []
            for i, node in enumerate(phaseNodes):
                p = self._workdir / "input" / f"phase{i}.nii.gz"
                exportVolumeToNifti(node, p)
                phasePaths.append(p)

            self.logic.useTta = self.ttaCheckBox.isChecked()
            # TODO: device is currently honored only via nnU-Net env/CUDA
            # visibility; pass it through to the package when supported.
            self.logic.startSegmentation(phasePaths, self._workdir)
        except Exception as exc:  # noqa: BLE001 - surface to the GUI log
            self._log(f"ERROR: {exc}")
            logging.exception("BreastMRISegmentator failed")
        finally:
            self.applyButton.setEnabled(True)

    def _loadSegmentationResults(self, labelPath) -> None:
        from .Utils import loadSegmentation

        segNode = loadSegmentation(Path(labelPath))
        self.outputSelector.setCurrentNode(segNode)
        self._styleSegments(segNode)
        self._log("Loaded segmentation. Labels: Breast / FGT / Tumor.")

    def _styleSegments(self, segNode) -> None:
        """Rename + recolor the 3 output segments. SCAFFOLD."""
        segmentation = segNode.GetSegmentation()
        for i, (name, hexc, op) in enumerate(zip(LABELS, COLORS_HEX, OPACITIES)):
            # nnU-Net writes labels 1,2,3 -> segment ids "1","2","3" (order may
            # differ across Slicer versions; TODO verify mapping at runtime).
            segId = segmentation.GetNthSegmentID(i)
            if not segId:
                continue
            seg = segmentation.GetSegment(segId)
            seg.SetName(name)
            seg.SetColor(*toRGB(hexc))
            dn = segNode.GetDisplayNode()
            if dn is not None:
                dn.SetSegmentOpacity3D(segId, op)

    def onClose(self) -> None:
        if self._workdir is not None:
            import shutil

            shutil.rmtree(self._workdir, ignore_errors=True)
            self._workdir = None

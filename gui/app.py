"""
Brain Tumour Detection & Segmentation — PyQt6 Desktop Application.

Layout
------
MainWindow
├── MenuBar  (File | Help)
├── ToolBar  (Open  Run-AI  Export-All)
├── QSplitter (horizontal)
│   ├── PatientPanel   — left   (patient / study tree)
│   ├── MriCanvas      — centre (matplotlib MRI viewer + overlay)
│   └── ClinicalPanel  — right  (results metrics + export tabs)
└── StatusBar (message + progress bar)
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Matplotlib Qt backend — must be set before importing pyplot / Figure
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("qtagg")                                        # noqa: E402
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.colors import ListedColormap                   # noqa: E402
from matplotlib.figure import Figure                           # noqa: E402

from PyQt6.QtCore import (
    QSettings, QSize, Qt, QThreadPool,
)
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSplitter, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QToolBar, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from gui.models import AppStorage, Patient, PredictionResult, Study, StudyStatus, get_storage
from gui.workers import ExportWorker, InferenceWorker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Segmentation colour map  (0=background transparent, 1=NCR red, 2=ET orange, 3=ED blue)
# ---------------------------------------------------------------------------
_SEG_CMAP = ListedColormap(["none", "#DC143C", "#FFA500", "#4169E1"])
_CLASS_LABELS = {
    1: "Necrotic Core (NCR)",
    2: "Enhancing Tumour (ET)",
    3: "Peritumoral Edema (ED)",
}


# ===========================================================================
# MRI Canvas
# ===========================================================================

class MriCanvas(FigureCanvasQTAgg):
    """Matplotlib figure embedded in Qt showing a single MRI axial slice
    with an optional 3-class segmentation overlay."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        self.fig = Figure(figsize=(6, 5), facecolor="#1e1e1e", tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._ax = self.fig.add_subplot(111)
        self._volume: Optional[np.ndarray] = None
        self._mask: Optional[np.ndarray] = None
        self._slice_idx: int = 0
        self._show_overlay: bool = True
        self._draw_empty()

    # --- public API ---

    def load_volume(self, volume: np.ndarray, mask: Optional[np.ndarray] = None) -> None:
        self._volume = volume
        self._mask = mask
        self._slice_idx = volume.shape[0] // 2
        self._redraw()

    def set_mask(self, mask: np.ndarray) -> None:
        self._mask = mask
        self._redraw()

    def set_slice(self, idx: int) -> None:
        if self._volume is not None:
            self._slice_idx = max(0, min(idx, self._volume.shape[0] - 1))
            self._redraw()

    def toggle_overlay(self, visible: bool) -> None:
        self._show_overlay = visible
        self._redraw()

    def slice_count(self) -> int:
        return self._volume.shape[0] if self._volume is not None else 0

    # --- private ---

    def _draw_empty(self) -> None:
        self._ax.clear()
        self._ax.set_facecolor("#1e1e1e")
        self._ax.text(
            0.5, 0.5, "Open a NIfTI or DICOM volume\nto begin",
            ha="center", va="center", color="#888888", fontsize=11,
            transform=self._ax.transAxes,
        )
        self._ax.axis("off")
        self.draw_idle()

    def _redraw(self) -> None:
        if self._volume is None:
            self._draw_empty()
            return

        self._ax.clear()
        self._ax.set_facecolor("#0a0a0a")

        sl = self._volume[self._slice_idx]
        vmin, vmax = float(np.percentile(sl, 1)), float(np.percentile(sl, 99))
        self._ax.imshow(sl, cmap="gray", vmin=vmin, vmax=vmax, origin="lower")

        if self._show_overlay and self._mask is not None:
            mask_sl = self._mask[self._slice_idx].astype(float)
            masked = np.ma.masked_where(mask_sl == 0, mask_sl)
            self._ax.imshow(
                masked, cmap=_SEG_CMAP, vmin=0, vmax=3, alpha=0.55, origin="lower"
            )
            # legend patches
            from matplotlib.patches import Patch
            legend_handles = [
                Patch(facecolor="#DC143C", label="NCR"),
                Patch(facecolor="#FFA500", label="ET"),
                Patch(facecolor="#4169E1", label="ED"),
            ]
            self._ax.legend(
                handles=legend_handles, loc="upper right",
                fontsize=7, framealpha=0.6,
                labelcolor="white", facecolor="#333333",
            )

        self._ax.set_title(
            f"Axial  ·  slice {self._slice_idx + 1} / {self._volume.shape[0]}",
            color="#cccccc", fontsize=9, pad=4,
        )
        self._ax.axis("off")
        self.draw_idle()


# ===========================================================================
# Left panel — Patient / Study tree
# ===========================================================================

class PatientPanel(QWidget):
    """Sidebar tree listing patients and their studies.

    Selecting a study row emits study_id via the public callback
    ``on_study_selected``.
    """

    def __init__(self, storage: AppStorage, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.storage = storage
        self.on_study_selected = None   # set by MainWindow

        self.setMinimumWidth(220)
        self.setMaximumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        lbl = QLabel("Patients / Studies")
        lbl.setFont(QFont("sans-serif", 9, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #aaaaaa; padding: 2px 4px;")
        layout.addWidget(lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name / File", "Status"])
        self.tree.setColumnWidth(0, 160)
        self.tree.setColumnWidth(1, 60)
        self.tree.setStyleSheet("""
            QTreeWidget { background: #1e1e1e; color: #dddddd;
                          border: 1px solid #444; font-size: 11px; }
            QTreeWidget::item:selected { background: #2a5c8f; }
            QHeaderView::section { background: #2d2d2d; color: #aaaaaa;
                                   border: none; padding: 3px; }
        """)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        self.refresh()

    def refresh(self) -> None:
        """Reload tree from storage."""
        self.tree.clear()
        for patient in self.storage.get_patients():
            p_item = QTreeWidgetItem([patient.name, ""])
            p_item.setData(0, Qt.ItemDataRole.UserRole, ("patient", patient.patient_id))
            for study in self.storage.get_studies(patient_id=patient.patient_id):
                fname = Path(study.file_path).name
                s_item = QTreeWidgetItem([fname, study.status])
                s_item.setData(0, Qt.ItemDataRole.UserRole, ("study", study.study_id))
                result = self.storage.get_result_for_study(study.study_id)
                if result:
                    s_item.setToolTip(0, f"Prediction: {result.prediction}  "
                                         f"Confidence: {result.confidence:.1%}")
                p_item.addChild(s_item)
            self.tree.addTopLevelItem(p_item)
            p_item.setExpanded(True)

    def add_study(self, patient: Patient, study: Study) -> None:
        self.storage.add_patient(patient)
        self.storage.add_study(study)
        self.refresh()

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == "study" and callable(self.on_study_selected):
            self.on_study_selected(data[1])


# ===========================================================================
# Right panel — tab 1: Results
# ===========================================================================

class ResultsWidget(QWidget):
    """Displays prediction badge + metric table after inference."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Prediction badge
        self.badge = QLabel("— awaiting segmentation —")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        self.badge.setStyleSheet(
            "background: #2d2d2d; color: #888888; border-radius: 6px; padding: 8px;"
        )
        self.badge.setMinimumHeight(44)
        layout.addWidget(self.badge)

        # Inference progress bar (hidden until running)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%  %v")
        self.progress.setVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar { background:#2d2d2d; border-radius:4px; } "
            "QProgressBar::chunk { background:#2a7abf; }"
        )
        layout.addWidget(self.progress)

        # Metrics table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Metric", "Value", "Unit"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 160)
        self.table.setColumnWidth(1, 80)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { background:#1e1e1e; color:#dddddd;
                           gridline-color:#3a3a3a; font-size:11px; }
            QHeaderView::section { background:#2d2d2d; color:#aaaaaa;
                                   border:none; padding:3px; }
        """)
        layout.addWidget(self.table)

    def set_progress(self, pct: int, msg: str) -> None:
        self.progress.setVisible(True)
        self.progress.setValue(pct)
        self.progress.setFormat(f"  {msg}  ({pct}%)")

    def hide_progress(self) -> None:
        self.progress.setVisible(False)

    def show_result(self, result: Dict[str, Any]) -> None:
        pred = result.get("prediction", "N/A")
        conf = result.get("confidence", 0.0)
        vols = result.get("class_volumes_cm3", {})
        t = result.get("processing_time_seconds", 0.0)

        colour = "#27ae60" if pred == "tumor_detected" else "#2980b9"
        label = pred.replace("_", " ").title()
        self.badge.setText(f"{label}   ({conf:.1%})")
        self.badge.setStyleSheet(
            f"background:{colour}; color:white; border-radius:6px; "
            "padding:8px; font-size:11pt; font-weight:bold;"
        )

        rows: List[tuple] = [
            ("Prediction", label, ""),
            ("Confidence", f"{conf:.1%}", ""),
            ("Whole Tumour (WT)", f"{vols.get('whole_tumour_cm3', 0):.2f}", "cm³"),
            ("Enhancing Tumour (ET)", f"{vols.get('enhancing_tumour_cm3', 0):.2f}", "cm³"),
            ("Necrotic Core (NCR)", f"{vols.get('necrotic_core_cm3', 0):.2f}", "cm³"),
            ("Peritumoral Edema (ED)", f"{vols.get('peritumoral_edema_cm3', 0):.2f}", "cm³"),
            ("Segmentation Time", f"{t:.2f}", "seconds"),
            ("Device", result.get("device", "N/A"), ""),
            ("Model", result.get("model", "N/A"), ""),
            ("Volume Shape", str(result.get("volume_shape", "")), "voxels"),
        ]
        self.table.setRowCount(len(rows))
        for r, (metric, val, unit) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(metric))
            self.table.setItem(r, 1, QTableWidgetItem(val))
            self.table.setItem(r, 2, QTableWidgetItem(unit))
        self.table.resizeRowsToContents()
        self.hide_progress()


# ===========================================================================
# Right panel — tab 2: Export
# ===========================================================================

class ExportWidget(QWidget):
    """Export options: NIfTI mask, CSV metrics, PDF report, FHIR R4 bundle."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.on_export_requested = None  # set by MainWindow: (types, dir) -> None
        self._result: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        lbl = QLabel("Export Results")
        lbl.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #cccccc;")
        layout.addWidget(lbl)

        # Patient name entry
        grp_patient = QGroupBox("Patient")
        grp_patient.setStyleSheet(
            "QGroupBox { color:#aaaaaa; border:1px solid #444; border-radius:4px; "
            "margin-top:8px; padding:6px; } "
            "QGroupBox::title { subcontrol-origin:margin; left:8px; color:#888888; }"
        )
        patient_layout = QHBoxLayout(grp_patient)
        patient_layout.addWidget(QLabel("Name:"))
        self.patient_name_input = QLineEdit()
        self.patient_name_input.setPlaceholderText("Patient name for reports")
        self.patient_name_input.setStyleSheet(
            "QLineEdit { background:#2d2d2d; color:#dddddd; "
            "border:1px solid #555; border-radius:3px; padding:3px; }"
        )
        patient_layout.addWidget(self.patient_name_input)
        layout.addWidget(grp_patient)

        # Format checkboxes
        grp_fmt = QGroupBox("Output Formats")
        grp_fmt.setStyleSheet(grp_patient.styleSheet())
        fmt_layout = QVBoxLayout(grp_fmt)
        self.cb_nifti = QCheckBox("NIfTI Segmentation Mask  (.nii.gz)")
        self.cb_csv   = QCheckBox("Volume Metrics  (.csv)")
        self.cb_pdf   = QCheckBox("Clinical PDF Report  (.pdf)")
        self.cb_fhir  = QCheckBox("FHIR R4 DiagnosticReport  (.json)")
        for cb in (self.cb_nifti, self.cb_csv, self.cb_pdf, self.cb_fhir):
            cb.setChecked(True)
            cb.setStyleSheet("color: #cccccc;")
            fmt_layout.addWidget(cb)
        layout.addWidget(grp_fmt)

        # Directory picker
        dir_row = QHBoxLayout()
        self.dir_label = QLabel("./exports")
        self.dir_label.setStyleSheet(
            "background:#2d2d2d; color:#aaaaaa; border:1px solid #3a3a3a; "
            "border-radius:3px; padding:4px; font-size:10px;"
        )
        dir_row.addWidget(self.dir_label, 1)
        btn_dir = QPushButton("Browse…")
        btn_dir.setFixedWidth(70)
        btn_dir.setStyleSheet(
            "QPushButton { background:#3a3a3a; color:#cccccc; border-radius:3px; "
            "padding:4px 8px; } QPushButton:hover { background:#4a4a4a; }"
        )
        btn_dir.clicked.connect(self._pick_dir)
        dir_row.addWidget(btn_dir)
        layout.addLayout(dir_row)

        # Export button
        self.btn_export = QPushButton("Export Selected")
        self.btn_export.setMinimumHeight(38)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet(
            "QPushButton { background:#1f6398; color:white; border-radius:5px; "
            "font-size:12px; font-weight:bold; } "
            "QPushButton:hover { background:#2a7abf; } "
            "QPushButton:disabled { background:#3a3a3a; color:#666666; }"
        )
        self.btn_export.clicked.connect(self._do_export)
        layout.addWidget(self.btn_export)

        # Export progress
        self.export_progress = QProgressBar()
        self.export_progress.setRange(0, 100)
        self.export_progress.setVisible(False)
        self.export_progress.setStyleSheet(
            "QProgressBar { background:#2d2d2d; border-radius:4px; } "
            "QProgressBar::chunk { background:#27ae60; }"
        )
        layout.addWidget(self.export_progress)

        layout.addStretch()
        self._export_dir = "./exports"

    def set_result(self, result: Dict[str, Any]) -> None:
        self._result = result
        self.btn_export.setEnabled(True)

    def set_export_progress(self, pct: int, msg: str) -> None:
        self.export_progress.setVisible(True)
        self.export_progress.setValue(pct)
        self.export_progress.setFormat(f"  {msg}  ({pct}%)")

    def finish_export(self) -> None:
        self.export_progress.setVisible(False)

    def _pick_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Export Directory", self._export_dir)
        if d:
            self._export_dir = d
            self.dir_label.setText(d)

    def _do_export(self) -> None:
        if not self._result:
            return
        types = []
        if self.cb_nifti.isChecked(): types.append("nifti")
        if self.cb_csv.isChecked():   types.append("csv")
        if self.cb_pdf.isChecked():   types.append("pdf")
        if self.cb_fhir.isChecked():  types.append("fhir")
        if types and callable(self.on_export_requested):
            self.on_export_requested(types, self._export_dir)


# ===========================================================================
# Main Window
# ===========================================================================

class MainWindow(QMainWindow):
    """Top-level clinical desktop application window."""

    APP_NAME = "Brain Tumour AI"
    ORG_NAME  = "tumor-detection"

    def __init__(self) -> None:
        super().__init__()
        self.storage = get_storage()
        self._thread_pool = QThreadPool.globalInstance()
        self._current_study_id: Optional[str] = None
        self._current_result: Optional[Dict[str, Any]] = None

        self._build_ui()
        self._restore_state()
        self.setWindowTitle(self.APP_NAME)
        self.setMinimumSize(1100, 700)

    # -------------------------------------------------------------------
    # UI construction
    # -------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

    def _build_menu(self) -> None:
        mb = self.menuBar()
        mb.setStyleSheet(
            "QMenuBar { background:#252525; color:#cccccc; } "
            "QMenuBar::item:selected { background:#3a3a3a; } "
            "QMenu { background:#2d2d2d; color:#cccccc; border:1px solid #444; } "
            "QMenu::item:selected { background:#2a5c8f; }"
        )

        file_menu = mb.addMenu("File")
        self._act_open_nifti = QAction("Open NIfTI Volume…", self)
        self._act_open_nifti.setShortcut("Ctrl+O")
        self._act_open_nifti.triggered.connect(self._open_nifti)
        file_menu.addAction(self._act_open_nifti)

        self._act_open_dicom = QAction("Open DICOM Directory…", self)
        self._act_open_dicom.setShortcut("Ctrl+D")
        self._act_open_dicom.triggered.connect(self._open_dicom)
        file_menu.addAction(self._act_open_dicom)

        file_menu.addSeparator()
        quit_act = QAction("Exit", self)
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        help_menu = mb.addMenu("Help")
        about_act = QAction("About", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(22, 22))
        tb.setStyleSheet(
            "QToolBar { background:#252525; border:none; spacing:4px; padding:2px; } "
            "QToolButton { color:#cccccc; padding:4px 10px; border-radius:4px; } "
            "QToolButton:hover { background:#3a3a3a; } "
            "QToolButton:pressed { background:#2a5c8f; }"
        )
        self.addToolBar(tb)

        btn_nifti = QToolButton()
        btn_nifti.setText("Open NIfTI")
        btn_nifti.clicked.connect(self._open_nifti)
        tb.addWidget(btn_nifti)

        btn_dicom = QToolButton()
        btn_dicom.setText("Open DICOM Dir")
        btn_dicom.clicked.connect(self._open_dicom)
        tb.addWidget(btn_dicom)

        tb.addSeparator()

        self.btn_run = QToolButton()
        self.btn_run.setText("Run AI Segmentation")
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet(
            "QToolButton { background:#1f6398; color:white; padding:4px 14px; "
            "border-radius:4px; font-weight:bold; } "
            "QToolButton:hover { background:#2a7abf; } "
            "QToolButton:disabled { background:#3a3a3a; color:#666666; }"
        )
        self.btn_run.clicked.connect(self._run_segmentation)
        tb.addWidget(self.btn_run)

        tb.addSeparator()

        # Overlay toggle
        self.btn_overlay = QToolButton()
        self.btn_overlay.setText("Toggle Overlay")
        self.btn_overlay.setCheckable(True)
        self.btn_overlay.setChecked(True)
        self.btn_overlay.clicked.connect(
            lambda checked: self._mri_canvas.toggle_overlay(checked)
        )
        tb.addWidget(self.btn_overlay)

    def _build_central(self) -> None:
        # Dark background for the whole app
        self.setStyleSheet(
            "QMainWindow, QWidget { background:#1a1a1a; color:#cccccc; } "
            "QSplitter::handle { background:#3a3a3a; }"
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)

        # --- Left: patient panel ---
        self._patient_panel = PatientPanel(self.storage)
        self._patient_panel.on_study_selected = self._on_study_selected
        splitter.addWidget(self._patient_panel)

        # --- Centre: MRI viewer ---
        centre = QWidget()
        centre_layout = QVBoxLayout(centre)
        centre_layout.setContentsMargins(4, 4, 4, 4)
        centre_layout.setSpacing(4)

        self._file_label = QLabel("No volume loaded")
        self._file_label.setStyleSheet("color:#777777; font-size:10px; padding:2px 6px;")
        centre_layout.addWidget(self._file_label)

        self._mri_canvas = MriCanvas(centre)
        centre_layout.addWidget(self._mri_canvas, 1)

        # Slice navigation
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Slice:"))
        self._slice_slider = QSlider(Qt.Orientation.Horizontal)
        self._slice_slider.setRange(0, 0)
        self._slice_slider.setEnabled(False)
        self._slice_slider.setStyleSheet(
            "QSlider::groove:horizontal { background:#3a3a3a; height:4px; border-radius:2px; } "
            "QSlider::handle:horizontal { background:#2a7abf; width:14px; height:14px; "
            "margin:-5px 0; border-radius:7px; }"
        )
        self._slice_slider.valueChanged.connect(self._on_slice_changed)
        slider_row.addWidget(self._slice_slider, 1)
        self._slice_lbl = QLabel("— / —")
        self._slice_lbl.setFixedWidth(60)
        self._slice_lbl.setStyleSheet("color:#888888; font-size:10px;")
        slider_row.addWidget(self._slice_lbl)
        centre_layout.addLayout(slider_row)

        splitter.addWidget(centre)

        # --- Right: clinical panel ---
        right = QWidget()
        right.setMinimumWidth(270)
        right.setMaximumWidth(380)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabWidget::pane { border:1px solid #3a3a3a; } "
            "QTabBar::tab { background:#252525; color:#888888; padding:6px 14px; "
            "border-top-left-radius:4px; border-top-right-radius:4px; } "
            "QTabBar::tab:selected { background:#1a1a1a; color:#cccccc; "
            "border-bottom:2px solid #2a7abf; } "
            "QTabBar::tab:hover { background:#2d2d2d; }"
        )

        self._results_widget = ResultsWidget()
        tabs.addTab(self._results_widget, "Results")

        self._export_widget = ExportWidget()
        self._export_widget.on_export_requested = self._run_export
        tabs.addTab(self._export_widget, "Export")

        right_layout.addWidget(tabs)
        splitter.addWidget(right)

        splitter.setSizes([240, 700, 310])
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _build_statusbar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(
            "QStatusBar { background:#252525; color:#888888; font-size:10px; } "
            "QStatusBar::item { border:none; }"
        )
        self._status_lbl = QLabel("Ready")
        sb.addWidget(self._status_lbl, 1)
        self._status_progress = QProgressBar()
        self._status_progress.setRange(0, 100)
        self._status_progress.setFixedWidth(180)
        self._status_progress.setVisible(False)
        self._status_progress.setStyleSheet(
            "QProgressBar { background:#3a3a3a; border-radius:3px; } "
            "QProgressBar::chunk { background:#2a7abf; }"
        )
        sb.addPermanentWidget(self._status_progress)
        self.setStatusBar(sb)

    # -------------------------------------------------------------------
    # File loading
    # -------------------------------------------------------------------

    def _open_nifti(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open NIfTI Volume", "",
            "NIfTI Files (*.nii *.nii.gz);;All Files (*)"
        )
        if path:
            self._load_file(path)

    def _open_dicom(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open DICOM Directory")
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        patient = Patient(name=Path(path).stem)
        study = Study(patient_id=patient.patient_id, file_path=path)
        self._patient_panel.add_study(patient, study)
        self._activate_study(study)

    def _activate_study(self, study: Study) -> None:
        self._current_study_id = study.study_id
        self._file_label.setText(f"  {Path(study.file_path).name}  "
                                   f"({study.study_id[:8]}…)")
        self._status_lbl.setText(f"Loaded: {Path(study.file_path).name}")
        self.btn_run.setEnabled(True)
        # Light load to display the volume immediately (no inference yet)
        try:
            volume, _ = InferenceWorker(study.file_path, study.study_id)._load_volume(study.file_path)
            n = volume.shape[0]
            self._slice_slider.setRange(0, n - 1)
            self._slice_slider.setValue(n // 2)
            self._slice_slider.setEnabled(True)
            self._mri_canvas.load_volume(volume)
            self._slice_lbl.setText(f"{n // 2 + 1} / {n}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not pre-load volume for display: %s", exc)

    # -------------------------------------------------------------------
    # Study selection from tree
    # -------------------------------------------------------------------

    def _on_study_selected(self, study_id: str) -> None:
        studies = self.storage.get_studies()
        study = next((s for s in studies if s.study_id == study_id), None)
        if study is None:
            return
        self._activate_study(study)
        # If result already exists, show it
        result = self.storage.get_result_for_study(study_id)
        if result:
            self._show_result_in_ui(
                {
                    "study_id": result.study_id,
                    "model": result.model,
                    "model_id": result.model_id,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "tumor_volume_voxels": result.tumor_volume_voxels,
                    "class_volumes_cm3": result.class_volumes_cm3,
                    "processing_time_seconds": result.processing_time_seconds,
                    "mask_path": result.mask_path,
                    "device": result.device,
                    "volume_shape": result.volume_shape,
                }
            )

    # -------------------------------------------------------------------
    # Slice navigation
    # -------------------------------------------------------------------

    def _on_slice_changed(self, value: int) -> None:
        total = self._mri_canvas.slice_count()
        self._slice_lbl.setText(f"{value + 1} / {total}")
        self._mri_canvas.set_slice(value)

    # -------------------------------------------------------------------
    # Inference
    # -------------------------------------------------------------------

    def _run_segmentation(self) -> None:
        if not self._current_study_id:
            return
        studies = self.storage.get_studies()
        study = next((s for s in studies if s.study_id == self._current_study_id), None)
        if study is None:
            return

        self.btn_run.setEnabled(False)
        self.storage.update_study_status(self._current_study_id, StudyStatus.PROCESSING)
        self._patient_panel.refresh()
        self._status_lbl.setText("Segmentation running…")
        self._status_progress.setVisible(True)
        self._results_widget.set_progress(0, "Starting…")

        worker = InferenceWorker(
            file_path=study.file_path,
            study_id=study.study_id,
        )
        worker.signals.progress.connect(self._on_inference_progress)
        worker.signals.finished.connect(self._on_inference_done)
        worker.signals.error.connect(self._on_inference_error)
        self._thread_pool.start(worker)

    def _on_inference_progress(self, pct: int, msg: str) -> None:
        self._status_progress.setValue(pct)
        self._status_lbl.setText(f"Segmentation: {msg}")
        self._results_widget.set_progress(pct, msg)

    def _on_inference_done(self, result: Dict[str, Any]) -> None:
        self._current_result = result
        volume = result.pop("volume", None)
        mask = result.pop("mask", None)
        _affine = result.pop("affine", None)

        # Persist (without numpy arrays)
        pred_result = PredictionResult(
            study_id=result["study_id"],
            model_id=result.get("model_id", "unet"),
            model=result.get("model", "unet"),
            prediction=result["prediction"],
            confidence=result["confidence"],
            tumor_volume_voxels=result["tumor_volume_voxels"],
            class_volumes_cm3=result.get("class_volumes_cm3", {}),
            processing_time_seconds=result.get("processing_time_seconds", 0.0),
            mask_path=result.get("mask_path"),
            device=result.get("device", "cpu"),
            volume_shape=result.get("volume_shape", []),
        )
        self.storage.add_result(pred_result)
        self.storage.update_study_status(result["study_id"], StudyStatus.COMPLETED)

        # Re-attach arrays for display only
        result["volume"] = volume
        result["mask"] = mask

        self._show_result_in_ui(result)
        self._patient_panel.refresh()
        self.btn_run.setEnabled(True)
        self._status_progress.setVisible(False)
        self._status_lbl.setText(
            f"Done  ·  {result.get('prediction','').replace('_',' ')}  "
            f"·  {result.get('processing_time_seconds',0):.1f}s"
        )

    def _on_inference_error(self, err: str) -> None:
        self.btn_run.setEnabled(True)
        self._status_progress.setVisible(False)
        self._status_lbl.setText(f"Error: {err[:80]}")
        self._results_widget.hide_progress()
        if self._current_study_id:
            self.storage.update_study_status(self._current_study_id, StudyStatus.FAILED)
            self._patient_panel.refresh()
        QMessageBox.critical(self, "Segmentation Error", err)

    def _show_result_in_ui(self, result: Dict[str, Any]) -> None:
        self._results_widget.show_result(result)
        self._export_widget.set_result(result)
        volume = result.get("volume")
        mask = result.get("mask")
        if volume is not None and mask is not None:
            self._mri_canvas.load_volume(volume, mask)
            n = volume.shape[0]
            self._slice_slider.setRange(0, n - 1)
            self._slice_slider.setValue(n // 2)
            self._slice_lbl.setText(f"{n // 2 + 1} / {n}")

    # -------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------

    def _run_export(self, types: List[str], export_dir: str) -> None:
        if not self._current_result:
            return
        patient_name = self._export_widget.patient_name_input.text().strip() or "Unknown"
        self._export_widget.set_export_progress(0, "Starting…")

        worker = ExportWorker(
            result={k: v for k, v in self._current_result.items()
                    if not isinstance(v, np.ndarray)},
            export_dir=export_dir,
            export_types=types,
            patient_name=patient_name,
        )
        worker.signals.progress.connect(self._on_export_progress)
        worker.signals.finished.connect(self._on_export_done)
        worker.signals.error.connect(self._on_export_error)
        self._thread_pool.start(worker)

    def _on_export_progress(self, pct: int, msg: str) -> None:
        self._export_widget.set_export_progress(pct, msg)
        self._status_lbl.setText(f"Exporting: {msg}")

    def _on_export_done(self, result: Dict[str, Any]) -> None:
        self._export_widget.finish_export()
        exported = result.get("exported", {})
        paths = "\n".join(f"  {k}: {v}" for k, v in exported.items())
        self._status_lbl.setText(f"Exported {len(exported)} file(s)")
        QMessageBox.information(
            self, "Export Complete",
            f"Files saved:\n{paths}"
        )

    def _on_export_error(self, err: str) -> None:
        self._export_widget.finish_export()
        QMessageBox.critical(self, "Export Error", err)

    # -------------------------------------------------------------------
    # Window state persistence
    # -------------------------------------------------------------------

    def _restore_state(self) -> None:
        settings = QSettings(self.ORG_NAME, self.APP_NAME)
        geo = settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event) -> None:
        settings = QSettings(self.ORG_NAME, self.APP_NAME)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    # -------------------------------------------------------------------
    # About dialog
    # -------------------------------------------------------------------

    def _show_about(self) -> None:
        QMessageBox.about(
            self, f"About {self.APP_NAME}",
            "<b>Brain Tumour AI — Desktop Edition</b><br><br>"
            "PyQt6 desktop application for AI-assisted brain tumour "
            "detection and segmentation.<br><br>"
            "Outputs: NIfTI segmentation mask · CSV volume metrics · "
            "PDF clinical report · FHIR R4 DiagnosticReport bundle.<br><br>"
            "AI backend: MONAI Label · 3D Slicer integration available.<br><br>"
            "<small>Apache 2.0 · github.com/hkevin01/tumor-detection-segmentation</small>"
        )

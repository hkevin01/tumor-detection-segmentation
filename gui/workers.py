"""
Qt worker threads for background inference and export operations.

Uses QRunnable + WorkerSignals(QObject) so long-running tasks never block
the UI thread. Signals are safely emitted across thread boundaries.
"""

import csv
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
    _QT_AVAILABLE = True
except ImportError:  # pragma: no cover — allow import in headless/test envs
    _QT_AVAILABLE = False

    class QObject:  # type: ignore
        pass

    class QRunnable:  # type: ignore
        def setAutoDelete(self, _: bool) -> None: pass

    def pyqtSignal(*_args, **_kwargs):  # type: ignore
        return property()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared signal class
# ---------------------------------------------------------------------------

class WorkerSignals(QObject):
    """Signals for communicating from worker threads back to the main thread."""
    progress = pyqtSignal(int, str)   # (percent 0-100, message)
    finished = pyqtSignal(dict)       # result dict
    error = pyqtSignal(str)           # error message string


# ---------------------------------------------------------------------------
# Inference Worker
# ---------------------------------------------------------------------------

class InferenceWorker(QRunnable):
    """Runs AI tumour segmentation in a background thread.

    Falls back to a synthetic segmentation mask when no model checkpoint is
    available so the application remains demonstrable without a GPU or trained
    weights.
    """

    def __init__(
        self,
        file_path: str,
        study_id: str,
        model_path: Optional[str] = None,
        model_name: str = "unet",
        device: str = "auto",
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self.file_path = file_path
        self.study_id = study_id
        self.model_path = model_path
        self.model_name = model_name
        self.device = device
        self.setAutoDelete(True)

    def run(self) -> None:  # called by QThreadPool
        t_start = datetime.now()
        try:
            self.signals.progress.emit(5, "Loading volume...")
            volume, affine = self._load_volume(self.file_path)

            self.signals.progress.emit(20, "Running segmentation...")
            mask, device_used = self._run_inference(volume)

            self.signals.progress.emit(80, "Computing metrics...")
            voxel_mm3 = self._voxel_volume_mm3(affine)
            class_vols = self._class_volumes(mask, voxel_mm3)
            total_voxels = float(np.sum(mask > 0))

            self.signals.progress.emit(90, "Saving NIfTI mask...")
            mask_path = self._save_mask(mask, affine, self.study_id)

            elapsed = (datetime.now() - t_start).total_seconds()
            self.signals.progress.emit(100, "Segmentation complete")

            self.signals.finished.emit({
                "study_id": self.study_id,
                "model_id": self.model_name,
                "model": self.model_name,
                "prediction": "tumor_detected" if total_voxels > 50 else "no_tumor",
                "confidence": min(0.99, max(0.10, float(np.mean(mask > 0)))),
                "tumor_volume_voxels": total_voxels,
                "class_volumes_cm3": class_vols,
                "processing_time_seconds": elapsed,
                "mask_path": str(mask_path),
                "device": device_used,
                "volume_shape": list(volume.shape),
                # Pass arrays for in-process display (not persisted)
                "volume": volume,
                "mask": mask,
                "affine": affine,
            })

        except Exception as exc:  # noqa: BLE001
            logger.exception("Inference failed for study %s", self.study_id)
            self.signals.error.emit(str(exc))

    # --- private helpers ---

    def _load_volume(self, file_path: str):
        """Load NIfTI, DICOM directory, or NumPy volume.
        Returns (float32 ndarray shape (D,H,W), affine 4x4)."""
        path = Path(file_path)

        # NIfTI
        if path.suffix in {".gz", ".nii"} or str(path).endswith(".nii.gz"):
            try:
                import nibabel as nib  # type: ignore
                img = nib.load(str(path))
                data = np.asarray(img.dataobj, dtype=np.float32)
                affine = img.affine
                if data.ndim == 4:
                    data = data[..., 0]  # first modality
                return data, affine
            except ImportError:
                logger.warning("nibabel not available; falling back for %s", file_path)

        # DICOM directory
        if path.is_dir():
            try:
                import pydicom  # type: ignore
                dcm_files = sorted(path.glob("**/*.dcm"))
                if dcm_files:
                    slices = sorted(
                        [pydicom.dcmread(str(f)) for f in dcm_files],
                        key=lambda s: float(getattr(s, "InstanceNumber", 0)),
                    )
                    vol = np.stack(
                        [s.pixel_array for s in slices], axis=0
                    ).astype(np.float32)
                    return vol, np.eye(4)
            except ImportError:
                logger.warning("pydicom not available; falling back for %s", file_path)

        # NumPy .npy
        if path.suffix == ".npy" and path.exists():
            return np.load(str(path)).astype(np.float32), np.eye(4)

        # Synthetic / demo
        logger.warning("Cannot load %s — using synthetic 64³ volume", file_path)
        rng = np.random.default_rng(seed=42)
        return rng.random((64, 64, 64), dtype=np.float32), np.eye(4)

    def _run_inference(self, volume: np.ndarray):
        """Run model inference or generate a synthetic mask for demo."""
        if self.model_path and Path(self.model_path).exists():
            try:
                import torch  # type: ignore
                from src.clinical.monai_label_app import TumorSegmentationInfer  # type: ignore

                device_used = "cuda" if torch.cuda.is_available() else "cpu"
                infer = TumorSegmentationInfer(
                    model_path=self.model_path, device=device_used
                )
                result = infer(self.file_path)
                mask_path = result.get("segmentation", "")
                if mask_path and Path(str(mask_path)).exists():
                    try:
                        import nibabel as nib  # type: ignore
                        mask_img = nib.load(str(mask_path))
                        return np.asarray(mask_img.dataobj, dtype=np.int32), device_used
                    except ImportError:
                        pass
            except Exception as exc:  # noqa: BLE001
                logger.warning("Model inference failed (%s); using synthetic mask", exc)

        return self._synthetic_mask(volume), "synthetic (demo)"

    def _synthetic_mask(self, volume: np.ndarray) -> np.ndarray:
        """Ellipsoidal 3-class mask centred in the volume for demo."""
        s = volume.shape
        zz = np.arange(s[0])[:, None, None]
        yy = np.arange(s[1])[None, :, None]
        xx = np.arange(s[2])[None, None, :]
        c = np.array(s) // 2
        d2 = (
            ((zz - c[0]) / (s[0] * 0.15)) ** 2
            + ((yy - c[1]) / (s[1] * 0.12)) ** 2
            + ((xx - c[2]) / (s[2] * 0.12)) ** 2
        )
        mask = np.zeros(s, dtype=np.int32)
        mask[d2 < 1.0] = 3   # peritumoral edema (ED)
        mask[d2 < 0.5] = 2   # enhancing tumour (ET)
        mask[d2 < 0.2] = 1   # necrotic core (NCR)
        return mask

    def _voxel_volume_mm3(self, affine: np.ndarray) -> float:
        vox = np.sqrt(np.sum(affine[:3, :3] ** 2, axis=0))
        return float(np.prod(vox))

    def _class_volumes(self, mask: np.ndarray, vox_mm3: float) -> Dict[str, float]:
        mm3_per_cm3 = 1000.0
        return {
            "necrotic_core_cm3": float(np.sum(mask == 1)) * vox_mm3 / mm3_per_cm3,
            "enhancing_tumour_cm3": float(np.sum(mask == 2)) * vox_mm3 / mm3_per_cm3,
            "peritumoral_edema_cm3": float(np.sum(mask == 3)) * vox_mm3 / mm3_per_cm3,
            "whole_tumour_cm3": float(np.sum(mask > 0)) * vox_mm3 / mm3_per_cm3,
        }

    def _save_mask(self, mask: np.ndarray, affine: np.ndarray, study_id: str) -> Path:
        masks_dir = Path("./masks")
        masks_dir.mkdir(parents=True, exist_ok=True)
        nifti_path = masks_dir / f"{study_id}_mask.nii.gz"
        try:
            import nibabel as nib  # type: ignore
            nib.save(nib.Nifti1Image(mask, affine), str(nifti_path))
            return nifti_path
        except ImportError:
            npy_path = masks_dir / f"{study_id}_mask.npy"
            np.save(str(npy_path), mask)
            return npy_path


# ---------------------------------------------------------------------------
# Export Worker
# ---------------------------------------------------------------------------

class ExportWorker(QRunnable):
    """Exports segmentation results: NIfTI mask, CSV metrics, PDF report,
    FHIR R4 DiagnosticReport bundle. Each export type is independently optional.
    """

    def __init__(
        self,
        result: Dict[str, Any],
        export_dir: str,
        export_types: List[str],   # subset of ["nifti","csv","pdf","fhir"]
        patient_name: str = "Unknown",
        patient_id: str = "",
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self.result = result
        self.export_dir = Path(export_dir)
        self.export_types = export_types
        self.patient_name = patient_name
        self.patient_id = patient_id or str(result.get("study_id", "unknown"))
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            exported: Dict[str, str] = {}
            n = max(len(self.export_types), 1)

            for i, etype in enumerate(self.export_types):
                self.signals.progress.emit(int(i / n * 90), f"Exporting {etype}…")
                if etype == "nifti":
                    p = self._export_nifti()
                    if p:
                        exported["nifti"] = str(p)
                elif etype == "csv":
                    exported["csv"] = str(self._export_csv())
                elif etype == "pdf":
                    exported["pdf"] = str(self._export_pdf())
                elif etype == "fhir":
                    exported["fhir"] = str(self._export_fhir())

            self.signals.progress.emit(100, "Export complete")
            self.signals.finished.emit({"exported": exported})

        except Exception as exc:  # noqa: BLE001
            logger.exception("Export failed")
            self.signals.error.emit(str(exc))

    # --- exporters ---

    def _export_nifti(self) -> Optional[Path]:
        src_str = self.result.get("mask_path") or ""
        src = Path(src_str)
        if not src.exists():
            return None
        dst = self.export_dir / src.name
        shutil.copy2(str(src), str(dst))
        return dst

    def _export_csv(self) -> Path:
        sid = self.result.get("study_id", "unknown")
        path = self.export_dir / f"metrics_{sid}.csv"
        vols = self.result.get("class_volumes_cm3", {})
        rows = [
            ["Metric", "Value", "Unit"],
            ["Patient", self.patient_name, ""],
            ["Study ID", sid, ""],
            ["Prediction", self.result.get("prediction", ""), ""],
            ["Confidence", f"{self.result.get('confidence', 0):.3f}", ""],
            ["Whole Tumour Volume", f"{vols.get('whole_tumour_cm3', 0):.2f}", "cm³"],
            ["Enhancing Tumour Volume", f"{vols.get('enhancing_tumour_cm3', 0):.2f}", "cm³"],
            ["Necrotic Core Volume", f"{vols.get('necrotic_core_cm3', 0):.2f}", "cm³"],
            ["Peritumoral Edema Volume", f"{vols.get('peritumoral_edema_cm3', 0):.2f}", "cm³"],
            ["Segmentation Time", f"{self.result.get('processing_time_seconds', 0):.2f}", "seconds"],
            ["Model", self.result.get("model", ""), ""],
            ["Device", self.result.get("device", ""), ""],
            ["Volume Shape", str(self.result.get("volume_shape", "")), "voxels"],
            ["Timestamp", datetime.now().isoformat(), ""],
        ]
        with open(str(path), "w", newline="") as fh:
            csv.writer(fh).writerows(rows)
        return path

    def _export_pdf(self) -> Path:
        sid = self.result.get("study_id", "unknown")
        path = self.export_dir / f"report_{sid}.pdf"
        vols = self.result.get("class_volumes_cm3", {})
        wt = max(vols.get("whole_tumour_cm3", 0.001), 0.001)

        def pct(v: float) -> str:
            return f"{100 * v / wt:.1f}%"

        try:
            from reportlab.lib import colors  # type: ignore
            from reportlab.lib.pagesizes import A4  # type: ignore
            from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
            from reportlab.lib.units import cm  # type: ignore
            from reportlab.platypus import (  # type: ignore
                Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
            )

            doc = SimpleDocTemplate(str(path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("Brain Tumour Segmentation Report", styles["Title"]))
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph(
                f"<i>Generated: {datetime.now().strftime('%Y-%m-%d  %H:%M')}</i>",
                styles["Normal"],
            ))
            story.append(Spacer(1, 0.6 * cm))

            story.append(Paragraph("Patient Information", styles["Heading2"]))
            t_patient = Table([
                ["Patient Name", self.patient_name],
                ["Patient ID", self.patient_id],
                ["Study ID", self.result.get("study_id", "N/A")],
                ["Model", self.result.get("model", "N/A")],
                ["Device", self.result.get("device", "N/A")],
            ], colWidths=[6 * cm, 11 * cm])
            t_patient.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t_patient)
            story.append(Spacer(1, 0.6 * cm))

            pred = self.result.get("prediction", "N/A").replace("_", " ").title()
            conf = self.result.get("confidence", 0)
            story.append(Paragraph("AI Findings", styles["Heading2"]))
            story.append(Paragraph(
                f"<b>Prediction:</b> {pred} &nbsp;&nbsp; <b>Confidence:</b> {conf:.1%}",
                styles["Normal"],
            ))
            story.append(Spacer(1, 0.4 * cm))

            story.append(Paragraph("Tumour Volume Measurements", styles["Heading2"]))
            t_vols = Table([
                ["Sub-region", "Volume (cm³)", "% of Whole Tumour"],
                ["Whole Tumour (WT)", f"{wt:.2f}", "100.0%"],
                ["Enhancing Tumour (ET)", f"{vols.get('enhancing_tumour_cm3', 0):.2f}",
                 pct(vols.get("enhancing_tumour_cm3", 0))],
                ["Necrotic Core (NCR)", f"{vols.get('necrotic_core_cm3', 0):.2f}",
                 pct(vols.get("necrotic_core_cm3", 0))],
                ["Peritumoral Edema (ED)", f"{vols.get('peritumoral_edema_cm3', 0):.2f}",
                 pct(vols.get("peritumoral_edema_cm3", 0))],
            ], colWidths=[7 * cm, 5 * cm, 5 * cm])
            t_vols.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(t_vols)
            story.append(Spacer(1, 0.6 * cm))

            story.append(Paragraph("Technical Details", styles["Heading2"]))
            t_tech = Table([
                ["Parameter", "Value"],
                ["Segmentation Time", f"{self.result.get('processing_time_seconds', 0):.2f} s"],
                ["Volume Shape", str(self.result.get("volume_shape", "N/A"))],
            ], colWidths=[7 * cm, 10 * cm])
            t_tech.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ]))
            story.append(t_tech)
            story.append(Spacer(1, 0.8 * cm))
            story.append(Paragraph(
                "<i>This report is AI-generated. Radiologist sign-off required before clinical use.</i>",
                styles["Normal"],
            ))
            doc.build(story)

        except ImportError:
            # Plain-text fallback when reportlab is not installed
            txt = path.with_suffix(".txt")
            lines = [
                "BRAIN TUMOUR SEGMENTATION REPORT",
                "=" * 50,
                f"Generated : {datetime.now().isoformat()}",
                f"Patient   : {self.patient_name}",
                f"Study ID  : {self.result.get('study_id', 'N/A')}",
                "",
                "FINDINGS",
                f"  Prediction  : {self.result.get('prediction', 'N/A')}",
                f"  Confidence  : {self.result.get('confidence', 0):.1%}",
                "",
                "VOLUMES",
                f"  Whole Tumour         : {wt:.2f} cm³",
                f"  Enhancing Tumour     : {vols.get('enhancing_tumour_cm3', 0):.2f} cm³",
                f"  Necrotic Core        : {vols.get('necrotic_core_cm3', 0):.2f} cm³",
                f"  Peritumoral Edema    : {vols.get('peritumoral_edema_cm3', 0):.2f} cm³",
                "",
                f"Segmentation time : {self.result.get('processing_time_seconds', 0):.2f} s",
                "",
                "NOTE: reportlab not installed. PDF not generated; plain text saved instead.",
            ]
            txt.write_text("\n".join(lines))
            path = txt

        return path

    def _export_fhir(self) -> Path:
        """Export FHIR R4 DiagnosticReport Bundle as JSON."""
        sid = self.result.get("study_id", "unknown")
        path = self.export_dir / f"fhir_{sid}.json"
        vols = self.result.get("class_volumes_cm3", {})

        bundle = {
            "resourceType": "Bundle",
            "id": sid,
            "type": "document",
            "timestamp": datetime.now().isoformat() + "Z",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": self.patient_id,
                        "name": [{"text": self.patient_name}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "DiagnosticReport",
                        "id": sid,
                        "status": "final",
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "24606-4",
                                "display": "MR Brain with contrast WO and W",
                            }]
                        },
                        "subject": {"reference": f"Patient/{self.patient_id}"},
                        "issued": datetime.now().isoformat() + "Z",
                        "conclusion": (
                            f"{self.result.get('prediction', 'N/A').replace('_', ' ')}. "
                            f"Whole tumour volume: {vols.get('whole_tumour_cm3', 0):.2f} cm³. "
                            f"Confidence: {self.result.get('confidence', 0):.1%}. "
                            "Requires radiologist sign-off."
                        ),
                        "result": [
                            {
                                "resourceType": "Observation",
                                "status": "final",
                                "code": {
                                    "coding": [{
                                        "system": "http://loinc.org",
                                        "code": "59772-4",
                                        "display": "Tumor volume",
                                    }]
                                },
                                "component": [
                                    {
                                        "code": {"text": label},
                                        "valueQuantity": {
                                            "value": round(val, 3),
                                            "unit": "cm3",
                                            "system": "http://unitsofmeasure.org",
                                            "code": "cm3",
                                        },
                                    }
                                    for label, val in vols.items()
                                ],
                            }
                        ],
                        "extension": [{
                            "url": "http://tumor-detection-ai.local/segmentation-metadata",
                            "extension": [
                                {"url": "model", "valueString": self.result.get("model", "")},
                                {"url": "device", "valueString": self.result.get("device", "")},
                                {
                                    "url": "processing_time_seconds",
                                    "valueDecimal": round(
                                        self.result.get("processing_time_seconds", 0), 3
                                    ),
                                },
                            ],
                        }],
                    }
                },
            ],
        }

        path.write_text(json.dumps(bundle, indent=2))
        return path

"""
DICOM Server Core Module

This module implements the foundation for a DICOM server that can receive,
store, and serve medical images for the hospital workflow integration.

Features:
- DICOM C-STORE SCP (Storage Service Class Provider)
- DICOM C-FIND SCP (Query/Retrieve Service Class Provider)
- DICOM C-MOVE SCP (Move Service Class Provider)
- DICOM Echo SCP (Verification Service Class Provider)
- Integration with AI processing pipeline
- Audit logging and security features
"""

import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from pydicom import Dataset
    from pydicom.uid import UID
    from pynetdicom import AE, AllStoragePresentationContexts, evt
    from pynetdicom.sop_class import (
        StudyRootQueryRetrieveInformationModelFind,
        StudyRootQueryRetrieveInformationModelMove, Verification)
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    Dataset = None
    AE = None
    evt = None


logger = logging.getLogger(__name__)


class DICOMServerConfig:
    """Configuration for DICOM server operations."""

    def __init__(self):
        self.ae_title = "TUMOR_AI_SCP"
        self.bind_address = "localhost"
        self.port = 11112
        self.storage_path = Path("data/dicom_storage")
        self.max_pdu_size = 16384
        self.network_timeout = 30
        self.acse_timeout = 30
        self.dimse_timeout = 30

        # Security settings
        self.require_calling_ae_title = False
        self.allowed_ae_titles = []
        self.require_authentication = False

        # Storage settings
        self.auto_create_directories = True
        self.organize_by_study = True
        self.organize_by_patient = True

        # AI Processing settings
        self.enable_ai_processing = True
        self.ai_processing_queue = "redis://localhost:6379/0"
        self.ai_processing_timeout = 300  # 5 minutes

        # Audit logging
        self.enable_audit_logging = True
        self.audit_log_path = Path("logs/dicom_audit.log")


class DICOMServer:
    """
    DICOM Server for hospital workflow integration.

    Implements DICOM network services for receiving, storing, and serving
    medical images with integration to AI processing pipeline.
    """

    def __init__(self, config: Optional[DICOMServerConfig] = None):
        if not DICOM_AVAILABLE:
            raise ImportError(
                "pydicom and pynetdicom are required for DICOM server functionality. "
                "Install with: pip install pydicom pynetdicom"
            )

        self.config = config or DICOMServerConfig()
        self.ae = None
        self.is_running = False
        self.server_thread = None

        # Initialize storage
        self._setup_storage()

        # Initialize audit logging
        self._setup_audit_logging()

        # Statistics
        self.stats = {
            'studies_received': 0,
            'images_stored': 0,
            'queries_processed': 0,
            'moves_processed': 0,
            'errors': 0,
            'start_time': None
        }

    def _setup_storage(self):
        """Set up DICOM storage directories."""
        if self.config.auto_create_directories:
            self.config.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"DICOM storage initialized at: {self.config.storage_path}")

    def _setup_audit_logging(self):
        """Set up audit logging for DICOM operations."""
        if self.config.enable_audit_logging:
            audit_logger = logging.getLogger('dicom_audit')
            audit_logger.setLevel(logging.INFO)

            # Create audit log directory
            self.config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

            # File handler for audit logs
            handler = logging.FileHandler(self.config.audit_log_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            audit_logger.addHandler(handler)

            self.audit_logger = audit_logger
            logger.info("DICOM audit logging enabled")

    def start_server(self):
        """Start the DICOM server in a separate thread."""
        if self.is_running:
            logger.warning("DICOM server is already running")
            return

        logger.info("Starting DICOM server...")

        # Create Application Entity
        self.ae = AE(ae_title=self.config.ae_title)

        # Add supported presentation contexts
        self._add_presentation_contexts()

        # Add event handlers
        self._add_event_handlers()

        # Start server in separate thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()

        # Wait a moment for server to start
        time.sleep(1)

        if self.is_running:
            self.stats['start_time'] = datetime.now()
            logger.info(
                f"DICOM server started successfully on {self.config.bind_address}:"
                f"{self.config.port} (AE Title: {self.config.ae_title})"
            )
        else:
            logger.error("Failed to start DICOM server")

    def stop_server(self):
        """Stop the DICOM server."""
        if not self.is_running:
            logger.warning("DICOM server is not running")
            return

        logger.info("Stopping DICOM server...")
        self.is_running = False

        if self.ae:
            self.ae.shutdown()

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)

        logger.info("DICOM server stopped")

    def _add_presentation_contexts(self):
        """Add supported DICOM presentation contexts."""
        # Storage Service Class Provider
        self.ae.supported_contexts = AllStoragePresentationContexts

        # Query/Retrieve Service Class Provider
        self.ae.add_supported_context(StudyRootQueryRetrieveInformationModelFind)
        self.ae.add_supported_context(StudyRootQueryRetrieveInformationModelMove)

        # Verification Service Class Provider
        self.ae.add_supported_context(Verification)

        logger.info("Added DICOM presentation contexts")

    def _add_event_handlers(self):
        """Add DICOM event handlers."""
        # Storage events
        self.ae.add_handlers([
            (evt.EVT_C_STORE, self._handle_store),
            (evt.EVT_C_FIND, self._handle_find),
            (evt.EVT_C_MOVE, self._handle_move),
            (evt.EVT_C_ECHO, self._handle_echo),
            (evt.EVT_CONN_OPEN, self._handle_connection_open),
            (evt.EVT_CONN_CLOSE, self._handle_connection_close),
        ])

        logger.info("Added DICOM event handlers")

    def _run_server(self):
        """Run the DICOM server."""
        try:
            self.is_running = True
            self.ae.start_server(
                (self.config.bind_address, self.config.port),
                block=True,
                evt_handlers=None  # Handlers already added
            )
        except Exception as e:
            logger.error(f"DICOM server error: {e}")
            self.is_running = False

    def _handle_store(self, event):
        """Handle C-STORE requests (incoming DICOM images)."""
        try:
            # Get the dataset
            ds = event.dataset

            # Generate storage path
            storage_path = self._get_storage_path(ds)

            # Save the dataset
            ds.save_as(storage_path, write_like_original=False)

            # Update statistics
            self.stats['images_stored'] += 1

            # Audit log
            if hasattr(self, 'audit_logger'):
                self.audit_logger.info(
                    f"C-STORE: Stored image {ds.get('SOPInstanceUID', 'Unknown')} "
                    f"from {event.assoc.requestor.ae_title}"
                )

            # Queue for AI processing if enabled
            if self.config.enable_ai_processing:
                self._queue_ai_processing(ds, storage_path)

            logger.info(f"Stored DICOM image: {storage_path}")

            # Return success status
            return 0x0000

        except Exception as e:
            logger.error(f"Error handling C-STORE: {e}")
            self.stats['errors'] += 1
            return 0xC000  # Failure status

    def _handle_find(self, event):
        """Handle C-FIND requests (DICOM queries)."""
        try:
            # This is a basic implementation - in production you'd want
            # a proper DICOM database with query capabilities
            logger.info("C-FIND request received")

            self.stats['queries_processed'] += 1

            # Audit log
            if hasattr(self, 'audit_logger'):
                self.audit_logger.info(
                    f"C-FIND: Query from {event.assoc.requestor.ae_title}"
                )

            # Return no matches for now (basic implementation)
            yield 0xFF00, None

        except Exception as e:
            logger.error(f"Error handling C-FIND: {e}")
            self.stats['errors'] += 1

    def _handle_move(self, event):
        """Handle C-MOVE requests (DICOM retrievals)."""
        try:
            logger.info("C-MOVE request received")

            self.stats['moves_processed'] += 1

            # Audit log
            if hasattr(self, 'audit_logger'):
                self.audit_logger.info(
                    f"C-MOVE: Request from {event.assoc.requestor.ae_title}"
                )

            # Basic implementation - return no matches
            yield 0x0000, None

        except Exception as e:
            logger.error(f"Error handling C-MOVE: {e}")
            self.stats['errors'] += 1

    def _handle_echo(self, event):
        """Handle C-ECHO requests (DICOM verification)."""
        logger.info("C-ECHO request received")

        # Audit log
        if hasattr(self, 'audit_logger'):
            self.audit_logger.info(
                f"C-ECHO: Request from {event.assoc.requestor.ae_title}"
            )

        return 0x0000  # Success

    def _handle_connection_open(self, event):
        """Handle connection open events."""
        logger.info(f"DICOM connection opened from {event.assoc.requestor.ae_title}")

    def _handle_connection_close(self, event):
        """Handle connection close events."""
        logger.info(f"DICOM connection closed from {event.assoc.requestor.ae_title}")

    def _get_storage_path(self, dataset: Dataset) -> Path:
        """Generate storage path for DICOM dataset."""
        base_path = self.config.storage_path

        # Organize by patient and study if configured
        if self.config.organize_by_patient:
            patient_id = dataset.get('PatientID', 'Unknown')
            # Sanitize patient ID for filesystem
            patient_id = self._sanitize_filename(patient_id)
            base_path = base_path / patient_id

        if self.config.organize_by_study:
            study_uid = dataset.get('StudyInstanceUID', 'Unknown')
            study_uid = self._sanitize_filename(study_uid)
            base_path = base_path / study_uid

        # Create directory
        base_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        sop_instance_uid = dataset.get('SOPInstanceUID', 'Unknown')
        filename = f"{self._sanitize_filename(sop_instance_uid)}.dcm"

        return base_path / filename

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as filename."""
        import re

        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Limit length
        return sanitized[:100]

    def _queue_ai_processing(self, dataset: Dataset, file_path: Path):
        """Queue DICOM image for AI processing."""
        try:
            # In a full implementation, this would add the image to a processing queue
            # For now, just log that it would be queued
            study_uid = dataset.get('StudyInstanceUID', 'Unknown')
            series_uid = dataset.get('SeriesInstanceUID', 'Unknown')

            logger.info(
                f"Queued for AI processing: Study {study_uid}, "
                f"Series {series_uid}, File {file_path}"
            )

            # TODO: Integrate with Redis/Celery queue or similar
            # TODO: Trigger AI inference pipeline
            # TODO: Store results and generate reports

        except Exception as e:
            logger.error(f"Error queuing AI processing: {e}")

    def get_status(self) -> Dict:
        """Get server status and statistics."""
        uptime = None
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']

        return {
            'running': self.is_running,
            'ae_title': self.config.ae_title,
            'bind_address': self.config.bind_address,
            'port': self.config.port,
            'uptime': str(uptime) if uptime else None,
            'statistics': self.stats.copy(),
            'storage_path': str(self.config.storage_path),
            'ai_processing_enabled': self.config.enable_ai_processing
        }


def create_dicom_server(config: Optional[DICOMServerConfig] = None) -> DICOMServer:
    """Create and configure a DICOM server instance."""
    return DICOMServer(config)


if __name__ == "__main__":
    # Basic test/demo
    import sys

    if not DICOM_AVAILABLE:
        print("DICOM libraries not available. Install with: pip install pydicom pynetdicom")
        sys.exit(1)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and start server
    config = DICOMServerConfig()
    config.port = 11112  # Standard DICOM port

    server = create_dicom_server(config)

    try:
        server.start_server()
        print(f"DICOM server running on port {config.port}. Press Ctrl+C to stop.")

        # Keep running until interrupted
        while server.is_running:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down DICOM server...")
        server.stop_server()
    except Exception as e:
        print(f"Error: {e}")
        server.stop_server()
        sys.exit(1)

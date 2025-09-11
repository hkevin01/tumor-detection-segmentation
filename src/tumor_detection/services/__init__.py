"""
Medical Services Integration Module

Service integrations for medical imaging workflows
"""

# Import all service modules
try:
    from .dicom import DicomClient, DicomService
except ImportError:
    DicomService = None
    DicomClient = None

try:
    from .fhir import FhirClient, FhirService
except ImportError:
    FhirService = None
    FhirClient = None

try:
    from .cloud import CloudComputeClient, CloudService, CloudStorageClient
except ImportError:
    CloudService = None
    CloudStorageClient = None
    CloudComputeClient = None

__all__ = [
    # DICOM Services
    "DicomService",
    "DicomClient",
    # FHIR Services
    "FhirService",
    "FhirClient",
    # Cloud Services
    "CloudService",
    "CloudStorageClient",
    "CloudComputeClient",
]

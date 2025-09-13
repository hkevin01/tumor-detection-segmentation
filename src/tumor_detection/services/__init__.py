"""
Medical Services Integration Module

NASA-STD-8739.8 Requirement Implementation Traceability:
=========================================================

REQ-I-001: DICOM Interface
- DICOM service integration for medical imaging workflows
- Hospital PACS system connectivity and interoperability
- Standard DICOM protocol compliance for clinical integration

REQ-I-004: FHIR Interface
- FHIR service integration for healthcare interoperability
- Clinical data exchange and patient record management
- Standard healthcare data interchange protocols

REQ-F-008: Clinical User Interface (Service Backend)
- Service integration layer for clinical applications
- Medical workflow automation and system integration
- Clinical data processing and management services

REQ-F-006: Medical Data Security Framework (Service Security)
- Secure medical service communication protocols
- Encrypted data transmission for medical services
- Compliance with healthcare data security standards

REQ-I-002: Clinical Interface (Service Integration)
- Clinical system integration through standardized services
- Healthcare workflow automation and data exchange
- Interoperability with existing hospital systems

REQ-NF-R-001: System Availability (Service Reliability)
- Reliable medical service provision for clinical operations
- High availability service architecture
- Robust service communication and error handling

REQ-F-004: Clinical Deployment Automation (Service Deployment)
- Automated service deployment for clinical environments
- Cloud service integration for scalable healthcare solutions
- Service orchestration and management

Technical Implementation:
- Comprehensive medical service integration layer
- DICOM, FHIR, and cloud service connectivity
- Production-ready healthcare service architecture
- Clinical-grade security and compliance

Author: Medical Imaging AI Team
Classification: Unclassified
Version: 2.0
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

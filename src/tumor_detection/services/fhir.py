"""
FHIR (Fast Healthcare Interoperability Resources) service integration
Provides standardized healthcare data exchange capabilities
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    requests = None


class FhirClient:
    """
    FHIR client for healthcare data integration
    """

    def __init__(self,
                 base_url: str,
                 auth_token: Optional[str] = None,
                 timeout: int = 30):
        """
        Initialize FHIR client

        Args:
            base_url: FHIR server base URL
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> Optional[Any]:
        """Create HTTP session with authentication"""
        if requests is None:
            return None

        session = requests.Session()
        if self.auth_token:
            session.headers.update({
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/fhir+json'
            })
        return session

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieve patient resource

        Args:
            patient_id: FHIR patient identifier

        Returns:
            Patient resource as dictionary
        """
        if not self.session:
            return {"error": "requests library not available"}

        try:
            url = urljoin(f"{self.base_url}/", f"Patient/{patient_id}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to retrieve patient: {str(e)}"}

    def search_imaging_studies(self,
                             patient_id: Optional[str] = None,
                             modality: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for imaging studies

        Args:
            patient_id: Optional patient identifier filter
            modality: Optional imaging modality filter (e.g., 'MR', 'CT')

        Returns:
            Bundle of ImagingStudy resources
        """
        if not self.session:
            return {"error": "requests library not available"}

        try:
            url = urljoin(f"{self.base_url}/", "ImagingStudy")
            params = {}

            if patient_id:
                params['patient'] = patient_id
            if modality:
                params['modality'] = modality

            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to search imaging studies: {str(e)}"}

    def create_diagnostic_report(self,
                               patient_id: str,
                               imaging_study_id: str,
                               findings: List[str],
                               conclusion: str) -> Dict[str, Any]:
        """
        Create diagnostic report for tumor detection results

        Args:
            patient_id: FHIR patient identifier
            imaging_study_id: Related imaging study identifier
            findings: List of clinical findings
            conclusion: Diagnostic conclusion

        Returns:
            Created DiagnosticReport resource
        """
        if not self.session:
            return {"error": "requests library not available"}

        report = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "RAD",
                    "display": "Radiology"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "18748-4",
                    "display": "Diagnostic imaging study"
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "imagingStudy": [{
                "reference": f"ImagingStudy/{imaging_study_id}"
            }],
            "conclusion": conclusion,
            "presentedForm": [{
                "contentType": "text/plain",
                "data": "\n".join(findings)
            }]
        }

        try:
            url = urljoin(f"{self.base_url}/", "DiagnosticReport")
            response = self.session.post(
                url,
                json=report,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to create diagnostic report: {str(e)}"}


class FhirService:
    """
    High-level FHIR service for medical imaging workflows
    """

    def __init__(self,
                 fhir_config: Dict[str, str]):
        """
        Initialize FHIR service

        Args:
            fhir_config: Configuration dictionary with server details
        """
        self.config = fhir_config
        self.client = FhirClient(
            base_url=fhir_config.get('server_url', 'http://localhost:8080/fhir'),
            auth_token=fhir_config.get('auth_token'),
            timeout=fhir_config.get('timeout', 30)
        )

    def integrate_tumor_detection_results(self,
                                        patient_id: str,
                                        imaging_study_id: str,
                                        detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate tumor detection results into FHIR workflow

        Args:
            patient_id: Patient identifier
            imaging_study_id: Imaging study identifier
            detection_results: AI model detection results

        Returns:
            Integration status and created resources
        """
        try:
            # Extract findings from detection results
            findings = []
            if detection_results.get('tumors_detected'):
                findings.append(f"Tumor detected with confidence: {detection_results.get('confidence', 'unknown')}")

                if 'tumor_location' in detection_results:
                    findings.append(f"Location: {detection_results['tumor_location']}")

                if 'tumor_size' in detection_results:
                    findings.append(f"Estimated size: {detection_results['tumor_size']}")
            else:
                findings.append("No tumors detected in imaging study")

            # Create conclusion
            confidence = detection_results.get('confidence', 0)
            if confidence > 0.8:
                conclusion = "High confidence tumor detection result"
            elif confidence > 0.5:
                conclusion = "Moderate confidence tumor detection result"
            else:
                conclusion = "Low confidence result - recommend review"

            # Create diagnostic report
            report = self.client.create_diagnostic_report(
                patient_id=patient_id,
                imaging_study_id=imaging_study_id,
                findings=findings,
                conclusion=conclusion
            )

            return {
                "success": True,
                "diagnostic_report": report,
                "findings_count": len(findings)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"FHIR integration failed: {str(e)}"
            }

    def get_patient_imaging_history(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieve patient's imaging history for context

        Args:
            patient_id: Patient identifier

        Returns:
            Patient imaging history summary
        """
        try:
            # Get patient details
            patient = self.client.get_patient(patient_id)

            # Search for imaging studies
            studies = self.client.search_imaging_studies(patient_id=patient_id)

            return {
                "success": True,
                "patient": patient,
                "imaging_studies": studies
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve patient history: {str(e)}"
            }


# Convenience functions
def create_fhir_service(config_path: Optional[str] = None) -> FhirService:
    """
    Create FHIR service from configuration

    Args:
        config_path: Path to FHIR configuration file

    Returns:
        Configured FHIR service instance
    """
    if config_path:
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception:
            config = {"server_url": "http://localhost:8080/fhir"}
    else:
        # Default configuration
        config = {
            "server_url": "http://localhost:8080/fhir",
            "timeout": 30
        }

    return FhirService(config)


def integrate_results_with_fhir(patient_id: str,
                               study_id: str,
                               results: Dict[str, Any],
                               fhir_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Convenience function to integrate detection results with FHIR

    Args:
        patient_id: Patient identifier
        study_id: Imaging study identifier
        results: Detection results
        fhir_config: Optional FHIR configuration

    Returns:
        Integration result
    """
    config = fhir_config or {"server_url": "http://localhost:8080/fhir"}
    service = FhirService(config)

    return service.integrate_tumor_detection_results(
        patient_id=patient_id,
        imaging_study_id=study_id,
        detection_results=results
    )

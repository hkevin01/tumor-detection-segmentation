"""
GUI Integration Utility for Tumor Detection System.

This script provides utilities to register studies and push overlay predictions
to the GUI backend for visualization.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional

import requests


class GUIIntegrationClient:
    """Client for integrating with the tumor detection GUI."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize GUI integration client.

        Args:
            base_url: Base URL of the GUI backend API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def register_study(
        self,
        study_id: str,
        patient_id: str,
        image_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Register a new study with the GUI backend.

        Args:
            study_id: Unique study identifier
            patient_id: Patient identifier
            image_path: Path to the medical image
            metadata: Optional metadata dictionary

        Returns:
            Response from the API
        """
        endpoint = f"{self.base_url}/api/studies"

        payload = {
            "study_id": study_id,
            "patient_id": patient_id,
            "image_path": image_path,
            "metadata": metadata or {}
        }

        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}

    def upload_overlay(
        self,
        study_id: str,
        mask_path: str,
        overlay_type: str = "segmentation"
    ) -> Dict:
        """
        Upload overlay mask for a study.

        Args:
            study_id: Study identifier
            mask_path: Path to the segmentation mask
            overlay_type: Type of overlay (segmentation, probability, etc.)

        Returns:
            Response from the API
        """
        endpoint = f"{self.base_url}/api/studies/{study_id}/overlay"

        try:
            # Upload the mask file
            with open(mask_path, 'rb') as f:
                files = {'mask': f}
                data = {'overlay_type': overlay_type}

                response = self.session.post(endpoint, files=files, data=data)
                response.raise_for_status()
                return response.json()

        except (requests.exceptions.RequestException, FileNotFoundError) as e:
            return {"error": str(e), "status": "failed"}

    def get_study_info(self, study_id: str) -> Dict:
        """
        Get information about a registered study.

        Args:
            study_id: Study identifier

        Returns:
            Study information from the API
        """
        endpoint = f"{self.base_url}/api/studies/{study_id}"

        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}

    def get_overlay_url(self, study_id: str) -> str:
        """
        Get the GUI URL to view the overlay for a study.

        Args:
            study_id: Study identifier

        Returns:
            GUI URL for viewing the overlay
        """
        return f"{self.base_url}/viewer/{study_id}"

    def health_check(self) -> bool:
        """
        Check if the GUI backend is available.

        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


def push_inference_results(
    client: GUIIntegrationClient,
    study_id: str,
    patient_id: str,
    image_path: str,
    mask_path: str,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Push complete inference results to the GUI.

    Args:
        client: GUI integration client
        study_id: Study identifier
        patient_id: Patient identifier
        image_path: Path to original image
        mask_path: Path to segmentation mask
        metadata: Optional metadata

    Returns:
        Combined results from registration and overlay upload
    """
    # Register the study
    reg_result = client.register_study(
        study_id=study_id,
        patient_id=patient_id,
        image_path=image_path,
        metadata=metadata
    )

    if "error" in reg_result:
        return reg_result

    # Upload the overlay
    overlay_result = client.upload_overlay(
        study_id=study_id,
        mask_path=mask_path
    )

    # Combine results
    return {
        "study_id": study_id,
        "registration": reg_result,
        "overlay": overlay_result,
        "viewer_url": client.get_overlay_url(study_id),
        "status": "success" if "error" not in overlay_result else "partial"
    }


def main():
    """Main function for GUI integration script."""
    parser = argparse.ArgumentParser(
        description="Push inference results to tumor detection GUI"
    )
    parser.add_argument(
        "--study-id",
        type=str,
        required=True,
        help="Unique study identifier"
    )
    parser.add_argument(
        "--patient-id",
        type=str,
        required=True,
        help="Patient identifier"
    )
    parser.add_argument(
        "--image-path",
        type=str,
        required=True,
        help="Path to the original medical image"
    )
    parser.add_argument(
        "--mask-path",
        type=str,
        required=True,
        help="Path to the segmentation mask"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default="http://localhost:8000",
        help="GUI backend URL"
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        help="Optional JSON file with additional metadata"
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Check backend health before pushing"
    )

    args = parser.parse_args()

    # Validate file paths
    image_path = Path(args.image_path)
    mask_path = Path(args.mask_path)

    if not image_path.exists():
        print(f"Error: Image file not found: {image_path}")
        return 1

    if not mask_path.exists():
        print(f"Error: Mask file not found: {mask_path}")
        return 1

    # Load metadata if provided
    metadata = None
    if args.metadata_file:
        metadata_path = Path(args.metadata_file)
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            print(f"Warning: Metadata file not found: {metadata_path}")

    # Initialize client
    client = GUIIntegrationClient(args.backend_url)

    # Check backend health if requested
    if args.check_health:
        print("Checking backend health...")
        if not client.health_check():
            print(f"Error: Backend not available at {args.backend_url}")
            return 1
        print("✓ Backend is healthy")

    # Push results
    print(f"Pushing inference results for study: {args.study_id}")
    print(f"  Patient ID: {args.patient_id}")
    print(f"  Image: {image_path}")
    print(f"  Mask: {mask_path}")

    result = push_inference_results(
        client=client,
        study_id=args.study_id,
        patient_id=args.patient_id,
        image_path=str(image_path),
        mask_path=str(mask_path),
        metadata=metadata
    )

    # Display results
    if result.get("status") == "success":
        print("✓ Successfully pushed to GUI!")
        print(f"  Study registered: {result['registration'].get('status', 'unknown')}")
        print(f"  Overlay uploaded: {result['overlay'].get('status', 'unknown')}")
        print(f"  Viewer URL: {result['viewer_url']}")
    else:
        print("✗ Failed to push to GUI")
        if "error" in result:
            print(f"  Error: {result['error']}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
    exit(main())

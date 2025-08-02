"""
Data preprocessing module for medical images.
Handles various medical image formats and prepares them for the AI model.
"""

import os
from typing import Union, Tuple, List, Dict
import numpy as np
import nibabel as nib
import pydicom
from PIL import Image
import SimpleITK as sitk
from monai.transforms import (
    Compose,
    LoadImaged,
    AddChanneld,
    ScaleIntensityd,
    Orientationd,
    Spacingd,
    Resized,
    NormalizeIntensityd,
    ToTensord
)


class MedicalImagePreprocessor:
    """Class for preprocessing medical images for AI model input."""
    
    def __init__(
        self,
        target_size: Tuple[int, int, int] = (128, 128, 128)
    ):
        """
        Initialize the preprocessor.
        
        Args:
            target_size: Target size for processed images (D, H, W)
        """
        self.target_size = target_size
        self.transform = self._get_transform_pipeline()
    
    def _get_transform_pipeline(self) -> Compose:
        """Create the MONAI transform pipeline."""
        return Compose([
            LoadImaged(keys=["image"]),
            AddChanneld(keys=["image"]),
            Orientationd(keys=["image"], axcodes="RAS"),
            Spacingd(
                keys=["image"],
                pixdim=(1.5, 1.5, 1.5),
                mode=("bilinear"),
            ),
            Resized(
                keys=["image"],
                spatial_size=self.target_size,
                mode="trilinear"
            ),
            ScaleIntensityd(keys=["image"]),
            NormalizeIntensityd(keys=["image"], nonzero=True),
            ToTensord(keys=["image"])
        ])
    
    def preprocess_nifti(self, file_path: str) -> np.ndarray:
        """
        Preprocess a NIfTI file.
        
        Args:
            file_path: Path to the NIfTI file
            
        Returns:
            Preprocessed image array
        """
        # Load NIfTI file
        nifti_img = nib.load(file_path)
        data = {"image": nifti_img}
        
        # Apply transform pipeline
        transformed = self.transform(data)
        return transformed["image"]
    
    def preprocess_dicom(self, dicom_files: List[str]) -> np.ndarray:
        """
        Preprocess a series of DICOM files.
        
        Args:
            dicom_files: List of paths to DICOM files in the series
            
        Returns:
            Preprocessed image array
        """
        # Sort DICOM files by instance number
        dicom_files.sort(key=lambda x: pydicom.dcmread(x).InstanceNumber)
        
        # Read DICOM series
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(dicom_files)
        image = reader.Execute()
        
        # Convert to numpy array
        array = sitk.GetArrayFromImage(image)
        data = {"image": array}
        
        # Apply transform pipeline
        transformed = self.transform(data)
        return transformed["image"]
    
    def preprocess_image(
        self,
        image_path: str,
        modality: str = "MRI"
    ) -> Dict[str, Union[np.ndarray, dict]]:
        """
        Preprocess any supported medical image format.
        
        Args:
            image_path: Path to the image file
            modality: Image modality (MRI, CT, etc.)
            
        Returns:
            Dictionary containing:
                - preprocessed_image: The preprocessed image array
                - metadata: Dictionary of relevant metadata
        """
        # Extract file extension
        _, ext = os.path.splitext(image_path)
        
        # Handle different file formats
        if ext.lower() in ['.nii', '.gz']:
            image = self.preprocess_nifti(image_path)
            metadata = self._extract_nifti_metadata(image_path)
        elif ext.lower() == '.dcm':
            # Assume single DICOM file for now
            image = self.preprocess_dicom([image_path])
            metadata = self._extract_dicom_metadata(image_path)
        else:
            # Handle standard image formats
            image = np.array(Image.open(image_path))
            image = self._preprocess_standard_image(image)
            metadata = {"modality": modality}
        
        return {
            "preprocessed_image": image,
            "metadata": metadata
        }
    
    def _extract_nifti_metadata(self, file_path: str) -> dict:
        """Extract relevant metadata from NIfTI file."""
        img = nib.load(file_path)
        return {
            "dimensions": img.shape,
            "affine": img.affine.tolist(),
            "header": dict(img.header)
        }
    
    def _extract_dicom_metadata(self, file_path: str) -> dict:
        """Extract relevant metadata from DICOM file."""
        dcm = pydicom.dcmread(file_path)
        return {
            "patient_id": str(dcm.PatientID),
            "study_date": str(dcm.StudyDate),
            "modality": str(dcm.Modality),
            "manufacturer": str(dcm.Manufacturer),
            "pixel_spacing": getattr(dcm, "PixelSpacing", None),
            "slice_thickness": getattr(dcm, "SliceThickness", None)
        }
    
    def _preprocess_standard_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess standard image formats."""
        # Add channel dimension if needed
        if len(image.shape) == 2:
            image = image[np.newaxis, ...]
        
        # Normalize to [0, 1]
        image = image.astype(float) / 255.0
        
        return image

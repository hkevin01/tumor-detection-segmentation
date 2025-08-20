#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration smoke tests for inference CLI to prevent regressions.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
import torch
from monai.networks.nets import UNet


@pytest.mark.cpu
class TestInferenceCLISmoke:
    """Smoke tests for the inference CLI using synthetic data."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.H, self.W, self.D = 32, 32, 32  # Small for fast testing
        self.C_in, self.C_out = 2, 2  # Simple 2-channel input, 2-class output

    def create_synthetic_nifti(self, output_path: Path) -> None:
        """Create a synthetic NIfTI file for testing."""
        # Create synthetic medical image data
        data = np.random.randn(self.H, self.W, self.D).astype(np.float32)
        # Add some structure to make it more realistic
        data[10:20, 10:20, 10:20] += 0.5  # Bright region

        affine = np.eye(4)
        nifti_img = nib.Nifti1Image(data, affine)
        nib.save(nifti_img, str(output_path))

    def create_synthetic_model(self, output_path: Path) -> None:
        """Create a synthetic model checkpoint for testing."""
        # Create a tiny UNet for fast testing
        model = UNet(
            spatial_dims=3,
            in_channels=self.C_in,
            out_channels=self.C_out,
            channels=[8, 16],  # Very small for speed
            strides=[2],
            num_res_units=1,
        )

        # Save random weights
        torch.save({"model": model.state_dict()}, output_path)

    def create_synthetic_config(self, output_path: Path) -> None:
        """Create a synthetic training config for testing."""
        config = {
            "model": {
                "arch": "unet",
                "img_size": [self.H, self.W, self.D],
                "in_channels": self.C_in,
                "out_channels": self.C_out,
                "channels": [8, 16],
                "strides": [2],
                "num_res_units": 1
            }
        }

        with open(output_path, "w") as f:
            json.dump(config, f)

    def test_inference_single_file(self):
        """Test inference on a single NIfTI file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test files
            input_nifti = tmp_path / "test_input.nii.gz"
            model_path = tmp_path / "test_model.pt"
            config_path = tmp_path / "test_config.json"
            output_dir = tmp_path / "outputs"

            self.create_synthetic_nifti(input_nifti)
            self.create_synthetic_model(model_path)
            self.create_synthetic_config(config_path)

            # Run inference CLI
            cmd = [
                "python", "src/inference/inference_enhanced.py",
                "--config", str(config_path),
                "--model", str(model_path),
                "--input", str(input_nifti),
                "--output-dir", str(output_dir),
                "--save-overlays",
                "--device", "cpu"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Check command succeeded
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check outputs were created
            assert output_dir.exists(), "Output directory not created"

            # Check for overlay PNG
            overlay_dir = output_dir / "overlays"
            if overlay_dir.exists():
                overlay_files = list(overlay_dir.glob("*.png"))
                assert len(overlay_files) > 0, "No overlay PNG files created"

                # Check file size is reasonable
                for overlay_file in overlay_files:
                    assert overlay_file.stat().st_size > 500, f"Overlay {overlay_file} too small"

    def test_inference_directory(self):
        """Test inference on a directory of NIfTI files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test files
            input_dir = tmp_path / "inputs"
            input_dir.mkdir()
            model_path = tmp_path / "test_model.pt"
            config_path = tmp_path / "test_config.json"
            output_dir = tmp_path / "outputs"

            # Create multiple test NIfTI files
            for i in range(2):
                input_nifti = input_dir / f"test_input_{i}.nii.gz"
                self.create_synthetic_nifti(input_nifti)

            self.create_synthetic_model(model_path)
            self.create_synthetic_config(config_path)

            # Run inference CLI on directory
            cmd = [
                "python", "src/inference/inference_enhanced.py",
                "--config", str(config_path),
                "--model", str(model_path),
                "--input", str(input_dir),
                "--output-dir", str(output_dir),
                "--save-overlays",
                "--device", "cpu"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Check command succeeded
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check outputs were created
            assert output_dir.exists(), "Output directory not created"

            # Check for multiple overlay PNGs
            overlay_dir = output_dir / "overlays"
            if overlay_dir.exists():
                overlay_files = list(overlay_dir.glob("*.png"))
                assert len(overlay_files) >= 2, "Not enough overlay files created"

    def test_inference_with_probability_maps(self):
        """Test inference with probability map generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test files
            input_nifti = tmp_path / "test_input.nii.gz"
            model_path = tmp_path / "test_model.pt"
            config_path = tmp_path / "test_config.json"
            output_dir = tmp_path / "outputs"

            self.create_synthetic_nifti(input_nifti)
            self.create_synthetic_model(model_path)
            self.create_synthetic_config(config_path)

            # Run inference CLI with probability maps
            cmd = [
                "python", "src/inference/inference_enhanced.py",
                "--config", str(config_path),
                "--model", str(model_path),
                "--input", str(input_nifti),
                "--output-dir", str(output_dir),
                "--save-overlays",
                "--save-prob-maps",
                "--class-index", "1",
                "--device", "cpu"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Check command succeeded
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check probability maps were created
            prob_dir = output_dir / "prob_maps"
            if prob_dir.exists():
                prob_files = list(prob_dir.glob("*.png"))
                assert len(prob_files) > 0, "No probability map files created"

    def test_inference_custom_slices(self):
        """Test inference with custom slice specification."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test files
            input_nifti = tmp_path / "test_input.nii.gz"
            model_path = tmp_path / "test_model.pt"
            config_path = tmp_path / "test_config.json"
            output_dir = tmp_path / "outputs"

            self.create_synthetic_nifti(input_nifti)
            self.create_synthetic_model(model_path)
            self.create_synthetic_config(config_path)

            # Run inference CLI with custom slices
            cmd = [
                "python", "src/inference/inference_enhanced.py",
                "--config", str(config_path),
                "--model", str(model_path),
                "--input", str(input_nifti),
                "--output-dir", str(output_dir),
                "--save-overlays",
                "--slices", "8,16,24",  # Custom slice indices
                "--device", "cpu"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Check command succeeded
            assert result.returncode == 0, f"CLI failed: {result.stderr}"

            # Check outputs were created
            assert output_dir.exists(), "Output directory not created"

    def test_cli_help(self):
        """Test that CLI help works without errors."""
        cmd = ["python", "src/inference/inference_enhanced.py", "--help"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        # Help should exit with code 0 and contain usage info
        assert result.returncode == 0, "Help command failed"
        assert "usage:" in result.stdout.lower(), "Help output malformed"
        assert "--save-overlays" in result.stdout, "Missing expected CLI flags"

    def test_invalid_input_handling(self):
        """Test graceful handling of invalid inputs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create valid model and config
            model_path = tmp_path / "test_model.pt"
            config_path = tmp_path / "test_config.json"
            output_dir = tmp_path / "outputs"

            self.create_synthetic_model(model_path)
            self.create_synthetic_config(config_path)

            # Run CLI with non-existent input
            cmd = [
                "python", "src/inference/inference_enhanced.py",
                "--config", str(config_path),
                "--model", str(model_path),
                "--input", str(tmp_path / "nonexistent.nii.gz"),
                "--output-dir", str(output_dir),
                "--device", "cpu"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Should fail gracefully (non-zero exit code)
            assert result.returncode != 0, "Should fail with invalid input"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_device_selection(self):
        """Test CUDA device selection when available."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test files
            input_nifti = tmp_path / "test_input.nii.gz"
            model_path = tmp_path / "test_model.pt"
            config_path = tmp_path / "test_config.json"
            output_dir = tmp_path / "outputs"

            self.create_synthetic_nifti(input_nifti)
            self.create_synthetic_model(model_path)
            self.create_synthetic_config(config_path)

            # Run inference CLI with CUDA
            cmd = [
                "python", "src/inference/inference_enhanced.py",
                "--config", str(config_path),
                "--model", str(model_path),
                "--input", str(input_nifti),
                "--output-dir", str(output_dir),
                "--save-overlays",
                "--device", "cuda",
                "--amp"  # Test mixed precision too
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )

            # Should succeed with CUDA
            assert result.returncode == 0, f"CUDA inference failed: {result.stderr}"


if __name__ == "__main__":
    pytest.main([__file__])

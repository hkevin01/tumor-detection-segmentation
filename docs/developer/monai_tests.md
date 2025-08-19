# MONAI Dataset Integration Tests

This directory contains comprehensive tests for the MONAI dataset integration system, including unit tests for transforms and integration tests for the complete data loading pipeline.

## Test Files

### Unit Tests (`tests/unit/test_transforms_presets.py`)

Tests the transform presets for medical imaging data:

- **BraTS-like transforms**: Multi-modal MRI (T1, T1c, T2, FLAIR) preprocessing
- **CT liver transforms**: Single-channel CT with HU windowing and normalization
- **Shape validation**: Ensures correct tensor dimensions and channel counts
- **Data integrity**: Validates no NaN values and proper normalization ranges

### Integration Tests (`tests/integration/test_monai_msd_loader.py`)

End-to-end tests for the MONAI Decathlon dataset loader:

- **Synthetic dataset creation**: Builds tiny MSD-like datasets on disk for testing
- **Dataset loading**: Tests the complete `load_monai_decathlon()` pipeline
- **DataLoader validation**: Ensures proper batch iteration and tensor shapes
- **Model compatibility**: Runs a lightweight UNet forward pass to validate end-to-end flow

## Running the Tests

### Individual Test Files

```bash
# Unit tests for transform presets
pytest -q tests/unit/test_transforms_presets.py

# Integration tests for MONAI MSD loader
pytest -q tests/integration/test_monai_msd_loader.py

# Run with specific markers
pytest -m cpu  # CPU-only tests
pytest -m unit  # All unit tests
pytest -m integration  # All integration tests
```

### Complete Test Suite

Use the demo script to run all MONAI-related tests:

```bash
python scripts/demo/test_monai_integration.py
```

This script provides:
- Detailed test execution with progress indicators
- Summary of results with pass/fail status
- Next steps for using the MONAI dataset system

### CI/CD Integration

The tests are designed to run in CI environments without requiring:
- Large dataset downloads
- GPU acceleration
- Network connectivity

They use the `@pytest.mark.cpu` marker and create small synthetic datasets for validation.

## Test Architecture

### Synthetic Data Generation

The integration tests create minimal but realistic medical imaging datasets:

```python
# Creates a tiny Decathlon-like structure:
# Task01_BrainTumour/
# ├── imagesTr/
# │   ├── case_000_flair.nii.gz  # 32x32x32 synthetic MRI
# │   ├── case_000_t1.nii.gz
# │   ├── case_000_t1ce.nii.gz
# │   └── case_000_t2.nii.gz
# ├── labelsTr/
# │   └── case_000.nii.gz        # Binary tumor mask
# └── Task01_BrainTumour.json    # Decathlon metadata
```

### Transform Validation

The unit tests validate transform presets with synthetic data:

- **Multi-modal MRI**: 4-channel input → proper channel ordering and normalization
- **CT imaging**: Single-channel → HU windowing and intensity scaling
- **Spatial transforms**: Resampling, cropping, and augmentation consistency

### Model Integration

Integration tests include lightweight model validation:

```python
# Smoke test with minimal UNet
model = UNet(spatial_dims=3, in_channels=4, out_channels=2,
             channels=(8, 16, 32), strides=(2, 2))
with torch.no_grad():
    y = model(batch["image"])  # Validates tensor flow
```

## Benefits

These tests provide:

1. **Fast Validation**: No large downloads, runs in seconds
2. **CI Compatibility**: CPU-only, no external dependencies
3. **Comprehensive Coverage**: Unit + integration testing
4. **Realistic Scenarios**: Mimics actual dataset usage patterns
5. **Clear Feedback**: Detailed error reporting and success indicators

## Usage in Development

Run these tests when:
- Modifying MONAI dataset loaders or transforms
- Adding new dataset configurations
- Validating model compatibility with data pipelines
- Before committing changes to data handling code

The tests ensure the critical path from dataset download → loading → preprocessing → model input works correctly across different medical imaging modalities.

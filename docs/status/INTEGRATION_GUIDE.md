# Using Tumor Detection Library in Other Applications

This guide shows you how to integrate the `tumor-detection-segmentation` library into your own applications and projects.

## 🚀 Quick Installation

```bash
# Install from PyPI
pip install tumor-detection-segmentation

# Or with specific features
pip install tumor-detection-segmentation[clinical,api,gui]
```

## 📋 Basic Integration Patterns

### Pattern 1: Simple Function Calls (Easiest)

```python
# Import and use directly
from tumor_detection import detect_tumors, segment_tumors

# Basic detection
results = detect_tumors("brain_scan.nii.gz", threshold=0.5)
print(f"Found {results['num_detections']} tumors")

# Basic segmentation
segmentation = segment_tumors("brain_scan.nii.gz", post_process=True)
print(f"Segmentation shape: {segmentation.shape}")
```

### Pattern 2: Class-Based Usage (More Control)

```python
from tumor_detection.api import TumorDetector, TumorSegmenter, ImagePreprocessor

# Initialize once, reuse multiple times
detector = TumorDetector(model_name="unetr_detection", device="auto")
segmenter = TumorSegmenter(model_name="unetr_segmentation", device="auto")
preprocessor = ImagePreprocessor()

# Process multiple images efficiently
for image_path in image_list:
    processed = preprocessor.preprocess(image_path)
    detections = detector.detect(processed)
    if detections["num_detections"] > 0:
        segmentation = segmenter.segment(processed)
        # Handle results...
```

### Pattern 3: Service Integration

```python
from tumor_detection.services import DicomService, FhirService, CloudService

# DICOM/PACS integration
dicom = DicomService("pacs.hospital.com")
studies = dicom.find_studies(patient_id="PATIENT_001")

# FHIR integration for results storage
fhir = FhirService("https://fhir.hospital.com")
observation = fhir.create_imaging_observation(patient_id, results)

# Cloud storage integration
cloud = CloudService(provider="aws")  # or "gcp", "azure"
cloud.upload_results(results, bucket="medical-ai-results")
```

## 🏗️ Integration Examples

### Web API Integration

```python
from fastapi import FastAPI, UploadFile
from tumor_detection import detect_tumors
import tempfile

app = FastAPI()

@app.post("/analyze")
async def analyze_image(file: UploadFile):
    with tempfile.NamedTemporaryFile(suffix=".nii.gz") as temp:
        content = await file.read()
        temp.write(content)
        temp.flush()

        results = detect_tumors(temp.name)
        return {"status": "success", "results": results}
```

### Batch Processing Pipeline

```python
class MedicalImagingPipeline:
    def __init__(self):
        from tumor_detection.api import TumorDetector, TumorSegmenter
        self.detector = TumorDetector(device="auto")
        self.segmenter = TumorSegmenter(device="auto")

    def process_folder(self, input_folder, output_folder):
        results = []
        for image_file in Path(input_folder).glob("*.nii.gz"):
            detection = self.detector.detect(str(image_file))
            if detection["num_detections"] > 0:
                segmentation = self.segmenter.segment(str(image_file))
                # Save results...
                results.append({
                    "file": image_file.name,
                    "detections": detection,
                    "segmentation_saved": True
                })
        return results
```

### Custom Application Class

```python
class MyMedicalApp:
    def __init__(self):
        from tumor_detection.api import TumorDetector, ImagePreprocessor
        from tumor_detection.services import DicomService

        self.detector = TumorDetector(device="auto")
        self.preprocessor = ImagePreprocessor()
        self.dicom = DicomService("your_pacs.com")  # Optional

    def analyze_patient(self, patient_id):
        # Get images from PACS
        studies = self.dicom.find_studies(patient_id=patient_id)

        results = []
        for study in studies:
            images = self.dicom.download_study(study["study_id"])
            for image_path in images:
                # Process with AI
                processed = self.preprocessor.preprocess(image_path)
                detection = self.detector.detect(processed)
                results.append({
                    "study_id": study["study_id"],
                    "image": image_path,
                    "results": detection
                })

        return results
```

## 🧪 Testing and Validation

```python
from tools.testing.model_validator import ModelValidator

# Validate your model performance
validator = ModelValidator()
results = validator.validate_model(
    model_path="path/to/your/model.pth",
    test_images=["test1.nii.gz", "test2.nii.gz"],
    metrics=["dice", "iou", "hd95"]
)

print(f"Validation results: {results}")
```

## ⚙️ Configuration Management

```python
from tumor_detection import load_recipe_config, load_dataset_config

# Load pre-configured settings
model_config = load_recipe_config("config/recipes/unetr_multimodal.json")
dataset_config = load_dataset_config("config/datasets/msd_task01_brain.json")

# Use with your models
from tumor_detection.api import TumorSegmenter
segmenter = TumorSegmenter(config=model_config, device="auto")
```

## 🔧 CLI Tools

The library provides command-line tools you can use in scripts:

```bash
# Train a model
tumor-detect-train --config config/recipes/unetr_multimodal.json --epochs 50

# Run inference
tumor-detect-infer --model models/best.pth --input data/ --output results/

# Validate model
tumor-detect-validate --model models/best.pth --test-data test/

# Deploy to production
tumor-deploy --config deployment/production.yaml
```

## 📦 Optional Dependencies

Install additional features as needed:

```bash
# Clinical features (DICOM, FHIR)
pip install tumor-detection-segmentation[clinical]

# Web API features
pip install tumor-detection-segmentation[api]

# GUI components
pip install tumor-detection-segmentation[gui]

# Everything
pip install tumor-detection-segmentation[all]
```

## 🎯 Common Integration Use Cases

### 1. Hospital Information System Integration

```python
from tumor_detection.services import DicomService, FhirService
from tumor_detection import detect_tumors

# Connect to hospital systems
dicom = DicomService("hospital-pacs.local")
fhir = FhirService("https://hospital-fhir.local")

# Automated screening workflow
def screen_patient(patient_id):
    studies = dicom.find_studies(patient_id=patient_id)
    for study in studies:
        images = dicom.download_study(study["study_id"])
        for image in images:
            results = detect_tumors(image)
            if results["num_detections"] > 0:
                # Alert radiologist and save to FHIR
                fhir.create_observation(patient_id, results)
```

### 2. Research Pipeline Integration

```python
from tumor_detection.api import TumorSegmenter, ModelEvaluator
import pandas as pd

# Research workflow
def research_pipeline(dataset_path, output_path):
    segmenter = TumorSegmenter()
    evaluator = ModelEvaluator()

    results = []
    for image_path in dataset_path.glob("*.nii.gz"):
        segmentation = segmenter.segment(str(image_path))
        metrics = evaluator.calculate_metrics(segmentation, ground_truth_path)
        results.append({
            "image": image_path.name,
            "dice": metrics["dice"],
            "iou": metrics["iou"]
        })

    # Save research results
    df = pd.DataFrame(results)
    df.to_csv(output_path / "results.csv")
```

### 3. Cloud-Native Application

```python
from tumor_detection import detect_tumors
from tumor_detection.services import CloudService
import boto3

# Cloud processing function (AWS Lambda compatible)
def lambda_handler(event, context):
    s3_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    s3_key = event["Records"][0]["s3"]["object"]["key"]

    # Download from S3
    s3 = boto3.client("s3")
    s3.download_file(s3_bucket, s3_key, "/tmp/image.nii.gz")

    # Process with AI
    results = detect_tumors("/tmp/image.nii.gz")

    # Upload results back to S3
    cloud = CloudService(provider="aws")
    cloud.upload_results(results, bucket="ai-results")

    return {"statusCode": 200, "results": results}
```

## 📚 Additional Resources

- **Examples**: Check `examples/integration/` for more patterns
- **Documentation**: [GitHub Repository](https://github.com/hkevin01/tumor-detection-segmentation)
- **API Reference**: See docstrings in the library modules
- **Configuration**: Review `config/recipes/` for pre-built configurations

## 🚀 Getting Started

1. **Install the library**: `pip install tumor-detection-segmentation`
2. **Run setup script**: `python setup_integration.py`
3. **Try the examples**: `python examples/integration/integration_examples.py`
4. **Integrate into your app**: Start with simple function calls, then explore classes and services

The library is designed to be modular and flexible - use only the components you need!

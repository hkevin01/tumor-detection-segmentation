# Tumor Detection and Segmentation using MONAI

This project uses MONAI for detecting and segmenting tumors in MRI or CT images.

## Directory Structure
- `data/`: Store datasets here.
- `models/`: Save trained models here.
- `notebooks/`: Jupyter notebooks for experiments.
- `src/`: Source code for training, evaluation, and inference.

## Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the training script:
   ```bash
   python src/train.py
   ```

## Documentation

Project documentation is available in the `docs/` directory. It includes details on the MONAI framework, data preprocessing, model training, and evaluation metrics. To build the documentation, navigate to the `docs/` directory and run:

```bash
make html
```

Open the generated HTML files in your browser to view the documentation.

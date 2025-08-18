# Data Sources and Licensing

This document outlines the data sources supported by the platform and their respective licensing requirements.

## MONAI Datasets (Primary)

### Medical Segmentation Decathlon (MSD)

The platform provides built-in support for MSD datasets via MONAI:

**Task01_BrainTumour**:
- **Description**: Multi-modal MRI brain tumor segmentation (T1, T1c, T2, FLAIR)
- **Source**: MONAI/Medical Decathlon
- **License**: Creative Commons Attribution-ShareAlike 4.0 International License
- **Usage**: `python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour`
- **Citation**: Required - see MONAI documentation

**Task03_Liver**:
- **Description**: CT liver and tumor segmentation
- **Source**: MONAI/Medical Decathlon
- **License**: Creative Commons Attribution-ShareAlike 4.0 International License
- **Usage**: `python scripts/data/pull_monai_dataset.py --dataset-id Task03_Liver`

### Other MSD Tasks

The platform can support any MSD task by creating appropriate dataset configs:
- Task02_Heart (Cardiac MRI)
- Task04_Hippocampus (MRI hippocampus)
- Task05_Prostate (MRI prostate)
- Task06_Lung (CT lung nodules)
- Task07_Pancreas (CT pancreas)
- Task08_HepaticVessel (CT hepatic vessels)
- Task09_Spleen (CT spleen)
- Task10_Colon (CT colon cancer)

## Hugging Face Datasets (Optional)

### Available Datasets

**BraTS Variants**:
- Multiple community-hosted BraTS dataset mirrors
- Multi-modal MRI with tumor annotations
- **License**: Varies by host; typically requires registration and acknowledgment
- **Access**: Requires Hugging Face account and license acceptance

**LiTS (Liver Tumor Segmentation)**:
- CT liver tumor datasets
- **License**: Varies by mirror; check dataset card
- **Access**: May require license acceptance

**LIDC-IDRI Derivatives**:
- Lung nodule detection and segmentation subsets
- **License**: Open access with citation requirements
- **Access**: Direct download after terms acceptance

### Using Hugging Face Datasets

```bash
# Future implementation - extendable architecture ready
python scripts/data/pull_hf_dataset.py --repo-id "organization/dataset_name" --target data/custom/
```

## Custom Datasets

### Supported Formats

- **BIDS-compatible**: Brain Imaging Data Structure layouts
- **NIfTI**: Medical imaging standard format
- **DICOM**: Clinical imaging format (via conversion utilities)

### Configuration

Create custom dataset configs in `config/datasets/` following the pattern:

```json
{
  "source": "custom",
  "data_root": "data/custom_dataset",
  "transforms": "brats_like",
  "spacing": [1.0, 1.0, 1.0],
  "cache": "smart"
}
```

## Licensing Compliance

### Requirements

1. **Citation**: Always cite original dataset sources
2. **Attribution**: Include dataset acknowledgments in publications
3. **Non-commercial**: Some datasets restrict commercial use
4. **Registration**: Certain datasets require user registration

### Best Practices

- Document dataset sources in your experiments
- Include LICENSE files for each dataset in `data/licenses/`
- Check dataset cards for specific terms before use
- Maintain audit trails for compliance reporting

## Contributing New Datasets

To add support for new datasets:

1. Create a dataset config in `config/datasets/`
2. Add appropriate transform presets in `src/data/transforms_presets.py`
3. Update documentation with licensing information
4. Test with the training pipeline

For questions about dataset licensing or access, consult:
- Original dataset documentation
- MONAI dataset guidelines
- Hugging Face dataset terms

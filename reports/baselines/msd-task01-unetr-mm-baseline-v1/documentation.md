# Baseline Model Documentation

Generated: 2025-09-06T00:13:54.227789
Model: UNETR MultiModal
Dataset: MSD Task01 BrainTumour

## Model Configuration

### Architecture
- **Model**: Multi-Modal UNETR
- **Input Channels**: 4 (T1, T1c, T2, FLAIR)
- **Output Channels**: 4 (background, necrotic core, edema, enhancing tumor)
- **Input Size**: [64, 64, 64]
- **Feature Size**: 16
- **Hidden Size**: 768

### Training Parameters
- **Batch Size**: 1
- **Learning Rate**: 1e-4
- **Epochs**: 50
- **Cache Mode**: smart
- **AMP**: False

### Hardware Configuration
- **GPU Memory**: 0GB
- **Configuration**: CPU only: Minimal configuration

## Performance Metrics

### Target Metrics
- **Dice Score**: > 0.80
- **Hausdorff 95**: < 5.0mm
- **Inference Time**: < 5.0s

### Achieved Metrics
(To be updated after training completion)
- **Dice Score**: TBD
- **Hausdorff 95**: TBD
- **Inference Time**: TBD

## Clinical Validation

### Dataset
- **Source**: Medical Segmentation Decathlon
- **Task**: Task01_BrainTumour
- **Training Cases**: 484
- **Test Cases**: 266

### Validation Protocol
1. Cross-validation on training set
2. Held-out test set evaluation
3. Clinical expert review
4. Comparative analysis with existing methods

## Deployment Information

### Model Files
- **Checkpoint**: models/unetr/best.pt
- **Config**: config/recipes/unetr_multimodal.json
- **Dataset Config**: config/datasets/msd_task01_brain.json

### Clinical Workflow
1. Data preprocessing and quality checks
2. Multi-modal inference
3. Overlay generation for clinical review
4. Report generation and archival

## Sign-off Checklist

- [ ] Model training completed successfully
- [ ] Performance metrics meet clinical requirements
- [ ] Clinical validation completed
- [ ] Integration testing passed
- [ ] Documentation complete
- [ ] Regulatory review (if applicable)
- [ ] Clinical sign-off obtained

## Contact Information

**Technical Lead**: Development Team
**Clinical Lead**: TBD
**QA Lead**: TBD

Date: 2025-09-06
Version: 1.0
Status: In Progress

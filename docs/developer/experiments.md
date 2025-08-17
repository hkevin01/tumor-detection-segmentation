# Experiments and Reproducible Baselines

Use these prompts to open issues/PRs and to run consistent experiments.

## Baselines

- Task: Train UNETR multimodal baseline
- Data: Small sample (e.g., BraTS subset)
- Config: `config/recipes/unetr_multimodal.json`
- Command:

```bash
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --seed 42
```

- Expected Artifacts:
  - MLflow run with params/metrics
  - Overlay PNGs in `tests/artifacts`
  - Model checkpoint in `models/`

## Cascade Pipeline

- Task: Two-stage detection+segmentation
- Config: `config/recipes/cascade_detection.json`
- Verify: runtime and memory usage; NMS and threshold sweeps

## NAS (DiNTS)

- Task: Search under VRAM/latency budget
- Config: `config/recipes/dints_nas.json`
- Output: best architecture dumped to `models/dints/best_arch.json`, retrain with fixed arch

## Evaluation

- Run:

```bash
python src/evaluation/evaluate.py --config config/recipes/unetr_multimodal.json --ckpt models/unetr/checkpoint.pt
```

- Metrics: Dice, IoU, HD95, ASSD; write per-case CSV + MLflow summary

## Inference

- Sliding window + TTA:

```bash
python src/inference/inference.py --config config/recipes/unetr_multimodal.json --ckpt models/unetr/checkpoint.pt --tta 1
```

## Issue/PR Prompts

- Baseline reliability improvements (early stopping, EMA, clipping): see checklist in `docs/developer/roadmap.md`.
- Fusion ablation study: early vs late fusion; modality dropout rates; calibration effects.
- Post-processing ablation: connected components, size filters thresholds grid.
- Active learning acquisitions: implement entropy/BALD/TTA disagreement; integrate with MONAI Label API.

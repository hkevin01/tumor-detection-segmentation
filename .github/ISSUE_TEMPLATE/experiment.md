---
name: Experiment request
about: Request a new experiment or baseline run
labels: experiment
assignees: ''
---

# Experiment Request

## Goal

Describe the experiment objective and expected outcome.

## Config

- Recipe: config/recipes/RECIPE_NAME.json
- Seed: 42
- Data subset: DATASET_OR_SAMPLE

## Metrics

- Dice, IoU, HD95, ASSD
- Calibration: ECE/Brier (if applicable)

## Artifacts

- MLflow run link
- Overlays in tests/artifacts
- Checkpoint in models/

## Checklist

- [ ] Reproducibility (fixed seeds, versions)
- [ ] Logs and artifacts saved
- [ ] Summary added to docs/developer/experiments.md

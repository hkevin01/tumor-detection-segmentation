# Action-oriented Tasks & Roadmap

This document captures an actionable plan for verifying the environment, smoke-testing MONAI datasets, baseline inference, MLflow integration, short-term improvements, and a medium-term roadmap.

## Immediate next steps (high impact, low friction)

- Verify environment and containers
  - Run: `./test_docker.sh` then `./run.sh start` and `./run.sh status`
  - Open services:
    - GUI: http://localhost:8000/gui
    - MLflow: http://localhost:5001
    - MONAI Label: http://localhost:8001
  - If GPU present, confirm CUDA/ROCm via `./run.sh logs` and `scripts/utilities/system_status.sh`

- Smoke-test MONAI datasets locally (CPU OK)
  - Pull brain dataset:
    - `python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour --root data/msd`
  - Quick training sanity check (few epochs):
    - `python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --epochs 2 --amp --save-overlays --overlays-max 3`
  - Validate:
    - `python scripts/demo/test_monai_integration.py`
    - `pytest -m cpu`

- Baseline inference and overlay export
  - If checkpoint exists in `models/`:
    - `python src/inference/inference.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --model models/unetr/best.pt --output-dir reports/inference_exports --save-overlays --save-prob-maps --slices auto --tta --amp`
  - Review outputs in `reports/inference_exports/`

- Enable MLflow tracking
  - Start the stack via Docker (Postgres backend as configured)
  - Confirm runs appear in MLflow during `train_enhanced.py`
  - Recommended: define experiment naming convention in `config.json` (e.g., `msd-task01-unetr-mm`)

## Short-term enhancements (1–2 sprints)

- Reproducible configs and data management
  - Pin dataset versions and splits in `config/datasets/*.json` with `seed` and `fold` info
  - Add an example `.env` (document which vars `run.sh` expects) and move environment management into Docker where appropriate
  - Verify `docker/docker_files_index.json` matches actual paths and remove any duplicates (e.g., ROCm path)

- Training robustness and performance
  - Document expected VRAM usage per ROI size and batch size for UNETR and UNet
  - Expose CLI flags: `--cache none|cache|smart`, spacing, ROI override
  - Add automatic gradient clipping and early stopping to `train_enhanced.py` if missing

- Evaluation completeness
  - Add HD95, ASSD, and per-structure metrics with class mapping
  - Add a cross-validation script to run k-folds and aggregate MLflow results
  - Add calibration checks (ECE) and reliability plots for probability maps

- Inference UX and safety
  - Add `--postproc` options (largest-component, small-object removal, hole filling) and export raw + post-processed masks
  - Add NIfTI header QA scripts to validate qform/sform consistency

## CI/CD and quality gates

- Ensure GitHub Actions runs: ruff, black --check, mypy, `pytest -m cpu`, Trivy, Syft SBOM
- Add pip and dataset mini-sample caches in CI to speed runs
- Ensure `pre-commit` is documented and used (`.pre-commit-config.yaml` exists)

## Medium-term roadmap

- Model zoo & recipes: provide ready recipes for SegResNet, UNet3D, DiNTS; publish lightweight demo checkpoints
- Multi-modal fusion maturity: benchmark early vs late vs cross-attention fusion; add modality dropout
- Cascade detection pipeline: provide end-to-end RetinaUNet3D → UNETR refinement script
- Interactive annotation loop: ship MONAI Label bundle + active learning strategies
- GUI/API polish: add fine-grained overlay endpoints, upload endpoint, user roles/auth
- Deployment hardening: compose profiles for cpu/cuda/rocm, persistent volumes, resource limits, health-check remediation

## Validation plan

- Reproduce baselines on MSD Task01 (UNETR multimodal) and Task03 (UNet/SegResNet)
- Save inference overlays and masks for a fixed validation subset in `reports/baselines/`
- Track runs in MLflow with tags: dataset, fold, model, roi, cache_mode, amp, tta, postproc

## Open questions

- Are pretrained checkpoints available for immediate GUI demo?
- Final default spacing/ROI per dataset and recommended GPU memory tiers?
- Are DiNTS and RetinaUNet3D implementations complete or experimental?
- Decide default cache mode for 16–24GB VRAM setups

## Quick command cheat sheet

```bash
# Start stack
./run.sh start

# Stop/cleanup
./run.sh stop && ./run.sh cleanup

# Pull dataset
python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour --root data/msd

# Train (brain)
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --amp --save-overlays

# Inference (with overlays)
python src/inference/inference.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --model models/unetr/best.pt --save-overlays --save-prob-maps --slices auto --tta

# Tests
pytest -m cpu
python scripts/demo/test_monai_integration.py
```

---

If you provide your hardware (GPU VRAM, CPU/RAM) and preferred dataset, I can generate tuned ROI, batch size, cache settings and a ready-to-run command set.

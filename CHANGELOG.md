# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [2.0.2] — 2026-04-08

### Added
- `src/tumor_detection/models/dints_search.py` — DiNTS (Differentiable Neural Topology Search) two-stage NAS pipeline: `build_dints_search_model` (Stage 1) and `build_dints_instance` (Stage 2 deploy)
- `src/tumor_detection/models/mednext_wrapper.py` — MedNext large-kernel CNN wrapper (MONAI 1.5 `#8004`) with S/B/M/L size presets and SwinUNETR/UNet fallback chain
- `src/tumor_detection/models/vista3d_integration.py` — VISTA3D foundation model integration with interactive prompted segmentation and encoder fine-tuning helpers
- `src/training/hybrid_supervised.py` — DiceCE + NACLLoss + label_smoothing hybrid trainer with LinearWarmupCosineAnnealing scheduler
- `src/training/semi_supervised.py` — Mean Teacher EMA semi-supervised training for low-label regimes
- `src/training/mae_pretrain.py` — Masked Autoencoder self-supervised pre-training with 3-D volumetric patch masking
- `tests/test_unetr_dints.py` — UNETR shape/dtype/param tests + full DiNTS search-decode-deploy test suite (13 tests)
- `tests/training/simple_train_test.py` — Trainer smoke tests: single-batch, checkpoint save/load round-trip
- `pyproject.toml` `[tool.ruff]` and `[tool.mypy]` sections — centralised linting and type-check config

### Changed
- **trainer.py** rewritten: AMP GradScaler, `torch.compile`, `decollate_batch` Dice eval, `DiceCELoss(label_smoothing)`, `CosineAnnealingWarmRestarts`, `zero_grad(set_to_none=True)`, `weights_only=True` checkpoint loading
- **pyproject.toml**: `monai>=1.3.0` → `>=1.5.0`; `requires-python` `3.8` → `3.9`; corrected license classifier to Apache 2.0; added `src/tumor_detection/models` to wheel; added `[tool.hatch.build.targets.sdist]` excludes
- **README.md**: Added "Why This Tech Stack" section (Why UNETR, DiNTS search process diagram, Why MONAI comparison table); updated architecture diagram and models table to include DiNTS
- **MANIFEST.in**: Removed reference to deleted `LIBRARY_REFACTORING_PLAN.md`; added `src/tumor_detection/models`
- **Dockerfiles** (`Dockerfile`, `Dockerfile.cuda`, `Dockerfile.test-lite`): updated `COPY requirements.txt` → `COPY config/requirements/requirements.txt`
- **Makefile** `install-dev`: now references `config/requirements/requirements-dev.txt`

### Removed
- Root `requirements.txt` — superseded by `config/requirements/requirements.txt` + `pyproject.toml`
- Root `.ruff.toml` (empty) — config consolidated into `pyproject.toml [tool.ruff]`
- Root `setup.py` (empty), `run.sh` (empty), `data_config.yaml` (empty)
- `src/training/enhanced_trainer.py` (empty)
- `config/mypy.ini` (empty) — config in `pyproject.toml [tool.mypy]`
- `config/pytest.ini` (empty) — config in `pyproject.toml [tool.pytest.ini_options]`
- 31 stale completion/status `.md` files from `docs/` (Copilot session artifacts, PYPI_*/INTEGRATION_*/VERIFICATION_* reports)
- `scripts/cleanup/` and `scripts/organization/` directories (already-run one-off scripts)

---

## [2.0.1] — 2025-12-01

### Added
- PyPI package publication: `pip install tumor-detection-segmentation`
- CLI entry points: `tumor-detect-train`, `tumor-detect-infer`
- MONAI bundle integration and SlidingWindowInferer pipeline
- Docker multi-stage builds for CPU and CUDA environments
- REST API via FastAPI with DICOM/NIfTI upload endpoints

---

## [2.0.0] — 2025-10-01

### Added
- Initial production release
- UNETR, SwinUNETR, SegResNet, UNet model registry
- BraTS multi-modal (T1/T1c/T2/FLAIR) training pipeline
- DICOM-SR and FHIR R4 clinical output generation
- 3D Slicer plugin via MONAI Label

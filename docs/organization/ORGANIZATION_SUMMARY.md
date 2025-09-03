# Repository Organization Summary

This document summarizes the recent reorganization work and current actionable items.

Highlights

- Docker artifacts centralized under `docker/`.

- Lightweight test image added: `docker/Dockerfile.test-lite` for fast CI and smoke tests.

- Heavy image for full MONAI/PyTorch integration: `docker/Dockerfile.phase4` (GPU/CUDA aware).

- Task tracking added via `organization_tasks.json` and `task_manager.py`.

- Validation scripts under `scripts/validation/` for pre-flight checks.

Next steps

- Run `scripts/validation/test_docker.sh` locally to verify Docker readiness.

- Use `scripts/tools/smoke_train_launcher.sh` to build and run a 2-epoch smoke training inside Docker (recommended for reproducibility).

- Run `python3 scripts/tools/auto_update_tasks.py` to reconcile repository artifacts with task statuses.

Notes

- Heavy image builds require significant disk/time and may need GPU drivers (nvidia-docker) if you want CUDA acceleration.

- Host Python does not have MONAI or torch installed; running training on host is not recommended.

Verification

- After running the smoke train, run `python3 task_manager.py list` to see updated task statuses.

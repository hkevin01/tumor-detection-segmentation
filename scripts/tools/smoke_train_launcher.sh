#!/usr/bin/env bash
# Build and run a lightweight smoke training run inside the heavy Docker image.
# Usage:
#   ./smoke_train_launcher.sh build   # only build image
#   ./smoke_train_launcher.sh run     # build (if needed) and run smoke train
#   ./smoke_train_launcher.sh dry-run # print commands but don't execute

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE="$ROOT_DIR/docker/Dockerfile.phase4"
IMAGE_NAME="tds:phase4-smoke"

usage() {
  echo "Usage: $0 {build|run|dry-run}"
  exit 2
}

if [[ ${#} -ne 1 ]]; then
  usage
fi

MODE=$1

if [[ "$MODE" != "build" && "$MODE" != "run" && "$MODE" != "dry-run" ]]; then
  usage
fi

BUILD_CMD=(docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" "$ROOT_DIR")
RUN_CMD=(docker run --rm -it --gpus all -v "$ROOT_DIR":/workspace -w /workspace "$IMAGE_NAME" \
  bash -lc "python3 src/training/train_enhanced.py --epochs 2 --dataset-config data/config.json")

echo "DOCKERFILE: $DOCKERFILE"
echo "IMAGE: $IMAGE_NAME"

if [[ "$MODE" == "dry-run" ]]; then
  echo "DRY-RUN: build command: ${BUILD_CMD[*]}"
  echo "DRY-RUN: run command: ${RUN_CMD[*]}"
  exit 0
fi

if [[ "$MODE" == "build" || "$MODE" == "run" ]]; then
  echo "Building image..."
  "${BUILD_CMD[@]}"
fi

if [[ "$MODE" == "run" ]]; then
  echo "Running smoke training (2 epochs)..."
  "${RUN_CMD[@]}"
fi

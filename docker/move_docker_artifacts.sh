#!/usr/bin/env bash
# Safe move script for docker artifacts into structured subfolders.
# Review docker/docker_files_index.json before running.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# create target folders
mkdir -p docker/images docker/compose docker/scripts

# read index and move files if they exist
INDEX="docker/docker_files_index.json"
if [ ! -f "$INDEX" ]; then
  echo "Index $INDEX not found. Create it first." >&2
  exit 2
fi

moves=(
  "Dockerfile:docker/images/Dockerfile"
  "Dockerfile.simple:docker/images/Dockerfile.simple"
  "Dockerfile.cuda:docker/images/Dockerfile.cuda"
  "Dockerfile.phase4:docker/images/Dockerfile.phase4"
  "Dockerfile.test-lite:docker/images/Dockerfile.test-lite"
  "docker-compose.yml:docker/compose/docker-compose.yml"
  "docker-compose.cpu.yml:docker/compose/docker-compose.cpu.yml"
  "docker-compose.phase4.yml:docker/compose/docker-compose.phase4.yml"
  "docker-compose.test-lite.yml:docker/compose/docker-compose.test-lite.yml"
  "docker-helper.sh:docker/scripts/docker-helper.sh"
  "docker-manager:docker/scripts/docker-manager"
  ".env:docker/.env"
)

echo "Planned moves (only if source exists and destination empty):"
for m in "${moves[@]}"; do
  src=${m%%:*}
  dst=${m#*:}
  if [ -e "$src" ]; then
    if [ -e "$dst" ]; then
      echo "SKIP: $src -> $dst (destination exists)"
    else
      echo "MOVE: $src -> $dst"
    fi
  else
    echo "NOOP: $src (not found)"
  fi
done

read -p "Run the moves? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  for m in "${moves[@]}"; do
    src=${m%%:*}
    dst=${m#*:}
    if [ -e "$src" ] && [ ! -e "$dst" ]; then
      mv "$src" "$dst"
      echo "Moved $src -> $dst"
    fi
  done
  echo "Done. Review changes and update references if needed."
else
  echo "Aborted. No files moved."
fi

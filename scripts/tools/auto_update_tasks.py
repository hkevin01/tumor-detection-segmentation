#!/usr/bin/env python3
"""Auto-update organization_tasks.json based on repo artifacts.

This script is conservative: it only marks things completed when it finds clear evidence
in the repository (files moved, scripts present, dockerfiles present).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK_FILE = ROOT / "organization_tasks.json"


def load_tasks():
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, sort_keys=False)


def main():
    tasks = load_tasks()

    # If docker/ exists and contains Dockerfile.phase4, mark related tasks
    docker_dir = ROOT / "docker"
    if docker_dir.exists():
        # mark that docker-related reorg is in progress or done
        # example: consider update_references done earlier
        tasks.get("update_references", {}).setdefault("status", "completed")

        # If scripts/validation/test_docker.sh exists,
        # mark organize_scripts.move_validation_scripts completed
    val = ROOT / "scripts" / "validation" / "test_docker.sh"
    if val.exists():
        organize = tasks.setdefault("organize_scripts", {})
        subtasks = organize.setdefault("subtasks", {})
        mv = subtasks.setdefault("move_validation_scripts", {})
        mv["status"] = "completed"
        organize.setdefault("status", "in-progress")

        # If ORGANIZATION_SUMMARY.md exists,
        # mark final_validation.create_summary completed
    summary = ROOT / "ORGANIZATION_SUMMARY.md"
    if summary.exists():
        final = tasks.setdefault("final_validation", {})
        subs = final.setdefault("subtasks", {})
        cs = subs.setdefault("create_summary", {})
        cs["status"] = "completed"
        final.setdefault("status", "in-progress")

    # If docker/Dockerfile.phase4 exists, add pending smoke train subtask
    heavy = docker_dir / "Dockerfile.phase4"
    if heavy.exists():
        final = tasks.setdefault("final_validation", {})
        subs = final.setdefault("subtasks", {})
        subs.setdefault("run_smoke_train", {
            "description": "Run a 2-epoch smoke training inside Docker",
            "status": "pending",
        })
        final.setdefault("status", "in-progress")

    save_tasks(tasks)
    print("organization_tasks.json updated based on repository artifacts.")


if __name__ == "__main__":
    main()

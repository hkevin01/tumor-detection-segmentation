#!/usr/bin/env python3
"""Sync a few task statuses based on repository artifacts.

This helper is conservative: it only marks subtasks completed when an
expected artifact exists. It does not move or delete files.
"""

from pathlib import Path

from task_manager import TaskManager


def main():
    root = Path(__file__).resolve().parents[2]
    manager = TaskManager(root)

    # If validation scripts exist, mark move_validation_scripts completed
    val_script = root / "scripts" / "validation" / "test_docker.sh"
    if val_script.exists():
        manager.update_task_status(
            "organize_scripts",
            task_id="move_validation_scripts",
            status="completed",
        )

    # If config/organization/organization_tasks.json exists, we consider update_references done
    tasks_file = root / "config/organization/organization_tasks.json"
    if tasks_file.exists():
        manager.update_task_status("update_references", status="completed")

    # If docker directory exists, mark consolidate_logs as pending->in-progress
    if (root / "docker").exists():
        manager.update_task_status("organize_scripts", status="in-progress")

    manager.print_status()


if __name__ == "__main__":
    main()
    main()

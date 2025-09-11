import json
from pathlib import Path

from task_manager import TaskManager


def test_task_manager_load_and_update(tmp_path: Path):
    root = tmp_path
    manager = TaskManager(root)

    # initial file created
    assert (root / "config/organization/config/organization/organization_tasks.json").exists()

    # update a subtask
    ok = manager.update_task_status(
        "organize_scripts",
        task_id="move_validation_scripts",
        status="completed",
    )
    assert ok

    data = json.loads((root / "config/organization/config/organization/organization_tasks.json").read_text())
    assert (
        data["organize_scripts"]["subtasks"]["move_validation_scripts"][
            "status"
        ]
        == "completed"
    )

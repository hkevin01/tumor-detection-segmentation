import json
from pathlib import Path

from scripts.tools import sync_tasks_from_fs


def test_sync_runs_and_writes_tasks():
    # Run the sync helper; it should not raise and should produce a valid JSON
    sync_tasks_from_fs.main()

    tasks_file = (
        Path(__file__).resolve().parents[1] / "config/organization/organization_tasks.json"
    )
    assert tasks_file.exists()

    data = json.loads(tasks_file.read_text())
    assert isinstance(data, dict)

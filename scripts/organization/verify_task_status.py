#!/usr/bin/env python3
"""
Quick task status verification
"""

import json
from pathlib import Path


def main():
    project_root = Path("/home/kevin/Projects/tumor-detection-segmentation")
    tasks_file = project_root / "config/organization/organization_tasks.json"

    if not tasks_file.exists():
        print("❌ config/organization/organization_tasks.json not found")
        return

    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    print("🎯 TASK STATUS VERIFICATION")
    print("=" * 50)

    total_tasks = 0
    completed_tasks = 0

    for category, task_info in tasks.items():
        total_tasks += 1
        status = task_info.get("status", "pending")

        if status == "completed":
            completed_tasks += 1
            print(f"✅ {category}: {task_info.get('title', 'Unknown')}")
        else:
            print(f"⏳ {category}: {task_info.get('title', 'Unknown')} [{status}]")

        # Check subtasks
        subtasks = task_info.get("subtasks", {})
        for subtask_id, subtask_info in subtasks.items():
            total_tasks += 1
            sub_status = subtask_info.get("status", "pending")
            if sub_status == "completed":
                completed_tasks += 1
                print(f"  ✅ {subtask_id}: {subtask_info.get('description', 'Unknown')}")
            else:
                print(f"  ⏳ {subtask_id}: {subtask_info.get('description', 'Unknown')} [{sub_status}]")

    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {completed_tasks}/{total_tasks} tasks completed ({completed_tasks/total_tasks*100:.1f}%)")

    if completed_tasks == total_tasks:
        print("🎉 ALL TASKS COMPLETED!")
        return True
    else:
        print(f"⚠️  {total_tasks - completed_tasks} tasks remaining")
        return False

if __name__ == "__main__":
    main()
    main()

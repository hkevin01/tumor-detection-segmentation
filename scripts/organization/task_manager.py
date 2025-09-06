#!/usr/bin/env python3
"""
Project Organization Task Manager

This script manages and tracks the remaining project organization tasks.
"""

import argparse
import json
from pathlib import Path


class TaskManager:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.tasks_file = self.project_root / "config/organization/organization_tasks.json"
        self.tasks = self.load_tasks()

    def load_tasks(self):
        """Load existing tasks or create default task list."""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Create comprehensive task list
        tasks = {
            "configuration_files": {
                "title": "Organize Configuration Files",
                "description": "Move config files to appropriate directories",
                "status": "pending",
                "subtasks": {
                    "move_config_json": {
                        "description": "Move config.json to config/ directory",
                        "status": "pending"
                    },
                    "move_env_files": {
                        "description": "Move .env and .env.example to config/",
                        "status": "pending"
                    },
                    "move_pytest_config": {
                        "description": "Move pytest.ini to config/ directory",
                        "status": "pending"
                    },
                    "move_mypy_config": {
                        "description": "Move mypy.ini to config/ directory",
                        "status": "pending"
                    },
                    "consolidate_requirements": {
                        "description": (
                            "Review and organize requirements files"
                        ),
                        "status": "pending"
                    }
                }
            },
            "cleanup_temp_files": {
                "title": "Clean Up Temporary Files",
                "description": "Remove or organize temporary and test files",
                "status": "pending",
                "subtasks": {
                    "remove_test_temp": {
                        "description": (
                            "Remove test.tmp, test2.pyc, test_temp/, test_viz/"
                        ),
                        "status": "pending"
                    },
                    "cleanup_temp_dir": {
                        "description": "Clean up temp/ directory",
                        "status": "pending"
                    },
                    "move_coverage": {
                        "description": "Move .coverage to reports/ directory",
                        "status": "pending"
                    }
                }
            },
            "organize_scripts": {
                "title": "Organize Scripts and Utilities",
                "description": "Move scripts to appropriate locations",
                "status": "pending",
                "subtasks": {
                    "move_run_script": {
                        "description": "Move run.sh to scripts/ directory",
                        "status": "pending"
                    },
                    "move_validation_scripts": {
                        "description": (
                            "Move validation scripts to tools/ directory"
                        ),
                        "status": "pending"
                    }
                }
            },
            "consolidate_logs": {
                "title": "Consolidate Log Directories",
                "description": "Merge log/ and logs/ directories",
                "status": "pending",
                "subtasks": {
                    "merge_log_dirs": {
                        "description": (
                            "Merge log/ and logs/ into single logs/ directory"
                        ),
                        "status": "pending"
                    }
                }
            },
            "update_references": {
                "title": "Update File References",
                "description": "Update all references to moved files",
                "status": "pending",
                "subtasks": {
                    "update_config_references": {
                        "description": (
                            "Update references to config.json in scripts"
                            " and docs"
                        ),
                        "status": "pending"
                    },
                    "update_script_references": {
                        "description": "Update references to moved scripts",
                        "status": "pending"
                    },
                    "update_documentation": {
                        "description": (
                            "Update documentation with new file paths"
                        ),
                        "status": "pending"
                    }
                }
            },
            "final_validation": {
                "title": "Final Validation",
                "description": "Validate the complete organization",
                "status": "pending",
                "subtasks": {
                    "validate_structure": {
                        "description": (
                            "Run comprehensive structure validation"
                        ),
                        "status": "pending"
                    },
                    "test_references": {
                        "description": (
                            "Test that all file references work correctly"
                        ),
                        "status": "pending"
                    },
                    "create_summary": {
                        "description": (
                            "Create final organization summary"
                        ),
                        "status": "pending"
                    }
                }
            }
        }

        self.save_tasks(tasks)
        return tasks

    def save_tasks(self, tasks=None):
        """Save tasks to file."""
        if tasks is None:
            tasks = self.tasks
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)

    def update_task_status(self, category, task_id=None, status="completed"):
        """Update the status of a specific subtask or whole category.

        If task_id is None, update the category's overall status.
        status should be one of: 'pending', 'in-progress', 'completed'.
        """
        if status not in {"pending", "in-progress", "completed"}:
            raise ValueError(
                "status must be 'pending', 'in-progress' or 'completed'"
            )

        if category not in self.tasks:
            return False

        if task_id is None:
            # update category-level status
            self.tasks[category]["status"] = status
            self.save_tasks()
            return True

        if task_id in self.tasks[category].get("subtasks", {}):
            self.tasks[category]["subtasks"][task_id]["status"] = status
            # if any subtask is in-progress, bubble up category status
            subs = self.tasks[category]["subtasks"]
            if any(s.get("status") == "in-progress" for s in subs.values()):
                self.tasks[category]["status"] = "in-progress"
            elif all(s.get("status") == "completed" for s in subs.values()):
                self.tasks[category]["status"] = "completed"
            else:
                self.tasks[category]["status"] = "pending"

            self.save_tasks()
            return True

        return False

    def get_pending_tasks(self):
        """Get all pending tasks."""
        pending = []
        for category, category_data in self.tasks.items():
            # include categories that are pending or in-progress
            if category_data["status"] in {"pending", "in-progress"}:
                pending.append({
                    "category": category,
                    "title": category_data["title"],
                    "description": category_data.get("description", ""),
                    "status": category_data["status"],
                })
            # include individual subtasks that are pending or in-progress
            for task_id, task_data in (
                category_data.get("subtasks", {}).items()
            ):
                if task_data["status"] in {"pending", "in-progress"}:
                    pending.append({
                        "category": category,
                        "task_id": task_id,
                        "title": task_data["description"],
                        "status": task_data["status"],
                    })
        return pending

    def get_completed_tasks(self):
        """Get all completed tasks."""
        completed = []
        for category, category_data in self.tasks.items():
            for task_id, task_data in category_data["subtasks"].items():
                if task_data["status"] == "completed":
                    completed.append({
                        "category": category,
                        "task_id": task_id,
                        "title": task_data["description"]
                    })
        return completed

    def print_status(self):
        """Print current task status."""
        print("🎯 PROJECT ORGANIZATION TASK STATUS")
        print("=" * 60)
        pending = self.get_pending_tasks()
        completed = self.get_completed_tasks()

        print(f"\n✅ COMPLETED TASKS ({len(completed)}):")
        for task in completed:
            print(f"  • {task['title']}")

        print(f"\n⏳ PENDING/IN-PROGRESS TASKS ({len(pending)}):")
        for i, task in enumerate(pending, 1):
            status = task.get("status", "pending")
            if "task_id" in task:
                print(
                    "  {}. [{}] {}::{} - {}".format(
                        i,
                        status,
                        task["category"],
                        task["task_id"],
                        task["title"],
                    )
                )
            else:
                print(
                    "  {}. [{}] [{}] {}".format(
                        i, status, task["category"], task["title"]
                    )
                )

        total_tasks = len(completed) + len(pending)
        progress = (
            len(completed) / total_tasks * 100 if total_tasks > 0 else 0
        )

        print(
            "\n📊 PROGRESS: {}/{} tasks completed ({:.1f}%)".format(
                len(completed), total_tasks, progress
            )
        )

        if pending:
            print("\n🚀 NEXT TASKS TO WORK ON:")
            for i, task in enumerate(pending[:3], 1):  # Show next 3 tasks
                if "task_id" in task:
                    print(
                        "  {}. [{}] {}::{} - {}".format(
                            i,
                            task.get("status", "pending"),
                            task["category"],
                            task["task_id"],
                            task["title"],
                        )
                    )
                else:
                    print(
                        "  {}. [{}] [{}] {}".format(
                            i,
                            task.get("status", "pending"),
                            task["category"],
                            task["title"],
                        )
                    )


def main():
    """Main function to display task status."""
    parser = argparse.ArgumentParser(
        description="Project Organization Task Manager"
    )
    parser.add_argument(
        "--root",
        help="project root",
        default=str(Path(__file__).resolve().parent),
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    sub.add_parser("list", help="Print task status")

    set_parser = sub.add_parser(
        "set-status", help="Set status for a category or subtask"
    )
    set_parser.add_argument(
        "category", help="Category name (top-level key)"
    )
    set_parser.add_argument(
        "status",
        help="Status: pending|in-progress|completed",
    )
    set_parser.add_argument("--task-id", help="Subtask id (optional)")

    args = parser.parse_args()
    project_root = args.root
    manager = TaskManager(project_root)

    if args.cmd == "set-status":
        task_id = getattr(args, "task_id", None)
        ok = manager.update_task_status(
            args.category, task_id=task_id, status=args.status
        )
        if not ok:
            print(
                "Failed to update status for {} / {}".format(
                    args.category, task_id
                )
            )
        manager.print_status()
    else:
        manager.print_status()


if __name__ == "__main__":
    main()

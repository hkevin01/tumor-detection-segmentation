#!/usr/bin/env python3
"""
Project Organization Task Manager

This script manages and tracks the remaining project organization tasks.
"""

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
                        "description": "Review and organize requirements files",
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
                        "description": "Remove test.tmp, test2.pyc, test_temp/, test_viz/",
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
                        "description": "Move validation scripts to tools/ directory",
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
                        "description": "Merge log/ and logs/ into single logs/ directory",
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
                        "description": "Update references to config.json in scripts and docs",
                        "status": "pending"
                    },
                    "update_script_references": {
                        "description": "Update references to moved scripts",
                        "status": "pending"
                    },
                    "update_documentation": {
                        "description": "Update documentation with new file paths",
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
                        "description": "Run comprehensive structure validation",
                        "status": "pending"
                    },
                    "test_references": {
                        "description": "Test that all file references work correctly",
                        "status": "pending"
                    },
                    "create_summary": {
                        "description": "Create final organization summary",
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
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)

    def update_task_status(self, category, task_id, status):
        """Update the status of a specific task."""
        if (category in self.tasks and
                task_id in self.tasks[category]["subtasks"]):
            self.tasks[category]["subtasks"][task_id]["status"] = status
            self.save_tasks()
            return True
        return False

    def get_pending_tasks(self):
        """Get all pending tasks."""
        pending = []
        for category, category_data in self.tasks.items():
            if category_data["status"] == "pending":
                pending.append({
                    "category": category,
                    "title": category_data["title"],
                    "description": category_data["description"]
                })
            else:
                for task_id, task_data in category_data["subtasks"].items():
                    if task_data["status"] == "pending":
                        pending.append({
                            "category": category,
                            "task_id": task_id,
                            "title": task_data["description"]
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

        print(f"\n⏳ PENDING TASKS ({len(pending)}):")
        for i, task in enumerate(pending, 1):
            if "task_id" in task:
                print(f"  {i}. {task['title']}")
            else:
                print(f"  {i}. [{task['category']}] {task['title']}")

        total_tasks = len(completed) + len(pending)
        progress = (len(completed) / total_tasks * 100
                    if total_tasks > 0 else 0)

        print(f"\n📊 PROGRESS: {len(completed)}/{total_tasks} tasks completed "
              f"({progress:.1f}%)")

        if pending:
            print("\n🚀 NEXT TASKS TO WORK ON:")
            for i, task in enumerate(pending[:3], 1):  # Show next 3 tasks
                if "task_id" in task:
                    print(f"  {i}. {task['title']}")
                else:
                    print(f"  {i}. [{task['category']}] {task['title']}")


def main():
    """Main function to display task status."""
    project_root = "/home/kevin/Projects/tumor-detection-segmentation"
    manager = TaskManager(project_root)
    manager.print_status()


if __name__ == "__main__":
    main()

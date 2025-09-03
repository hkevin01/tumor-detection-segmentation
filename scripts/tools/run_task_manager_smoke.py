#!/usr/bin/env python3
"""Simple runner to exercise TaskManager.print_status."""

from pathlib import Path

from task_manager import TaskManager


def main():
    root = Path(__file__).resolve().parents[2]
    manager = TaskManager(root)
    manager.print_status()


if __name__ == "__main__":
    main()
    main()

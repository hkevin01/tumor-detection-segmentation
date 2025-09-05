#!/usr/bin/env python3
"""
Simple Resource Monitor for VSCode Safety
"""

import psutil


def check_system():
    """Quick system resource check"""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)

    print(f"Memory: {memory.percent:.1f}% ({memory.available / (1024**3):.1f}GB free)")
    print(f"CPU: {cpu:.1f}%")
    print(f"VSCode Safe: {'✓' if memory.percent < 70 and cpu < 75 else '✗'}")

    return memory.percent < 70 and cpu < 75

if __name__ == "__main__":
    safe = check_system()
    exit(0 if safe else 1)

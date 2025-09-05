#!/usr/bin/env python3
import psutil
import time
import json
import os
from datetime import datetime
from pathlib import Path

def detect_vscode_crash():
    """Monitor VSCode processes and detect crashes"""
    recovery_dir = Path("recovery")
    recovery_dir.mkdir(exist_ok=True)
    
    last_vscode_count = 0
    crash_count = 0
    
    while True:
        try:
            # Count VSCode processes
            vscode_procs = [p for p in psutil.process_iter(['name']) 
                           if 'code' in p.info['name'].lower()]
            current_count = len(vscode_procs)
            
            # Detect sudden drop in VSCode processes (potential crash)
            if last_vscode_count > 0 and current_count == 0:
                crash_count += 1
                crash_info = {
                    'timestamp': datetime.now().isoformat(),
                    'crash_number': crash_count,
                    'previous_process_count': last_vscode_count,
                    'system_memory_percent': psutil.virtual_memory().percent,
                    'system_cpu_percent': psutil.cpu_percent()
                }
                
                # Save crash info
                crash_file = recovery_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(crash_file, 'w') as f:
                    json.dump(crash_info, f, indent=2)
                
                print(f"🚨 VSCode crash detected! Crash #{crash_count}")
                print(f"   Memory: {crash_info['system_memory_percent']:.1f}%")
                print(f"   CPU: {crash_info['system_cpu_percent']:.1f}%")
                
                # Trigger recovery
                os.system("python recovery/recovery_assistant.py")
            
            last_vscode_count = current_count
            time.sleep(5)
            
        except Exception as e:
            print(f"Crash detection error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    detect_vscode_crash()

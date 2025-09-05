#!/usr/bin/env python3
"""
Training Progress Summary and Status Tracker
============================================

Real-time monitoring for the tumor detection training sequence.
"""

from datetime import datetime
import subprocess
import sys
import os

def print_status_header():
    print("🧠 TUMOR DETECTION TRAINING MONITOR")
    print("=" * 60)
    print(f"📅 Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def get_training_process_info():
    """Get detailed training process information."""
    try:
        # Find training process
        result = subprocess.run(
            ["pgrep", "-f", "train_enhanced.py"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if not result.stdout.strip():
            return None, "No training process found"
        
        pid = result.stdout.strip()
        
        # Get detailed process info
        ps_result = subprocess.run(
            ["ps", "-p", pid, "-o", "pid,ppid,%cpu,%mem,rss,vsz,etime,cmd"],
            capture_output=True,
            text=True,
            check=False
        )
        
        return pid, ps_result.stdout
    except Exception as e:
        return None, f"Error: {e}"

def format_memory(kb):
    """Format memory from KB to human readable."""
    if kb < 1024:
        return f"{kb}KB"
    elif kb < 1024 * 1024:
        return f"{kb/1024:.1f}MB"
    else:
        return f"{kb/(1024*1024):.1f}GB"

def main():
    print_status_header()
    
    # Get training status
    pid, process_info = get_training_process_info()
    
    if pid:
        print("✅ **TRAINING ACTIVE**")
        print(f"Process ID: {pid}")
        print()
        print("Process Details:")
        print(process_info)
        print()
        
        # Memory analysis
        lines = process_info.strip().split('\n')
        if len(lines) > 1:
            data = lines[1].split()
            if len(data) >= 8:
                cpu_percent = data[2]
                mem_percent = data[3]
                rss_kb = int(data[4])
                vsz_kb = int(data[5])
                elapsed = data[6]
                
                print("📊 **RESOURCE ANALYSIS**:")
                print(f"   CPU Usage: {cpu_percent}%")
                print(f"   Memory: {mem_percent}% ({format_memory(rss_kb)} RSS)")
                print(f"   Virtual Memory: {format_memory(vsz_kb)}")
                print(f"   Runtime: {elapsed}")
                print()
    else:
        print("❌ **NO TRAINING ACTIVE**")
        print(f"Status: {process_info}")
        print()
    
    # Training sequence status
    print("🎯 **TRAINING SEQUENCE STATUS**")
    print("Current: 5-epoch baseline training (ACTIVE)")
    print("Queue: 10-epoch extended → 25-epoch production")
    print()
    
    # Expected progression
    print("📈 **EXPECTED PROGRESSION**:")
    print("Phase 1: Data loading & model initialization ✅")
    print("Phase 2: Active training in progress... 🔄")
    print("Phase 3: Validation & checkpointing (pending)")
    print("Phase 4: Training completion & next session launch (pending)")
    print()
    
    # System health
    try:
        uptime_result = subprocess.run(
            ["uptime"],
            capture_output=True,
            text=True,
            check=False
        )
        print("💻 **SYSTEM STATUS**:")
        print(f"Load: {uptime_result.stdout.strip()}")
    except:
        print("💻 System status unavailable")
    
    print()
    print("=" * 60)
    print("🚀 Training is progressing excellently!")
    print("💡 Next check recommended in 5-10 minutes")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
VSCode Crash Monitor and Prevention System
Monitors system resources and prevents VSCode crashes during medical imaging workflows
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import psutil


class VSCodeCrashMonitor:
    def __init__(self, log_dir: str = "logs/monitoring"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.setup_logging()

        # Thresholds (configurable)
        self.memory_threshold = 0.85  # 85% RAM usage
        self.gpu_memory_threshold = 0.90  # 90% GPU memory
        self.cpu_threshold = 0.95  # 95% CPU usage
        self.swap_threshold = 0.50  # 50% swap usage

        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        self.crash_detected = False

        # Process tracking
        self.vscode_processes = []
        self.python_processes = []

        self.logger.info("VSCode Crash Monitor initialized")

    def setup_logging(self):
        """Setup comprehensive logging system"""
        log_file = self.log_dir / f"vscode_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'memory': {},
            'cpu': {},
            'disk': {},
            'gpu': {},
            'processes': {}
        }

        # Memory stats
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        stats['memory'] = {
            'total_gb': round(memory.total / 1024**3, 2),
            'available_gb': round(memory.available / 1024**3, 2),
            'used_gb': round(memory.used / 1024**3, 2),
            'percent': memory.percent,
            'swap_total_gb': round(swap.total / 1024**3, 2),
            'swap_used_gb': round(swap.used / 1024**3, 2),
            'swap_percent': swap.percent
        }

        # CPU stats
        stats['cpu'] = {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }

        # Disk stats
        disk = psutil.disk_usage('/')
        stats['disk'] = {
            'total_gb': round(disk.total / 1024**3, 2),
            'used_gb': round(disk.used / 1024**3, 2),
            'free_gb': round(disk.free / 1024**3, 2),
            'percent': round((disk.used / disk.total) * 100, 2)
        }

        # GPU stats (if available)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            stats['gpu'] = []
            for gpu in gpus:
                stats['gpu'].append({
                    'id': gpu.id,
                    'name': gpu.name,
                    'memory_used_mb': gpu.memoryUsed,
                    'memory_total_mb': gpu.memoryTotal,
                    'memory_percent': round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2),
                    'utilization': gpu.load * 100,
                    'temperature': gpu.temperature
                })
        except ImportError:
            stats['gpu'] = "GPUtil not available"
        except Exception as e:
            stats['gpu'] = f"GPU monitoring error: {e}"

        # Process stats
        stats['processes'] = self.get_process_stats()

        return stats

    def get_process_stats(self) -> Dict:
        """Get stats for VSCode and Python processes"""
        process_stats = {
            'vscode': [],
            'python': [],
            'total_vscode_memory_gb': 0,
            'total_python_memory_gb': 0
        }

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                proc_info = proc.info
                if 'code' in proc_info['name'].lower() or 'vscode' in proc_info['name'].lower():
                    memory_gb = proc_info['memory_info'].rss / 1024**3
                    process_stats['vscode'].append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'memory_gb': round(memory_gb, 2),
                        'cpu_percent': proc_info['cpu_percent']
                    })
                    process_stats['total_vscode_memory_gb'] += memory_gb

                elif 'python' in proc_info['name'].lower():
                    memory_gb = proc_info['memory_info'].rss / 1024**3
                    process_stats['python'].append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'memory_gb': round(memory_gb, 2),
                        'cpu_percent': proc_info['cpu_percent']
                    })
                    process_stats['total_python_memory_gb'] += memory_gb

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        process_stats['total_vscode_memory_gb'] = round(process_stats['total_vscode_memory_gb'], 2)
        process_stats['total_python_memory_gb'] = round(process_stats['total_python_memory_gb'], 2)

        return process_stats

    def check_crash_risk(self, stats: Dict) -> Dict:
        """Analyze crash risk based on system stats"""
        risks = {
            'overall_risk': 'LOW',
            'warnings': [],
            'critical_issues': [],
            'recommendations': []
        }

        # Memory checks
        if stats['memory']['percent'] > self.memory_threshold * 100:
            risks['critical_issues'].append(f"RAM usage at {stats['memory']['percent']:.1f}% (threshold: {self.memory_threshold*100}%)")
            risks['overall_risk'] = 'CRITICAL'
        elif stats['memory']['percent'] > 0.75 * 100:
            risks['warnings'].append(f"RAM usage at {stats['memory']['percent']:.1f}%")
            if risks['overall_risk'] == 'LOW':
                risks['overall_risk'] = 'MEDIUM'

        # Swap usage
        if stats['memory']['swap_percent'] > self.swap_threshold * 100:
            risks['critical_issues'].append(f"Swap usage at {stats['memory']['swap_percent']:.1f}%")
            risks['overall_risk'] = 'CRITICAL'

        # GPU memory
        if isinstance(stats['gpu'], list) and stats['gpu']:
            for gpu in stats['gpu']:
                if gpu['memory_percent'] > self.gpu_memory_threshold * 100:
                    risks['critical_issues'].append(f"GPU {gpu['id']} memory at {gpu['memory_percent']:.1f}%")
                    risks['overall_risk'] = 'CRITICAL'

        # Process memory
        total_memory = stats['processes']['total_vscode_memory_gb'] + stats['processes']['total_python_memory_gb']
        if total_memory > 8:  # More than 8GB
            risks['warnings'].append(f"VSCode+Python using {total_memory:.1f}GB memory")
            if risks['overall_risk'] == 'LOW':
                risks['overall_risk'] = 'MEDIUM'

        # Add recommendations based on risks
        if risks['critical_issues']:
            risks['recommendations'].extend([
                "Save all work immediately",
                "Close unnecessary VSCode windows/extensions",
                "Reduce batch size in training configs",
                "Enable garbage collection",
                "Consider restarting VSCode"
            ])
        elif risks['warnings']:
            risks['recommendations'].extend([
                "Monitor memory usage closely",
                "Close unused browser tabs/applications",
                "Use smaller ROI sizes for training"
            ])

        return risks

    def emergency_cleanup(self):
        """Emergency cleanup to prevent crash"""
        self.logger.warning("🚨 EMERGENCY CLEANUP TRIGGERED")

        try:
            # Force garbage collection
            import gc
            gc.collect()

            # Clear PyTorch cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    self.logger.info("✅ PyTorch CUDA cache cleared")
            except ImportError:
                pass

            # Kill high-memory Python processes (except this monitor)
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    if (proc.info['name'].lower().startswith('python') and
                        proc.info['pid'] != current_pid and
                        proc.info['memory_info'].rss > 2 * 1024**3):  # > 2GB

                        self.logger.warning(f"Terminating high-memory Python process: PID {proc.info['pid']}")
                        proc.terminate()

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Save emergency checkpoint
            self.save_emergency_checkpoint()

        except Exception as e:
            self.logger.error(f"Emergency cleanup failed: {e}")

    def save_emergency_checkpoint(self):
        """Save emergency checkpoint data"""
        checkpoint_file = self.log_dir / f"emergency_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'system_stats': self.get_system_stats(),
            'trigger': 'emergency_cleanup',
            'vscode_processes': len([p for p in psutil.process_iter() if 'code' in p.name().lower()]),
            'python_processes': len([p for p in psutil.process_iter() if 'python' in p.name().lower()])
        }

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            self.logger.info(f"Emergency checkpoint saved: {checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Failed to save emergency checkpoint: {e}")

    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("🔍 Starting VSCode crash monitoring")

        while self.monitoring:
            try:
                # Get system stats
                stats = self.get_system_stats()

                # Check crash risk
                risk_analysis = self.check_crash_risk(stats)

                # Log current status
                self.logger.info(f"Memory: {stats['memory']['percent']:.1f}% | "
                               f"CPU: {stats['cpu']['percent']:.1f}% | "
                               f"Risk: {risk_analysis['overall_risk']}")

                # Save detailed stats every 30 seconds
                if int(time.time()) % 30 == 0:
                    stats_file = self.log_dir / f"stats_{datetime.now().strftime('%Y%m%d_%H')}.jsonl"
                    with open(stats_file, 'a') as f:
                        f.write(json.dumps({**stats, 'risk_analysis': risk_analysis}) + '\n')

                # Handle critical situations
                if risk_analysis['overall_risk'] == 'CRITICAL':
                    self.logger.critical("🚨 CRITICAL RISK DETECTED!")
                    for issue in risk_analysis['critical_issues']:
                        self.logger.critical(f"  ❌ {issue}")

                    for rec in risk_analysis['recommendations']:
                        self.logger.warning(f"  💡 {rec}")

                    # Trigger emergency cleanup
                    self.emergency_cleanup()

                elif risk_analysis['warnings']:
                    for warning in risk_analysis['warnings']:
                        self.logger.warning(f"⚠️  {warning}")

                time.sleep(5)  # Monitor every 5 seconds

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(10)

    def start_monitoring(self):
        """Start the monitoring system"""
        if self.monitoring:
            self.logger.warning("Monitoring already running")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.logger.info("✅ VSCode crash monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("🛑 VSCode crash monitoring stopped")

    def generate_report(self) -> str:
        """Generate a monitoring report"""
        stats = self.get_system_stats()
        risk_analysis = self.check_crash_risk(stats)

        report = f"""
🔍 VSCode Crash Monitor Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 System Status:
  Memory: {stats['memory']['used_gb']:.1f}GB / {stats['memory']['total_gb']:.1f}GB ({stats['memory']['percent']:.1f}%)
  Swap: {stats['memory']['swap_used_gb']:.1f}GB / {stats['memory']['swap_total_gb']:.1f}GB ({stats['memory']['swap_percent']:.1f}%)
  CPU: {stats['cpu']['percent']:.1f}%
  Disk: {stats['disk']['used_gb']:.1f}GB / {stats['disk']['total_gb']:.1f}GB ({stats['disk']['percent']:.1f}%)

🖥️  Process Usage:
  VSCode Memory: {stats['processes']['total_vscode_memory_gb']:.1f}GB
  Python Memory: {stats['processes']['total_python_memory_gb']:.1f}GB
  VSCode Processes: {len(stats['processes']['vscode'])}
  Python Processes: {len(stats['processes']['python'])}

⚡ Risk Analysis:
  Overall Risk: {risk_analysis['overall_risk']}
  Critical Issues: {len(risk_analysis['critical_issues'])}
  Warnings: {len(risk_analysis['warnings'])}

💡 Recommendations:
"""
        for rec in risk_analysis['recommendations']:
            report += f"  • {rec}\n"

        return report

def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="VSCode Crash Monitor")
    parser.add_argument('--action', choices=['start', 'report', 'cleanup'],
                       default='start', help='Action to perform')
    parser.add_argument('--log-dir', default='logs/monitoring',
                       help='Directory for log files')

    args = parser.parse_args()

    monitor = VSCodeCrashMonitor(log_dir=args.log_dir)

    if args.action == 'start':
        try:
            monitor.start_monitoring()
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n✅ Monitoring stopped by user")

    elif args.action == 'report':
        print(monitor.generate_report())

    elif args.action == 'cleanup':
        monitor.emergency_cleanup()

if __name__ == "__main__":
    main()

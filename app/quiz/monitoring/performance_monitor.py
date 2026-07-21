"""
Hardware performance monitoring for StudyBot.

Tracks:
- CPU usage
- RAM usage
- Process memory
- Generation timing
"""

import time
import os
import psutil
import subprocess

class PerformanceMonitor:

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None

    def get_gpu_info(self):
        """
        Get NVIDIA GPU metrics using nvidia-smi.
        """

        try:
            result = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                encoding="utf-8",
            )

            gpu, memory_used, memory_total, temperature = result.strip().split(",")

            return {
                "gpu_usage_percent": int(gpu.strip()),
                "gpu_memory_used_mb": int(memory_used.strip()),
                "gpu_memory_total_mb": int(memory_total.strip()),
                "gpu_temperature_c": int(temperature.strip()),
            }

        except Exception:
            return {
                "gpu_usage_percent": 0,
                "gpu_memory_used_mb": 0,
                "gpu_memory_total_mb": 0,
                "gpu_temperature_c": 0,
            }


    def start(self):
        """Start measuring generation performance."""
        self.start_time = time.perf_counter()


    def stop(self):
        """Return performance snapshot."""
        elapsed = 0

        if self.start_time:
            elapsed = time.perf_counter() - self.start_time

        memory = self.process.memory_info()

        performance = {
            "generation_time": round(elapsed, 4),

            "cpu_usage_percent": psutil.cpu_percent(
                interval=0.5
            ),

            "ram_usage_percent": psutil.virtual_memory().percent,

            "process_memory_mb": round(
                memory.rss / 1024 / 1024,
                2
            ),

            "cpu_frequency_mhz": round(
                psutil.cpu_freq().current,
                2
            )
            if psutil.cpu_freq()
            else 0
        }

        performance.update(
            self.get_gpu_info()
        )

        disk = psutil.disk_io_counters()

        if disk:
            performance.update({
                "disk_read_mb": round(
                    disk.read_bytes / 1024 / 1024,
                    2
                ),
                "disk_write_mb": round(
                    disk.write_bytes / 1024 / 1024,
                    2
                ),
            })
        else:
            performance.update({
                "disk_read_mb": 0,
                "disk_write_mb": 0,
            })

        return performance


if __name__ == "__main__":

    monitor = PerformanceMonitor()

    monitor.start()

    time.sleep(2)

    result = monitor.stop()

    print("\n===== PERFORMANCE TEST =====")
    for key, value in result.items():
        print(f"{key}: {value}")
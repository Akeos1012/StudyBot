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


class PerformanceMonitor:

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None


    def start(self):
        """Start measuring generation performance."""
        self.start_time = time.perf_counter()


    def stop(self):
        """Return performance snapshot."""
        elapsed = 0

        if self.start_time:
            elapsed = time.perf_counter() - self.start_time

        memory = self.process.memory_info()

        return {
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


if __name__ == "__main__":

    monitor = PerformanceMonitor()

    monitor.start()

    time.sleep(2)

    result = monitor.stop()

    print("\n===== PERFORMANCE TEST =====")
    for key, value in result.items():
        print(f"{key}: {value}")
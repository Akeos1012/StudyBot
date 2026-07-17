"""
Performance Profiler Module

Responsible for measuring execution performance.

This module does NOT contain:
- Quiz generation logic
- LLM logic
- Validation logic
- Business rules

It only measures execution time and stores metrics.

Architecture:

Quiz Generator
      |
      v
Performance Profiler
      |
      ├── Timing
      ├── Counters
      └── Reporting
"""

import logging
import time
from contextlib import contextmanager
from typing import Dict, Any


logger = logging.getLogger(__name__)


# ============================================================
# GLOBAL METRICS STORAGE
# ============================================================

_metrics = {
    "calls": {},
    "total_time": {},
}


# ============================================================
# BASIC TIMER
# ============================================================

@contextmanager
def profile_time(name: str):
    """
    Measure execution time of a code block.

    Example:

        with profile_time("llm_generation"):
            response = llm.generate(prompt)

    """

    start = time.perf_counter()

    try:
        yield

    finally:
        elapsed = time.perf_counter() - start

        _record_metric(name, elapsed)

        logger.info(
            "[PROFILE] %s: %.4fs",
            name,
            elapsed,
        )

        print(
            f"⏱️ {name}: {elapsed:.4f}s"
        )


# ============================================================
# METRIC STORAGE
# ============================================================

def _record_metric(name: str, elapsed: float):
    """
    Store timing information.
    """

    if name not in _metrics["calls"]:
        _metrics["calls"][name] = 0
        _metrics["total_time"][name] = 0.0

    _metrics["calls"][name] += 1
    _metrics["total_time"][name] += elapsed



# ============================================================
# REPORTING
# ============================================================

def get_performance_metrics() -> Dict[str, Any]:
    """
    Return collected performance metrics.
    """

    result = {}

    for name in _metrics["calls"]:

        calls = _metrics["calls"][name]
        total = _metrics["total_time"][name]

        result[name] = {
            "calls": calls,
            "total_time": round(total, 4),
            "average_time": round(
                total / calls,
                4
            )
        }

    return result



# ============================================================
# RESET
# ============================================================

def reset_metrics():
    """
    Clear stored metrics.
    Useful for testing.
    """

    _metrics["calls"].clear()
    _metrics["total_time"].clear()
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def profile_time(name: str):
    """
    Measure execution time of a block of code.
    """

    start = time.perf_counter()

    try:
        yield

    finally:
        elapsed = time.perf_counter() - start

        logger.info(
            "[PROFILE] %s: %.4fs",
            name,
            elapsed,
        )

        print(f"⏱️ {name}: {elapsed:.4f}s")
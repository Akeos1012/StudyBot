"""
StudyBot Configuration

Single source of truth for application settings.
Environment variables (STUDYBOT_* prefix) override defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(key: str, default: bool) -> bool:
    """Parse a boolean env var (true/false/1/0)."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes")


def _get_list(key: str, default: list) -> list:
    """Parse a comma-separated env var into a list."""
    val = os.getenv(key)
    if val is None:
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


# ==========================================================
# APPLICATION
# ==========================================================

DEBUG = _get_bool("STUDYBOT_DEBUG", True)


# ==========================================================
# API CONFIGURATION
# ==========================================================

API_HOST = os.getenv("STUDYBOT_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("STUDYBOT_API_PORT", "8000"))
API_RELOAD = _get_bool("STUDYBOT_API_RELOAD", True)
ALLOWED_ORIGINS = _get_list("STUDYBOT_ALLOWED_ORIGINS", [
    "http://localhost:5173",
    "http://localhost:3000",
])
ANALYTICS_API_PREFIX = "/analytics"


# ==========================================================
# DATA
# ==========================================================

NOTES_DIRECTORY = os.getenv("STUDYBOT_NOTES_DIRECTORY", "sample_notes")


# ==========================================================
# RAG CONFIGURATION
# ==========================================================

RAG_RETRIEVAL_LIMIT = 5


# ==========================================================
# TUTOR CONFIGURATION
# ==========================================================

TUTOR_RETRIEVAL_LIMIT = 5


# ==========================================================
# CACHE CONFIGURATION
# ==========================================================

FACTS_CACHE_FILE = "facts_cache.json"


# ==========================================================
# GROUNDING CONFIGURATION
# ==========================================================

MIN_FACT_SCORE = 5
MAX_SUPPORTING_FACT_LENGTH = 220
MIN_SUPPORTING_FACT_WORDS = 4
MAX_SUPPORTING_FACT_WORDS = 24

# ==========================================================
# QUIZ
# ==========================================================

DEFAULT_QUESTION_COUNT = 10

MIN_POOL_SIZE = 5

MAX_FACTS_PER_NOTE = 10

MAX_NOTES_FOR_CONTEXT = 3

MAX_GENERATION_RETRIES = 3


# ==========================================================
# LLM CONFIGURATION
# ==========================================================

LLM_MODEL = os.getenv("STUDYBOT_LLM_MODEL", "qwen2.5:3b")
LLM_DEFAULT_TIMEOUT = int(os.getenv("STUDYBOT_LLM_DEFAULT_TIMEOUT", "30"))
LLM_TEMPERATURE = float(os.getenv("STUDYBOT_LLM_TEMPERATURE", "0.3"))
LLM_TOP_P = 0.7
LLM_NUM_PREDICT = 800


# ==========================================================
# VALIDATION
# ==========================================================

MIN_QUALITY_SCORE = 0.50


# ==========================================================
# QUIZ SCORING CONFIGURATION
# ==========================================================

DEFAULT_MIN_SCORE = 0.6
IDEAL_OVERLAP_MIN = 0.1
IDEAL_OVERLAP_MAX = 0.4
MAX_QUESTION_LENGTH = 250
MAX_EXPLANATION_LENGTH = 200
MAX_EXPLANATION_WORDS = 30


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DEFAULT_DB_PATH = os.getenv("STUDYBOT_DB_PATH", "analytics.db")


# ==========================================================
# GENERATION
# ==========================================================

MAX_FACTS_PER_REQUEST = 30
SIMILARITY_THRESHOLD = 0.90
RETRIEVAL_LIMIT = 20
FACT_MULTIPLIER = 3
FILL_BLANK_FACT_LIMIT = 5
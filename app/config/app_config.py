"""
Application Configuration.

Central location for global application settings.

Only application-wide settings belong here:
- FastAPI
- Server
- CORS
- Paths
- Debug

Do NOT place quiz, LLM, cache, or validation settings here.
"""

# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = "AI Study Companion"

DEBUG = True

RELOAD = True


# ==========================================================
# SERVER
# ==========================================================

HOST = "127.0.0.1"

PORT = 8000


# ==========================================================
# CORS
# ==========================================================

ALLOWED_ORIGINS = [
    "http://localhost:5173",
]


# ==========================================================
# DATA
# ==========================================================

NOTES_DIRECTORY = "sample_notes"

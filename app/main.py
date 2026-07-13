"""
AI Study Companion - Main Application Entry Point.

This module sets up the FastAPI application and mounts routes.
Business logic is delegated to services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .rag.metadata_loader import MetadataLoader
from .api.routes import setup_routes


# Create FastAPI app
app = FastAPI(title="AI Study Companion")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load metadata
metadata_loader = MetadataLoader("sample_notes")
metadata = metadata_loader.load_metadata()


# Setup routes
router = setup_routes(metadata_loader, metadata)
app.include_router(router)


# Direct execution support
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
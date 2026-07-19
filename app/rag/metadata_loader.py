"""
Metadata Loader Module - Clean metadata indexing service for Obsidian vaults.

This module is responsible ONLY for:
- Indexing markdown files in a vault
- Loading and caching metadata
- Providing efficient note content retrieval

It does NOT handle:
- Fact extraction
- Quiz generation
- Embeddings or retrieval
- Grounding or validation

The module is designed to be production-ready and extensible for large vaults.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Default paths
DEFAULT_NOTES_PATH = "sample_notes"
METADATA_FILENAME = "metadata.json"
FILE_INDEX_FILENAME = ".file_index.json"

# File reading limits
FRONTMATTER_READ_SIZE = 2000  # Read enough for frontmatter + title
DEFAULT_TRUNCATE_CHARS = 2000
MIN_CONTENT_FOR_TRUNCATE = 100

# File types
MARKDOWN_EXTENSIONS = {".md", ".markdown"}

# Frontmatter markers
FRONTMATTER_START = "---"
FRONTMATTER_END = "---"


# ============================================================================
# EXCEPTIONS
# ============================================================================


class MetadataLoaderError(Exception):
    """Base exception for metadata loader errors."""

    pass


class CacheLoadError(MetadataLoaderError):
    """Raised when cache cannot be loaded."""

    pass


class CacheSaveError(MetadataLoaderError):
    """Raised when cache cannot be saved."""

    pass


# ============================================================================
# MAIN CLASS
# ============================================================================


class MetadataLoader:
    """
    Metadata indexing service for Obsidian vaults.

    This class manages metadata for markdown files in a vault,
    providing efficient access to note metadata and content.

    Features:
    - Lazy loading of full note contents
    - In-memory note caching
    - File modification detection for cache invalidation
    - Topic and subtopic organization

    Usage:
        loader = MetadataLoader("sample_notes")
        metadata = loader.load_metadata()
        content = loader.get_note_content("path/to/note.md")
        notes = loader.get_notes_by_topic("Cloud")
    """

    def __init__(self, notes_path: str = DEFAULT_NOTES_PATH):
        """
        Initialize the metadata loader.

        Args:
            notes_path: Path to the notes vault directory
        """
        self.notes_path = Path(notes_path)
        self.metadata_file = self.notes_path / METADATA_FILENAME
        self.file_index_file = self.notes_path / FILE_INDEX_FILENAME
        self.metadata: List[Dict[str, Any]] = []
        self.notes_cache: Dict[str, str] = {}
        self.file_index: Dict[str, str] = {}  # path -> hash

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def load_metadata(self, force_rebuild: bool = False) -> List[Dict[str, Any]]:
        """
        Load metadata from cache or rebuild from scratch.

        Args:
            force_rebuild: If True, rebuild metadata even if cache exists

        Returns:
            List of metadata dictionaries

        Raises:
            CacheLoadError: If cache loading fails and rebuilding fails
        """
        if not force_rebuild and self._try_load_cached_metadata():
            return self.metadata

        logger.info("Building metadata index...")
        self.metadata = self._build_metadata_index()

        if self.metadata:
            self._save_metadata_cache()

        return self.metadata

    def get_note_content(self, note_path: str) -> str:
        """
        Load full content for a single note.

        Args:
            note_path: Path to the note file

        Returns:
            Note content with frontmatter removed
        """
        if note_path in self.notes_cache:
            return self.notes_cache[note_path]

        try:
            content = self._read_note_content(note_path)
            self.notes_cache[note_path] = content
            return content
        except Exception as e:
            logger.error(f"Could not load note {note_path}: {e}")
            return ""

    def get_truncated_content(
        self, note_path: str, max_chars: int = DEFAULT_TRUNCATE_CHARS
    ) -> str:
        """
        Get content truncated at a sentence boundary.

        Args:
            note_path: Path to the note file
            max_chars: Maximum characters to return

        Returns:
            Truncated content, cut at a sentence boundary if possible
        """
        content = self.get_note_content(note_path)

        if len(content) <= max_chars:
            return content

        # Truncate at max_chars
        truncated = content[:max_chars]

        # Find sentence boundary
        sentence_endings = [". ", "? ", "! ", ".\n", "?\n", "!\n"]
        last_end = -1

        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_end:
                last_end = pos

        if last_end > 0:
            return truncated[: last_end + 1]

        # No sentence boundary found, cut at space near limit
        if max_chars > MIN_CONTENT_FOR_TRUNCATE:
            last_space = truncated.rfind(" ")
            if last_space > max_chars - 50:
                return truncated[:last_space] + "..."

        return truncated + "..."

    def get_notes_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get metadata for notes in a topic.

        Args:
            topic: The topic name (case-insensitive)

        Returns:
            List of metadata dictionaries for the topic
        """
        if not self.metadata:
            self.load_metadata()
        return [n for n in self.metadata if n["topic"].lower() == topic.lower()]

    def get_subtopics_by_topic(self, topic: str) -> List[str]:
        """
        Get all subtopics for a given topic.

        Args:
            topic: The topic name (case-insensitive)

        Returns:
            Sorted list of unique subtopics
        """
        if not self.metadata:
            self.load_metadata()

        subtopics = set()
        for note in self.metadata:
            if note["topic"].lower() == topic.lower():
                subtopic = note.get("subtopic", "")
                if subtopic:
                    subtopics.add(subtopic)

        return sorted(subtopics)

    def get_notes_by_subtopic(self, topic: str, subtopic: str) -> List[Dict[str, Any]]:
        """
        Get metadata for notes in a specific subtopic.

        Args:
            topic: The topic name (case-insensitive)
            subtopic: The subtopic name (case-insensitive)

        Returns:
            List of metadata dictionaries for the subtopic
        """
        if not self.metadata:
            self.load_metadata()

        return [
            n
            for n in self.metadata
            if n["topic"].lower() == topic.lower()
            and n.get("subtopic", "").lower() == subtopic.lower()
        ]

    def get_all_topics(self) -> List[str]:
        """
        Get all unique topics.

        Returns:
            Sorted list of all topics
        """
        if not self.metadata:
            self.load_metadata()

        topics = set()
        for note in self.metadata:
            topics.add(note["topic"])

        return sorted(topics)

    def get_topic_summary(self) -> Dict[str, int]:
        """
        Get a summary of topics and note counts.

        Returns:
            Dictionary mapping topic names to note counts
        """
        if not self.metadata:
            self.load_metadata()

        summary = {}
        for note in self.metadata:
            topic = note["topic"]
            summary[topic] = summary.get(topic, 0) + 1

        return summary

    def clear_cache(self) -> None:
        """Clear the in-memory note content cache."""
        self.notes_cache.clear()

    def clear_metadata_cache(self) -> None:
        """Clear both metadata and file index cache files."""
        try:
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                logger.info(f"Removed metadata cache: {self.metadata_file}")
            if self.file_index_file.exists():
                self.file_index_file.unlink()
                logger.info(f"Removed file index cache: {self.file_index_file}")
            self.metadata = []
            self.file_index = {}
            self.notes_cache.clear()
        except Exception as e:
            logger.error(f"Could not clear cache: {e}")

    # =========================================================================
    # PRIVATE HELPERS - CACHE MANAGEMENT
    # =========================================================================

    def _try_load_cached_metadata(self) -> bool:
        """
        Try to load metadata from cache.

        Returns:
            True if cache was loaded successfully, False otherwise
        """
        # Check if cache files exist
        if not self.metadata_file.exists():
            return False

        # Check if we need to rebuild due to file changes
        if self._needs_rebuild():
            logger.info("Files changed since last cache, rebuilding...")
            return False

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded {len(self.metadata)} notes from cache")
            return True
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupt metadata cache: {e}")
            return False
        except Exception as e:
            logger.warning(f"Could not load metadata cache: {e}")
            return False

    def _needs_rebuild(self) -> bool:
        """
        Check if metadata cache needs to be rebuilt.

        Uses file modification times and content hashes to detect changes.

        Returns:
            True if cache should be rebuilt, False otherwise
        """
        if not self.metadata_file.exists():
            return True

        # Load file index if it exists
        if not self.file_index_file.exists():
            return True

        try:
            with open(self.file_index_file, "r", encoding="utf-8") as f:
                self.file_index = json.load(f)
        except Exception:
            return True

        # Check each markdown file
        md_files = self._find_markdown_files()

        # If number of files changed
        if len(md_files) != len(self.file_index):
            return True

        # Check each file's hash
        for md_file in md_files:
            current_hash = self._compute_file_hash(md_file)
            cached_hash = self.file_index.get(str(md_file))

            if current_hash != cached_hash:
                return True

        return False

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute a hash of the file for change detection.

        Args:
            file_path: Path to the file

        Returns:
            MD5 hash of the file content
        """
        try:
            with open(file_path, "rb") as f:
                content = f.read(8192)  # Read first 8KB
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _save_metadata_cache(self) -> None:
        """Save metadata cache to disk."""
        if not self.metadata:
            return

        try:
            # Save metadata
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)

            # Save file index
            with open(self.file_index_file, "w", encoding="utf-8") as f:
                json.dump(self.file_index, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved metadata cache with {len(self.metadata)} notes")
        except Exception as e:
            logger.error(f"Could not save metadata cache: {e}")

    # =========================================================================
    # PRIVATE HELPERS - INDEXING
    # =========================================================================

    def _build_metadata_index(self) -> List[Dict[str, Any]]:
        """
        Build metadata index from scratch.

        Returns:
            List of metadata dictionaries
        """
        metadata = []
        self.file_index = {}

        md_files = self._find_markdown_files()

        for md_file in md_files:
            try:
                file_path = str(md_file)
                self.file_index[file_path] = self._compute_file_hash(md_file)

                meta = self._extract_metadata(md_file)
                if meta:
                    metadata.append(meta)

            except Exception as e:
                logger.warning(f"Could not load {md_file.name}: {e}")
                continue

        return metadata

    def _find_markdown_files(self) -> List[Path]:
        """
        Find all markdown files in the notes path.

        Returns:
            List of Path objects for markdown files
        """
        md_files = []
        for ext in MARKDOWN_EXTENSIONS:
            md_files.extend(self.notes_path.glob(f"**/*{ext}"))
        return md_files

    def _extract_metadata(self, md_file: Path) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a markdown file.

        Args:
            md_file: Path to the markdown file

        Returns:
            Metadata dictionary, or None if extraction fails
        """
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                # Read enough for frontmatter + title
                content = f.read(FRONTMATTER_READ_SIZE)

            # Parse frontmatter
            frontmatter = self._parse_frontmatter(content)

            # Get topic from frontmatter or parent directory
            topic = frontmatter.get("topic", md_file.parent.name)

            # Get subtopic from frontmatter
            subtopic = frontmatter.get("subtopic", "")

            # Get content length without loading full file
            full_content = self._read_note_content(str(md_file))
            content_length = len(full_content) if full_content else 0

            return {
                "path": str(md_file),
                "topic": topic,
                "subtopic": subtopic,
                "title": md_file.stem,
                "content_length": content_length,
                "metadata": frontmatter,
            }

        except Exception as e:
            logger.debug(f"Could not extract metadata from {md_file.name}: {e}")
            return None

    # =========================================================================
    # PRIVATE HELPERS - FRONTMATTER PARSING
    # =========================================================================

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Parse frontmatter from markdown content.

        Args:
            content: Markdown content with possible frontmatter

        Returns:
            Dictionary of frontmatter values
        """
        # Remove BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        if not content.startswith(FRONTMATTER_START):
            return {}

        parts = content.split(FRONTMATTER_START, 2)
        if len(parts) < 3:
            return {}

        frontmatter_text = parts[1]
        frontmatter = {}

        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Parse list values
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip() for v in value[1:-1].split(",")]

                frontmatter[key] = value

        return frontmatter

    # =========================================================================
    # PRIVATE HELPERS - FILE READING
    # =========================================================================

    def _read_note_content(self, note_path: str) -> str:
        """
        Read and clean note content.

        Args:
            note_path: Path to the note file

        Returns:
            Note content with frontmatter removed
        """
        path = Path(note_path)
        if not path.exists():
            return ""

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove frontmatter
        if content.startswith(FRONTMATTER_START):
            parts = content.split(FRONTMATTER_START, 2)
            if len(parts) >= 3:
                content = parts[2]

        return content

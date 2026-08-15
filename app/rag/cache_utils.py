import hashlib
from pathlib import Path
from typing import Dict

def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of file content."""
    if not file_path.exists():
        return ""
    return hashlib.md5(file_path.read_bytes()).hexdigest()

def get_all_notes_hashes(notes_path: Path) -> Dict[str, str]:
    """Calculate hashes for all markdown notes."""
    hashes = {}
    for md_file in notes_path.glob("**/*.md"):
        hashes[str(md_file.relative_to(notes_path))] = get_file_hash(md_file)
    return hashes

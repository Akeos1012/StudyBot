import hashlib

def generate_question_id(question_text: str) -> str:
    """Generate a deterministic ID for a question based on its text."""
    return hashlib.md5(question_text.encode("utf-8")).hexdigest()

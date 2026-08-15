import json
import hashlib
import os

def generate_question_id(question_text: str) -> str:
    """Generate a deterministic ID for a question based on its text."""
    return hashlib.md5(question_text.encode("utf-8")).hexdigest()

def repair_cache(cache_file_path):
    if not os.path.exists(cache_file_path):
        print(f"Cache file not found at {cache_file_path}")
        return

    with open(cache_file_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    modified_count = 0
    total_questions = 0
    
    # Assuming structure is something like {topic: {subtopic: {difficulty: {type: [questions]}}}}
    # We need to traverse to the question lists.
    
    def traverse_and_repair(obj):
        nonlocal modified_count, total_questions
        if isinstance(obj, list):
            for q in obj:
                if isinstance(q, dict) and "question" in q:
                    total_questions += 1
                    if "question_id" not in q or not q["question_id"]:
                        q["question_id"] = generate_question_id(q.get("question", ""))
                        modified_count += 1
        elif isinstance(obj, dict):
            for value in obj.values():
                traverse_and_repair(value)

    traverse_and_repair(cache)

    print(f"Total questions scanned: {total_questions}")
    print(f"Questions repaired: {modified_count}")

    if modified_count > 0:
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
        print(f"Successfully repaired {cache_file_path}")
    else:
        print("No repairs needed.")

if __name__ == "__main__":
    # Assuming the cache file is in the root directory
    cache_file = "question_cache.json"
    repair_cache(cache_file)

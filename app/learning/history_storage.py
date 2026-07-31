import json
import os
from typing import Dict, Any, List

class HistoryStorage:
    def __init__(self, storage_path: str = "learning_history.jsonl"):
        self.storage_path = storage_path

    def append_attempt(self, attempt: Dict[str, Any]):
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(attempt) + "\n")

    def get_all_attempts(self) -> List[Dict[str, Any]]:
        attempts = []
        if not os.path.exists(self.storage_path):
            return attempts
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                attempts.append(json.loads(line))
        return attempts

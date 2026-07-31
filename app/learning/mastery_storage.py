import json
import os
from typing import Dict, Any, Optional

class MasteryStorage:
    def __init__(self, storage_path: str = "mastery_data.json"):
        self.storage_path = storage_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w") as f:
                json.dump({"users": {}}, f)

    def load_all(self) -> Dict[str, Any]:
        with open(self.storage_path, "r") as f:
            return json.load(f)

    def save_all(self, data: Dict[str, Any]):
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_user_records(self, user_id: str) -> Dict[str, Any]:
        data = self.load_all()
        return data.get("users", {}).get(user_id, {})

    def save_user_records(self, user_id: str, records: Dict[str, Any]):
        data = self.load_all()
        if "users" not in data:
            data["users"] = {}
        data["users"][user_id] = records
        self.save_all(data)

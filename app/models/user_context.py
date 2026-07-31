from dataclasses import dataclass
from typing import Optional


@dataclass
class UserContext:
    user_id: Optional[str] = None

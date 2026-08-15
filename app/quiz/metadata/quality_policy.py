from enum import Enum
from typing import Dict, List, Set

class ExposureLevel(Enum):
    LOW = 1.0    # No mention or natural context
    MEDIUM = 0.5 # Concept mentioned, but not trivial
    HIGH = 0.0   # Trivial restatement or circular

# Centralized policy for cognitive types
COGNITIVE_VALIDITY_POLICY: Dict[str, Dict[str, List[str]]] = {
    "comparison": {
        "keywords": ["compare", "difference", "versus", "contrast"],
        "min_concepts": 2
    },
    "classification": {
        "keywords": ["type", "category", "classify", "kind of"],
        "min_concepts": 1
    },
    "relationship": {
        "keywords": ["relates", "how does", "interaction", "link"],
        "min_concepts": 1
    },
    "application": {
        "keywords": ["scenario", "use", "apply", "when", "example"],
        "min_concepts": 1
    },
    "error_detection": {
        "keywords": ["incorrect", "error", "what is wrong", "false"],
        "min_concepts": 1
    }
}

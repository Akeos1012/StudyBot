"""
Domain correctness validation.
Checks if generated questions follow basic technical meaning.
"""

from typing import Dict, Any


DOMAIN_RULES = {
    "edge computing": {
        "latency": [
            "reduce",
            "lower",
            "decrease",
            "minimize"
        ],
        "processing": [
            "closer",
            "source",
            "device",
            "sensor"
        ]
    },

    "cloud storage": {
        "data storage": [
            "store",
            "files",
            "remote",
            "internet"
        ]
    },

    "cloud database": {
        "database services": [
            "database",
            "internet",
            "managed"
        ]
    }
}


def validate_domain_correctness(question: Dict[str, Any]) -> bool:
    """
    Reject technically incorrect questions.
    """

    text = (
        question.get("question", "") +
        " " +
        question.get("explanation", "")
    ).lower()


    for domain, rules in DOMAIN_RULES.items():

        if domain in text:

            # check required concept alignment
            for concept, keywords in rules.items():

                if concept in text:

                    if not any(
                        word in text
                        for word in keywords
                    ):
                        print(
                            f"⚠️ Domain mismatch: {concept}"
                        )
                        return False


    return True
"""
Domain correctness validation.
Checks if generated questions follow basic technical meaning.
"""

from typing import Dict, Any

DOMAIN_RULES = {
    "edge computing": {
        "latency": ["reduce", "lower", "decrease", "minimize"],
        "processing": ["closer", "source", "device", "sensor"],
    },
    "cloud storage": {"data storage": ["store", "files", "remote", "internet"]},
    "cloud database": {"database services": ["database", "internet", "managed"]},
}


def validate_domain_correctness(
    question: Dict[str, Any],
    answer: str,
    supporting_fact: str,
) -> bool:
    """
    Reject only clear technical contradictions.
    Do not reject questions simply because they omit
    certain keywords.
    """

    text = " ".join(
        [
            question.get("question", ""),
            answer,
            supporting_fact,
        ]
    ).lower()
    
    for domain, rules in DOMAIN_RULES.items():

        if domain not in text:
            continue

        for keywords in rules.values():

            # At least ONE supporting keyword is enough.
            if any(keyword in text for keyword in keywords):
                return True

            print(f"⚠️ Domain mismatch: {domain}")
            return False

    # If no specific domain rule applies,
    # don't reject the question.
    return True

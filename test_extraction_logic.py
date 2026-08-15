
import re
from pathlib import Path

# Mock classes to run the extraction logic
class ConceptValidator:
    def is_valid(self, concept):
        return True, ""

class SemanticConceptExtractor:
    VERB_STARTS = {"uses", "repeats"}
    ADVERB_STARTS = {"commonly"}
    FILLER_STARTS = {"the"}
    SECTION_LABELS = {"overview"}
    PREDICATE_VERBS = {"is"}
    VALID_ACRONYMS = {"AI"}

    def __init__(self, validator):
        self.concept_validator = validator
        self.ADVERB_STARTS = self.ADVERB_STARTS
        self.VERB_STARTS = self.VERB_STARTS
        self.FILLER_STARTS = self.FILLER_STARTS
        self.SECTION_LABELS = self.SECTION_LABELS
        self.PREDICATE_VERBS = self.PREDICATE_VERBS
        self._valid_acronyms = self.VALID_ACRONYMS

    def _normalize_concept(self, concept):
        return concept.title()

    def _is_canonical_concept(self, concept):
        # Based on the file content
        concept_lower = concept.lower()
        words = concept.split()
        first_word = words[0]
        # This simulates the case-sensitivity bug
        if first_word in self.ADVERB_STARTS:
            return False
        if first_word in self.VERB_STARTS:
            return False
        return True


    def extract(self, text):
        match = re.search(
            r"^([A-Z][a-zA-Z\s]{2,})\s+(uses|repeats)",
            text,
            re.IGNORECASE,
        )
        if match:
            concept = match.group(1).strip()
            print(f"DEBUG: Extracted concept: '{concept}'")
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)
        return None

# Test the sanitization and extraction
def sanitize_text(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*[-*+]\s*", "", cleaned)
    return cleaned

extractor = SemanticConceptExtractor(ConceptValidator())

text1 = "- Commonly uses Deep Learning models"
sanitized1 = sanitize_text(text1)
print(f"Sanitized1: '{sanitized1}'")
concept1 = extractor.extract(sanitized1)
print(f"Concept1: '{concept1}'")

text2 = "- Repeats until model improves"
sanitized2 = sanitize_text(text2)
print(f"Sanitized2: '{sanitized2}'")
concept2 = extractor.extract(sanitized2)
print(f"Concept2: '{concept2}'")

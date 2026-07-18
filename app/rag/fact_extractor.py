import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from .fact_cleaner import clean_fact
import logging

from ..models.fact_schema import (
    create_fact,
    is_weak_concept,
    detect_concept_type,
    ConceptType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ExtractionStats:
    """Tracks extraction statistics for reporting."""

    total_lines: int = 0
    candidate_lines: int = 0
    extracted_facts: int = 0
    skipped_structural: int = 0
    skipped_invalid_concept: int = 0
    skipped_duplicate: int = 0
    skipped_other: int = 0

    def summary(self) -> str:
        return (
            f"Lines: {self.total_lines}, Candidates: {self.candidate_lines}, "
            f"Extracted: {self.extracted_facts}, Skipped structural: {self.skipped_structural}, "
            f"Invalid concepts: {self.skipped_invalid_concept}, Duplicates: {self.skipped_duplicate}"
        )


class RejectionReason(Enum):
    """Reasons for skipping a candidate."""

    EMPTY = "empty"
    TOO_SHORT = "too_short"
    CODE_BLOCK = "code_block"
    MARKER = "invalid_marker"
    STRUCTURAL_HEADING = "structural_heading"
    NO_CONCEPT = "no_concept"
    INVALID_CONCEPT = "invalid_concept"
    DUPLICATE = "duplicate"
    CREATION_ERROR = "creation_error"


@dataclass
class RejectionInfo:
    """Information about why a candidate was rejected."""

    reason: RejectionReason
    detail: str = ""
    line: str = ""


# =============================================================================
# HEADING FILTER
# =============================================================================


class HeadingFilter:
    """
    Detects structural headings using document heuristics.
    """

    ORGANIZATIONAL_SUFFIXES = {
        "overview",
        "summary",
        "introduction",
        "conclusion",
        "advantages",
        "disadvantages",
        "applications",
        "examples",
        "notes",
        "references",
        "further reading",
        "analysis",
        "level",
        "requirements",
        "features",
        "workflow",
        "implementation",
        "discussion",
        "classification",
        "categories",
        "types",
        "architecture",
    }

    CONCEPT_PREDICATES = {
        "is",
        "are",
        "refers to",
        "means",
        "stands for",
        "allows",
        "enables",
        "provides",
        "stores",
        "manages",
        "reduces",
        "improves",
        "uses",
        "supports",
        "offers",
        "helps",
        "contains",
        "includes",
    }

    def __init__(self):
        self._section_depth = 0
        self._heading_stack: List[str] = []

    def reset(self):
        self._section_depth = 0
        self._heading_stack = []

    def is_structural(self, line: str, context: str = "") -> Tuple[bool, str]:
        if not line:
            return False, ""

        stripped = line.strip()
        if not stripped.startswith("#"):
            return False, ""

        heading = re.sub(r"^#+\s*", "", stripped).strip()
        if not heading:
            return False, ""

        heading_lower = heading.lower()

        for pred in HeadingFilter.CONCEPT_PREDICATES:
            if pred in heading_lower:
                return False, ""

        words = heading_lower.split()
        if words:
            last_word = words[-1].rstrip(".,;:")
            if last_word in HeadingFilter.ORGANIZATIONAL_SUFFIXES:
                return True, f"organizational_suffix: {last_word}"

        if len(words) <= 4 and not any(
            p in heading_lower for p in HeadingFilter.CONCEPT_PREDICATES
        ):
            return True, "title_only_heading"

        structural_markers = {
            "overview",
            "summary",
            "introduction",
            "conclusion",
            "analysis",
        }
        for marker in structural_markers:
            if marker in heading_lower:
                return True, f"structural_marker: {marker}"

        return False, ""


# =============================================================================
# SEMANTIC CONCEPT EXTRACTOR
# =============================================================================


class SemanticConceptExtractor:
    """
    Extracts concepts using strict semantic validation.

    A concept MUST be:
    - A noun or noun phrase
    - Names a thing, system, algorithm, protocol, hardware component,
      data structure, language, model, metric, process, architecture, or technology
    - Could realistically be the answer to a quiz question

    If uncertain, reject the concept.
    Precision > Recall
    """

    # Words that indicate a concept is actually a verb phrase
    VERB_STARTS = {
        "allows",
        "enabling",
        "enables",
        "provides",
        "providing",
        "stores",
        "storing",
        "manages",
        "managing",
        "reduces",
        "reducing",
        "improves",
        "improving",
        "uses",
        "using",
        "supports",
        "supporting",
        "offers",
        "offering",
        "helps",
        "helping",
        "contains",
        "containing",
        "includes",
        "including",
        "focuses",
        "focusing",
        "creates",
        "creating",
        "runs",
        "running",
        "processes",
        "processing",
        "handles",
        "handling",
        "generates",
        "generating",
        "builds",
        "building",
        "works",
        "working",
        "makes",
        "making",
        "takes",
        "taking",
        "gives",
        "giving",
        "shows",
        "showing",
        "does",
        "doing",
        "performs",
        "performing",
        "executes",
        "executing",
    }

    # Filler words that should never start a concept
    FILLER_STARTS = {
        "the",
        "this",
        "these",
        "those",
        "where",
        "when",
        "why",
        "how",
        "using",
        "used",
        "because",
        "since",
        "during",
        "after",
        "before",
        "through",
        "without",
        "with",
        "for",
        "from",
        "into",
        "onto",
        "upon",
        "via",
        "between",
        "among",
        "within",
        "outside",
    }

    # Section labels that are not concepts (unless overridden)
    SECTION_LABELS = {
        "overview",
        "summary",
        "introduction",
        "conclusion",
        "applications",
        "advantages",
        "disadvantages",
        "examples",
        "notes",
        "references",
        "architecture",
        "workflow",
        "implementation",
        "discussion",
        "analysis",
        "level",
        "foundation",
        "foundations",
        "requirements",
        "features",
        "classification",
        "categories",
        "types",
        "architecture",
    }

    # Words that indicate a grammatical predicate (concept contains a verb)
    PREDICATE_VERBS = {
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "has",
        "have",
        "had",
        "does",
        "do",
        "did",
        "will",
        "would",
        "could",
        "should",
        "might",
        "can",
        "may",
        "must",
        "shall",
    }

    # Common acronyms that are valid single-word concepts
    VALID_ACRONYMS = {
        "CPU",
        "GPU",
        "RAM",
        "ROM",
        "BIOS",
        "USB",
        "HDMI",
        "PCI",
        "SSD",
        "HDD",
        "LAN",
        "WAN",
        "VPN",
        "DNS",
        "DHCP",
        "TCP",
        "UDP",
        "IP",
        "HTTP",
        "HTTPS",
        "FTP",
        "SSH",
        "SMTP",
        "POP3",
        "IMAP",
        "API",
        "SQL",
        "DBMS",
        "IoT",
        "ML",
        "AI",
        "NLP",
        "CNN",
        "RNN",
        "GPT",
        "BERT",
        "OOP",
        "ACID",
        "JSON",
        "XML",
        "HTML",
        "CSS",
        "JS",
        "PHP",
        "C++",
        "C#",
        "REST",
        "SOAP",
    }

    def __init__(self, concept_validator):
        self.concept_validator = concept_validator
        self._concept_type_overrides = concept_validator.concept_type_overrides
        self._valid_acronyms = self.VALID_ACRONYMS

    def extract(self, text: str) -> Optional[str]:
        """Extract a concept from text using strict semantic rules."""
        if not text:
            return None

        text = text.strip()

        # Pattern 1: "X is Y" - subject is X (strongest signal)
        match = re.search(
            r"^([A-Z][a-zA-Z\s]{2,})\s+(is|are|refers to|means|stands for)",
            text,
            re.IGNORECASE,
        )
        if match:
            concept = match.group(1).strip()
            concept = " ".join(concept.split()[:4])
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)

        # Pattern 2: "X allows/stores..." - subject is X
        match = re.search(
            r"^([A-Z][a-zA-Z\s]{2,})\s+(allows|enables|provides|stores|manages|"
            r"reduces|improves|uses|supports|offers|helps|contains|includes)",
            text,
            re.IGNORECASE,
        )
        if match:
            concept = match.group(1).strip()
            concept = " ".join(concept.split()[:4])
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)

        # Pattern 3: "called X" or "known as X"
        match = re.search(
            r"(?:called|known as|termed)\s+([A-Z][a-zA-Z\s]{2,})(?:\.|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            concept = match.group(1).strip()
            concept = " ".join(concept.split()[:4])
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)

        # Pattern 4: "X - Y" or "X — Y" (subject is X)
        match = re.search(r"^([A-Z][a-zA-Z\s]{2,})\s*[—\-]\s+", text)
        if match:
            concept = match.group(1).strip()
            concept = " ".join(concept.split()[:4])
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)

        # Pattern 5: "X (Y)" - X is the concept, Y is the acronym
        match = re.search(r"^([A-Z][a-zA-Z\s]{2,})\s*\(([A-Z]{2,})\)", text)
        if match:
            concept = match.group(1).strip()
            concept = " ".join(concept.split()[:4])
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)

        # Pattern 6: "X:" - X is the concept
        match = re.search(r"^([A-Z][a-zA-Z\s]{2,})\s*:", text)
        if match:
            concept = match.group(1).strip()
            concept = " ".join(concept.split()[:4])
            if self._is_canonical_concept(concept):
                return self._normalize_concept(concept)

        return None

    def _is_canonical_concept(self, concept: str) -> bool:
        """
        Determine if a concept is a canonical noun phrase suitable for quiz questions.

        Returns True only if ALL of:
        - Is a noun or noun phrase
        - Names a thing, system, algorithm, protocol, hardware component,
          data structure, language, model, metric, process, architecture, or technology
        - Could realistically be the answer to a quiz question
        """
        if not concept:
            return False

        # Validate against schema first
        is_valid, _ = self.concept_validator.is_valid(concept)
        if not is_valid:
            return False

        concept_lower = concept.lower()
        words = concept_lower.split()

        if not words:
            return False

        first_word = words[0]
        last_word = words[-1]
        concept_clean = concept_lower.replace("_", " ").replace("-", " ")

        # 1. REJECT filler starts
        if first_word in self.FILLER_STARTS:
            logger.debug(f"Rejected '{concept}': starts with filler '{first_word}'")
            return False

        # 2. REJECT verb starts
        if first_word in self.VERB_STARTS:
            logger.debug(f"Rejected '{concept}': starts with verb '{first_word}'")
            return False

        # 3. REJECT grammatical predicates (contains verbs)
        for verb in self.PREDICATE_VERBS:
            # Check if the verb appears as a whole word in the concept
            if re.search(r"\b" + verb + r"\b", concept_lower):
                logger.debug(f"Rejected '{concept}': contains predicate verb '{verb}'")
                return False

        # 4. REJECT section labels at end (unless overridden)
        if last_word in self.SECTION_LABELS:
            # Allow if the concept is in overrides (e.g., "Architecture" as a concept)
            if concept in self._concept_type_overrides:
                return True
            # Allow single-word section labels (e.g., "Architecture" can be a concept)
            if len(words) == 1:
                return True
            logger.debug(f"Rejected '{concept}': ends with section label '{last_word}'")
            return False

        # 5. Check for section labels in the middle
        for word in words:
            if word in self.SECTION_LABELS and len(words) > 1:
                if concept not in self._concept_type_overrides:
                    logger.debug(
                        f"Rejected '{concept}': contains section label '{word}'"
                    )
                    return False

        # 6. REJECT verb phrase patterns (e.g., "Focuses On How", "Improves Time")
        verb_phrase_patterns = [
            r"^focuses\s+on\s+",
            r"^focusing\s+on\s+",
            r"^improves\s+",
            r"^improving\s+",
            r"^allows\s+the\s+",
            r"^provides\s+",
            r"^providing\s+",
            r"^supports\s+",
            r"^supporting\s+",
            r"^enables\s+",
            r"^enabling\s+",
            r"^uses\s+",
            r"^using\s+",
            r"^contains\s+",
            r"^containing\s+",
            r"^includes\s+",
            r"^including\s+",
            r"^manages\s+",
            r"^managing\s+",
            r"^reduces\s+",
            r"^reducing\s+",
            r"^creates\s+",
            r"^creating\s+",
            r"^processes\s+",
            r"^processing\s+",
            r"^handles\s+",
            r"^handling\s+",
            r"^generates\s+",
            r"^generating\s+",
            r"^runs\s+",
            r"^running\s+",
        ]
        for pattern in verb_phrase_patterns:
            if re.match(pattern, concept_lower):
                logger.debug(f"Rejected '{concept}': matches verb phrase pattern")
                return False

        # 7. REJECT question-word starts
        if first_word in {
            "where",
            "when",
            "why",
            "how",
            "what",
            "which",
            "who",
            "whom",
        }:
            logger.debug(
                f"Rejected '{concept}': starts with question word '{first_word}'"
            )
            return False

        # 8. REJECT phrases with "The" at start
        if concept_lower.startswith("the "):
            logger.debug(f"Rejected '{concept}': starts with 'The'")
            return False

        # 9. REJECT concepts that are clearly sentences or fragments
        # Check for ending punctuation
        if concept.endswith(".") or concept.endswith("!") or concept.endswith("?"):
            return False

        # Check for multiple sentences (periods inside)
        if concept.count(".") > 1:
            return False

        # 10. REJECT concepts that are too vague
        vague_terms = {
            "system",
            "process",
            "method",
            "approach",
            "technique",
            "mechanism",
            "framework",
        }
        if len(words) == 1:
            if first_word in vague_terms:
                logger.debug(f"Rejected '{concept}': too vague")
                return False

        # 11. Check for lowercase words in the middle (should be all capitalized for multi-word)
        if len(words) >= 2:
            for w in words:
                # Allow acronyms
                if w.upper() in self._valid_acronyms:
                    continue
                # Check if the word is capitalized or is a common word like "and", "of", "for"
                if not w[0].isupper() and w not in {
                    "and",
                    "of",
                    "for",
                    "in",
                    "on",
                    "at",
                    "to",
                    "by",
                    "with",
                    "without",
                }:
                    # It might still be valid if it's a proper noun phrase
                    pass

        return True

    def _normalize_concept(self, concept: str) -> str:
        """Normalize concept text."""
        concept = concept.strip()

        # Remove leading articles
        concept = re.sub(
            r"^(a|an|the)\s+",
            "",
            concept,
            flags=re.IGNORECASE,
        )

        concept = re.sub(r"\s+", " ", concept)
        concept = concept.title()

        # Fix acronyms
        acronyms = {
            "Ai": "AI",
            "Cpu": "CPU",
            "Gpu": "GPU",
            "Sql": "SQL",
            "Api": "API",
            "Dbms": "DBMS",
            "Iot": "IoT",
            "Ml": "ML",
            "Nlp": "NLP",
            "Os": "OS",
            "Ram": "RAM",
            "Rom": "ROM",
            "Bios": "BIOS",
            "Usb": "USB",
            "Hdmi": "HDMI",
            "Pci": "PCI",
            "Ssd": "SSD",
            "Hdd": "HDD",
            "Lan": "LAN",
            "Wan": "WAN",
            "Vpn": "VPN",
            "Dns": "DNS",
            "Dhcp": "DHCP",
            "Tcp": "TCP",
            "Udp": "UDP",
            "Ip": "IP",
            "Http": "HTTP",
            "Https": "HTTPS",
            "Ftp": "FTP",
            "Ssh": "SSH",
            "Smtp": "SMTP",
            "Pop3": "POP3",
            "Imap": "IMAP",
        }
        for k, v in acronyms.items():
            concept = concept.replace(k, v)
        concept = concept.replace("Ai Model", "AI Model")
        concept = concept.replace("Ai", "AI")

        return concept

    def extract_from_filename(self, source: str) -> Optional[str]:
        """Extract concept from filename (FINAL fallback only)."""
        if not source:
            return None

        source_path = Path(str(source))
        filename = source_path.stem

        if not filename or filename == "inline":
            return None

        concept = filename.strip()
        concept = re.sub(r"[-_\.]", " ", concept)
        concept = re.sub(r"\s+", " ", concept).strip()
        concept = " ".join(concept.split()[:4])
        concept = self._normalize_concept(concept)

        if self._is_canonical_concept(concept):
            return concept

        return None


# =============================================================================
# CONCEPT VALIDATOR
# =============================================================================


class ConceptValidator:
    """
    Validates concepts against schema rules.
    """

    def __init__(self):
        self.concept_type_overrides = {
            "Quick Sort": "algorithm",
            "Merge Sort": "algorithm",
            "Bubble Sort": "algorithm",
            "Binary Search": "algorithm",
            "Dynamic Programming": "algorithm",
            "Greedy": "algorithm",
            "Divide and Conquer": "algorithm",
            "Recursion": "algorithm",
            "Deep Learning": "model",
            "Neural Network": "model",
            "CNN": "model",
            "RNN": "model",
            "Transformer": "model",
            "Time Complexity": "metric",
            "Space Complexity": "metric",
            "Big O": "metric",
            "Array": "data_structure",
            "Linked List": "data_structure",
            "Stack": "data_structure",
            "Queue": "data_structure",
            "Tree": "data_structure",
            "Graph": "data_structure",
            "DBMS": "system",
            "Operating System": "system",
            "File System": "system",
            "Normalization": "process",
            "Backpropagation": "process",
            "Gradient Descent": "process",
        }

        self.weak_single_words = {
            "concept",
            "example",
            "method",
            "approach",
            "technique",
            "process",
            "system",
            "layer",
            "type",
            "category",
            "classification",
            "service",
            "platform",
            "solution",
            "resource",
            "component",
            "module",
            "architecture",
        }

    def is_valid(self, concept: str) -> Tuple[bool, str]:
        """Validate a concept."""
        if not concept or len(concept) < 2:
            return False, "empty_or_too_short"

        words = concept.split()

        if len(words) > 4:
            return False, "too_many_words"

        if len(words) == 1:
            if not concept[0].isupper():
                return False, "single_word_not_capitalized"
            if concept.lower() in self.weak_single_words:
                return False, "single_word_weak"
            if len(concept) < 3:
                return False, "single_word_too_short"
            return True, ""

        if not concept[0].isupper():
            return False, "not_capitalized"

        return True, ""


# =============================================================================
# FACT EXTRACTOR
# =============================================================================


class FactExtractor:
    def __init__(self, notes_path="sample_notes"):
        self.notes_path = Path(notes_path)

        # Acronym mapping
        self.acronyms = {
            "Ai": "AI",
            "Cpu": "CPU",
            "Gpu": "GPU",
            "Sql": "SQL",
            "Api": "API",
            "Dbms": "DBMS",
            "Iot": "IoT",
            "Ml": "ML",
            "Nlp": "NLP",
            "Os": "OS",
            "Ram": "RAM",
            "Rom": "ROM",
            "Bios": "BIOS",
            "Usb": "USB",
            "Hdmi": "HDMI",
            "Pci": "PCI",
            "Ssd": "SSD",
            "Hdd": "HDD",
            "Lan": "LAN",
            "Wan": "WAN",
            "Vpn": "VPN",
            "Dns": "DNS",
            "Dhcp": "DHCP",
            "Tcp": "TCP",
            "Udp": "UDP",
            "Ip": "IP",
            "Http": "HTTP",
            "Https": "HTTPS",
            "Ftp": "FTP",
            "Ssh": "SSH",
            "Smtp": "SMTP",
            "Pop3": "POP3",
            "Imap": "IMAP",
        }

        # Concept type overrides
        self.concept_type_overrides = {
            "Quick Sort": "algorithm",
            "Merge Sort": "algorithm",
            "Bubble Sort": "algorithm",
            "Binary Search": "algorithm",
            "Dynamic Programming": "algorithm",
            "Greedy": "algorithm",
            "Divide and Conquer": "algorithm",
            "Recursion": "algorithm",
            "Deep Learning": "model",
            "Neural Network": "model",
            "CNN": "model",
            "RNN": "model",
            "Transformer": "model",
            "Time Complexity": "metric",
            "Space Complexity": "metric",
            "Big O": "metric",
            "Array": "data_structure",
            "Linked List": "data_structure",
            "Stack": "data_structure",
            "Queue": "data_structure",
            "Tree": "data_structure",
            "Graph": "data_structure",
            "DBMS": "system",
            "Operating System": "system",
            "File System": "system",
            "Normalization": "process",
            "Backpropagation": "process",
            "Gradient Descent": "process",
        }

        # Initialize components
        self.heading_filter = HeadingFilter()
        self.concept_validator = ConceptValidator()
        self.semantic_extractor = SemanticConceptExtractor(self.concept_validator)

    # ========== CORE UTILITIES ==========

    def normalize_concept(self, text: str) -> str:
        """Normalize concept text: title case, fix acronyms."""
        return self.semantic_extractor._normalize_concept(text)

    def _sanitize_text(self, text: str) -> str:
        """Clean text for extraction."""
        if not text:
            return ""
        cleaned = text.strip()
        cleaned = re.sub(r"^\s*#+\s*", "", cleaned)
        cleaned = re.sub(r"^\s*[-*+]\s*", "", cleaned)
        cleaned = re.sub(r"^\s*\d+\.\s*", "", cleaned)
        cleaned = re.sub(r"\[\[(.*?)\]\]", r"\1", cleaned)
        cleaned = re.sub(r"[*_`>#]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.rstrip(" .")

    def _slugify(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(text or "").lower()).strip("_")

    # ========== CONCEPT EXTRACTION ==========

    def _extract_concept_from_text(self, text: str) -> Optional[str]:
        """Extract concept from text content."""
        return self.semantic_extractor.extract(text)

    def _extract_concept_from_filename(self, source: str) -> Optional[str]:
        """Extract concept from filename (FINAL fallback)."""
        return self.semantic_extractor.extract_from_filename(source)

    # ========== FACT BUILDING ==========

    def _build_atomic_fact(
        self, text: str, topic: str, source: str, weight: int = 7
    ) -> Tuple[Optional[Dict[str, Any]], Optional[RejectionInfo]]:
        """Build a single atomic fact from a line of text."""
        cleaned = self._sanitize_text(text)

        if not cleaned:
            return None, RejectionInfo(RejectionReason.EMPTY, "empty_line", text)

        if len(cleaned.split()) < 4:
            return None, RejectionInfo(
                RejectionReason.TOO_SHORT, "less_than_4_words", text
            )

        if any(
            marker in cleaned.lower() for marker in ["#", "[[", "]]", "---", "http"]
        ):
            return None, RejectionInfo(RejectionReason.MARKER, "invalid_marker", text)

        is_structural, reason = self.heading_filter.is_structural(text, cleaned)
        if is_structural:
            return None, RejectionInfo(RejectionReason.STRUCTURAL_HEADING, reason, text)

        concept = self._extract_concept_from_text(cleaned)

        # Filename is the FINAL fallback only
        if not concept:
            concept = self._extract_concept_from_filename(source)

        if not concept:
            return None, RejectionInfo(
                RejectionReason.NO_CONCEPT, "no_concept_extracted", text
            )

        is_valid, reason = self.concept_validator.is_valid(concept)
        if not is_valid:
            return None, RejectionInfo(RejectionReason.INVALID_CONCEPT, reason, text)

        concept = " ".join(concept.split()[:4])

        try:
            concept_type = self.concept_type_overrides.get(
                concept, detect_concept_type(concept, cleaned)
            )
            source_note = (
                Path(str(source)).name
                if str(source) and str(source) != "inline"
                else "inline"
            )

            fact = create_fact(
                concept=concept,
                definition=cleaned,
                topic=topic,
                source=source,
                concept_type=concept_type,
            )

            statement = cleaned[:220]
            fact_id = f"{self._slugify(topic)}_{self._slugify(source_note)}_{self._slugify(concept)[:20]}"

            fact["fact_id"] = fact_id
            fact["source_note"] = source_note
            fact["supporting_fact"] = statement
            fact["statement"] = statement
            fact["answer"] = concept
            fact["weight"] = weight

            return clean_fact(fact), None

        except ValueError as e:
            return None, RejectionInfo(RejectionReason.CREATION_ERROR, str(e), text)
        except Exception as e:
            return None, RejectionInfo(RejectionReason.CREATION_ERROR, str(e), text)

    def _extract_atomic_facts(
        self, content: str, topic: str, source: str
    ) -> List[Dict[str, Any]]:
        """Extract facts from content lines and bullets."""
        facts = []
        seen = set()
        stats = ExtractionStats()

        self.heading_filter.reset()
        in_structural_section = False

        for raw_line in content.splitlines():
            stats.total_lines += 1
            line = raw_line.strip()

            if not line or line.startswith("```"):
                continue

            if line.startswith("#"):
                is_structural, _ = self.heading_filter.is_structural(line, "")
                if is_structural:
                    in_structural_section = True
                    continue
                else:
                    in_structural_section = False

            if in_structural_section:
                continue

            cleaned = self._sanitize_text(line)
            if not cleaned or len(cleaned.split()) < 4:
                continue

            stats.candidate_lines += 1

            fact, rejection = self._build_atomic_fact(cleaned, topic, source)

            if rejection:
                if rejection.reason == RejectionReason.STRUCTURAL_HEADING:
                    stats.skipped_structural += 1
                    logger.debug(
                        f"Skipped heading: {rejection.detail} | {rejection.line[:50]}..."
                    )
                elif rejection.reason == RejectionReason.INVALID_CONCEPT:
                    stats.skipped_invalid_concept += 1
                    logger.debug(
                        f"Skipped invalid concept: {rejection.detail} | {rejection.line[:50]}..."
                    )
                else:
                    stats.skipped_other += 1
                    logger.debug(
                        f"Skipped: {rejection.reason.value} | {rejection.line[:50]}..."
                    )
                continue

            if not fact:
                stats.skipped_other += 1
                continue

            key = fact["supporting_fact"].lower()
            if key in seen:
                stats.skipped_duplicate += 1
                continue

            seen.add(key)
            facts.append(fact)
            stats.extracted_facts += 1

        logger.info(f"Extraction summary: {stats.summary()}")

        return facts

    # ========== PUBLIC API ==========

    def extract_facts(
        self, content: str, topic: str, source: str = "inline"
    ) -> List[Dict[str, Any]]:
        if not content or not str(content).strip():
            return []
        return self._extract_atomic_facts(content, topic, source)

    def extract_from_file(self, file_path: str, topic: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.extract_facts(content, topic, file_path)

    def extract_topic(self, topic: str) -> List[Dict[str, Any]]:
        folder = self.notes_path / topic
        if not folder.exists():
            return []

        all_facts = []
        for md_file in folder.glob("*.md"):
            facts = self.extract_from_file(str(md_file), topic)
            all_facts.extend(facts)

        unique_facts = {}
        for f in all_facts:
            key = f["concept"].lower()
            if key in unique_facts:
                if f.get("weight", 0) > unique_facts[key].get("weight", 0):
                    unique_facts[key] = f
                elif len(f.get("supporting_fact", "")) > len(
                    unique_facts[key].get("supporting_fact", "")
                ):
                    unique_facts[key] = f
            else:
                unique_facts[key] = f

        facts = list(unique_facts.values())
        print(f"  ✅ {topic}: {len(facts)} facts")
        return facts

    def extract_all(self) -> Dict[str, List[Dict[str, Any]]]:
        all_facts = {}
        for folder in self.notes_path.iterdir():
            if folder.is_dir() and not folder.name.startswith("."):
                topic = folder.name
                facts = self.extract_topic(topic)
                if facts:
                    all_facts[topic] = facts
        return all_facts


if __name__ == "__main__":
    extractor = FactExtractor()
    all_facts = extractor.extract_all()
    total = sum(len(v) for v in all_facts.values())
    print(f"\nTotal: {total} facts across {len(all_facts)} topics")

"""
Data Cleaner Utility - Find and fix data quality issues in facts.

This module provides utilities for:
- Finding duplicate concepts
- Finding corrupted concepts
- Reporting data quality issues
- Suggesting (and optionally applying) fixes

This is a DEVELOPMENT/DATA MAINTENANCE tool, not part of the main pipeline.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Redundant patterns to detect (generalized)
REDUNDANT_PATTERNS = [
    # (pattern_words, suggested_fix)
    (["world", "data"], "Data"),
    (["data", "augmentation"], "Augmentation"),
    (["machine", "learning"], "Machine Learning"),
    (["neural", "network"], "Neural Network"),
]

# Invalid concept patterns
INVALID_PATTERNS = [
    r"^\s*#+\s*",  # Headers
    r"^\s*[-*+]\s*",  # Bullets
    r"^types?\s+of",
    r"^why\s",
    r"^how\s",
    r".*layer$",
    r".*&.*layer",
]

# Words that indicate weak concepts
WEAK_INDICATORS = {
    "example",
    "examples",
    "technique",
    "techniques",
    "approach",
    "approaches",
    "method",
    "methods",
    "process",
    "processes",
    "concept",
    "concepts",
    "system",
    "systems",
    "layer",
    "layers",
    "overview",
    "summary",
    "introduction",
    "conclusion",
    "types",
    "categories",
    "classification",
}


# ============================================================================
# MAIN CLASS
# ============================================================================


class DataCleaner:
    """
    Data quality utility for facts.

    This class provides methods to find and report data quality issues
    in the fact cache. It can optionally apply fixes.

    Usage:
        cleaner = DataCleaner()
        report = cleaner.generate_report()
        if report['issues']:
            cleaner.fix_issues(report)
    """

    def __init__(self, fact_cache=None, cache_file: str = "facts_cache.json"):
        """
        Initialize the data cleaner.

        Args:
            fact_cache: Optional FactCache instance. If None, creates one.
            cache_file: Path to cache file if creating new cache.
        """
        if fact_cache:
            self.cache = fact_cache
        else:
            from app.rag.fact_cache import FactCache

            self.cache = FactCache(cache_file=cache_file)
            self.cache.load()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report.

        Returns:
            Dictionary with:
            - total_facts: Total number of facts
            - duplicate_groups: List of duplicate concept groups
            - corrupted_concepts: List of corrupted concepts
            - weak_concepts: List of weak concepts
            - summary: Summary statistics
            - issues: List of all issues found
        """
        facts = self._get_facts()

        if not facts:
            return {
                "total_facts": 0,
                "duplicate_groups": [],
                "corrupted_concepts": [],
                "weak_concepts": [],
                "summary": {},
                "issues": ["No facts found in cache"],
            }

        # Find issues
        duplicates = self.find_duplicates(facts)
        corrupted = self.find_corrupted_concepts(facts)
        weak = self.find_weak_concepts(facts)

        # Build summary
        summary = {
            "total_facts": len(facts),
            "duplicate_groups": len(duplicates),
            "corrupted_concepts": len(corrupted),
            "weak_concepts": len(weak),
            "unique_concepts": len(set(f.get("concept", "") for f in facts)),
        }

        # Collect all issues
        issues = []
        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate concept groups")
        if corrupted:
            issues.append(f"Found {len(corrupted)} corrupted concepts")
        if weak:
            issues.append(f"Found {len(weak)} weak concepts")

        return {
            "total_facts": len(facts),
            "duplicate_groups": duplicates,
            "corrupted_concepts": corrupted,
            "weak_concepts": weak,
            "summary": summary,
            "issues": issues,
        }

    def find_duplicates(
        self, facts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find duplicate or near-duplicate concepts.

        Args:
            facts: Optional list of facts. If None, loads from cache.

        Returns:
            Dictionary mapping normalized concept -> list of facts
        """
        if facts is None:
            facts = self._get_facts()

        concept_map = defaultdict(list)

        for f in facts:
            concept = f.get("concept", "")
            if concept:
                normalized = self._normalize_concept(concept)
                concept_map[normalized].append(f)

        return {k: v for k, v in concept_map.items() if len(v) > 1}

    def find_corrupted_concepts(
        self, facts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find concepts that are clearly corrupted.

        Checks:
        - Duplicate words
        - Redundant patterns
        - Invalid patterns

        Args:
            facts: Optional list of facts. If None, loads from cache.

        Returns:
            List of corrupted concept reports
        """
        if facts is None:
            facts = self._get_facts()

        corrupted = []

        for f in facts:
            concept = f.get("concept", "")
            if not concept:
                continue

            issues = []
            suggestion = concept

            # Check for duplicate words
            words = concept.split()
            if len(words) != len(set(words)):
                issues.append("duplicate_words")
                suggestion = " ".join(sorted(set(words), key=words.index))

            # Check for redundant patterns
            concept_lower = concept.lower()
            for pattern_words, suggested in REDUNDANT_PATTERNS:
                if all(p in concept_lower for p in pattern_words):
                    issues.append("redundant_pattern")
                    # Build suggestion by removing pattern words
                    for p in pattern_words:
                        suggestion = re.sub(
                            r"\b" + p + r"\b", "", suggestion, flags=re.IGNORECASE
                        )
                    suggestion = re.sub(r"\s+", " ", suggestion).strip()
                    if not suggestion:
                        suggestion = suggested
                    break

            # Check for invalid patterns
            for pattern in INVALID_PATTERNS:
                if re.match(pattern, concept_lower):
                    issues.append("invalid_pattern")
                    break

            if issues:
                # Clean up suggestion
                suggestion = self._clean_concept_name(suggestion)

                corrupted.append(
                    {"concept": concept, "issues": issues, "suggestion": suggestion}
                )

        return corrupted

    def find_weak_concepts(
        self, facts: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Find weak or generic concepts.

        Args:
            facts: Optional list of facts. If None, loads from cache.

        Returns:
            List of weak concept names
        """
        if facts is None:
            facts = self._get_facts()

        weak = []

        for f in facts:
            concept = f.get("concept", "")
            if not concept:
                continue

            concept_lower = concept.lower()

            # Check against weak indicators
            if concept_lower in WEAK_INDICATORS:
                weak.append(concept)
                continue

            # Check single-word generic concepts
            if len(concept.split()) == 1 and len(concept) < 4:
                if concept_lower not in [
                    "ai",
                    "ml",
                    "api",
                    "sql",
                ]:  # Allow common acronyms
                    weak.append(concept)

        return weak

    def fix_issues(
        self, report: Dict[str, Any], apply_fixes: bool = False
    ) -> Dict[str, Any]:
        """
        Fix issues found in the report.

        Args:
            report: Report from generate_report()
            apply_fixes: If True, actually apply fixes to cache

        Returns:
            Dictionary with fix results
        """
        results = {
            "fixed_duplicates": 0,
            "fixed_corrupted": 0,
            "fixed_weak": 0,
            "errors": [],
        }

        # Fix corrupted concepts
        for corrupted in report.get("corrupted_concepts", []):
            concept = corrupted["concept"]
            suggestion = corrupted["suggestion"]

            if not suggestion or suggestion == concept:
                continue

            if apply_fixes:
                # Find and update the fact
                updated = self._update_concept_in_cache(concept, suggestion)
                if updated:
                    results["fixed_corrupted"] += 1
                else:
                    results["errors"].append(f"Could not update: {concept}")

        # Save cache if fixes were applied
        if apply_fixes and (
            results["fixed_corrupted"] > 0 or results["fixed_duplicates"] > 0
        ):
            self.cache.save()
            logger.info(f"Applied fixes to cache: {results}")

        return results

    def suggest_fixes(self, report: Dict[str, Any]) -> str:
        """
        Generate human-readable suggestions from a report.

        Args:
            report: Report from generate_report()

        Returns:
            Formatted string with suggestions
        """
        lines = ["\n🔧 Suggested Fixes:"]

        if report["duplicate_groups"]:
            lines.append(
                f"\n1. Resolve {len(report['duplicate_groups'])} duplicate groups:"
            )
            for norm, items in list(report["duplicate_groups"].items())[:3]:
                concepts = [f["concept"] for f in items]
                lines.append(f"   - '{norm}': {concepts}")

        if report["corrupted_concepts"]:
            lines.append(
                f"\n2. Fix {len(report['corrupted_concepts'])} corrupted concepts:"
            )
            for c in report["corrupted_concepts"][:5]:
                lines.append(f"   - '{c['concept']}' → '{c['suggestion']}'")

        if report["weak_concepts"]:
            lines.append(f"\n3. Review {len(report['weak_concepts'])} weak concepts:")
            for w in report["weak_concepts"][:5]:
                lines.append(f"   - '{w}'")

        lines.append("\n4. To apply fixes automatically, run:")
        lines.append("   from app.utils.clean_data import DataCleaner")
        lines.append("   cleaner = DataCleaner()")
        lines.append("   report = cleaner.generate_report()")
        lines.append("   cleaner.fix_issues(report, apply_fixes=True)")

        return "\n".join(lines)

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _get_facts(self) -> List[Dict[str, Any]]:
        """Get facts from cache."""
        if hasattr(self.cache, "get_all_facts"):
            return self.cache.get_all_facts()
        elif hasattr(self.cache, "get_facts"):
            # Get all topics
            topics = (
                self.cache.get_all_topics()
                if hasattr(self.cache, "get_all_topics")
                else []
            )
            facts = []
            for topic in topics:
                facts.extend(self.cache.get_facts(topic))
            return facts
        return []

    def _normalize_concept(self, concept: str) -> str:
        """Normalize concept for comparison."""
        if not concept:
            return ""
        # Remove extra spaces
        normalized = re.sub(r"\s+", " ", concept).strip()
        return normalized.lower()

    def _clean_concept_name(self, concept: str) -> str:
        """Clean a concept name."""
        if not concept:
            return ""

        # Remove extra spaces
        cleaned = re.sub(r"\s+", " ", concept).strip()

        # Remove trailing punctuation
        cleaned = re.sub(r"[.,;:]$", "", cleaned)

        # Capitalize
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned

    def _update_concept_in_cache(self, old_concept: str, new_concept: str) -> bool:
        """Update a concept name in the cache."""
        try:
            # Get all facts
            facts = self._get_facts()

            updated = False
            for f in facts:
                if f.get("concept") == old_concept:
                    f["concept"] = new_concept
                    f["answer"] = new_concept
                    updated = True

            if updated:
                # Update the cache's internal storage
                if hasattr(self.cache, "facts"):
                    # Rebuild facts dict
                    self.cache.facts = {f["concept"].lower(): f for f in facts}
                elif hasattr(self.cache, "_facts"):
                    self.cache._facts = {f["concept"].lower(): f for f in facts}

            return updated

        except Exception as e:
            logger.error(f"Failed to update concept: {e}")
            return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def check_data_quality(cache_file: str = "facts_cache.json") -> Dict[str, Any]:
    """
    Quick function to check data quality.

    Args:
        cache_file: Path to cache file

    Returns:
        Quality report
    """
    cleaner = DataCleaner(cache_file=cache_file)
    return cleaner.generate_report()


def clean_data(
    cache_file: str = "facts_cache.json", dry_run: bool = True
) -> Dict[str, Any]:
    """
    Clean data in the cache.

    Args:
        cache_file: Path to cache file
        dry_run: If True, only report issues; if False, apply fixes

    Returns:
        Results dictionary
    """
    cleaner = DataCleaner(cache_file=cache_file)
    report = cleaner.generate_report()

    if dry_run:
        print(cleaner.suggest_fixes(report))
        return {"dry_run": True, "report": report}

    return cleaner.fix_issues(report, apply_fixes=True)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean fact cache data")
    parser.add_argument("--fix", action="store_true", help="Apply fixes automatically")
    parser.add_argument("--cache", default="facts_cache.json", help="Cache file path")
    args = parser.parse_args()

    if args.fix:
        print("Applying fixes...")
        results = clean_data(cache_file=args.cache, dry_run=False)
        print(f"Fixed: {results}")
    else:
        print("Generating report...")
        report = check_data_quality(cache_file=args.cache)
        print(f"Total facts: {report['total_facts']}")
        print(f"Issues found: {len(report['issues'])}")

        cleaner = DataCleaner(cache_file=args.cache)
        print(cleaner.suggest_fixes(report))

import ollama
import json
import re
from difflib import SequenceMatcher
from json_repair import repair_json
from typing import List, Dict, Any, Optional, Tuple

from .question_cache import QuestionCache
from .question_scorer import QuestionScorer
from .question_validator import is_valid_question
from .question_similarity import is_similar_to_pool

# Import centralized option parser
from .options_parser import (
    extract_option_text,
    extract_option_letter,
    format_option,
    get_correct_text_from_options,
    get_distractor_texts,
    normalize_options,
    validate_options_format
)


# ============ CONSTANTS ============

# Concept hierarchy for topic relevance
CONCEPT_HIERARCHY = {
    'cloud': [
        'cloud storage', 'cloud database', 'cloud computing',
        'cloud infrastructure', 'virtual machine', 'data center',
        'edge computing', 'serverless', 'containerization',
        'block storage', 'object storage', 'file storage'
    ],
    'database': [
        'sql', 'nosql', 'relational', 'mongodb', 'postgresql',
        'mysql', 'query', 'indexing', 'normalization'
    ],
    'algorithm': [
        'sorting', 'searching', 'recursion', 'dynamic programming',
        'greedy', 'backtracking', 'divide and conquer', 'complexity'
    ],
    'programming': [
        'function', 'variable', 'class', 'object', 'inheritance',
        'polymorphism', 'encapsulation', 'oop', 'functional'
    ]
}

# Banned layer phrases
BANNED_LAYER_PATTERNS = [
    r'foundational layer',
    r'communication layer',
    r'performance layer',
    r'control layer',
    r'execution layer',
    r'learning layer',
    r'optimization layer',
    r'architecture layer',
    r'layer that',
    r'layer allows',
    r'layer provides',
    r'layer enables',
    r'layer manages',
]

# Words that indicate invalid concepts
INVALID_CONCEPT_WORDS = {
    'allows', 'provides', 'enables', 'stores', 'manages', 'reduces', 'improves',
    'uses', 'supports', 'offers', 'helps', 'contains', 'includes', 'does', 'doing',
    'responsible', 'processing', 'maintaining', 'organizing', 'allow', 'provide',
    'enable', 'store', 'manage', 'reduce', 'improve', 'use', 'support', 'offer',
    'help', 'contain', 'include', 'do', 'concept', 'example', 'method', 'approach',
    'technique', 'process', 'system', 'layer', 'type', 'category', 'classification',
    'service', 'platform', 'solution', 'resource', 'infrastructure', 'component',
    'module'
}

# Stop words for grounding validation
STOP_WORDS = {
    'the', 'this', 'that', 'with', 'from', 'have', 'will', 'they',
    'what', 'when', 'where', 'which', 'their', 'there', 'about',
    'concept', 'using', 'used', 'also', 'can', 'for', 'are', 'has'
}

# Generic explanation phrases that indicate weak explanations
GENERIC_PHRASES = [
    "the correct answer is",
    "because it is the correct answer",
    "because it is correct",
    "this option is correct",
    "this answer is correct",
    "the answer is"
]

# Maximum lengths
MAX_QUESTION_LENGTH = 250
MAX_EXPLANATION_WORDS = 24
MAX_SUPPORTING_WORDS = 24
MIN_SUPPORTING_WORDS = 3


# ============ UTILITY FUNCTIONS ============

def has_garbled_text(text: str) -> bool:
    """Check if text contains non-printable or control characters."""
    if not isinstance(text, str):
        return True
    return bool(re.search(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', text))


def normalize_supporting_fact(text: str) -> str:
    """Turn a raw note fragment into a short atomic supporting fact."""
    if not text:
        return ""

    cleaned = str(text).strip()
    cleaned = re.sub(r'^\s*#+\s*', '', cleaned)
    cleaned = re.sub(r'^\s*[-*+]\s*', '', cleaned)
    cleaned = re.sub(r'^\s*\d+\.\s*', '', cleaned)
    cleaned = re.sub(r'\[\[(.*?)\]\]', r'\1', cleaned)
    cleaned = re.sub(r'[*_`>#]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.rstrip(' .')

    if not cleaned:
        return ""
    if any(marker in cleaned.lower() for marker in ['#', '[[', ']]', '---', 'http', 'https']):
        return ""
    if len(cleaned.split()) > MAX_SUPPORTING_WORDS:
        cleaned = ' '.join(cleaned.split()[:MAX_SUPPORTING_WORDS]).rstrip(' .')
    if cleaned.lower().startswith(('how ', 'why ', 'what ', 'when ', 'where ',
                                    'conclusion', 'summary', 'overview', 'references')):
        return ""
    return cleaned


def filter_similar_questions(questions: List[Dict[str, Any]], threshold: float = 0.6) -> List[Dict[str, Any]]:
    """Remove similar questions using question_similarity module."""
    if not questions:
        return []
    
    unique = []
    seen_answers = set()
    
    for q in questions:
        correct_letter = q.get('correct', '')
        options = q.get('options', [])
        correct_text = get_correct_text_from_options(options, correct_letter).lower()
        
        if correct_text and correct_text in seen_answers:
            continue
        
        if is_similar_to_pool(q, unique, threshold):
            continue
        
        unique.append(q)
        if correct_text:
            seen_answers.add(correct_text)
    
    return unique


def log_validation_failure(question: dict, stage: str, reason: str, details: dict = None):
    """Log detailed validation failures for debugging."""
    print(f"\n❌ VALIDATION FAILED at stage: {stage}")
    print(f"   Reason: {reason}")
    
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")
    
    if question:
        print(f"   Question preview: {question.get('question', 'N/A')[:80]}...")
        print(f"   Options: {question.get('options', 'N/A')}")
        print(f"   Correct: {question.get('correct', 'N/A')}")
        print(f"   Concept: {question.get('concept', 'N/A') or question.get('correct_text', 'N/A')}")


# ============ LAYER PHRASE FILTERING ============

def is_layer_phrase(text: str) -> bool:
    """Check if a supporting fact contains generic layer phrases."""
    text_lower = text.lower()
    for pattern in BANNED_LAYER_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def sanitize_supporting_fact(supporting_fact: str, concept: str) -> Optional[str]:
    """Sanitize a supporting fact to remove generic layer phrases."""
    if not supporting_fact:
        return None
    
    if "layer" in concept.lower():
        return supporting_fact
    
    if is_layer_phrase(supporting_fact):
        print(f"⚠️ Rejecting supporting fact with banned layer phrase: {supporting_fact[:60]}...")
        return None
    
    return supporting_fact


# ============ TOPIC RELEVANCE ============

def is_relevant_to_topic(question: str, topic: str, answer: str = "", supporting_fact: str = "") -> bool:
    """
    Check if content is relevant to the topic using concept hierarchy.
    Does NOT depend on FactExtractor private methods.
    """
    topic_lower = topic.lower()
    
    # Combine all text to check
    combined_text = question.lower()
    if answer:
        combined_text += " " + answer.lower()
    if supporting_fact:
        combined_text += " " + supporting_fact.lower()
    
    # Build topic keywords from the topic name
    topic_keywords = [topic_lower]
    topic_words = topic_lower.split()
    for word in topic_words:
        if len(word) > 3:
            topic_keywords.append(word)
    
    # Add child concepts from hierarchy
    for key, children in CONCEPT_HIERARCHY.items():
        if key in topic_lower:
            topic_keywords.extend(children)
    
    # Remove duplicates
    topic_keywords = list(set(topic_keywords))
    
    # Check if any keyword appears in combined text
    for keyword in topic_keywords:
        if keyword in combined_text:
            return True
    
    # If answer is a valid concept, check if it's related
    if answer:
        answer_lower = answer.lower()
        for keyword in topic_keywords:
            if len(keyword) > 3 and keyword in answer_lower:
                return True
        
        # Check if answer is a child concept
        for key, children in CONCEPT_HIERARCHY.items():
            if key in topic_lower:
                for child in children:
                    if child in answer_lower:
                        return True
    
    # Check supporting fact
    if supporting_fact:
        for keyword in topic_keywords:
            if keyword in supporting_fact.lower():
                return True
    
    log_validation_failure(
        None,
        "topic_relevance",
        "No topic keywords found in combined text",
        {
            "topic": topic,
            "question_preview": question[:60] + "...",
            "answer_preview": answer[:60] + "..." if answer else "None",
            "topic_keywords": topic_keywords[:10]
        }
    )
    return False


# ============ QUESTION FOCUS VALIDATION ============

def validate_question_focus(question: dict, concept: str) -> bool:
    """Validate that the generated question focuses on the correct concept."""
    q_text = question.get('question', '').lower()
    concept_lower = concept.lower()
    
    if 'layer' in q_text and 'layer' not in concept_lower:
        print(f"⚠️ Question uses 'layer' but concept is '{concept}'")
        return False
    
    if concept_lower in q_text:
        return True
    
    concept_words = concept_lower.split()
    significant_words = [w for w in concept_words if len(w) > 3 and w not in ['the', 'this', 'that']]
    if significant_words:
        matched = sum(1 for w in significant_words if w in q_text)
        if matched / len(significant_words) < 0.5:
            print(f"⚠️ Question doesn't reference concept '{concept}': {q_text[:60]}...")
            return False
    
    return True


# ============ VALIDATION STAGES ============

def validate_structure(question: dict) -> bool:
    """Check that the question has all required fields with correct types."""
    required = ['question', 'options', 'correct', 'explanation']
    missing = [f for f in required if f not in question]
    
    if missing:
        log_validation_failure(question, "structure", f"Missing required fields: {missing}", {"missing_fields": missing})
        return False
    
    if not isinstance(question['options'], list) or len(question['options']) != 4:
        log_validation_failure(question, "structure", "Options must be a list of 4 items", {"options_count": len(question.get('options', []))})
        return False
    
    q_text = question['question'].strip()
    if not q_text.endswith('?'):
        log_validation_failure(question, "structure", "Question doesn't end with '?'", {"question": q_text[:80] + "..."})
        return False
    
    if len(q_text) > MAX_QUESTION_LENGTH:
        log_validation_failure(question, "structure", f"Question too long ({len(q_text)} chars)", {"length": len(q_text)})
        return False
    
    if re.search(r'\b[A-D]\)', q_text):
        log_validation_failure(question, "structure", "Question contains leaked option markers", {"question": q_text[:80] + "..."})
        return False
    
    return True


def validate_grounding(question: dict, context: str, supporting_fact: str = "") -> bool:
    """
    Check if the correct answer is grounded in the note-backed context.
    Uses flexible matching: exact, keyword, and phrase-level.
    """
    if 'correct' not in question or 'options' not in question:
        return False
    
    correct_letter = question['correct']
    options = question['options']
    correct_text = get_correct_text_from_options(options, correct_letter)
    
    if not correct_text:
        log_validation_failure(question, "grounding", "Could not extract correct text from options", {"correct_letter": correct_letter})
        return False
    
    # Prefer supporting_fact, fallback to context
    grounding_context = supporting_fact or context or ""
    if not grounding_context:
        log_validation_failure(question, "grounding", "No context provided for grounding check")
        return False

    context_lower = grounding_context.lower()
    correct_lower = correct_text.lower()
    correct_words = correct_lower.split()
    
    # Level 1: Exact match
    if correct_lower in context_lower:
        print(f"✅ Grounding: exact match for '{correct_text}'")
        return True
    
    # Level 2: Any significant word appears in context
    for word in correct_words:
        if len(word) > 3 and word not in STOP_WORDS:
            if word in context_lower:
                print(f"✅ Grounding: found keyword '{word}' from '{correct_text}'")
                return True
    
    # Level 3: Multi-word phrase matching (at least 60% of words appear together)
    if len(correct_words) >= 2:
        sentences = re.split(r'[.!?\n]', context_lower)
        for sentence in sentences:
            sentence_words = set(sentence.split())
            matched_words = [w for w in correct_words if w in sentence_words]
            if len(matched_words) >= len(correct_words) * 0.6:
                print(f"✅ Grounding: phrase match for '{correct_text}' in sentence")
                return True
    
    log_validation_failure(question, "grounding", "Correct answer not found in context", {
        "correct_text": correct_text,
        "context_preview": grounding_context[:100] + "...",
        "correct_words": correct_words[:3]
    })
    return False


def question_equals_answer(question_text: str, options: list) -> bool:
    """Check if the question is just restating the correct answer."""
    q_clean = question_text.strip().lower().rstrip('.?')
    for opt in options:
        opt_text = extract_option_text(opt).lower().rstrip('.')
        if opt_text and (opt_text in q_clean or q_clean in opt_text) and len(opt_text) > 20:
            print(f"⚠️ Option text duplicates question text: '{opt_text[:40]}...'")
            return True
    return False


def has_redundant_options(options) -> bool:
    """Check if one option contains another option."""
    texts = [extract_option_text(opt).lower() for opt in options]
    
    for i, text in enumerate(texts):
        for j, other in enumerate(texts):
            if i != j and len(other) > 3 and other in text:
                print(f"⚠️ Option overlap: '{other}' found inside '{text}'")
                return True
    
    for i, text in enumerate(texts):
        parts = [p.strip() for p in text.split(',')]
        if len(parts) > 2:
            for j, other in enumerate(texts):
                if i != j and any(other in part for part in parts):
                    print(f"⚠️ Option contains parts of another option: '{text}' contains '{other}'")
                    return True
    
    return False


def explanation_contradicts_answer(question: dict) -> bool:
    """Check if the explanation text actually supports the marked-correct option."""
    correct_letter = question.get('correct', '')
    options = question.get('options', [])
    explanation = question.get('explanation', '').strip().lower()

    if not options or not correct_letter:
        return True

    correct_text = get_correct_text_from_options(options, correct_letter)
    if not correct_text:
        return True

    if not explanation:
        return False

    correct_text_lower = correct_text.lower()
    explanation_words = [w for w in re.split(r'[^a-z0-9]+', explanation) if len(w) > 2]
    correct_words = [w for w in re.split(r'[^a-z0-9]+', correct_text_lower) if len(w) > 2]

    if not correct_words:
        return True

    # Check if explanation supports another option more strongly
    other_option_texts = []
    for opt in options:
        opt_letter = extract_option_letter(opt)
        if opt_letter and opt_letter != correct_letter:
            opt_text = extract_option_text(opt).lower()
            if opt_text:
                other_option_texts.append(opt_text)

    for other_text in other_option_texts:
        other_words = [w for w in re.split(r'[^a-z0-9]+', other_text) if len(w) > 2]
        if not other_words:
            continue
        other_overlap = set(explanation_words) & set(other_words)
        correct_overlap = set(explanation_words) & set(correct_words)
        if len(other_overlap) > len(correct_overlap):
            print(f"⚠️ Explanation appears to support another option: '{other_text}'")
            return True

    # Reject explanations that don't mention the correct answer
    if len(correct_overlap := set(explanation_words) & set(correct_words)) < 1:
        print(f"⚠️ Explanation doesn't mention the correct answer text: '{correct_text}'")
        return True

    # Reject generic explanations that don't provide grounding
    if any(phrase in explanation for phrase in GENERIC_PHRASES):
        if len(correct_overlap) < 2:
            print(f"⚠️ Explanation is too generic to support '{correct_text}'")
            return True

    return False


def validate_semantic(question: dict) -> bool:
    """Check semantic quality of the question."""
    if has_redundant_options(question.get('options', [])):
        log_validation_failure(question, "semantic", "Redundant options detected")
        return False
    
    if explanation_contradicts_answer(question):
        log_validation_failure(question, "semantic", "Explanation contradicts answer")
        return False
    
    if has_garbled_text(question.get('question', '')):
        log_validation_failure(question, "semantic", "Garbled text in question")
        return False
    
    for opt in question.get('options', []):
        if has_garbled_text(str(opt)):
            log_validation_failure(question, "semantic", "Garbled text in option")
            return False
    
    return True


def normalize_and_validate_correct_field(question: dict) -> bool:
    """Ensure 'correct' is exactly one of A/B/C/D."""
    correct = str(question.get('correct', '')).strip()
    options = question.get('options', [])
    
    if not options or len(options) != 4:
        log_validation_failure(question, "correct_field", "Invalid options count", {"options_count": len(options)})
        return False
    
    if correct in ['A', 'B', 'C', 'D']:
        question['correct'] = correct
        return True
    
    letter_match = re.match(r'^([A-D])\s*[\)\.\-\s]', correct)
    if letter_match:
        question['correct'] = letter_match.group(1)
        return True
    
    for opt in options:
        opt_letter = extract_option_letter(opt)
        opt_text = extract_option_text(opt).lower()
        if opt_text == correct.lower():
            question['correct'] = opt_letter
            return True
    
    for opt in options:
        opt_text = extract_option_text(opt).lower()
        if correct.lower() in opt_text or opt_text in correct.lower():
            opt_letter = extract_option_letter(opt)
            if opt_letter:
                question['correct'] = opt_letter
                print(f"✅ Fuzzy matched '{correct}' to '{opt_text}' -> {opt_letter}")
                return True
    
    log_validation_failure(question, "correct_field", "Could not resolve correct field", {"correct_value": correct})
    return False


# ============ GROUNDING ATTACHMENT ============

def build_consistent_explanation(question_text: str, options: list, correct_letter: str,
                                  correct_text: str, context: str = "", facts: list = None) -> str:
    """Build a short explanation from a single selected supporting fact."""
    if not correct_text:
        return ""

    correct_text = correct_text.strip()
    if not correct_text:
        return ""

    if facts:
        for fact in facts:
            supporting_fact = normalize_supporting_fact(
                str(fact.get('supporting_fact') or fact.get('sentence') or fact.get('definition') or '').strip()
            )
            if not supporting_fact:
                continue
            supporting_lower = supporting_fact.lower()
            correct_lower = correct_text.lower()
            if correct_lower in supporting_lower or any(
                word in supporting_lower for word in 
                [w for w in re.split(r'[^a-z0-9]+', correct_lower) if len(w) > 2]
            ):
                explanation = f"{correct_text} is correct because {supporting_fact}"
                if len(explanation.split()) <= MAX_EXPLANATION_WORDS:
                    return explanation

    if context:
        cleaned_context = normalize_supporting_fact(context)
        if cleaned_context:
            explanation = f"{correct_text} is correct because {cleaned_context}"
            if len(explanation.split()) <= MAX_EXPLANATION_WORDS:
                return explanation

    return ""


def _attach_grounding_fields(question: dict, correct_text: str, supporting_fact: str, context: str = "") -> bool:
    """Attach correct_text/supporting_fact/explanation to a question."""
    if not question or not isinstance(question, dict):
        return False

    question['correct_text'] = correct_text or ""
    question['supporting_fact'] = normalize_supporting_fact(supporting_fact or "")

    if not question['supporting_fact']:
        question['supporting_fact'] = normalize_supporting_fact(context or "")

    # Try to build a proper explanation
    if correct_text and question['supporting_fact']:
        explanation = build_consistent_explanation(
            question_text=question.get('question', ''),
            options=question.get('options', []),
            correct_letter=question.get('correct', ''),
            correct_text=correct_text,
            context=question['supporting_fact'],
            facts=[{'supporting_fact': question['supporting_fact']}]
        )
        if explanation and not question.get('explanation'):
            question['explanation'] = explanation
        return True
    
    # Fallback: create a simple grounded explanation
    if correct_text and question['supporting_fact']:
        question['explanation'] = f"{correct_text} is correct because {question['supporting_fact']}"
        return True
    elif correct_text:
        question['explanation'] = f"{correct_text} is the correct answer."
        return True
    
    question['explanation'] = ""
    return True


def _select_supporting_fact(correct_text: str, supporting_facts: list = None,
                            fallback_context: str = "") -> str:
    """Pick the strongest note-backed supporting sentence for a question."""

    candidates = []

    if supporting_facts:
        for fact in supporting_facts:
            if isinstance(fact, dict):
                candidate = (
                    fact.get('supporting_fact')
                    or fact.get('sentence')
                    or fact.get('definition')
                    or ""
                )
            else:
                candidate = str(fact)

            cleaned = normalize_supporting_fact(candidate)

            if cleaned:
                candidates.append(cleaned)

    if fallback_context:
        sentences = re.split(r'[.!?\n]+', fallback_context)

        for sentence in sentences:
            cleaned = normalize_supporting_fact(sentence)

            if cleaned:
                candidates.append(cleaned)


    if not candidates:
        return ""


    correct_words = [
        w.lower()
        for w in re.findall(r'\w+', correct_text)
        if len(w) > 2
    ]


    best_candidate = ""
    best_score = 0


    for candidate in candidates:

        candidate_lower = candidate.lower()

        score = 0

        for word in correct_words:
            if word in candidate_lower:
                score += 1


        if correct_text.lower() in candidate_lower:
            score += 5


        if score > best_score:
            best_score = score
            best_candidate = candidate


    return best_candidate or candidates[0]


# ============ QUIZ GENERATOR CLASS ============

class QuizGenerator:
    def __init__(self, model: str = "qwen2.5:3b", min_quality_score: float = 0.6):
        self.model = model
        self.cache = QuestionCache()
        self.scorer = QuestionScorer()
        self.min_quality_score = min_quality_score
        self._supporting_facts = []

    def _check_quality(self, question: dict, facts: list = None) -> Tuple[bool, float, Dict[str, float]]:
        """Check question quality using QuestionScorer."""
        if facts is None:
            facts = []
        
        is_acceptable, score, scores, issues = self.scorer.is_acceptable(question, facts)
        
        if not is_acceptable:
            print(f"⚠️ Quality check failed: score={score:.2f} (threshold={self.min_quality_score})")
            print(f"   Scores: {scores}")
            print(f"   Issues: {issues}")
        else:
            print(f"✅ Quality check passed: score={score:.2f}")
        
        return is_acceptable, score, scores

    def _is_valid_concept(self, concept: str) -> bool:
        """Check if a concept is valid (not a verb, adjective, or generic word)."""
        if not concept or len(concept) < 2:
            return False
        
        concept_lower = concept.lower()
        
        if concept_lower in INVALID_CONCEPT_WORDS:
            return False
        
        if len(concept_lower) == 1:
            return False
        
        if len(concept.split()) >= 2:
            return True

        if concept.lower() in ["database", "cloud", "algorithm", "programming"]:
            return False
        
        if concept[0].isupper() and len(concept) > 2:
            return True
        
        return False

    def _find_supporting_fact_for_concept(self, concept: str, context: str) -> str:
        """Find a supporting fact for a concept from the context."""
        if not context or not concept:
            return ""
        
        sentences = re.split(r'[.!?\n]+', context)
        for sentence in sentences:
            if concept.lower() in sentence.lower():
                cleaned = normalize_supporting_fact(sentence)
                if cleaned and len(cleaned.split()) >= MIN_SUPPORTING_WORDS:
                    return cleaned
        
        for sentence in sentences:
            cleaned = normalize_supporting_fact(sentence)
            if cleaned and len(cleaned.split()) >= MIN_SUPPORTING_WORDS:
                return cleaned
        
        return context[:200] + "..."

    def _create_fact_based_question(self, concept: str, supporting_fact: str, topic: str) -> dict:
        """Create a question directly from an extracted fact."""
        supporting_fact = normalize_supporting_fact(supporting_fact)
        if not supporting_fact:
            supporting_fact = f"Provides information about {concept}."
        
        fact_clean = supporting_fact
        if concept.lower() in fact_clean.lower():
            fact_clean = re.sub(re.escape(concept), '_______', fact_clean, flags=re.IGNORECASE)
            question_text = f"Complete the statement: {fact_clean}"
        else:
            question_text = f"What is the correct term for: {supporting_fact}?"
        
        options = [
            f"A) {concept}",
            "B) Related Technology",
            "C) Alternative Approach",
            "D) Different Concept"
        ]
        
        return {
            "question": question_text,
            "options": options,
            "correct": "A",
            "correct_text": concept,
            "supporting_fact": supporting_fact,
            "explanation": f"{concept} is correct because {supporting_fact}",
            "source_note": "fact_based_fallback",
            "fact_id": f"fact_fallback_{concept.lower().replace(' ', '_')}",
            "_is_fallback": True,
            "_quality_score": 0.7,
            "_quality_scores": {
                "semantic_coherence": 1.0,
                "distractor_plausibility": 0.5,
                "type_consistency": 1.0
            }
        }

    def _generate_fallback_question(self, context: str, topic: str,
                                    extracted_concepts: list = None) -> Optional[dict]:
        """Generate a fallback question using extracted concepts."""
        if extracted_concepts:
            for concept in extracted_concepts:
                if concept and self._is_valid_concept(concept):
                    supporting_fact = self._find_supporting_fact_for_concept(concept, context)
                    if supporting_fact:
                        return self._create_fact_based_question(concept, supporting_fact, topic)
        
        if self._supporting_facts:
            for sf in self._supporting_facts:
                if isinstance(sf, dict):
                    concept = sf.get('concept') or sf.get('correct_text') or sf.get('answer')
                    supporting_fact = sf.get('supporting_fact') or sf.get('statement') or sf.get('definition')
                    if concept and self._is_valid_concept(concept) and supporting_fact:
                        return self._create_fact_based_question(concept, supporting_fact, topic)
        
        context_concepts = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\b', context)
        for concept in context_concepts:
            if self._is_valid_concept(concept):
                supporting_fact = self._find_supporting_fact_for_concept(concept, context)
                if supporting_fact:
                    return self._create_fact_based_question(concept, supporting_fact, topic)
        
        if topic and self._is_valid_concept(topic):
            return self._create_fact_based_question(topic, context[:200] + "...", topic)
        
        return None

    def _generate_generic_fallback(self, context: str, topic: str) -> dict:
        """Last resort generic fallback when no concepts are available."""
        return {
            "question": f"What is the main concept discussed in {topic}?",
            "options": ["A) The Main Concept", "B) Related Technology", "C) Alternative Approach", "D) Different Concept"],
            "correct": "A",
            "correct_text": "The Main Concept",
            "supporting_fact": context[:200] + "...",
            "explanation": "The main concept is the correct answer based on the content.",
            "source_note": "generic_fallback",
            "fact_id": f"generic_fallback_{topic.lower().replace(' ', '_')}",
            "_is_fallback": True,
            "_quality_score": 0.5,
            "_quality_scores": {
                "semantic_coherence": 0.5,
                "distractor_plausibility": 0.3,
                "type_consistency": 0.7
            }
        }

    def generate_with_retry(self, fact: str, answer: str, topic: str,
                           max_attempts: int = 3, fact_data: dict = None) -> Optional[dict]:
        """Generate a question with retries if validation fails."""
        for attempt in range(max_attempts):
            question = self.generate_from_fact(fact, answer, topic, fact_data=fact_data)
            if question:
                print(f"✅ Question generated on attempt {attempt+1}")
                return question
            print(f"⚠️ Attempt {attempt+1}/{max_attempts} failed, retrying...")
        print(f"⚠️ All {max_attempts} attempts failed for this fact, skipping")
        return None

    def generate_from_fact(self, fact: str, answer: str, topic: str,
                          fact_data: dict = None) -> Optional[dict]:
        """Generate a question from a single fact with coherence checking."""
        fact_data = fact_data or {}
        supporting_fact = fact_data.get('supporting_fact') or fact_data.get('sentence') or fact_data.get('definition') or fact or ""
        
        sanitized_supporting_fact = sanitize_supporting_fact(supporting_fact, answer)
        if not sanitized_supporting_fact:
            print(f"⚠️ Skipping fact due to layer phrase: {supporting_fact[:60]}...")
            return None
        
        fact_for_prompt = sanitized_supporting_fact
        
        # Improved prompt: clearer, more specific, with stronger grounding requirement
        prompt = f"""You are a computer science tutor creating a multiple-choice question.

FACT: {fact_for_prompt}
CORRECT ANSWER: {answer}
TOPIC: {topic}

Requirements:
1. Question must end with "?"
2. Option A MUST be "{answer}" exactly
3. Correct field must be "A", "B", "C", or "D"
4. Explanation must reference the fact
5. All distractors must be plausible but incorrect
6. Return ONLY valid JSON

Example output:
{{
  "question": "What provides database services over the Internet instead of local storage systems?",
  "options": ["A) Cloud Database", "B) Local Storage", "C) Network Database", "D) Distributed Storage"],
  "correct": "A",
  "explanation": "Cloud Database is correct because it provides database services over the Internet."
}}

Generate 5 different questions now:"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "num_predict": 800
                }
            )
            
            content = response['message']['content']
            print(f"Fact-based response received: {len(content)} characters")
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                log_validation_failure(None, "json_parse", "No JSON found in response")
                return None
            
            content = json_match.group()
            content = content.replace('```json', '').replace('```', '').strip()
            
            try:
                repaired = repair_json(content)
                result = json.loads(repaired)
                print(f"✅ JSON repaired successfully")
            except Exception as e:
                print(f"⚠️ JSON repair failed: {e}")
                content = content.replace("'", '"')
                content = re.sub(r',\s*}', '}', content)
                content = re.sub(r',\s*]', ']', content)
                try:
                    result = json.loads(content)
                except Exception as e2:
                    log_validation_failure(None, "json_parse", f"Failed to parse JSON: {e2}")
                    return None
            
            if 'questions' in result and len(result['questions']) > 0:
                question = result['questions'][0]
                
                # Format options immediately
                options = question.get('options', [])
                if options:
                    question['options'] = normalize_options(options)
                
                # ===== VALIDATION PIPELINE =====
                
                # Stage 1: Structure
                if not validate_structure(question):
                    return None
                
                # Stage 2: Content - Grounding (uses supporting_fact)
                if not validate_grounding(question, fact, supporting_fact=sanitized_supporting_fact):
                    return None
                
                # Stage 2: Content - Topic relevance
                if not is_relevant_to_topic(
                    question.get('question', ''),
                    topic,
                    answer,
                    sanitized_supporting_fact
                ):
                    return None
                
                # Stage 2: Content - Question restates answer
                if question_equals_answer(question.get('question', ''), question.get('options', [])):
                    log_validation_failure(question, "content", "Question restates the answer")
                    return None
                
                # Stage 2: Content - Placeholder detection
                q_text = question.get('question', '')
                if 'testing the fact' in q_text.lower() or 'question about' in q_text.lower() and len(q_text) < 40:
                    log_validation_failure(question, "content", "Placeholder question detected")
                    return None
                
                # Stage 2: Content - Question focus validation
                if not validate_question_focus(question, answer):
                    log_validation_failure(question, "focus", f"Question doesn't focus on concept '{answer}'")
                    return None
                
                # Stage 3: Semantic
                if not validate_semantic(question):
                    return None
                
                # Normalize correct field
                if not normalize_and_validate_correct_field(question):
                    return None
                
                # Extract and attach grounding fields
                correct_letter = question.get('correct', '')
                correct_text = get_correct_text_from_options(question.get('options', []), correct_letter)
                supporting_fact = question.get('supporting_fact') or fact_data.get('supporting_fact') or fact
                question['fact_id'] = fact_data.get('fact_id') or f"fact_{abs(hash(fact))}"
                question['source_note'] = fact_data.get('source_note') or 'inline'
                
                if not _attach_grounding_fields(question, correct_text, sanitized_supporting_fact, context=fact):
                    print(f"⚠️ Could not attach grounded explanation for fact-based question")
                    # Continue - we already have a fallback in _attach_grounding_fields
                
                # Quality scoring
                facts = self.cache.get_facts(topic) if hasattr(self.cache, 'get_facts') else []
                is_acceptable, score, scores = self._check_quality(question, facts)
                
                if not is_acceptable:
                    print(f"⚠️ Question scored {score:.2f} - below threshold ({self.min_quality_score}), rejecting")
                    return None
                
                question['_quality_score'] = score
                question['_quality_scores'] = scores
                
                return question
            return None
            
        except Exception as e:
            print(f"Error generating from fact: {e}")
            return None

    def generate_questions(self, context: str, topic: str, count: int = 1,
                          supporting_facts: list = None) -> Dict[str, Any]:
        """Generate a single quiz question from context."""
        self._supporting_facts = supporting_facts or []
        
        prompt = f"""You are a computer science tutor creating a multiple-choice question.

TOPIC: {topic}
CONTENT: {context}

Requirements:
1. The question field must be an actual question, not a statement.
2. The question field must use question wording (What, Why, How, Which, When).
3. The question field MUST end with "?". Nothing may appear after the question mark.
4. Never put A), B), C), or D) inside the question field.
5. You MUST generate exactly 4 options separately.
6. Options MUST be formatted:
   ["A) Option", "B) Option", "C) Option", "D) Option"]
7. Correct field must only contain A, B, C, or D.
8. Explanation must reference the content.
9. Return ONLY valid JSON.

Example:
{{
  "questions": [
    {{
      "question": "What does database normalization reduce?",
      "options": [
        "A) Redundancy",
        "B) Processing speed",
        "C) File size",
        "D) Network traffic"
      ],
      "correct": "A",
      "explanation": "Redundancy is correct because database normalization reduces duplicate data."
    }}
  ]
}}

Generate 1 question now:"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature":0.2,
                    "top_p":0.8,
                    "num_predict":2000,
                    "stop":["```"]
                }
)
            
            content = response['message']['content']

            print("RAW RESPONSE:")
            print(response)

            print(f"CONTENT LENGTH: {len(content)}")
            print(content)  
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                print("No JSON found in response")
                return {"questions": []}
            
            content = json_match.group()
            content = content.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(content)
                print(f"✅ JSON parsed successfully")
            except json.JSONDecodeError:
                try:
                    repaired = repair_json(content)
                    result = json.loads(repaired)
                    print(f"✅ JSON repaired successfully")
                except Exception as e:
                    print(f"⚠️ JSON repair failed: {e}")
                    return {"questions": []}
            
            if 'questions' not in result:
                if isinstance(result, dict) and 'question' in result:

                    # Repair missing options from bad LLM output
                    if 'options' not in result:
                        print("⚠️ LLM forgot options, rejecting question")
                        return {"questions": []}

                    result = {"questions": [result]}

                else:
                    return {"questions": []}
            
            valid_questions = []

            for q in result['questions']:

                if 'options' in q and len(q['options']) == 4:

                    # Normalize options first
                    q['options'] = normalize_options(q['options'])

                   # Reject statements pretending to be questions
                    if 'question' in q:
                        if not q['question'].strip().endswith('?'):
                            print("⚠️ LLM generated statement instead of question")
                            continue 

                    # Remove leaked options from question text
                    if 'question' in q:
                        q['question'] = re.split(
                            r'\s*\[A\)',
                            q['question'],
                            flags=re.IGNORECASE
                        )[0].strip()         

                    options_text = ' '.join(
                        str(opt)
                        for opt in q['options']
                    ).lower()

                    if 'correct answer' in options_text or 'wrong answer' in options_text:
                        print("Skipping placeholder question")
                        continue
                    
                    # Stage 1: Structure
                    if not validate_structure(q):

                        # Attempt question repair
                        q_text = q.get("question", "").strip()

                        if q_text and not q_text.endswith("?"):
                            q["question"] = f"What is true about: {q_text}?"

                            print("🔧 Repaired question format")

                        if not validate_structure(q):
                            print(f"⚠️ Skipping malformed question")
                            continue
                    
                    # Stage 2: Content - Grounding
                    if not validate_grounding(q, context):
                        print(f"⚠️ Skipping ungrounded question")
                        continue
                    
                    # Stage 2: Content - Topic relevance
                    correct_letter = q.get('correct', '')
                    correct_text = get_correct_text_from_options(q.get('options', []), correct_letter)
                    supporting_fact = _select_supporting_fact(correct_text, supporting_facts, fallback_context=context)
                    
                    if not is_relevant_to_topic(
                        q.get('question', ''),
                        topic,
                        correct_text,
                        supporting_fact
                    ):
                        print(f"⚠️ Skipping irrelevant question")
                        continue
                    
                    if question_equals_answer(q.get('question', ''), q.get('options', [])):
                        print(f"⚠️ Skipping question that restates answer")
                        continue
                    
                    # Stage 3: Semantic
                    if not validate_semantic(q):
                        print(f"⚠️ Skipping question due to semantic issues")
                        continue
                    
                    # Normalize correct field
                    if not normalize_and_validate_correct_field(q):
                        print(f"⚠️ Skipping question with unresolvable correct field")
                        continue

                    # Attach grounding fields
                    if not _attach_grounding_fields(q, correct_text, supporting_fact, context=context):
                        print(f"⚠️ Could not attach grounded supporting fact, using fallback")
                        q['supporting_fact'] = normalize_supporting_fact(context[:200] + "...")
                        q['explanation'] = f"{correct_text} is correct based on the content."
                    
                    # Quality scoring
                    facts = self.cache.get_facts(topic) if hasattr(self.cache, 'get_facts') else []
                    is_acceptable, score, scores = self._check_quality(q, facts)
                    
                    if not is_acceptable:
                        print(f"⚠️ Question scored {score:.2f} - below threshold, skipping")
                        continue
                    
                    q['_quality_score'] = score
                    q['_quality_scores'] = scores
                    
                    valid_questions.append(q)
            
            if valid_questions:
                valid_questions = filter_similar_questions(valid_questions, threshold=0.5)
            
            if not valid_questions:
                print("No valid LLM questions generated, using fact-based fallback...")
                
                extracted_concepts = []
                if supporting_facts:
                    for sf in supporting_facts:
                        if isinstance(sf, dict):
                            concept = sf.get('concept') or sf.get('correct_text') or sf.get('answer')
                            if not concept:
                                statement = sf.get('supporting_fact') or sf.get('statement') or sf.get('definition') or ""
                                if statement:
                                    concept_match = re.search(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\b', statement)
                                    if concept_match:
                                        concept = concept_match.group(1)
                            if concept and self._is_valid_concept(concept):
                                extracted_concepts.append(concept)
                
                if not extracted_concepts:
                    context_concepts = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\b', context)
                    for concept in context_concepts:
                        if self._is_valid_concept(concept):
                            extracted_concepts.append(concept)
                
                fallback = self._generate_fallback_question(context, topic, extracted_concepts)
                if fallback:
                    facts = self.cache.get_facts(topic) if hasattr(self.cache, 'get_facts') else []
                    is_acceptable, score, scores = self._check_quality(fallback, facts)
                    if is_acceptable:
                        fallback['_quality_score'] = score
                        fallback['_quality_scores'] = scores
                        fallback['concept'] = fallback.get('correct_text', '')
                        valid_questions = [fallback]
                    else:
                        print(f"⚠️ Fallback question scored {score:.2f} - below threshold, skipping")
                else:
                    print("⚠️ No concepts available, using generic fallback...")
                    generic_fallback = self._generate_generic_fallback(context, topic)
                    if generic_fallback:
                        valid_questions = [generic_fallback]
            
            return {"questions": valid_questions}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"questions": []}

    def generate_fill_blank(self, context: str, topic: str) -> Dict[str, Any]:
        """Generate a fill-in-the-blank question from context."""
        prompt = f"""You are a computer science tutor creating a fill-in-the-blank question.

TOPIC: {topic}
CONTENT: {context}

Requirements:
1. Question must use "_______" for the blank
2. The blank must be a KEY TERM or CONCEPT from the content
3. Include the correct answer
4. Include a short explanation
5. Return ONLY valid JSON

Example:
{{
  "questions": [
    {{
      "question": "Database normalization reduces _______.",
      "correct": "redundancy",
      "explanation": "Normalization reduces redundancy in the database."
    }}
  ]
}}

Generate 1 fill-in-the-blank question now:"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "top_p": 0.7,
                    "num_predict": 800
                }
            )
            
            content = response['message']['content']
            print(f"Fill-blank response: {len(content)} characters")
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                print("No JSON found")
                return {"questions": []}
            
            content = json_match.group()
            content = content.replace('```json', '').replace('```', '').strip()
            
            try:
                repaired = repair_json(content)
                result = json.loads(repaired)
                print(f"✅ Fill-blank JSON repaired successfully")
            except Exception as e:
                print(f"⚠️ Fill-blank JSON repair failed: {e}")
                content = content.replace("'", '"')
                content = re.sub(r',\s*}', '}', content)
                content = re.sub(r',\s*]', ']', content)
                try:
                    result = json.loads(content)
                except:
                    q_match = re.search(r'"question"\s*:\s*"([^"]+)"', content)
                    a_match = re.search(r'"correct"\s*:\s*"([^"]+)"', content)
                    e_match = re.search(r'"explanation"\s*:\s*"([^"]+)"', content)
                    if q_match and a_match:
                        result = {
                            "questions": [{
                                "question": q_match.group(1),
                                "correct": a_match.group(1),
                                "explanation": e_match.group(1) if e_match else "Based on the content."
                            }]
                        }
                    else:
                        return {"questions": []}
            
            if 'questions' not in result:
                return {"questions": []}
            
            valid = []
            for q in result['questions']:
                if 'question' in q and 'correct' in q and '_______' in q['question']:
                    if has_garbled_text(q['question']) or has_garbled_text(q['correct']):
                        print(f"⚠️ Skipping fill-blank with garbled text")
                        continue
                    
                    # Stronger grounding: correct answer must appear in context
                    if q['correct'].lower() in context.lower():
                        valid.append(q)
                        print(f"✅ Fill-blank question generated and grounded")
                    else:
                        print(f"⚠️ Fill-blank grounding failed: '{q['correct']}' not in context")
            
            return {"questions": valid}
            
        except Exception as e:
            print(f"Error generating fill-blank: {e}")
            return {"questions": []}


if __name__ == "__main__":
    context = """
    Cloud computing provides computing resources over the internet.
    Cloud storage allows users to store files remotely.
    Virtual machines create virtualized computing environments.
    Object storage stores data as objects instead of traditional files.
    Cloud databases provide managed database services through cloud platforms.
    """

    gen = QuizGenerator()

    result = gen.generate_questions(
        context,
        "Cloud Computing",
        count=5
    )

    print(json.dumps(result, indent=2))
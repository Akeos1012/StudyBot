# question_scorer.py
from typing import Dict, List, Any, Tuple, Optional
import re

# NEW: Import centralized option parser
from .utils.options_parser import (
    extract_option_text,
    extract_option_letter,
    format_option,
    get_correct_text_from_options,
    get_distractor_texts,
    normalize_options,
    validate_options_format
)

class QuestionScorer:
    """
    Scores questions on multiple quality metrics.
    Integrated with QuizGenerator to filter low-quality questions.
    """
    
    def __init__(self):
        self.weights = {
            'semantic_coherence': 0.35,
            'distractor_plausibility': 0.35,
            'type_consistency': 0.30
        }
        self.min_acceptable_score = 0.6  # Questions below this get rejected
    
    def score_question(self, question: Dict[str, Any], facts: List[Dict[str, Any]]) -> Tuple[float, Dict[str, float]]:
        """
        Score a question on quality metrics.
        Returns: (total_score, individual_scores)
        """
        scores = {
            'semantic_coherence': self._score_semantic(question, facts),
            'distractor_plausibility': self._score_distractors(question, facts),
            'type_consistency': self._score_types(question, facts)
        }
        
        total = sum(scores[k] * self.weights.get(k, 0) for k in scores)
        return total, scores
    
    def is_acceptable(self, question: Dict[str, Any], facts: List[Dict[str, Any]]) -> Tuple[bool, float, Dict[str, float]]:
        """
        Check if a question meets the quality threshold.
        Returns: (is_acceptable, total_score, individual_scores)
        """
        total, scores = self.score_question(question, facts)
        is_acceptable = total >= self.min_acceptable_score
        return is_acceptable, total, scores
    
    def _score_semantic(self, question: Dict, facts: List) -> float:
        """
        Score if question matches answer semantically.
        Checks: concept reference, word overlap, context alignment.
        
        FIX: Uses ONLY 'correct' field (not 'correct_answer')
        """
        # FIX: Use only 'correct' field - single source of truth
        answer = question.get('correct', '')
        if not answer:
            return 0.0
        
        answer = answer.lower()
        question_text = question.get('question', '').lower()
        
        # Level 1: Exact concept reference
        if answer in question_text:
            return 1.0
        
        # Level 2: Word overlap (significant words only)
        stop_words = {'the', 'this', 'that', 'with', 'from', 'have', 'will', 'they',
                      'what', 'when', 'where', 'which', 'their', 'there', 'about',
                      'concept', 'using', 'used', 'also', 'can', 'for', 'are', 'has'}
        
        answer_words = set(w for w in answer.split() if len(w) > 3 and w not in stop_words)
        question_words = set(w for w in question_text.split() if len(w) > 3 and w not in stop_words)
        
        if not answer_words:
            return 0.5  # Neutral if no significant words
        
        overlap = len(answer_words & question_words) / len(answer_words)
        return min(overlap * 1.5, 1.0)  # Boost slightly
    
    def _score_distractors(self, question: Dict, facts: List) -> float:
        """
        Score if distractors are plausible.
        Checks: same topic, not too similar to correct answer.
        
        FIX: Uses centralized option parser
        """
        # FIX: Use only 'correct' field - single source of truth
        correct_letter = question.get('correct', '')
        if not correct_letter:
            return 0.0
        
        options = question.get('options', [])
        
        # FIX: Use centralized parser
        correct_text = get_correct_text_from_options(options, correct_letter)
        
        # If we couldn't find it, fall back to using the letter as the answer
        if not correct_text:
            correct_text = correct_letter
        
        # FIX: Use centralized parser for distractors
        distractors = get_distractor_texts(options, correct_letter)
        
        if not distractors:
            return 0.0
        
        # Check 1: Distractors should be different lengths/words from correct
        correct_words = set(correct_text.lower().split())
        distractor_scores = []
        
        for d in distractors:
            d_words = set(d.lower().split())
            # High overlap = bad distractor (too similar)
            overlap = len(correct_words & d_words) / max(len(correct_words), 1)
            # Ideal overlap: 0.1-0.4 (some similarity but not too much)
            if 0.1 <= overlap <= 0.4:
                d_score = 1.0
            elif overlap < 0.1:
                d_score = 0.7  # Too different, might be too easy
            else:
                d_score = 0.3  # Too similar, confusing
            
            # Check length similarity (more plausible if similar length)
            len_diff = abs(len(correct_text) - len(d))
            if len_diff < 3:
                d_score *= 1.2
            elif len_diff < 6:
                d_score *= 1.0
            else:
                d_score *= 0.8
            
            distractor_scores.append(min(d_score, 1.0))
        
        # Average distractor scores
        avg_score = sum(distractor_scores) / len(distractor_scores)
        return min(avg_score, 1.0)
    
    def _score_types(self, question: Dict, facts: List) -> float:
        """
        Score if all options are the same type (concept_type).
        Uses concept_type from facts if available.
        
        FIX: Uses centralized option parser
        """
        options = question.get('options', [])
        if len(options) < 2:
            return 0.0
        
        # FIX: Use centralized parser
        option_texts = [extract_option_text(opt) for opt in options]
        
        # Build a mapping of concept -> type from facts
        fact_type_map = {}
        if facts:
            for f in facts:
                concept = f.get('concept', '').lower()
                concept_type = f.get('concept_type', 'concept')
                fact_type_map[concept] = concept_type
        
        # Get types for each option
        types = []
        for opt_text in option_texts:
            opt_lower = opt_text.lower()
            # Try exact match
            if opt_lower in fact_type_map:
                types.append(fact_type_map[opt_lower])
            else:
                # Try partial match (some option might have extra words)
                matched = False
                for concept, ctype in fact_type_map.items():
                    if concept in opt_lower or opt_lower in concept:
                        types.append(ctype)
                        matched = True
                        break
                if not matched:
                    # Unknown type - treat as neutral
                    types.append('unknown')
        
        # Check if all types are the same (or mostly the same)
        if not types:
            return 0.5
        
        # Count type frequencies
        type_counts = {}
        for t in types:
            type_counts[t] = type_counts.get(t, 0) + 1
        
        most_common = max(type_counts.values()) if type_counts else 0
        ratio = most_common / len(types)
        
        # Boost score if all same type, reduce if mixed
        if ratio == 1.0:
            return 1.0
        elif ratio >= 0.75:
            return 0.8
        elif ratio >= 0.5:
            return 0.5
        else:
            return 0.3
    
    def get_detailed_report(self, question: Dict[str, Any], facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a detailed quality report for a question.
        Useful for debugging and improvement.
        
        FIX: Uses centralized option parser
        """
        total, scores = self.score_question(question, facts)
        
        correct_letter = question.get('correct', '')
        options = question.get('options', [])
        
        # FIX: Use centralized parser
        correct_answer = get_correct_text_from_options(options, correct_letter)
        
        return {
            'total_score': total,
            'scores': scores,
            'is_acceptable': total >= self.min_acceptable_score,
            'question': question.get('question', '')[:100] + '...' if len(question.get('question', '')) > 100 else question.get('question', ''),
            'correct_answer': correct_answer,
            'correct_letter': correct_letter,
            'num_options': len(options),
        }
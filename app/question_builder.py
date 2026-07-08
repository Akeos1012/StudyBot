import random
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re

from .quiz_generator import build_consistent_explanation
from .schema import (
    normalize_fact, is_weak_concept, Fact, can_compare_concepts, 
    get_compatible_types, validate_concept_name, get_question_types_for_type,
    get_question_difficulty, get_type_hierarchy
)

class QuestionBuilder:
    def __init__(self):
        # Question type templates with ontology awareness
        self.question_templates = {
            "definition": [
                "What is {concept}?",
                "What does {concept} mean?",
                "What is the definition of {concept}?",
                "Which term matches: {definition}?",
                "What concept is defined as {definition}?",
                "In the context of {topic}, what is {concept}?",
                "How would you define {concept}?"
            ],
            "comparison": [
                "What is the main difference between {concept} and {distractor1}?",
                "How does {concept} differ from {distractor1}?",
                "Which statement best describes the relationship between {concept} and {distractor1}?",
                "What distinguishes {concept} from {distractor1}?",
                "Between {concept} and {distractor1}, which one {context}?"
            ],
            "application": [
                "In what scenario would {concept} be most useful?",
                "When would you use {concept}?",
                "Which situation best demonstrates the use of {concept}?",
                "What problem does {concept} solve?",
                "What is the primary use case for {concept}?"
            ],
            "scenario": [
                "A developer needs to {scenario}. Which concept fits best?",
                "You are building a system that requires {scenario}. Which concept should you use?",
                "A student is trying to understand {scenario}. Which concept explains this?",
                "Which concept would help solve: {scenario}?",
                "Given the task of {scenario}, which approach would you use?"
            ],
            "reverse_definition": [
                "What term is defined as: {definition}?",
                "Which concept matches this description: {definition}?",
                "What do we call {definition}?",
                "Fill in the blank: {definition} is known as _______."
            ]
        }
        
        # Question type weights by concept type (more nuanced)
        self.type_weights = {
            "algorithm": {"definition": 0.25, "comparison": 0.25, "application": 0.25, "scenario": 0.15, "reverse_definition": 0.10},
            "model": {"definition": 0.30, "comparison": 0.20, "application": 0.25, "scenario": 0.15, "reverse_definition": 0.10},
            "metric": {"definition": 0.35, "comparison": 0.20, "application": 0.20, "scenario": 0.10, "reverse_definition": 0.15},
            "system": {"definition": 0.25, "comparison": 0.20, "application": 0.30, "scenario": 0.15, "reverse_definition": 0.10},
            "process": {"definition": 0.25, "comparison": 0.15, "application": 0.30, "scenario": 0.20, "reverse_definition": 0.10},
            "concept": {"definition": 0.35, "comparison": 0.15, "application": 0.20, "scenario": 0.20, "reverse_definition": 0.10},
            "data_structure": {"definition": 0.30, "comparison": 0.20, "application": 0.25, "scenario": 0.15, "reverse_definition": 0.10},
            "framework": {"definition": 0.30, "comparison": 0.25, "application": 0.25, "scenario": 0.10, "reverse_definition": 0.10},
        }
        
        # Legacy clusters - kept for backward compatibility
        self.clusters = {
            "Database": {
                "querying": ["SQL", "SELECT", "JOIN", "WHERE", "GROUP BY", "ORDER BY"],
                "structure": ["DBMS", "Schema", "Table", "Indexing", "Primary Key", "Foreign Key"],
                "normalization": ["1NF", "2NF", "3NF", "Normalization", "Redundancy"],
                "transactions": ["ACID", "Transactions", "Commit", "Rollback"],
                "data_types": ["Integer", "String", "Boolean", "Float", "Date", "Time"]
            },
            "Algorithms": {
                "sorting": ["Bubble Sort", "Quick Sort", "Merge Sort", "Insertion Sort", "Selection Sort"],
                "searching": ["Binary Search", "Linear Search", "Hash Search"],
                "complexity": ["Time Complexity", "Space Complexity", "Big O", "Theta", "Omega"],
                "optimization": ["Memoization", "Dynamic Programming", "Greedy", "Divide and Conquer"],
                "data_structures": ["Array", "Linked List", "Stack", "Queue", "Tree", "Graph"]
            },
            "AI": {
                "learning_types": ["Supervised", "Unsupervised", "Reinforcement", "Semi-supervised"],
                "models": ["Deep Learning", "Neural Network", "CNN", "RNN", "Transformer"],
                "concepts": ["Backpropagation", "Gradient Descent", "Loss Function", "Activation"],
                "applications": ["Computer Vision", "NLP", "Speech Recognition", "Recommendation"]
            },
            "Programming": {
                "concepts": ["Variable", "Function", "Class", "Object", "Inheritance", "Polymorphism"],
                "paradigms": ["OOP", "Functional", "Procedural", "Declarative"],
                "best_practices": ["DRY", "KISS", "YAGNI", "SOLID"],
                "tools": ["Compiler", "Interpreter", "Debugger", "IDE"]
            }
        }
        
        self.fallback_cluster = ["Concept", "Topic", "Term", "Idea", "Approach"]
        
    def normalize_fact(self, fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a fact using shared schema"""
        return normalize_fact(fact)
    
    def get_concept_type(self, fact: Dict[str, Any]) -> str:
        """Get concept type from fact, with fallback detection"""
        if "concept_type" in fact and fact["concept_type"]:
            return fact["concept_type"]
        return "concept"
    
    def get_compatible_facts(self, facts: List[Dict[str, Any]], fact: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get only facts that are semantically compatible with this fact"""
        concept_type = self.get_concept_type(fact)
        compatible_types = get_compatible_types(concept_type)
        
        compatible = []
        for other in facts:
            if other["concept"] == fact["concept"]:
                continue
            other_type = self.get_concept_type(other)
            if other_type in compatible_types or other_type == concept_type:
                compatible.append(other)
        
        return compatible
    
    def score_distractor(self, correct: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Score a candidate distractor based on multiple factors.
        Higher score = better distractor.
        """
        score = 0.0
        
        # 1. Same type (mandatory - already filtered, but check anyway)
        if self.get_concept_type(correct) == self.get_concept_type(candidate):
            score += 1.0
        else:
            return 0.0
        
        # 2. Similar length (plausibility)
        len_diff = abs(len(correct['concept']) - len(candidate['concept']))
        if len_diff < 3:
            score += 0.3
        elif len_diff < 5:
            score += 0.1
        
        # 3. Semantic similarity (not too close, not too far)
        words1 = set(correct['concept'].lower().split())
        words2 = set(candidate['concept'].lower().split())
        
        if words1 and words2:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            # Sweet spot: some overlap but not too much
            if 0.1 < overlap < 0.6:
                score += 0.4
            elif overlap == 0:
                # Too different - might be too easy
                score += 0.1
            else:
                # Too similar - might confuse with correct
                score += 0.2
        
        # 4. Same topic bonus
        if correct.get('topic') == candidate.get('topic'):
            score += 0.2
        
        # 5. Different first letter (reduces guessing)
        if correct['concept'][0] != candidate['concept'][0]:
            score += 0.1
        
        return score
    
    def get_smart_distractors(self, facts: List[Dict[str, Any]], fact: Dict[str, Any], count: int = 3) -> List[str]:
        """
        Get semantically valid distractors using advanced scoring.
        Only returns distractors that are the same concept type.
        """
        # Get compatible facts (same or compatible types)
        compatible = self.get_compatible_facts(facts, fact)
        
        if len(compatible) < count:
            print(f"⚠️ Only {len(compatible)} compatible facts for '{fact['concept']}', using fallback")
            return self._get_topic_distractors(facts, fact["concept"], count)
        
        # Score each compatible fact
        scored = []
        for candidate in compatible:
            if candidate["concept"] == fact["concept"]:
                continue
            score = self.score_distractor(fact, candidate)
            scored.append((candidate, score))
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Select top distractors
        selected = []
        seen = set()
        for candidate, score in scored:
            concept = candidate["concept"]
            if concept not in seen:
                seen.add(concept)
                selected.append(concept)
                if len(selected) >= count:
                    break
        
        # If we don't have enough, fill with random
        if len(selected) < count:
            remaining = [f["concept"] for f in compatible if f["concept"] not in seen]
            random.shuffle(remaining)
            selected.extend(remaining[:count - len(selected)])
        
        return selected[:count]
    
    def generate_scenario(self, concept: str) -> str:
        """Generate a realistic scenario for a concept"""
        scenarios = {
            "SQL": "querying data from a large database",
            "Indexing": "speeding up database search queries",
            "Normalization": "organizing data to reduce duplication",
            "Binary Search": "finding an item in a sorted list",
            "Quick Sort": "sorting a large dataset efficiently",
            "Dynamic Programming": "optimizing complex problems with overlapping subproblems",
            "Memoization": "storing results of expensive function calls",
            "OOP": "organizing code into reusable objects",
            "SOLID": "writing maintainable and scalable code",
            "CNN": "processing image data for computer vision",
            "Gradient Descent": "optimizing machine learning models",
            "ACID": "ensuring reliable database transactions",
            "Supervised": "training models with labeled data",
            "Unsupervised": "finding patterns in unlabeled data",
            "Reinforcement": "training agents through rewards and punishments",
            "Big O": "analyzing algorithm efficiency",
            "Time Complexity": "measuring algorithm runtime",
            "Space Complexity": "measuring algorithm memory usage",
        }
        return scenarios.get(concept, f"understanding {concept}")
    
    def build_question(self, fact: Dict[str, Any], distractors: List[str]) -> Optional[Dict[str, Any]]:
        """Build a question from a fact and distractors with quality scoring"""
        concept = fact['concept']
        definition = fact['definition']
        topic = fact.get('topic', 'Unknown')
        concept_type = self.get_concept_type(fact)
        
        # Get recommended question types for this concept type
        recommended_types = get_question_types_for_type(concept_type)
        
        # Get weights for this type
        weights = self.type_weights.get(concept_type, self.type_weights.get("concept"))
        
        # Filter to recommended types
        available_types = [t for t in weights.keys() if t in recommended_types]
        if not available_types:
            available_types = ["definition"]
        
        # Avoid comparison if not enough distractors
        if len(distractors) < 2 and "comparison" in available_types:
            available_types.remove("comparison")
        
        # Normalize weights
        total_weight = sum(weights.get(t, 1.0) for t in available_types)
        question_weights = [weights.get(t, 1.0) / total_weight for t in available_types]
        
        # Select question type
        question_type = random.choices(available_types, weights=question_weights)[0]
        
        # Build question text based on type
        question_text = self._build_question_text(
            question_type, concept, definition, topic, distractors
        )
        
        # Build options
        options = [concept] + distractors[:3]
        random.shuffle(options)
        
        correct_letter = chr(65 + options.index(concept))
        formatted_options = [f"{chr(65 + i)}) {opt}" for i, opt in enumerate(options)]
        
        # Calculate difficulty
        difficulty = get_question_difficulty(concept_type, question_type)
        
        # Generate explanation
        supporting_fact = fact.get('supporting_fact') or fact.get('sentence') or fact.get('definition') or ""
        explanation = build_consistent_explanation(
            question_text=question_text,
            options=formatted_options,
            correct_letter=correct_letter,
            correct_text=concept,
            context=supporting_fact,
            facts=[{**fact, 'supporting_fact': supporting_fact}]
        )
        
        return {
            "question": question_text,
            "options": formatted_options,
            "correct_letter": correct_letter,
            "correct_answer": concept,
            "explanation": explanation,
            "source": fact.get('source', 'Unknown'),
            "difficulty": difficulty,
            "question_type": question_type,
            "concept": concept,
            "concept_type": concept_type,
            "topic": topic
        }
    
    def _build_question_text(self, question_type: str, concept: str, definition: str, 
                             topic: str, distractors: List[str]) -> str:
        """Build the question text based on type"""
        short_def = definition[:80] + ("..." if len(definition) > 80 else "")
        
        if question_type == "definition":
            templates = self.question_templates["definition"]
            template = random.choice(templates)
            return template.format(concept=concept, definition=short_def, topic=topic)
        
        elif question_type == "comparison":
            if distractors and len(distractors) >= 1:
                distractor = distractors[0]
                templates = self.question_templates["comparison"]
                template = random.choice(templates)
                # Generate context
                context = f"is more efficient" if random.random() > 0.5 else "is more commonly used"
                return template.format(concept=concept, distractor1=distractor, context=context)
            else:
                return f"What is the main difference between {concept} and others?"
        
        elif question_type == "application":
            templates = self.question_templates["application"]
            template = random.choice(templates)
            return template.format(concept=concept)
        
        elif question_type == "scenario":
            scenario = self.generate_scenario(concept)
            templates = self.question_templates["scenario"]
            template = random.choice(templates)
            return template.format(scenario=scenario)
        
        elif question_type == "reverse_definition":
            templates = self.question_templates["reverse_definition"]
            template = random.choice(templates)
            return template.format(definition=short_def)
        
        else:
            return f"What is {concept}?"
    
    def is_valid_concept(self, text: str) -> bool:
        """Check if a text is a valid concept using schema validation"""
        if not text or len(text) < 3:
            return False
        return validate_concept_name(text)
    
    def build_quiz(self, facts: List[Dict[str, Any]], count: int = 3) -> List[Dict[str, Any]]:
        """Build a quiz from a list of facts with ontology-aware question generation"""
        # Normalize all facts first
        normalized_facts = []
        for f in facts:
            normalized = self.normalize_fact(f)
            if normalized:
                normalized_facts.append(normalized)
        
        if not normalized_facts:
            print("⚠️ No valid facts after normalization")
            return []
        
        facts = normalized_facts
        topic = facts[0].get('topic', 'Unknown') if facts else 'Unknown'
        
        # Store all facts for context
        for f in facts:
            f['_all_facts'] = facts
        
        # Filter out invalid facts using schema validation
        valid_facts = []
        for f in facts:
            concept = f.get('concept', '')
            if self.is_valid_concept(concept):
                valid_facts.append(f)
            else:
                print(f"⚠️ Filtering invalid concept: '{concept}'")
        
        # Filter out weak concepts
        weak_filtered = []
        for f in valid_facts:
            concept = f.get('concept', '')
            if not is_weak_concept(concept):
                weak_filtered.append(f)
            else:
                print(f"⚠️ Filtering weak concept: '{concept}'")
        
        valid_facts = weak_filtered
        
        print(f"🔍 Valid facts after filtering: {len(valid_facts)} out of {len(facts)}")
        
        if len(valid_facts) < count:
            count = len(valid_facts)
            print(f"⚠️ Not enough valid facts, reducing count to {count}")
        
        if count == 0:
            return []
        
        # Group facts by concept type for better distribution
        facts_by_type = defaultdict(list)
        for f in valid_facts:
            concept_type = self.get_concept_type(f)
            facts_by_type[concept_type].append(f)
        
        # Print type distribution
        print(f"📊 Concept type distribution:")
        for type_name, type_facts in facts_by_type.items():
            print(f"  {type_name}: {len(type_facts)} facts")
        
        # Prevent duplicate concepts
        used_concepts = set()
        unique_facts = []
        for f in valid_facts:
            concept_lower = f['concept'].lower()
            if concept_lower not in used_concepts:
                used_concepts.add(concept_lower)
                unique_facts.append(f)
        
        # Prioritize facts with good distractor candidates
        scored_facts = []
        for f in unique_facts:
            compatible = self.get_compatible_facts(valid_facts, f)
            score = len(compatible)  # More compatible facts = better chance for good distractors
            scored_facts.append((f, score))
        
        scored_facts.sort(key=lambda x: x[1], reverse=True)
        selected_facts = [f for f, _ in scored_facts[:count]]
        
        questions = []
        for fact in selected_facts:
            concept = fact['concept']
            concept_type = self.get_concept_type(fact)
            
            # Use ontology-aware distractor selection with scoring
            distractors = self.get_smart_distractors(valid_facts, fact, count=3)
            
            if len(distractors) >= 2:
                question = self.build_question(fact, distractors)
                if question:
                    questions.append(question)
                    print(f"✅ Generated '{concept_type}' question for '{concept}' with {len(distractors)} distractors")
            else:
                print(f"⚠️ Not enough compatible distractors for '{concept}' (type: {concept_type}), skipping")
        
        return questions
    
    def _get_topic_distractors(self, facts: List[Dict[str, Any]], concept: str, count: int = 3) -> List[str]:
        """Fallback: get distractors from same topic"""
        candidates = []
        for f in facts:
            candidate = f.get('concept', '')
            if candidate and candidate != concept and self.is_valid_concept(candidate):
                candidates.append(candidate)
        
        seen = set()
        clean_candidates = []
        for c in candidates:
            if c.lower() not in seen:
                seen.add(c.lower())
                clean_candidates.append(c)
        
        random.shuffle(clean_candidates)
        return clean_candidates[:count]
    
    def score_question_quality(self, question: Dict[str, Any]) -> Dict[str, float]:
        """Score the quality of a generated question"""
        scores = {}
        
        # 1. Semantic coherence - does question match answer?
        answer = question['correct_answer'].lower()
        question_text = question['question'].lower()
        if answer in question_text:
            scores['semantic_coherence'] = 1.0
        else:
            answer_words = set(answer.split())
            question_words = set(question_text.split())
            overlap = len(answer_words & question_words) / max(len(answer_words), 1)
            scores['semantic_coherence'] = min(overlap * 2, 1.0)
        
        # 2. Distractor quality
        options = [opt.split(') ')[1] for opt in question['options']]
        distractors = [o for o in options if o != question['correct_answer']]
        if distractors:
            # Check if distractors are same type
            correct_type = question.get('concept_type', 'unknown')
            # This would need type lookup - simplified
            scores['distractor_quality'] = 0.8
        else:
            scores['distractor_quality'] = 0.0
        
        # 3. Difficulty appropriateness
        scores['difficulty_appropriateness'] = min(question.get('difficulty', 0.5) * 2, 1.0)
        
        # 4. Overall
        scores['overall'] = sum(scores.values()) / len(scores)
        
        return scores


if __name__ == "__main__":
    from fact_cache import FactCache
    
    cache = FactCache()
    cache.load()
    
    builder = QuestionBuilder()
    facts = cache.get_facts("Algorithms")
    
    if facts:
        questions = builder.build_quiz(facts, count=3)
        
        print("\n📝 Generated Quiz:")
        for i, q in enumerate(questions):
            print(f"\nQ{i+1}: {q['question']}")
            print(f"Options: {q['options']}")
            print(f"Correct: {q['correct_letter']} ({q['correct_answer']})")
            print(f"Difficulty: {q.get('difficulty', 0.5):.2f}")
            print(f"Question Type: {q.get('question_type', 'unknown')}")
            print(f"Concept Type: {q.get('concept_type', 'unknown')}")
            
            # Score the question
            scores = builder.score_question_quality(q)
            print(f"Quality Score: {scores['overall']:.2f}")
            print(f"Explanation: {q['explanation'][:100]}...")
    else:
        print("No facts found for Algorithms")
import json
import re

from difflib import SequenceMatcher
from json_repair import repair_json
from typing import List, Dict, Any, Optional, Tuple

from .question_cache import QuestionCache
from .question_scorer import QuestionScorer
from .question_similarity import is_similar_to_pool
from .question_prompt import build_fact_question_prompt
from .explanation_validator import validate_explanation
from .question_validator import is_duplicate_question
from ..rag.fact_cache import FactCache
from .llm_parser import LLMParser
from .llm_client import LLMClient
from app.utils.performance_profiler import profile_time

from .question_semantic import (
    validate_semantic,
    has_garbled_text,
)

from .validation_logger import log_validation_failure

from .options_parser import (
    normalize_options,
    extract_option_letter,
    extract_option_text,
    get_correct_text_from_options,
)

from .question_grounding import (
    validate_grounding,
    normalize_supporting_fact,
    attach_grounding_fields,
    select_supporting_fact,
    question_equals_answer,
)

from .question_fallback import (
    generate_fallback_question,
    generate_generic_fallback,
    is_valid_concept,
)

from .question_validator import (
    validate_structure,
    normalize_and_validate_correct_field,
    validate_question_focus,
    is_relevant_to_topic,
)

from .domain_validator import validate_domain_correctness
from ..rag.fact_cleaner import clean_text
from ..rag.retriever import Retriever

# ============ CONSTANTS ============
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

# ============ UTILITY FUNCTIONS ============



def filter_similar_questions(
    questions: List[Dict[str, Any]],
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """Remove duplicate questions and similar answers."""

    if not questions:
        return []

    unique = []
    seen_answers = []

    for q in questions:
        correct_letter = q.get('correct', '')
        options = q.get('options', [])

        correct_text = get_correct_text_from_options(
            options,
            correct_letter
        ).lower()

        # Check answer similarity
        duplicate_answer = False

        if correct_text:
            for seen in seen_answers:
                similarity = SequenceMatcher(
                    None,
                    correct_text,
                    seen
                ).ratio()

                if similarity > 0.90 and is_similar_to_pool(q, unique, 0.85):
                    duplicate_answer = True
                    break

        if duplicate_answer:
            print(f"❌ Removed duplicate answer: {q['question']}")
            continue

        # Check question similarity
        if is_similar_to_pool(q, unique, threshold):
            print(f"❌ Removed similar question: {q['question']}")
            continue

        unique.append(q)

        if correct_text:
            seen_answers.append(correct_text)

    return unique


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

# ============ QUIZ GENERATOR CLASS ============

class QuizGenerator:
    def __init__(
        self,
        model: str = "qwen2.5:3b",
        min_quality_score: float = 0.6
    ):
        self.model = model
        self.llm = LLMClient(model=model)
     
        # Cache of previously generated questions
        self.cache = QuestionCache()

        # Knowledge base
        self.fact_cache = FactCache()
        self.fact_cache.load()
        print("FACT CACHE TYPE:", type(self.fact_cache))
        print("HAS get_facts:", hasattr(self.fact_cache, "get_facts"))
        print("HAS get_topics:", hasattr(self.fact_cache, "get_topics"))

        # Fact retriever
        self.retriever = Retriever(self.fact_cache)

        self.parser = LLMParser()
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
        
        prompt = build_fact_question_prompt(
            fact_for_prompt,
            answer,
            topic
        )

        try:
            content = self.llm.generate(prompt)

            print(f"Fact-based response received: {len(content)} characters")
            result = self.parser.parse(content)

            if result is None:
                log_validation_failure(None, "json_parse", "Failed to parse LLM response")
                return None

            questions = self.parser.extract_questions(result)

            if not questions:
                log_validation_failure(None, "json_parse", "No questions found")
                return None

            question = questions[0]

            # Format options immediately
            options = question.get('options', [])

            if options:
                question['options'] = normalize_options(options)


            # ===== VALIDATION PIPELINE =====

                # Stage 1: Structure
                if not validate_structure(question):
                    log_validation_failure(
                        question,
                        "structure",
                        "Structure validation failed"
                    )
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
                    log_validation_failure(
                        question,
                        "semantic",
                        "Semantic validation failed"
                    )
                    return None
                
                if not validate_domain_correctness(question):
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
                
                if not attach_grounding_fields(question, correct_text, sanitized_supporting_fact, context=fact):
                    print("⚠️ Could not attach grounded explanation for fact-based question")
                    # Continue - we already have a fallback in _attach_grounding_fields
                
                    # Quality scoring
                    print("Retriever cache type:", type(self.retriever.fact_cache))
                    print("Retriever has get_facts:", hasattr(self.retriever.fact_cache, "get_facts"))

                    facts = self.retriever.retrieve(
                        topic=topic,
                        limit=20
                    )
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
10. Randomize the correct answer position.
11. Do not always place the correct answer in option A.

Example:
{{
  "questions": [
    {{
      "question": "What does database normalization reduce?",
      "options": [
        "A) Processing speed",
        "B) File size",
        "C) Redundancy",
        "D) Network traffic"
      ],
      "correct": "C",
      "explanation": "Redundancy is correct because database normalization reduces duplicate data."
    }}
  ]
}}

Generate 5 questions now:"""

        try:
            content = self.llm.generate(
                prompt,
                temperature=0.2,
                top_p=0.8,
                num_predict=2000,
                stop=["```"]
            )

            print("RAW RESPONSE:")
            print(content)

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
                print("✅ JSON parsed successfully")
            except json.JSONDecodeError:
                try:
                    repaired = repair_json(content)
                    result = json.loads(repaired)
                except Exception as e:
                    print(f"⚠️ JSON repair failed: {e}")
                    return {"questions": []}
            
                # Normalize every valid JSON format into:
                # {"questions": [...]}

                if isinstance(result, list):
                    result = {"questions": result}

                elif isinstance(result, dict):

                    if "questions" in result:
                        pass

                    elif "question" in result:

                        if "options" not in result:
                            print("⚠️ LLM forgot options, rejecting question")
                            return {"questions": []}

                        result = {"questions": [result]}

                    else:
                        print("⚠️ Unknown JSON format")
                        return {"questions": []}

                else:
                    print("⚠️ Invalid JSON root")
                    return {"questions": []}
            
            valid_questions = []

            for q in result['questions']:

                if 'options' in q and len(q['options']) == 4:

                    # Normalize options first
                    q['options'] = normalize_options(q['options'])
                    # Reject invented layer taxonomy
                    if any(
                        is_layer_phrase(q.get("question", "")) or
                        is_layer_phrase(str(option))
                        for option in q.get("options", [])
                    ):
                        print("⚠️ Skipping invented layer taxonomy")
                        continue

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
                            print("⚠️ Skipping malformed question")
                            continue

                    # Get answer text first
                    correct_letter = q.get('correct', '')
                    correct_text = get_correct_text_from_options(
                        q.get('options', []),
                        correct_letter
                    )

                    supporting_fact = select_supporting_fact(
                        correct_text,
                        supporting_facts,
                        fallback_context=context
                    )

                    # Stage 2: Content - Grounding
                    if not validate_grounding(
                        q,
                        supporting_fact
                    ):
                        log_validation_failure(
                            q,
                            "grounding",
                            "Question answer not supported by source content"
                        )
                        print("⚠️ Skipping ungrounded question")
                        continue
                    
                    if not is_relevant_to_topic(
                        q.get('question', ''),
                        topic,
                        correct_text,
                        supporting_fact
                    ):
                        print("⚠️ Skipping irrelevant question")
                        continue
                    
                    if question_equals_answer(q.get('question', ''), q.get('options', [])):
                        print("⚠️ Skipping question that restates answer")
                        continue
                    
                    # Stage 3: Semantic
                    if not validate_semantic(q):
                        print("⚠️ Skipping question due to semantic issues")
                        continue

                    # Stage 3: Domain correctness
                    if not validate_domain_correctness(q):
                        log_validation_failure(
                            q,
                            "domain",
                            "Question contains incorrect domain knowledge"
                        )
                        print("⚠️ Skipping domain incorrect question")
                        continue

                    # Stage 4: Explanation validation
                    if not validate_explanation(q, supporting_fact):
                        print("⚠️ Skipping invalid explanation")
                        continue
                    
                    # Normalize correct field
                    if not normalize_and_validate_correct_field(q):
                        log_validation_failure(
                            q,
                            "correct_field",
                            "Correct answer field could not be matched to options"
                        )
                        print("⚠️ Skipping question with unresolvable correct field")
                        continue

                    # Attach grounding fields
                    if not attach_grounding_fields(
                        q,
                        correct_text,
                        supporting_fact,
                        context=context
                    ):
                        print("⚠️ Could not attach grounded supporting fact, using fallback")
                        q['supporting_fact'] = normalize_supporting_fact(context[:200] + "...")
                        q['explanation'] = f"{correct_text} is correct based on the content."

                    # Clean LLM-generated text before caching
                    for field in [
                        "question",
                        "explanation",
                        "correct_text",
                        "supporting_fact"
                    ]:
                        if q.get(field):
                            q[field] = clean_text(q[field])

                    # Required for cache validation
                    q['fact_id'] = f"generated_{abs(hash(q.get('question', '')))}"
                    q['source_note'] = "llm_generated"
                    
                    # Quality scoring
                    facts = self.retriever.retrieve(
                        topic=topic,
                        limit=20
                    )
                    is_acceptable, score, scores = self._check_quality(q, facts)
                    
                    if not is_acceptable:
                        print(f"⚠️ Question scored {score:.2f} - below threshold, skipping")
                        continue
                    
                    q['_quality_score'] = score
                    q['_quality_scores'] = scores


                    # ===== Duplicate Question Check =====
                    existing_questions = [
                        item["question"]
                        for item in valid_questions
                    ]


                    if is_duplicate_question(
                        q["question"],
                        existing_questions
                    ):
                        print(
                            "⚠️ Duplicate question skipped:",
                            q["question"]
                        )
                        continue


                    valid_questions.append(q)
            
            if valid_questions:
                valid_questions = filter_similar_questions(
                    valid_questions,
                    threshold=0.90
                )
            
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
                            if concept and is_valid_concept(concept):
                                extracted_concepts.append(concept)
                
                if not extracted_concepts:
                    context_concepts = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\b', context)
                    for concept in context_concepts:
                        if is_valid_concept(concept):
                            extracted_concepts.append(concept)
                
                fallback = generate_fallback_question(context, topic, extracted_concepts, supporting_facts)
                if fallback:
                    facts = self.retriever.retrieve(
                        topic=topic,
                        limit=20
                    )
                    is_acceptable, score, scores = self._check_quality(fallback, facts)
                    if is_acceptable:
                        fallback['_quality_score'] = score
                        fallback['_quality_scores'] = scores
                        fallback['concept'] = fallback.get('correct_text', '')
                        for field in [
                            "question",
                            "explanation",
                            "correct_text",
                            "supporting_fact"
                        ]:
                            if fallback.get(field):
                                fallback[field] = clean_text(fallback[field])
                        valid_questions = [fallback]
                    else:
                        print(f"⚠️ Fallback question scored {score:.2f} - below threshold, skipping")
                else:
                    print("⚠️ No concepts available, using generic fallback...")
                    generic_fallback = generate_generic_fallback(context, topic)
                    if generic_fallback:
                        valid_questions = [generic_fallback]
            
            return {"questions": valid_questions}
            
        except Exception:
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
            content = self.llm.generate(
                prompt,
                temperature=0.3,
                top_p=0.7,
                num_predict=800
            )

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
                print("✅ Fill-blank JSON repaired successfully")
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
                        print("⚠️ Skipping fill-blank with garbled text")
                        continue
                    
                    # Stronger grounding: correct answer must appear in context
                    if q['correct'].lower() in context.lower():
                        valid.append(q)
                        print("✅ Fill-blank question generated and grounded")
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
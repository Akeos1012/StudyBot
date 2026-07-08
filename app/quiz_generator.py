import ollama
import json
import re
from difflib import SequenceMatcher
from json_repair import repair_json

from .fact_extractor import FactExtractor
from .question_cache import QuestionCache
from .question_scorer import QuestionScorer

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

# ============ UTILITY FUNCTIONS ============

def has_garbled_text(text: str) -> bool:
    """Check if text contains non-printable or control characters"""
    if not isinstance(text, str):
        return True
    if re.search(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', text):
        return True
    return False

def is_similar(q1: str, q2: str, threshold: float = 0.6) -> bool:
    """Check if two questions are too similar"""
    return SequenceMatcher(None, q1.lower(), q2.lower()).ratio() > threshold

def filter_similar_questions(questions, threshold=0.6):
    """Remove similar questions - check both text and answer"""
    unique = []
    seen_answers = set()
    
    for q in questions:
        correct_letter = q.get('correct', '')
        options = q.get('options', [])
        
        # FIX: Use centralized parser
        correct_text = get_correct_text_from_options(options, correct_letter).lower()
        
        if correct_text and correct_text in seen_answers:
            print(f"⚠️ Skipping duplicate answer: '{correct_text}'")
            continue
        
        q_text = q.get('question', '')
        is_duplicate = False
        for u in unique:
            u_text = u.get('question', '')
            q_words = set(q_text.lower().split())
            u_words = set(u_text.lower().split())
            overlap = len(q_words.intersection(u_words))
            min_len = min(len(q_words), len(u_words))
            if min_len > 0 and overlap / min_len > 0.5:
                is_duplicate = True
                print(f"Found duplicate (word overlap): '{q_text[:40]}' vs '{u_text[:40]}'")
                break
            
            ratio = SequenceMatcher(None, q_text.lower(), u_text.lower()).ratio()
            if ratio > threshold:
                is_duplicate = True
                print(f"Found duplicate (ratio): '{q_text[:50]}' vs '{u_text[:50]}' (ratio: {ratio:.2f})")
                break
        
        if not is_duplicate:
            unique.append(q)
            if correct_text:
                seen_answers.add(correct_text)
    
    return unique

# ============ STAGE 1: STRUCTURE VALIDATION ============

def validate_structure(question: dict) -> bool:
    """Check that the question has all required fields with correct types."""
    required = ['question', 'options', 'correct', 'explanation']
    for field in required:
        if field not in question:
            print(f"⚠️ Missing field: {field}")
            return False
    
    if not isinstance(question['options'], list) or len(question['options']) != 4:
        print(f"⚠️ Options must be a list of 4 items")
        return False
    
    q_text = question['question'].strip()
    if not q_text.endswith('?'):
        print(f"⚠️ Question doesn't end with '?'")
        return False
    
    if len(q_text) > 250:
        print(f"⚠️ Question too long ({len(q_text)} chars)")
        return False
    
    if re.search(r'\b[A-D]\)', q_text):
        print(f"⚠️ Question contains leaked option markers")
        return False
    
    return True

# ============ STAGE 2: CONTENT VALIDATION ============

def validate_grounding(question: dict, context: str, supporting_fact: str = "") -> bool:
    """
    Check if the correct answer is grounded in the note-backed context.
    Uses flexible matching: exact, partial, and keyword-based.
    """
    if 'correct' not in question or 'options' not in question:
        return False
    
    correct_letter = question['correct']
    options = question['options']
    
    # FIX: Use centralized parser
    correct_text = get_correct_text_from_options(options, correct_letter)
    
    if not correct_text:
        return False
    
    grounding_context = supporting_fact or context or ""
    if not grounding_context:
        return False

    context_lower = grounding_context.lower()
    correct_lower = correct_text.lower()
    correct_words = correct_lower.split()
    
    # Level 1: Exact match
    if correct_lower in context_lower:
        print(f"✅ Grounding: exact match for '{correct_text}'")
        return True
    
    # Level 2: Any significant word appears in context
    stop_words = {'the', 'this', 'that', 'with', 'from', 'have', 'will', 'they', 
                  'what', 'when', 'where', 'which', 'their', 'there', 'about',
                  'concept', 'using', 'used', 'also', 'can', 'for', 'are', 'has'}
    
    for word in correct_words:
        if len(word) > 3 and word not in stop_words:
            if word in context_lower:
                print(f"✅ Grounding: found keyword '{word}' from '{correct_text}'")
                return True
    
    # Level 3: Multi-word phrase matching
    if len(correct_words) >= 2:
        sentences = re.split(r'[.!?\n]', context_lower)
        for sentence in sentences:
            sentence_words = set(sentence.split())
            matched_words = [w for w in correct_words if w in sentence_words]
            if len(matched_words) >= len(correct_words) * 0.6:
                print(f"✅ Grounding: phrase match for '{correct_text}' in sentence")
                return True
    
    print(f"⚠️ Grounding failed: '{correct_text}' not found in context")
    return False

def is_relevant_to_topic(question: str, topic: str) -> bool:
    """Check if a question is actually relevant to the topic using shared keywords"""
    topic_lower = topic.lower()
    question_lower = question.lower()
    
    fact_extractor = FactExtractor()
    topic_keywords = fact_extractor._get_topic_keywords(topic_lower)
    
    if topic_lower == 'algorithms':
        topic_keywords.extend([
            'memoization', 'recursion', 'amortized', 'big o', 
            'dynamic programming', 'complexity', 'optimization',
            'sorting', 'searching', 'iteration', 'divide and conquer',
            'greedy', 'backtracking', 'graph', 'tree', 'heap'
        ])
    
    for keyword in topic_keywords:
        if keyword in question_lower:
            return True
    
    print(f"⚠️ No topic keywords found in question: {question[:50]}...")
    return False

def question_equals_answer(question_text: str, options: list) -> bool:
    """Check if the question is just restating the correct answer"""
    q_clean = question_text.strip().lower().rstrip('.?')
    for opt in options:
        # FIX: Use centralized parser
        opt_text = extract_option_text(opt).lower().rstrip('.')
        if opt_text and (opt_text in q_clean or q_clean in opt_text) and len(opt_text) > 20:
            print(f"⚠️ Option text duplicates question text: '{opt_text[:40]}...'")
            return True
    return False


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
    if len(cleaned.split()) > 24:
        cleaned = ' '.join(cleaned.split()[:24]).rstrip(' .')
    if cleaned.lower().startswith(('how ', 'why ', 'what ', 'when ', 'where ', 'conclusion', 'summary', 'overview', 'references')):
        return ""
    return cleaned


def has_redundant_options(options):
    """Check if one option contains another option (distractor independence)"""
    # FIX: Use centralized parser
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

def build_consistent_explanation(question_text: str, options: list, correct_letter: str, correct_text: str, context: str = "", facts: list = None) -> str:
    """Build a short explanation from a single selected supporting fact."""
    if not correct_text:
        return ""

    correct_text = correct_text.strip()
    if not correct_text:
        return ""

    if facts:
        for fact in facts:
            supporting_fact = normalize_supporting_fact(str(fact.get('supporting_fact') or fact.get('sentence') or fact.get('definition') or '').strip())
            if not supporting_fact:
                continue
            supporting_lower = supporting_fact.lower()
            correct_lower = correct_text.lower()
            if correct_lower in supporting_lower or any(word in supporting_lower for word in [w for w in re.split(r'[^a-z0-9]+', correct_lower) if len(w) > 2]):
                explanation = f"{correct_text} is correct because {supporting_fact}"
                if len(explanation.split()) <= 24:
                    return explanation

    if context:
        cleaned_context = normalize_supporting_fact(context)
        if cleaned_context:
            explanation = f"{correct_text} is correct because {cleaned_context}"
            if len(explanation.split()) <= 24:
                return explanation

    return ""


def _select_supporting_fact(correct_text: str, supporting_facts: list = None, fallback_context: str = "") -> str:
    """Pick the strongest note-backed supporting sentence for a question."""
    if not supporting_facts:
        return normalize_supporting_fact(fallback_context or "")

    if isinstance(supporting_facts, str):
        return normalize_supporting_fact(supporting_facts)

    correct_words = [w for w in re.split(r'[^a-z0-9]+', (correct_text or '').lower()) if len(w) > 2]
    for fact in supporting_facts:
        if isinstance(fact, dict):
            candidate = fact.get('supporting_fact') or fact.get('sentence') or fact.get('definition') or ""
        else:
            candidate = str(fact)
        if not candidate:
            continue
        candidate = normalize_supporting_fact(candidate)
        if not candidate:
            continue
        candidate_lower = candidate.lower()
        if correct_text and correct_text.lower() in candidate_lower:
            return candidate
        if correct_words and any(word in candidate_lower for word in correct_words):
            return candidate

    for fact in supporting_facts:
        if isinstance(fact, dict):
            candidate = fact.get('supporting_fact') or fact.get('sentence') or fact.get('definition') or ""
        else:
            candidate = str(fact)
        candidate = normalize_supporting_fact(candidate)
        if candidate:
            return candidate

    return normalize_supporting_fact(fallback_context or "")


def _attach_grounding_fields(question: dict, correct_text: str, supporting_fact: str, context: str = "") -> bool:
    """Attach correct_text/supporting_fact/explanation to a question and reject unsupported ones."""
    if not question or not isinstance(question, dict):
        return False

    question['correct_text'] = correct_text or ""
    question['supporting_fact'] = normalize_supporting_fact(supporting_fact or "")

    if not correct_text or not question['supporting_fact']:
        question['explanation'] = ""
        return False

    explanation = build_consistent_explanation(
        question_text=question.get('question', ''),
        options=question.get('options', []),
        correct_letter=question.get('correct', ''),
        correct_text=correct_text,
        context=supporting_fact,
        facts=[{'supporting_fact': supporting_fact}]
    )

    if not explanation:
        question['explanation'] = ""
        return False

    question['explanation'] = explanation
    return True


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

    # Strongly reject explanations that mention a different option more clearly.
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

    # Reject generic explanations that only say the answer is correct without grounding it.
    if len(correct_overlap := set(explanation_words) & set(correct_words)) < 1:
        print(f"⚠️ Explanation doesn't mention the correct answer text: '{correct_text}'")
        return True

    # Reject explanations that are only a restatement of the source fact without tying it to the chosen option.
    generic_phrases = [
        "the correct answer is",
        "because it is the correct answer",
        "because it is correct",
        "this option is correct",
        "this answer is correct",
        "the answer is"
    ]
    if any(phrase in explanation for phrase in generic_phrases):
        if len(correct_overlap) < 2:
            print(f"⚠️ Explanation is too generic to support '{correct_text}'")
            return True

    return False

# ============ STAGE 3: SEMANTIC VALIDATION ============

def validate_semantic(question: dict) -> bool:
    """Check semantic quality of the question."""
    
    if has_redundant_options(question.get('options', [])):
        print(f"⚠️ Redundant options detected")
        return False
    
    if explanation_contradicts_answer(question):
        print(f"⚠️ Explanation contradicts answer")
        return False
    
    if has_garbled_text(question['question']):
        print(f"⚠️ Garbled text in question")
        return False
    
    for opt in question['options']:
        if has_garbled_text(str(opt)):
            print(f"⚠️ Garbled text in option")
            return False
    
    return True

# ============ NORMALIZE CORRECT FIELD ============

def normalize_and_validate_correct_field(question: dict) -> bool:
    """
    Ensure 'correct' is exactly one of A/B/C/D.
    This is the SINGLE SOURCE OF TRUTH for correct answer formatting.
    """
    correct = str(question.get('correct', '')).strip()
    options = question.get('options', [])
    
    if not options or len(options) != 4:
        print(f"⚠️ Invalid options count for correct field validation")
        return False
    
    # Case 1: Already a letter
    if correct in ['A', 'B', 'C', 'D']:
        question['correct'] = correct
        return True
    
    # Case 2: Letter with punctuation (e.g., "A)", "A.", "A -")
    letter_match = re.match(r'^([A-D])\s*[\)\.\-\s]', correct)
    if letter_match:
        question['correct'] = letter_match.group(1)
        return True
    
    # Case 3: Full text - find which option matches
    for opt in options:
        opt_letter = extract_option_letter(opt)
        opt_text = extract_option_text(opt).lower()
        if opt_text == correct.lower():
            question['correct'] = opt_letter
            return True
    
    # Case 4: Fuzzy matching
    for opt in options:
        opt_text = extract_option_text(opt).lower()
        if correct.lower() in opt_text or opt_text in correct.lower():
            opt_letter = extract_option_letter(opt)
            if opt_letter:
                question['correct'] = opt_letter
                print(f"✅ Fuzzy matched '{correct}' to '{opt_text}' -> {opt_letter}")
                return True
    
    print(f"⚠️ Could not resolve 'correct' field '{correct}' to a valid letter")
    return False

# ============ QUIZ GENERATOR CLASS ============

class QuizGenerator:
    def __init__(self, model="deepseek-r1:1.5b", min_quality_score: float = 0.6):
        self.model = model
        self.cache = QuestionCache()
        self.scorer = QuestionScorer()
        self.min_quality_score = min_quality_score
        
    def generate_with_retry(self, fact: str, answer: str, topic: str, max_attempts: int = 3, fact_data: dict = None):
        """Generate a question with retries if validation fails"""
        for attempt in range(max_attempts):
            question = self.generate_from_fact(fact, answer, topic, fact_data=fact_data)
            if question:
                print(f"✅ Question generated on attempt {attempt+1}")
                return question
            print(f"⚠️ Attempt {attempt+1}/{max_attempts} failed, retrying...")
        print(f"⚠️ All {max_attempts} attempts failed for this fact, skipping")
        return None
    
    def _check_quality(self, question: dict, facts: list = None) -> tuple:
        """
        Check question quality using QuestionScorer.
        Returns: (is_acceptable, score, scores_dict)
        """
        if facts is None:
            facts = []
        
        is_acceptable, score, scores = self.scorer.is_acceptable(question, facts)
        
        if not is_acceptable:
            print(f"⚠️ Quality check failed: score={score:.2f} (threshold={self.min_quality_score})")
            print(f"   Scores: {scores}")
        else:
            print(f"✅ Quality check passed: score={score:.2f}")
        
        return is_acceptable, score, scores
        
    def generate_from_fact(self, fact: str, answer: str, topic: str, fact_data: dict = None):
        """Generate a question from a single fact with coherence checking"""
        fact_data = fact_data or {}
        supporting_fact = fact_data.get('supporting_fact') or fact_data.get('sentence') or fact_data.get('definition') or fact or ""
        
        prompt = f"""You are a computer science tutor. Create 1 multiple-choice question based on this fact:

FACT: {fact}
CORRECT ANSWER: {answer}
TOPIC: {topic}

CRITICAL RULES:
- The question field MUST end with a question mark (?)
- The correct field MUST be ONLY one letter: "A", "B", "C", or "D"
- Do NOT put text in the correct field — only the letter!
- The correct answer is "{answer}" — this is non-negotiable.
- The question MUST NOT simply repeat the fact statement verbatim
- The question MUST be a proper interrogative sentence
- The explanation MUST explain why the selected correct option is correct and MUST NOT support a different option

Step 1: Write a question where "{answer}" is the ONLY correct answer.
Step 2: Write 4 options (A, B, C, D) where:
   - A) MUST be "{answer}" (exact text)
   - B), C), D) are plausible but clearly incorrect alternatives
   - All options must be the SAME type of thing

CRITICAL RULES FOR OPTIONS:
- Do NOT put synonyms in the options — use the exact term
- Do NOT make one option a list that contains the words from other options
- Do NOT make the correct answer a combination or summary of the wrong answers
- Each option must be a complete, standalone answer

Example:
{{
  "questions": [
    {{
      "question": "What technique stores results of expensive function calls to avoid recomputation?",
      "options": [
        "A) Memoization",
        "B) Recursion",
        "C) Iteration",
        "D) Optimization"
      ],
      "correct": "A",
      "explanation": "Memoization stores results of expensive function calls to avoid recomputation."
    }}
  ]
}}

Now generate 1 question. Return ONLY valid JSON."""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.2,
                    "top_p": 0.7,
                    "num_predict": 800
                }
            )
            
            content = response['message']['content']
            print(f"Fact-based response received: {len(content)} characters")
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
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
                result = json.loads(content)
            
            if 'questions' in result and len(result['questions']) > 0:
                question = result['questions'][0]
                
                # --- FORMAT OPTIONS IMMEDIATELY (BEFORE ANY VALIDATION) ---
                options = question.get('options', [])
                if options:
                    # FIX: Use centralized parser
                    question['options'] = normalize_options(options)
                # --- END FORMAT OPTIONS ---
                
                # ===== STAGE 1: STRUCTURE VALIDATION =====
                if not validate_structure(question):
                    print(f"⚠️ Structure validation failed")
                    return None
                
                # ===== STAGE 2: CONTENT VALIDATION =====
                if not validate_grounding(question, fact, supporting_fact=supporting_fact):
                    print(f"⚠️ Grounding failed for fact-based question")
                    return None
                
                if not is_relevant_to_topic(question.get('question', ''), topic):
                    print(f"⚠️ Topic relevance failed for fact-based question")
                    return None
                
                if question_equals_answer(question.get('question', ''), question.get('options', [])):
                    print(f"⚠️ Question restates the answer")
                    return None
                
                # Skip placeholder questions
                q_text = question.get('question', '')
                if 'testing the fact' in q_text.lower() or 'question about' in q_text.lower() and len(q_text) < 40:
                    print(f"⚠️ Skipping placeholder question")
                    return None
                
                # ===== STAGE 3: SEMANTIC VALIDATION =====
                if not validate_semantic(question):
                    print(f"⚠️ Semantic validation failed")
                    return None
                
                # Normalize correct field
                if not normalize_and_validate_correct_field(question):
                    print(f"⚠️ Rejecting question with unresolvable correct field")
                    return None

                correct_letter = question.get('correct', '')
                correct_text = get_correct_text_from_options(question.get('options', []), correct_letter)
                supporting_fact = question.get('supporting_fact') or fact_data.get('supporting_fact') or fact
                question['fact_id'] = fact_data.get('fact_id') or f"fact_{abs(hash(fact))}"
                question['source_note'] = fact_data.get('source_note') or 'inline'
                if not _attach_grounding_fields(question, correct_text, supporting_fact, context=fact):
                    print(f"⚠️ Could not attach grounded explanation for fact-based question")
                    return None
                
                # ===== QUALITY SCORING =====
                facts = self.cache.get_facts(topic) if hasattr(self.cache, 'get_facts') else []
                is_acceptable, score, scores = self._check_quality(question, facts)
                
                if not is_acceptable:
                    print(f"⚠️ Question scored {score:.2f} - below threshold ({self.min_quality_score}), rejecting")
                    return None
                
                # Add quality score to question for debugging
                question['_quality_score'] = score
                question['_quality_scores'] = scores
                
                return question
            return None
            
        except Exception as e:
            print(f"Error generating from fact: {e}")
            return None
        
    def generate_questions(self, context: str, topic: str, count: int = 1, supporting_facts: list = None):
        """Generate a single quiz question from context"""
        
        prompt = f"""You are a computer science tutor. Create 1 multiple-choice question about {topic}.

Here is the content to base your question on:
{context}

Instructions:
1. Read the content carefully
2. Create a question that tests understanding of this topic
3. Use facts and terms from the content
4. Write 4 options (A, B, C, D)
5. Only ONE option is correct
6. The correct answer MUST come from the content
7. Wrong answers should be plausible but incorrect
8. Include a short explanation that explains why the selected correct option is correct
9. The correct field MUST be ONLY one letter: "A", "B", "C", or "D"

CRITICAL RULES FOR OPTIONS:
- The question field MUST end with a question mark (?)
- Do NOT make one option a list that contains the words from other options
- Do NOT make the correct answer a combination or summary of the wrong answers
- Each option must be a complete, standalone answer

Example format:
{{
  "questions": [
    {{
      "question": "Your question here",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correct": "A",
      "explanation": "Explanation of why A is correct."
    }}
  ]
}}

Now generate 1 question about {topic} from the content above. Return ONLY valid JSON in this format."""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "top_p": 0.7,
                    "num_predict": 1200
                }
            )
            
            content = response['message']['content']
            print(f"Ollama response received: {len(content)} characters")
            
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
                    result = {"questions": [result]}
                else:
                    return {"questions": []}
            
            valid_questions = []
            for q in result['questions']:
                if 'options' in q and len(q['options']) == 4:
                    options_text = ' '.join(q['options']).lower()
                    if 'correct answer' in options_text or 'wrong answer' in options_text:
                        print("Skipping placeholder question")
                        continue
                    
                    # --- FORMAT OPTIONS IMMEDIATELY ---
                    # FIX: Use centralized parser
                    q['options'] = normalize_options(q['options'])
                    # --- END FORMAT OPTIONS ---
                    
                    # ===== STAGE 1: STRUCTURE =====
                    if not validate_structure(q):
                        print(f"⚠️ Skipping malformed question")
                        continue
                    
                    # ===== STAGE 2: CONTENT =====
                    if not validate_grounding(q, context):
                        print(f"⚠️ Skipping ungrounded question")
                        continue
                    
                    if not is_relevant_to_topic(q.get('question', ''), topic):
                        print(f"⚠️ Skipping irrelevant question")
                        continue
                    
                    if question_equals_answer(q.get('question', ''), q.get('options', [])):
                        print(f"⚠️ Skipping question that restates answer")
                        continue
                    
                    # ===== STAGE 3: SEMANTIC =====
                    if not validate_semantic(q):
                        print(f"⚠️ Skipping question due to semantic issues")
                        continue
                    
                    # Normalize correct field
                    if not normalize_and_validate_correct_field(q):
                        print(f"⚠️ Skipping question with unresolvable correct field")
                        continue

                    correct_letter = q.get('correct', '')
                    correct_text = get_correct_text_from_options(q.get('options', []), correct_letter)
                    supporting_fact = _select_supporting_fact(correct_text, supporting_facts, fallback_context=context)
                    if not _attach_grounding_fields(q, correct_text, supporting_fact, context=context):
                        print(f"⚠️ Skipping question without grounded supporting fact")
                        continue
                    
                    # ===== QUALITY SCORING =====
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
            
            # Fallback generation
            if not valid_questions:
                print("No valid questions generated, trying fallback...")
                fallback = self._generate_fallback_question(context, topic)
                if fallback:
                    # Score fallback question
                    facts = self.cache.get_facts(topic) if hasattr(self.cache, 'get_facts') else []
                    is_acceptable, score, scores = self._check_quality(fallback, facts)
                    if is_acceptable:
                        fallback['_quality_score'] = score
                        fallback['_quality_scores'] = scores
                        valid_questions = [fallback]
                    else:
                        print(f"⚠️ Fallback question scored {score:.2f} - below threshold, skipping")
            
            return {"questions": valid_questions}
            
        except Exception as e:
            print(f"Error generating quiz: {e}")
            return {"questions": []}

    def _generate_fallback_question(self, context: str, topic: str) -> dict:
        """Generate a fallback question when LLM fails"""
        clean_context = re.sub(r'#.*?\n', '\n', context)
        clean_context = re.sub(r'\*\*', '', clean_context)
        clean_context = re.sub(r'\[\[.*?\]\]', '', clean_context)
        clean_context = re.sub(r'`.*?`', '', clean_context)
        clean_context = re.sub(r'\s+', ' ', clean_context)
        
        sentences = clean_context.split('.')
        meaningful_sentences = [s.strip() for s in sentences if 40 < len(s.strip()) < 200 and '#' not in s]
        
        if not meaningful_sentences:
            return None
        
        import random
        main_sentence = random.choice(meaningful_sentences)
        main_sentence = re.sub(r'\s+', ' ', main_sentence).strip()
        
        words = main_sentence.split()
        stop_words = ['the', 'this', 'that', 'with', 'from', 'have', 'will', 'they', 
                      'what', 'when', 'where', 'which', 'their', 'there', 'about', 
                      'concept', 'using', 'used', 'also', 'can', 'for', 'are']
        important_words = [w for w in words if len(w) > 4 and w.lower() not in stop_words]
        
        if len(important_words) < 4:
            return None
        
        options = [w.capitalize() for w in important_words[:4]]
        unique_options = list(dict.fromkeys(options))
        
        while len(unique_options) < 4:
            if len(words) > len(unique_options):
                extra_word = words[len(unique_options) - 1]
                if extra_word.lower() not in [o.lower() for o in unique_options]:
                    unique_options.append(extra_word.capitalize())
                else:
                    unique_options.append("Related Term")
            else:
                unique_options.append("Related Term")
        
        unique_options = unique_options[:4]
        shuffled = random.sample(unique_options, len(unique_options))
        
        templates = [
            f"What is the key concept described in the text about {topic}?",
            f"Based on the content, what is the main idea related to {topic}?",
            f"Which term best captures the concept discussed in the text?",
            f"What does the text primarily focus on when discussing {topic}?"
        ]
        question_text = random.choice(templates)
        
        # FIX: Use format_option for consistency
        formatted_options = [format_option(chr(65 + i), opt) for i, opt in enumerate(shuffled)]
        correct_letter = "A"
        correct_text = get_correct_text_from_options(formatted_options, correct_letter)

        fallback_question = {
            "question": question_text,
            "options": formatted_options,
            "correct": correct_letter,
            "correct_text": correct_text or shuffled[0],
            "supporting_fact": normalize_supporting_fact(main_sentence),
            "source_note": "fallback_context",
            "fact_id": f"fallback_{topic.lower().replace(' ', '_')}",
            "_is_fallback": True
        }

        if not _attach_grounding_fields(fallback_question, fallback_question.get('correct_text'), fallback_question.get('supporting_fact'), context=main_sentence):
            fallback_question["explanation"] = ""

        if explanation_contradicts_answer(fallback_question):
            fallback_question["explanation"] = ""
            fallback_question["supporting_fact"] = normalize_supporting_fact(main_sentence)
            _attach_grounding_fields(fallback_question, fallback_question.get('correct_text'), fallback_question.get('supporting_fact'), context=main_sentence)

        return fallback_question

    def generate_fill_blank(self, context: str, topic: str):
        """Generate a fill-in-the-blank question from context"""
        
        prompt = f"""You are a computer science tutor. Create 1 fill-in-the-blank question about {topic}.

Here is the content to base your question on:
{context}

Instructions:
1. Read the content carefully
2. Create a question where the student must fill in a KEY TERM or CONCEPT
3. The blank should be an important term from the content
4. Use "_______" for the blank space
5. Include the correct answer and a short explanation
6. The answer MUST come from the content

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

Now generate 1 fill-in-the-blank question about {topic} from the content above.

Return ONLY valid JSON in this format."""

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
    context = "Database normalization reduces redundancy. 1NF requires atomic values."
    gen = QuizGenerator()
    result = gen.generate_questions(context, "Database", count=1)
    print(json.dumps(result, indent=2))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import random
from difflib import SequenceMatcher

from .metadata_loader import MetadataLoader
from .quiz_generator import QuizGenerator, is_relevant_to_topic
from .fact_extractor import FactExtractor

app = FastAPI(title="AI Study Companion")

# CORS middleware - allows React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load metadata on startup (lightweight)
metadata_loader = MetadataLoader("sample_notes")
metadata = metadata_loader.load_metadata()


def generate_new_questions_for_topic(topic: str, subtopic: str, difficulty: str, count: int = 15) -> List[Dict[str, Any]]:
    """Generate new questions for a topic to fill the pool"""
    print(f"🔄 Generating {count} new questions for {topic}...")
    
    # Get metadata
    if subtopic:
        topic_metadata = metadata_loader.get_notes_by_subtopic(topic, subtopic)
        if not topic_metadata:
            print(f"⚠️ No notes found for subtopic '{subtopic}', falling back to topic '{topic}'")
            topic_metadata = metadata_loader.get_notes_by_topic(topic)
    else:
        topic_metadata = metadata_loader.get_notes_by_topic(topic)
    
    if not topic_metadata:
        print(f"❌ No notes found for topic: {topic}")
        return []
    
    # Rank notes by content length
    def rank_notes(notes):
        return sorted(
            notes,
            key=lambda x: x.get("content_length", 0),
            reverse=True
        )
    
    ranked_notes = rank_notes(topic_metadata)
    
    # Use fact extractor
    fact_extractor = FactExtractor()
    
    # Build context from top notes
    full_context = ""
    for meta in ranked_notes[:3]:
        content = metadata_loader.get_truncated_content(meta["path"], 2000)
        full_context += content + "\n\n"
    
    # Extract atomic facts from each note so each question is grounded in a single concise fact.
    extracted_facts = []
    for meta in ranked_notes[:3]:
        content = metadata_loader.get_truncated_content(meta["path"], 2000)
        note_facts = fact_extractor.extract_facts(content, topic, source=meta["path"])
        extracted_facts.extend(note_facts)
    
    all_questions = []
    
    # Generate questions from facts
    generator = QuizGenerator()
    
    if extracted_facts:
        for fact_data in extracted_facts[:10]:  # Try up to 10 facts
            if len(all_questions) >= count:
                break
                
            if not isinstance(fact_data, dict):
                continue
                
            fact = fact_data.get("statement", "")
            answer = fact_data.get("answer", "")
            
            if not fact or not answer:
                continue
            
            question = generator.generate_with_retry(fact, answer, topic, fact_data=fact_data)
            if question:
                all_questions.append(question)
    
    # If we don't have enough, try fallback generation
    if len(all_questions) < count:
        print(f"⚠️ Only got {len(all_questions)} questions from facts, using fallback...")
        # Fall back to regular generation with retries
        max_attempts = 15
        top_notes = ranked_notes[:6] if len(ranked_notes) >= 6 else ranked_notes
        
        for attempt in range(max_attempts):
            if len(all_questions) >= count:
                break
                
            num_notes = min(3, len(top_notes))
            selected_meta = random.sample(top_notes, num_notes)
            
            context_parts = []
            for meta in selected_meta:
                content = metadata_loader.get_truncated_content(meta["path"], 2000)
                context_parts.append(f"# {meta['title']}\n{content}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            generator = QuizGenerator()
            result = generator.generate_questions(
                context=context,
                topic=topic,
                count=1
            )
            
            questions = result.get("questions", [])
            if questions and len(questions) > 0:
                q_text = questions[0].get('question', '')
                options_text = ' '.join(questions[0].get('options', []))
                
                if 'Option 1' in options_text or 'Option 2' in options_text:
                    continue
                    
                is_duplicate = False
                for existing in all_questions:
                    existing_text = existing.get('question', '')
                    ratio = SequenceMatcher(None, q_text.lower(), existing_text.lower()).ratio()
                    if ratio > 0.6:
                        is_duplicate = True
                        break
                
                if not is_duplicate and is_relevant_to_topic(q_text, topic):
                    all_questions.append(questions[0])
    
    print(f"✅ Generated {len(all_questions)} questions for {topic}")
    return all_questions[:count]


@app.get("/")
async def root():
    return {"message": "AI Study Companion API"}

@app.get("/topics")
async def get_topics():
    topics = list(set(note["topic"] for note in metadata))
    return {"topics": sorted(topics)}

@app.get("/topics/{topic}/subtopics")
async def get_subtopics(topic: str):
    """Get all subtopics for a topic"""
    subtopics = metadata_loader.get_subtopics_by_topic(topic)
    if not subtopics:
        raise HTTPException(404, f"No subtopics found for topic: {topic}")
    return {"topic": topic, "subtopics": subtopics}

@app.get("/topics/{topic}/{subtopic}")
async def get_notes_by_subtopic(topic: str, subtopic: str):
    """Get notes for a specific subtopic"""
    notes = metadata_loader.get_notes_by_subtopic(topic, subtopic)
    if not notes:
        raise HTTPException(404, f"No notes found for {topic} > {subtopic}")
    return {"topic": topic, "subtopic": subtopic, "notes": notes}

@app.get("/notes/{topic}")
async def get_notes_by_topic(topic: str):
    filtered = [n for n in metadata if n["topic"].lower() == topic.lower()]
    if not filtered:
        raise HTTPException(404, f"No notes found for topic: {topic}")
    return filtered

@app.post("/generate-quiz")
async def generate_quiz(request: dict):
    topic = request.get("topic", "Database")
    subtopic = request.get("subtopic", "")
    count = request.get("count", 3)
    difficulty = request.get("difficulty", "medium")
    fresh = request.get("fresh", False)
    
    generator = QuizGenerator()
    cache_key = f"{topic}_{subtopic}_{difficulty}"
    
    # If fresh is requested, clear the pool for this topic
    if fresh:
        print(f"🔄 Fresh requested - clearing pool for {topic}")
        generator.cache.invalidate_topic_cache(topic, subtopic, difficulty, "multiple")
    
    # Get current pool
    pool = generator.cache.get_pool(topic, subtopic, difficulty, "multiple")
    
    # Check if we need to generate more questions to fill the pool
    min_pool_size = 15  # Keep a buffer for variety
    if len(pool) < min_pool_size:
        print(f"⚠️ Pool too small ({len(pool)} questions), generating more...")
        
        # Generate more questions (target 15)
        new_questions = generate_new_questions_for_topic(topic, subtopic, difficulty, count=15)
        
        if new_questions:
            # Filter out fallback questions
            real_questions = [q for q in new_questions if not q.get('_is_fallback', False)]
            if real_questions:
                added_count = generator.cache.add_to_pool(topic, subtopic, difficulty, "multiple", real_questions)
                print(f"✅ Added {added_count} real questions to pool (excluded {len(new_questions) - len(real_questions)} fallback)")
            else:
                print(f"⚠️ No real questions generated, pool unchanged")
            pool = generator.cache.get_pool(topic, subtopic, difficulty, "multiple")
        
        # If still empty, return what we have
        if len(pool) < count:
            print(f"⚠️ Not enough questions in pool ({len(pool)}), using fallback")
            return {
                "topic": topic,
                "subtopic": subtopic if subtopic else None,
                "questions": pool[:count],
                "source_notes": ["Pool (insufficient)"]
            }
    
    # Sample questions from the pool
    sampled = generator.cache.sample(topic, subtopic, difficulty, "multiple", count)
    
    if not sampled:
        # Fallback: just take the first 'count' questions
        sampled = pool[:count]
        print(f"⚠️ Couldn't sample, using first {len(sampled)} questions")
    
    # Debug: Print final questions before sending
    print("\n" + "="*60)
    print("🔍 FINAL RESPONSE CHECK:")
    for i, q in enumerate(sampled):
        print(f"  Q{i+1}: {q.get('question', '')[:50]}...")
        print(f"    correct: '{q.get('correct', '')}'")
        print(f"    options: {[opt[:20] + '...' if len(opt) > 20 else opt for opt in q.get('options', [])]}")
    print("="*60 + "\n")
    
    return {
        "topic": topic,
        "subtopic": subtopic if subtopic else None,
        "questions": sampled,
        "source_notes": ["Pool sample"]
    }

@app.post("/generate-fill-blank")
async def generate_fill_blank(request: dict):
    topic = request.get("topic", "Database")
    subtopic = request.get("subtopic", "")
    difficulty = request.get("difficulty", "medium")
    fresh = request.get("fresh", False)
    
    # Initialize generator for cache
    generator = QuizGenerator()
    cache_key = f"{topic}_{subtopic}_{difficulty}_fillblank"
    
    # If fresh is requested, clear the pool for this topic
    if fresh:
        print(f"🔄 Fresh requested - clearing fill-blank pool for {topic}")
        generator.cache.invalidate_topic_cache(topic, subtopic, difficulty, "fillblank")
    
    # Get current pool
    pool = generator.cache.get_pool(topic, subtopic, difficulty, "fillblank")
    
    # Check if we need to generate more questions to fill the pool
    min_pool_size = 10  # Keep a buffer for variety
    if len(pool) < min_pool_size:
        print(f"⚠️ Fill-blank pool too small ({len(pool)} questions), generating more...")
        
        # Get metadata for this topic or subtopic
        if subtopic:
            topic_metadata = metadata_loader.get_notes_by_subtopic(topic, subtopic)
            if not topic_metadata:
                print(f"⚠️ No notes found for subtopic '{subtopic}', falling back to topic '{topic}'")
                topic_metadata = metadata_loader.get_notes_by_topic(topic)
        else:
            topic_metadata = metadata_loader.get_notes_by_topic(topic)
        
        if topic_metadata:
            # Rank notes by content length
            def rank_notes(notes):
                return sorted(
                    notes,
                    key=lambda x: x.get("content_length", 0),
                    reverse=True
                )
            
            ranked_notes = rank_notes(topic_metadata)
            top_notes = ranked_notes[:6] if len(ranked_notes) >= 6 else ranked_notes
            
            # Select random notes
            selected_meta = random.sample(top_notes, min(3, len(top_notes)))
            
            context_parts = []
            for meta in selected_meta:
                content = metadata_loader.get_truncated_content(meta["path"], 1200)
                context_parts.append(f"# {meta['title']}\n{content}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            generator = QuizGenerator()
            result = generator.generate_fill_blank(context=context, topic=topic)
            
            fill_blank_questions = result.get("questions", [])
            
            if fill_blank_questions:
                # Filter out fallback fill-blank questions
                real_fill_blank = [q for q in fill_blank_questions if not q.get('_is_fallback', False)]
                if real_fill_blank:
                    added_count = generator.cache.add_to_pool(topic, subtopic, difficulty, "fillblank", real_fill_blank)
                    print(f"✅ Added {added_count} real fill-blank questions to pool")
                else:
                    print(f"⚠️ No real fill-blank questions generated")
                pool = generator.cache.get_pool(topic, subtopic, difficulty, "fillblank")
    
    # Sample questions from the pool
    sampled = generator.cache.sample(topic, subtopic, difficulty, "fillblank", 3)
    
    if not sampled:
        sampled = pool[:3]
        print(f"⚠️ Couldn't sample fill-blank, using first {len(sampled)} questions")
    
    return {
        "topic": topic,
        "subtopic": subtopic if subtopic else None,
        "questions": sampled,
        "source_notes": ["Pool sample"]
    }

@app.post("/refresh-notes")
async def refresh_notes():
    global metadata, metadata_loader
    # Delete cache to force rebuild
    try:
        metadata_loader.metadata_file.unlink(missing_ok=True)
    except:
        pass
    # Reload metadata
    metadata = metadata_loader.load_metadata()
    topics = sorted(list(set(note["topic"] for note in metadata)))
    return {
        "message": "Notes refreshed successfully!",
        "total_notes": len(metadata),
        "topics": topics
    }
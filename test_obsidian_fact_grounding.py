from pathlib import Path
import asyncio

from app.main import generate_new_questions_for_topic
from app.quiz_generator import explanation_contradicts_answer
from app.fact_extractor import FactExtractor


def test_obsidian_notes_ground_questions():
    note_path = Path('sample_notes/Cloud/Cloud Storage.md')
    source = note_path.read_text(encoding='utf-8')

    extractor = FactExtractor(notes_path='sample_notes')
    facts = extractor.extract_facts(source, 'Cloud', str(note_path))
    assert facts, 'Expected at least one useful fact from the Obsidian note'

    questions = generate_new_questions_for_topic('Cloud', '', 'medium', count=5)
    assert questions, 'Expected at least one generated question'

    for question in questions:
        supporting_fact = question.get('supporting_fact', '')
        assert supporting_fact, 'Each question should carry a supporting fact'
        assert question.get('source_note'), 'Each question should record its source note'
        assert question.get('fact_id'), 'Each question should record a fact identifier'

        source_lower = source.lower()
        supporting_lower = supporting_fact.lower()
        assert supporting_lower in source_lower or any(term in source_lower for term in supporting_lower.split() if len(term) > 4), 'Supporting fact should be grounded in the markdown source'
        assert not explanation_contradicts_answer(question), 'Explanation should support the marked correct answer'
        assert question.get('correct_text') or question.get('correct'), 'Question should expose the correct answer text'

        assert len(supporting_fact.split()) <= 24, 'Supporting fact should stay atomic and concise'
        assert '#' not in supporting_fact and '[[' not in supporting_fact, 'Supporting fact should not contain raw markdown note structure'
        assert len(question.get('explanation', '').split()) <= 24, 'Explanation should stay concise'
        assert not any(marker in question.get('explanation', '').lower() for marker in ['#', '---', '[[', ']]']), 'Explanation should not copy note markdown'


if __name__ == '__main__':
    test_obsidian_notes_ground_questions()
    print('Obsidian fact grounding test passed')

import pytest
from app.quiz.metadata.question_diversity import calculate_diversity_score

def test_diversity_score():
    # Test identical concepts get low score
    batch = [{"concept": "A", "difficulty": "medium", "type": "multiple_choice"}]
    candidate = {"concept": "A", "difficulty": "medium", "type": "multiple_choice"}
    
    score = calculate_diversity_score(candidate, batch)
    assert score < 0.5 # Should be low because of matches
    
    # Test different concepts get high score
    candidate2 = {"concept": "B", "difficulty": "hard", "type": "fill_blank"}
    score2 = calculate_diversity_score(candidate2, batch)
    assert score2 > 0.5 # Should be higher

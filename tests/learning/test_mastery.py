import pytest
from unittest.mock import MagicMock
from app.models.user_context import UserContext
from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.mastery.mastery_tracker import update_concept_performance, create_concept_record

@pytest.fixture
def mock_repo():
    return MagicMock(spec=AnalyticsRepository)

def test_mastery_update(mock_repo):
    user_context = UserContext(user_id="user1")
    concept = "concept1"
    
    # Mock return value for get_mastery_records
    mock_repo.get_mastery_records.return_value = []
    
    # Simulate update logic directly using mastery_tracker
    concept_record = create_concept_record(concept)
    updated_record = update_concept_performance(concept_record, True)
    
    mock_repo.upsert_mastery_record(
        user_id=user_context.user_id,
        concept=concept,
        attempts=updated_record["attempts"],
        correct_count=updated_record["correct"],
        wrong_count=updated_record["wrong"],
        mastery_score=updated_record["mastery"],
        recommended_difficulty=updated_record["recommended_difficulty"]
    )
    
    # Verify call to upsert_mastery_record
    mock_repo.upsert_mastery_record.assert_called_once()
    args, kwargs = mock_repo.upsert_mastery_record.call_args
    assert kwargs["user_id"] == "user1"
    assert kwargs["concept"] == concept
    assert kwargs["attempts"] == 1
    assert kwargs["correct_count"] == 1


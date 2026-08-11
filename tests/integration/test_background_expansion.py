from fastapi.testclient import TestClient
from app.main import app, pool_manager

client = TestClient(app)


def test_background_expansion_triggered():
    """Verify the quiz endpoint can trigger pool expansion."""

    topic = "Cloud"

    pool_manager.finish_expansion(topic)

    response = client.post(
        "/quiz/session/create",
        json={
            "topic": topic,
            "count": 10,
            "difficulty": "medium",
            "fresh": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "questions" in data
    assert "session_id" in data


def test_duplicate_expansion_prevention():
    """Verify only one expansion can run for a topic at a time."""

    topic = "Cloud"

    pool_manager.finish_expansion(topic)

    assert pool_manager.try_start_expansion(topic) is True
    assert pool_manager.try_start_expansion(topic) is False

    pool_manager.finish_expansion(topic)

    assert pool_manager.try_start_expansion(topic) is True

    pool_manager.finish_expansion(topic)


def test_expansion_cleanup_on_exception():
    """Verify expansion state can be cleaned up after failure."""

    topic = "ErrorTopic"

    pool_manager.finish_expansion(topic)

    assert pool_manager.try_start_expansion(topic) is True

    pool_manager.finish_expansion(topic)

    assert pool_manager.is_expanding(topic) is False
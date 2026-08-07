import pytest

from app.quiz.generation.llm_client import LLMClient


@pytest.mark.integration
def test_real_ollama_connection():
    client = LLMClient()

    response = client.chat(
        [
            {
                "role": "user",
                "content": "Return only: OK"
            }
        ]
    )

    assert response
    assert "OK" in response

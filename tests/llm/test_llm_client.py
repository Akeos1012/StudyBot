import pytest
from unittest.mock import patch, MagicMock

from app.quiz.generation.llm_client import LLMClient


@pytest.fixture
def llm_client():
    return LLMClient()


@patch("app.quiz.generation.llm_client.ollama.chat")
def test_llm_client_chat_success(mock_chat, llm_client):
    mock_chat.return_value = {
        "message": {
            "content": "Test response"
        }
    }

    response = llm_client.chat(
        "Hello"
    )

    assert response is not None
    assert "Test response" in response


from app.quiz.generation.llm_client import LLMResponseError


@patch("app.quiz.generation.llm_client.ollama.chat")
def test_llm_client_chat_empty_response(mock_chat, llm_client):
    mock_chat.return_value = {
        "message": {
            "content": ""
        }
    }

    with pytest.raises(LLMResponseError):
        llm_client.chat(
            [
                {
                    "role": "user",
                    "content": "Hello"
                }
            ]
        )


@patch("app.quiz.generation.llm_client.ollama.chat")
def test_llm_client_chat_connection_error(mock_chat, llm_client):
    mock_chat.side_effect = Exception(
        "Connection failed"
    )

    with pytest.raises(Exception):
        llm_client.chat(
            "Hello"
        )

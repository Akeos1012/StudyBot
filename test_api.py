# test_api.py
"""Test the FastAPI endpoints."""

import requests
import json

BASE_URL = "http://localhost:5000"  # Adjust if your port is different


def test_health():
    """Test the health endpoint."""
    response = requests.get(f"{BASE_URL}/")
    print(f"Health: {response.json()}")


def test_topics():
    """Test getting topics."""
    response = requests.get(f"{BASE_URL}/topics")
    topics = response.json()
    print(f"Topics: {topics}")


def test_generate_quiz():
    """Test quiz generation endpoint."""
    payload = {
        "topic": "Cloud",
        "count": 3,
        "fresh": True
    }
    response = requests.post(f"{BASE_URL}/generate-quiz", json=payload)
    data = response.json()
    print(f"Generated {len(data.get('questions', []))} questions")
    for i, q in enumerate(data.get('questions', []), 1):
        print(f"  Q{i}: {q.get('question', '')[:60]}...")


def test_generate_fill_blank():
    """Test fill-blank generation endpoint."""
    payload = {
        "topic": "Cloud",
        "fresh": True
    }
    response = requests.post(f"{BASE_URL}/generate-fill-blank", json=payload)
    data = response.json()
    print(f"Generated {len(data.get('questions', []))} fill-blank questions")
    for i, q in enumerate(data.get('questions', []), 1):
        print(f"  Q{i}: {q.get('question', '')[:60]}...")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing API Endpoints")
    print("=" * 60)

    # Start server first: uvicorn app.main:app --reload
    print("\n⚠️ Make sure the server is running:")
    print("  uvicorn app.main:app --reload --port 5000")
    print()

    try:
        test_health()
        test_topics()
        test_generate_quiz()
        test_generate_fill_blank()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Start it with:")
        print("  uvicorn app.main:app --reload --port 5000")
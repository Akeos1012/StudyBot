# test_api.py
"""API endpoint integration tests for StudyBot."""

import requests


BASE_URL = "http://127.0.0.1:8000"


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_health():
    print_header("Testing Health")

    response = requests.get(f"{BASE_URL}/")

    print(response.status_code)
    print(response.json())


def test_topics():
    print_header("Testing Topics")

    response = requests.get(
        f"{BASE_URL}/topics"
    )

    data = response.json()

    print(response.status_code)
    print("Topics:")
    for topic in data.get("topics", []):
        print(f" - {topic}")


def test_generate_quiz():
    print_header("Testing Multiple Choice Quiz")

    payload = {
        "topic": "Cloud",
        "count": 3,
        "fresh": True
    }

    response = requests.post(
        f"{BASE_URL}/quiz/generate",
        json=payload
    )

    data = response.json()

    assert response.status_code == 200
    assert data["success"] is True
    assert len(data["questions"]) == 3

    for q in data["questions"]:
        assert q["question"]
        assert q["correct_text"]
        assert q["explanation"]
        assert q["supporting_fact"]
        assert q["source_note"]

    print("✅ Multiple choice response validation passed")
    print("Generated:", len(data["questions"]))

    for i, q in enumerate(data.get("questions", []), 1):

        print(f"\nQ{i}")
        print(q.get("question"))

        print("Answer:")
        print(q.get("correct_text"))

        print("Explanation:")
        print(q.get("explanation"))

        print("Source:")
        print(q.get("source_note"))


def test_generate_fill_blank():

    print_header("Testing Fill Blank")

    payload = {
        "topic": "Cloud",
        "count": 3,
        "fresh": True
    }

    response = requests.post(
        f"{BASE_URL}/generate-fill-blank",
        json=payload
    )

    data = response.json()

    assert response.status_code == 200
    assert data["success"] is True
    assert len(data["questions"]) == 3

    for q in data["questions"]:
        assert q["question"]
        assert q["correct"]
        assert q["explanation"]
        assert q["supporting_fact"]

    print("✅ Fill blank response validation passed")
    print("Generated:", len(data["questions"]))

    for i, q in enumerate(data.get("questions", []), 1):

        print(f"\nQ{i}")
        print(q.get("question"))

        print("Answer:")
        print(q.get("correct"))

        print("Explanation:")
        print(q.get("explanation"))


def test_cache_status():

    print_header("Testing Cache")

    response = requests.get(
        f"{BASE_URL}/cache/status"
    )

    print(response.status_code)
    print(response.json())


def test_invalid_topic():
    print("\n" + "=" * 60)
    print("Testing Invalid Topic")
    print("=" * 60)

    payload = {
        "topic": "NonExistingTopic",
        "count": 3,
        "fresh": True
    }

    response = requests.post(
        f"{BASE_URL}/quiz/generate",
        json=payload
    )

    print("Status:", response.status_code)
    print(response.json())


def test_count_limit():
    print("\n" + "=" * 60)
    print("Testing Count Limit")
    print("=" * 60)

    payload = {
        "topic": "Cloud",
        "count": 100,
        "fresh": True
    }

    response = requests.post(
        f"{BASE_URL}/quiz/generate",
        json=payload
    )

    print("Status:", response.status_code)
    print(response.json())


def test_missing_payload():
    print("\n" + "=" * 60)
    print("Testing Missing Payload")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/quiz/generate",
        json={}
    )

    print("Status:", response.status_code)
    print(response.json())


def test_wrong_method():
    print("\n" + "=" * 60)
    print("Testing Wrong Method")
    print("=" * 60)

    response = requests.get(
        f"{BASE_URL}/quiz/generate"
    )

    print("Status:", response.status_code)
    print(response.json())


if __name__ == "__main__":

    print("🧪 StudyBot API Integration Test")

    try:
        test_health()
        test_topics()
        test_generate_quiz()
        test_generate_fill_blank()
        test_cache_status()

        test_invalid_topic()
        test_count_limit()
        test_missing_payload()
        test_wrong_method()

        print("\n✅ All API tests completed")

    except requests.exceptions.ConnectionError:

        print("\n❌ Server not running.")
        print("Start with:")
        print("uvicorn app.main:app --reload")
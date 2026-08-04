from app.main import app
from fastapi.testclient import TestClient
import random, string

client = TestClient(app)
user_id = "runtime-verification-" + "".join(
    random.choice(string.ascii_lowercase) for _ in range(6)
)

resp = client.post(
    "/quiz/generate",
    json={
        "topic": "Programming",
        "subtopic": "",
        "difficulty": "medium",
        "count": 3,
        "fresh": True,
        "adaptive": False,
    },
    headers={"X-User-ID": user_id},
)
qs = resp.json().get("questions", [])
for q in qs[:3]:
    client.post(
        "/quiz/submit-answer",
        json={"question_id": q["question_id"], "answer": q.get("correct", "A")},
        headers={"X-User-ID": user_id},
    )

for path in [
    "/analytics/mastery",
    "/analytics/progress",
    "/analytics/summary",
    "/analytics/weak-topics",
    "/analytics/trend",
    "/analytics/recommendations",
]:
    r = client.get(path, headers={"X-User-ID": user_id})
    print(path, r.status_code)
    print(r.json())

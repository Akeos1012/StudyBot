from app.main import app
from fastapi.testclient import TestClient
import random, string, sqlite3, sys

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
print("GENERATE_STATUS", resp.status_code)
qs = resp.json().get("questions", [])
print("QUESTION_COUNT", len(qs))
if not qs:
    sys.exit(0)
for idx, q in enumerate(qs[:3], 1):
    answer = q.get("correct", "A")
    result = client.post(
        "/quiz/submit-answer",
        json={"question_id": q.get("question_id"), "answer": answer},
        headers={"X-User-ID": user_id},
    )
    print("ANSWER", idx, result.status_code, result.json())

conn = sqlite3.connect("analytics.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("select count(*) as c from learning_events where user_id=?", (user_id,))
print("EVENT_COUNT", cur.fetchone()["c"])
rows = cur.execute(
    "select * from learning_events where user_id=? order by event_id desc limit 5",
    (user_id,),
).fetchall()
print("EVENTS", [dict(r) for r in rows])
cur.execute("select count(*) as c from mastery_records where user_id=?", (user_id,))
print("MASTERY_RECORD_COUNT", cur.fetchone()["c"])
conn.close()

summary = client.get("/analytics/summary", headers={"X-User-ID": user_id})
print("SUMMARY_STATUS", summary.status_code)
print("SUMMARY_BODY", summary.json())

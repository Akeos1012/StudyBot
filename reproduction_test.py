
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def generate_quiz(topic, count=3, exclude_ids=None):
    payload = {
        "topic": topic,
        "count": count,
        "exclude_ids": exclude_ids
    }
    
    # Needs X-User-ID header now
    headers = {"X-User-ID": "test-user"}
    
    response = requests.post(
        f"{BASE_URL}/quiz/session/create",
        json=payload,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
    return response.json()

if __name__ == "__main__":
    topic = "AI"
    
    print("Generating initial quiz...")
    quiz1 = generate_quiz(topic)
    q_ids1 = [q['question_id'] for q in quiz1['questions']]
    print(f"Q IDs: {q_ids1}")
    
    print("\nGenerating quiz excluding initial Q IDs...")
    quiz2 = generate_quiz(topic, exclude_ids=q_ids1)
    q_ids2 = [q['question_id'] for q in quiz2['questions']]
    print(f"Q IDs: {q_ids2}")
    
    # Check for overlap
    overlap = set(q_ids1) & set(q_ids2)
    print(f"\nOverlap: {overlap}")
    
    if not overlap:
        print("✅ Freshness verified: No overlap between consecutive quizzes.")
    else:
        print("❌ Freshness failed: Overlap found.")


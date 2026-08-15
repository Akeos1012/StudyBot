from app.quiz.validation.question_grounding import question_equals_answer

def test_question_equals_answer():
    # Case 1: Valid contextual inclusion
    q1 = "In cloud computing, Block Storage is used to provide persistent storage. What is the primary characteristic of Block Storage?"
    opts1 = ["A) Block Storage", "B) Object Storage", "C) Cloud Database", "D) Data Center"]
    # Based on current implementation: "block storage" is in q1, so it restates.
    print(f"CASE 1 (Valid contextual inclusion): Expected PASS, got: {'REJECT' if question_equals_answer(q1, opts1) else 'PASS'}")

    # Case 2: Direct answer restatement
    q2 = "What is Block Storage?"
    opts2 = ["A) Block Storage", "B) Object Storage", "C) Cloud Database", "D) Data Center"]
    print(f"CASE 2 (Direct restatement): Expected REJECT, got: {'REJECT' if question_equals_answer(q2, opts2) else 'PASS'}")

    # Case 3: Answer appears naturally
    q3 = "Which storage technology provides persistent volumes, and how does Block Storage differ from object storage?"
    opts3 = ["A) Block Storage", "B) Object Storage", "C) Cloud Database", "D) Data Center"]
    print(f"CASE 3 (Natural inclusion): Expected PASS, got: {'REJECT' if question_equals_answer(q3, opts3) else 'PASS'}")

    # Case 4: Exact answer only
    q4 = "Block Storage"
    opts4 = ["A) Block Storage", "B) Object Storage", "C) Cloud Database", "D) Data Center"]
    print(f"CASE 4 (Exact only): Expected REJECT, got: {'REJECT' if question_equals_answer(q4, opts4) else 'PASS'}")

    # Case 5: Different answer
    q5 = "What storage technology provides persistent volumes?"
    opts5 = ["A) Block Storage", "B) Object Storage", "C) Cloud Database", "D) Data Center"]
    print(f"CASE 5 (Different answer): Expected PASS, got: {'REJECT' if question_equals_answer(q5, opts5) else 'PASS'}")

    # Case 7: Longer answer
    q7 = "What storage technology provides persistent volumes?"
    opts7 = ["A) Block Storage provides persistent volumes.", "B) Object Storage", "C) Cloud Database", "D) Data Center"]
    print(f"CASE 7 (Longer answer): Expected PASS, got: {'REJECT' if question_equals_answer(q7, opts7) else 'PASS'}")

test_question_equals_answer()

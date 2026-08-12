import re


def build_fill_blank_question(
    concept: str,
    definition: str
) -> str:

    text = definition.strip()

    # 1. Identify the core sentence containing the concept
    # If the concept is in the definition, find the sentence containing it.
    sentences = re.split(r'(?<=[.!?])\s+', text)

    target_sentence = ""
    for sentence in sentences:
        if re.search(rf"\b{re.escape(concept)}\b", sentence, re.IGNORECASE):
            target_sentence = sentence
            break

    if not target_sentence:
        # Fallback to full text if concept not found in sentences
        target_sentence = text

    # 2. Replace concept with blank
    question_text = re.sub(
        rf"\b{re.escape(concept)}\b",
        "_______",
        target_sentence,
        flags=re.IGNORECASE
    )

    # 3. Final cleaning
    question_text = question_text.strip()

    # Ensure it ends with punctuation
    if not question_text.endswith(('.', '?', '!')):
        question_text += '.'

    return question_text
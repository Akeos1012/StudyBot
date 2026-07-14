class QuestionTemplates:

    def build_question_text(
        self, question_type, concept, definition, topic, distractors
    ):
        return f"What is {concept} in {topic}?"

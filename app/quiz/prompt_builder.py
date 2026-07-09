"""
Prompt Builder Module - Pure prompt generation for question wording.

This module is responsible ONLY for generating question text from facts.
It does NOT handle:
- Fact normalization
- Ontology validation
- Distractor selection or scoring
- Quiz generation
- Quality scoring
- Concept validation wrappers
- Legacy topic clusters

This is a lightweight text-generation utility used by the quiz pipeline.
"""

import random
from typing import Dict, Any, Optional, List


# ============================================================================
# CONSTANTS
# ============================================================================

# Question type templates
QUESTION_TEMPLATES = {
    "definition": [
        "What is {concept}?",
        "What does {concept} mean?",
        "What is the definition of {concept}?",
        "Which term matches: {definition}?",
        "What concept is defined as {definition}?",
        "In the context of {topic}, what is {concept}?",
        "How would you define {concept}?"
    ],
    "comparison": [
        "What is the main difference between {concept} and {distractor1}?",
        "How does {concept} differ from {distractor1}?",
        "Which statement best describes the relationship between {concept} and {distractor1}?",
        "What distinguishes {concept} from {distractor1}?",
        "Between {concept} and {distractor1}, which one {context}?"
    ],
    "application": [
        "In what scenario would {concept} be most useful?",
        "When would you use {concept}?",
        "Which situation best demonstrates the use of {concept}?",
        "What problem does {concept} solve?",
        "What is the primary use case for {concept}?"
    ],
    "scenario": [
        "A developer needs to {scenario}. Which concept fits best?",
        "You are building a system that requires {scenario}. Which concept should you use?",
        "A student is trying to understand {scenario}. Which concept explains this?",
        "Which concept would help solve: {scenario}?",
        "Given the task of {scenario}, which approach would you use?"
    ],
    "reverse_definition": [
        "What term is defined as: {definition}?",
        "Which concept matches this description: {definition}?",
        "What do we call {definition}?",
        "Fill in the blank: {definition} is known as _______."
    ]
}

# Scenario mappings for generating realistic contexts
SCENARIO_MAP = {
    "SQL": "querying data from a large database",
    "Indexing": "speeding up database search queries",
    "Normalization": "organizing data to reduce duplication",
    "Binary Search": "finding an item in a sorted list",
    "Quick Sort": "sorting a large dataset efficiently",
    "Dynamic Programming": "optimizing complex problems with overlapping subproblems",
    "Memoization": "storing results of expensive function calls",
    "OOP": "organizing code into reusable objects",
    "SOLID": "writing maintainable and scalable code",
    "CNN": "processing image data for computer vision",
    "Gradient Descent": "optimizing machine learning models",
    "ACID": "ensuring reliable database transactions",
    "Supervised": "training models with labeled data",
    "Unsupervised": "finding patterns in unlabeled data",
    "Reinforcement": "training agents through rewards and punishments",
    "Big O": "analyzing algorithm efficiency",
    "Time Complexity": "measuring algorithm runtime",
    "Space Complexity": "measuring algorithm memory usage",
}


# ============================================================================
# PUBLIC API
# ============================================================================

class PromptBuilder:
    """
    Pure prompt generation for question wording.

    This class generates question text from facts. It does NOT handle
    options, explanations, validation, or any other quiz logic.

    Usage:
        builder = PromptBuilder()
        question_text = builder.build_question_text(
            concept="Cloud Storage",
            definition="Stores data on remote servers",
            question_type="definition"
        )
    """

    def __init__(self):
        """Initialize the prompt builder with default templates."""
        self.templates = QUESTION_TEMPLATES
        self.scenarios = SCENARIO_MAP

    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================

    def build_question_text(
        self,
        concept: str,
        definition: str,
        question_type: str = "definition",
        topic: str = "Unknown",
        distractors: Optional[List[str]] = None
    ) -> str:
        """
        Build a question text from a fact.

        Args:
            concept: The main concept (e.g., "Cloud Storage")
            definition: The definition or supporting fact
            question_type: Type of question ("definition", "comparison",
                           "application", "scenario", "reverse_definition")
            topic: The topic name for context
            distractors: List of distractor concepts (for comparison questions)

        Returns:
            A formatted question string

        Example:
            >>> builder = PromptBuilder()
            >>> builder.build_question_text(
            ...     concept="Cloud Storage",
            ...     definition="Stores digital data on remote servers",
            ...     question_type="definition"
            ... )
            'What is Cloud Storage?'
        """
        if not concept or not definition:
            return f"What is {concept}?" if concept else "What is the concept?"

        # Get the appropriate template list
        templates = self.templates.get(question_type, self.templates["definition"])

        # If no templates for this type, fall back to definition
        if not templates:
            templates = self.templates["definition"]

        # Select a random template
        template = random.choice(templates)

        # Build the question text
        question_text = self._format_template(
            template=template,
            concept=concept,
            definition=definition,
            topic=topic,
            distractors=distractors
        )

        return question_text

    def generate_scenario(self, concept: str) -> str:
        """
        Generate a realistic scenario for a concept.

        Args:
            concept: The concept name

        Returns:
            A scenario description string

        Example:
            >>> builder = PromptBuilder()
            >>> builder.generate_scenario("SQL")
            'querying data from a large database'
        """
        return self.scenarios.get(concept, f"understanding {concept}")

    def get_question_types(self) -> List[str]:
        """
        Get all available question types.

        Returns:
            List of question type names

        Example:
            >>> builder = PromptBuilder()
            >>> builder.get_question_types()
            ['definition', 'comparison', 'application', 'scenario', 'reverse_definition']
        """
        return list(self.templates.keys())

    def get_template_count(self, question_type: str) -> int:
        """
        Get the number of templates available for a question type.

        Args:
            question_type: The question type

        Returns:
            Number of templates for that type

        Example:
            >>> builder = PromptBuilder()
            >>> builder.get_template_count("definition")
            7
        """
        return len(self.templates.get(question_type, []))

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _format_template(
        self,
        template: str,
        concept: str,
        definition: str,
        topic: str,
        distractors: Optional[List[str]] = None
    ) -> str:
        """
        Format a template with the given values.

        Args:
            template: The template string with placeholders
            concept: The concept name
            definition: The definition text
            topic: The topic name
            distractors: List of distractors for comparison templates

        Returns:
            Formatted question string
        """
        # Shorten definition for display
        short_def = definition[:80] + ("..." if len(definition) > 80 else "")

        # Prepare format arguments
        format_args = {
            "concept": concept,
            "definition": short_def,
            "topic": topic,
        }

        # Add distractor if available
        if distractors and len(distractors) >= 1:
            format_args["distractor1"] = distractors[0]

        # Add context for comparison
        if "comparison" in template:
            format_args["context"] = self._generate_comparison_context()

        # Add scenario if needed
        if "{scenario}" in template:
            format_args["scenario"] = self.generate_scenario(concept)

        try:
            return template.format(**format_args)
        except KeyError:
            # If a placeholder is missing, return a simple question
            return f"What is {concept}?"

    def _generate_comparison_context(self) -> str:
        """
        Generate a random context for comparison questions.

        Returns:
            A comparison context phrase
        """
        contexts = [
            "is more efficient",
            "is more commonly used",
            "is more scalable",
            "is more reliable",
            "provides better performance",
            "is easier to implement"
        ]
        return random.choice(contexts)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def build_question(
    concept: str,
    definition: str,
    question_type: str = "definition",
    topic: str = "Unknown",
    distractors: Optional[List[str]] = None
) -> str:
    """
    Convenience function for building a single question.

    This is a thin wrapper around PromptBuilder for simple use cases.

    Args:
        concept: The main concept
        definition: The definition or supporting fact
        question_type: Type of question
        topic: The topic name
        distractors: List of distractor concepts

    Returns:
        A formatted question string

    Example:
        >>> question = build_question("Cloud Storage", "Stores data on remote servers")
        >>> print(question)
        'What is Cloud Storage?'
    """
    builder = PromptBuilder()
    return builder.build_question_text(
        concept=concept,
        definition=definition,
        question_type=question_type,
        topic=topic,
        distractors=distractors
    )


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    builder = PromptBuilder()

    print("=== PromptBuilder Tests ===\n")

    # Test each question type
    test_data = {
        "concept": "Cloud Storage",
        "definition": "Stores digital data on remote servers accessed over the internet",
        "topic": "Cloud"
    }

    for qtype in builder.get_question_types():
        question = builder.build_question_text(
            concept=test_data["concept"],
            definition=test_data["definition"],
            question_type=qtype,
            topic=test_data["topic"],
            distractors=["Local Storage", "Network Storage", "Distributed Storage"]
        )
        print(f"{qtype}: {question}")

    # Test scenario generation
    print(f"\nScenario for 'SQL': {builder.generate_scenario('SQL')}")
    print(f"Scenario for 'OOP': {builder.generate_scenario('OOP')}")

    # Test convenience function
    from prompt_builder import build_question
    q = build_question("Cloud Storage", "Stores data on remote servers")
    print(f"\nConvenience function: {q}")
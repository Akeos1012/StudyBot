"""
Option Builder

Responsible only for creating and formatting multiple-choice options.

QuestionBuilder should never know how options are shuffled or formatted.
"""

import random

from typing import List, Tuple


class OptionBuilder:
    """Builds multiple-choice options."""

    def build(
        self,
        correct_answer: str,
        distractors: List[str],
        count: int = 3,
    ) -> Tuple[List[str], str]:
        """
        Returns

        (
            [
                "A) ...",
                "B) ...",
                ...
            ],
            "B"
        )
        """

        distractors = distractors[:count]

        options = [correct_answer] + distractors

        random.shuffle(options)

        formatted = [f"{chr(65+i)}) {option}" for i, option in enumerate(options)]

        correct_letter = chr(65 + options.index(correct_answer))

        return formatted, correct_letter


_option_builder = OptionBuilder()


def build_options(
    correct_answer: str,
    distractors: List[str],
    count: int = 3,
):
    """
    Convenience wrapper.
    """

    return _option_builder.build(
        correct_answer,
        distractors,
        count,
    )

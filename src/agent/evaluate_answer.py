from typing import Any, Dict, Optional


def normalize_choice(choice: str) -> str:
    """
    Normalize MCQ answer letter.
    Example: ' a ' -> 'A'
    """

    if not choice:
        return ""

    return choice.strip().upper()


def evaluate_answer(
    question: str,
    options: Dict[str, str],
    learner_answer: str,
    correct_answer: str,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate one multiple-choice answer and return detailed feedback.

    Inputs:
    - question: The quiz question.
    - options: Dictionary of options A, B, C, D.
    - learner_answer: The learner selected answer letter.
    - correct_answer: The correct answer letter.
    - topic: Question topic.
    - difficulty: Question difficulty.

    Output:
    - is_correct
    - score
    - feedback
    - weakness
    """

    learner_answer = normalize_choice(learner_answer)
    correct_answer = normalize_choice(correct_answer)

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not options:
        raise ValueError("Options cannot be empty.")

    if correct_answer not in options:
        raise ValueError("Correct answer must be one of the options: A, B, C, or D.")

    learner_answer_text = options.get(learner_answer, "Invalid answer")
    correct_answer_text = options.get(correct_answer)

    is_correct = learner_answer == correct_answer

    if is_correct:
        feedback = (
            f"Correct. Great job! Your answer {learner_answer} is right."
        )
        weakness = None
        score = 1
    else:
        feedback = (
            f"Incorrect. You selected {learner_answer}: {learner_answer_text}. "
            f"The correct answer is {correct_answer}: {correct_answer_text}."
        )

        if topic:
            weakness = f"Review the topic: {topic}."
        else:
            weakness = "Review this question topic again."

        score = 0

    return {
        "question": question,
        "options": options,
        "learner_answer": learner_answer,
        "learner_answer_text": learner_answer_text,
        "correct_answer": correct_answer,
        "correct_answer_text": correct_answer_text,
        "is_correct": is_correct,
        "score": score,
        "feedback": feedback,
        "weakness": weakness,
        "topic": topic,
        "difficulty": difficulty
    }


if __name__ == "__main__":
    sample_question = {
        "question": "What is a Python variable?",
        "options": {
            "A": "A named container used to store data",
            "B": "A type of loop",
            "C": "A Python error",
            "D": "A function parameter only"
        },
        "correct_answer": "A",
        "topic": "variables",
        "difficulty": "beginner"
    }

    result = evaluate_answer(
        question=sample_question["question"],
        options=sample_question["options"],
        learner_answer="B",
        correct_answer=sample_question["correct_answer"],
        topic=sample_question["topic"],
        difficulty=sample_question["difficulty"]
    )

    print(result)

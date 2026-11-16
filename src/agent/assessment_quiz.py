import json
from src.agent.evaluate_answer import evaluate_answer
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.rag.vector_store import retrieve_knowledge
from src.agent.memory_tool import update_memory

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

def collect_topic_content(path, level, topics):
    """
    Retrieve content from multiple topics for the same level.
    """

    all_chunks = []

    for topic in topics:
        result = retrieve_knowledge(
            query=f"{path} {topic}",
            language=path.lower(),
            level=level
        )

        for item in result["results"]:
            all_chunks.append(item["content"])

    return "\n".join(all_chunks)

def generate_questions(content, difficulty, max_retries=3, subject="python"):

    prompt = f"""
You are a programming instructor for the {subject} programming language.

Based only on the provided content, generate 4 multiple-choice questions.

CRITICAL REQUIREMENT:
- All questions, concepts, terms, syntax, and options MUST be strictly about {subject}.
- DO NOT generate questions, examples, explanations, or options referencing other programming languages (e.g. if the subject is Python, do NOT mention Java, C++, C, or JavaScript keywords, syntax, or paradigms).
- Maintain the context of the programming language '{subject}' at all times.

Requirements:
- Difficulty: {difficulty}
- Generate exactly 4 questions
- Each question must contain:
    - question
    - options A, B, C, D
    - correct_answer
    - difficulty
    - topic

Return ONLY valid JSON.

Rules:
- Only ONE correct answer.
- Each question must contain:
    - question
    - options A, B, C, D
    - correct_answer
    - difficulty
    - topic

- topic must be one short topic name from the provided content.
- Examples of topic: variables, strings, lists, functions, classes, loops.

- Never use:
  - All of the above
  - None of the above
  - Both A and C
  - Both B and C
  - Multiple correct answers

- correct_answer must be exactly one letter:
  A
  B
  C
  or D

- All options must be standalone answers.
- Do not create combined-answer options.

Content:
{content}
"""

    invalid_options = [
        "all of the above",
        "none of the above",
        "both a and c",
        "both b and c",
        "both a and b",
        "both c and d"
    ]

    for attempt in range(max_retries):
        response = llm.invoke(prompt)

        clean_json = (
            response.content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        quiz_data = json.loads(clean_json)

        questions = quiz_data["questions"] if isinstance(quiz_data, dict) else quiz_data

        valid = True

        for question in questions:
            for option in question["options"].values():
                if option.lower() in invalid_options:
                    valid = False
                    break

            if not valid:
                break

        if valid:
            return questions[:4]

    raise ValueError("Failed to generate valid questions after multiple attempts.")

def generate_assessment_quiz(path: str):
    """
    Generate 12 assessment questions:
    - 4 Beginner
    - 4 Intermediate
    - 4 Advanced
    """

    beginner_text = collect_topic_content(
        path,
        "beginner",
        ["variables", "strings", "lists", "functions"]
    )

    intermediate_text = collect_topic_content(
        path,
        "intermediate",
        ["functions", "object oriented programming", "classes"]
    )

    advanced_text = collect_topic_content(
        path,
        "advanced",
        ["advanced programming concepts", "decorators", "error handling"]
    )


    beginner_questions = generate_questions(
        beginner_text,
        "beginner",
        subject=path
    )

    intermediate_questions = generate_questions(
        intermediate_text,
        "intermediate",
        subject=path
    )

    advanced_questions = generate_questions(
        advanced_text,
        "advanced",
        subject=path
    )

    return {
        "beginner": beginner_questions,
        "intermediate": intermediate_questions,
        "advanced": advanced_questions
    }


def evaluate_assessment(quiz, user_answers):
    """
    Evaluate assessment answers and calculate scores per difficulty.
    Also returns detailed feedback for each multiple-choice answer.
    """

    scores = {
        "beginner": 0,
        "intermediate": 0,
        "advanced": 0
    }

    wrong_questions = []
    evaluated_answers = []

    for difficulty in ["beginner", "intermediate", "advanced"]:
        questions = quiz[difficulty][:4]
        answers = user_answers[difficulty][:4]

        for question, user_answer in zip(questions, answers):
            correct_answer = question["correct_answer"]

            evaluation = evaluate_answer(
                question=question["question"],
                options=question.get("options", {}),
                learner_answer=user_answer,
                correct_answer=correct_answer,
                topic=question.get("topic", difficulty),
                difficulty=difficulty
            )

            evaluated_answers.append(evaluation)

            if evaluation["is_correct"]:
                scores[difficulty] += 1
            else:
                wrong_questions.append({
                    "difficulty": difficulty,
                    "topic": question.get("topic", difficulty),
                    "question": question["question"],
                    "options": question.get("options", {}),
                    "learner_answer": evaluation["learner_answer"],
                    "learner_answer_text": evaluation["learner_answer_text"],
                    "correct_answer": evaluation["correct_answer"],
                    "correct_answer_text": evaluation["correct_answer_text"],
                    "feedback": evaluation["feedback"],
                    "weakness": evaluation["weakness"]
                })

    return {
        "scores": scores,
        "wrong_questions": wrong_questions,
        "evaluated_answers": evaluated_answers
    }

def determine_level(
    beginner_score,
    intermediate_score,
    advanced_score
):
    """
    Determine learner level based on assessment scores.
    """

    if (
        beginner_score >= 3
        and intermediate_score >= 3
        and advanced_score >= 3
    ):
        return "advanced"

    if (
        beginner_score >= 3
        and intermediate_score >= 2
        and advanced_score < 3
    ):
        return "intermediate"

    return "beginner"


if __name__ == "__main__":

    quiz = generate_assessment_quiz("python")

    sample_answers = {
        "beginner": ["A", "B", "C", "D"],
        "intermediate": ["A", "B", "C", "D"],
        "advanced": ["A", "B", "C", "D"]
    }

    assessment_result = evaluate_assessment(quiz, sample_answers)
    scores = assessment_result["scores"]

    level = determine_level(
        scores["beginner"],
        scores["intermediate"],
        scores["advanced"]
    )

    memory_result = update_memory(
        learner_id="student_1",
        name="Njood",
        email="njood@example.com",
        skill_level=level,
        completed_topic="assessment",
        current_topic="review_weak_areas",
        wrong_questions=assessment_result["wrong_questions"]
    )
    from src.agent.learning_plan import update_learning_path
    
    path_result = update_learning_path(
        learner_id="student_1",
        name="Njood",
        email="njood@example.com",
        skill_level=level,
        goal="Learn Python and AI basics",
        wrong_questions=assessment_result["wrong_questions"],
        path="python",
    )

    print("SCORES:", scores)
    print("LEVEL:", level)
    print("WRONG QUESTIONS:", len(assessment_result["wrong_questions"]))
    print("MEMORY:", memory_result)

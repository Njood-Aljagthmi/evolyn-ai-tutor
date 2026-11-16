from src.rag.vector_store import retrieve_knowledge
from src.agent.assessment_quiz import generate_questions


def generate_quiz(path: str, level: str, topic: str):
    """
    Generate a learning quiz for a specific topic.
    """

    retrieved_content = retrieve_knowledge(
        query=f"{path} {level} {topic}",
        language=path.lower(),
        level=level.lower()
    )

    topic_text = "\n".join(
        item["content"]
        for item in retrieved_content["results"]
    )

    quiz = generate_questions(
        topic_text,
        level.lower()
    )

    return {
        "path": path.lower(),
        "level": level.lower(),
        "topic": topic,
        "quiz": quiz
    }


if __name__ == "__main__":
    result = generate_quiz(
        path="python",
        level="beginner",
        topic="variables"
    )

    print(result["quiz"])
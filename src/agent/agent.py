import threading
from database.progress_tool import get_progress
from src.rag.vector_store import retrieve_knowledge
from src.agent.assessment_quiz import (
    generate_assessment_quiz,
    evaluate_assessment,
    determine_level
)
from src.agent.learning_plan import update_learning_path
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
try:
    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Thread-local storage to pass the active learner context to the search tool
_active_session = threading.local()

def run_assessment_flow(
    learner_id,
    name,
    email,
    path,
    goal,
    user_answers
):
    quiz = generate_assessment_quiz(path)

    assessment_result = evaluate_assessment(
        quiz,
        user_answers
    )

    scores = assessment_result["scores"]

    level = determine_level(
        scores["beginner"],
        scores["intermediate"],
        scores["advanced"]
    )

    learning_path = update_learning_path(
        learner_id=learner_id,
        name=name,
        email=email,
        skill_level=level,
        goal=goal,
        wrong_questions=assessment_result["wrong_questions"],
        path=path
    )

    progress = get_progress(learner_id)

    return {
        "quiz": quiz,
        "scores": scores,
        "level": level,
        "wrong_questions": assessment_result["wrong_questions"],
        "learning_path": learning_path,
        "progress": progress
    }

@tool
def search_learning_content(query: str) -> str:
    """Retrieve learning content from the FAISS knowledge base."""
    learner_id = getattr(_active_session, "learner_id", "student_1")
    
    # Dynamically determine the user's active subject and level
    subject = "python"
    level = "beginner"
    try:
        progress = get_progress(learner_id)
        if progress and progress.get("learner"):
            goal = str(progress["learner"].get("goal", "")).lower()
            if "java" in goal:
                subject = "java"
            level = progress["learner"].get("skill_level", "beginner")
    except Exception:
        pass

    result = retrieve_knowledge(
        query=query,
        language=subject,
        level=level,
        k=3
    )

    results = result.get("results", [])

    if not results:
        return "No relevant content found."

    return "\n\n".join(
        item["content"][:500]
        for item in results
    )


@tool
def get_learner_progress(learner_id: str) -> str:
    """Retrieve learner progress, weak areas, and quiz history."""
    progress = get_progress(learner_id)

    if not progress.get("learner"):
        return "No learner progress found."

    weak_areas = progress.get("weak_areas", [])
    current_topic = progress.get("current_topic")

    weak_topics = [
        item["topic"]
        for item in weak_areas
    ]

    return (
        f"Current topic: {current_topic}\n"
        f"Weak areas: {weak_topics}\n"
        f"Quiz average: {progress.get('quiz_average')}"
    )


def run_tutor_agent(message: str, learner_id: str = "student_1"):
    """
    Run a LangChain tutor agent that can choose tools based on the learner message.
    """
    # Set the active learner ID in thread-local storage for the tool context
    _active_session.learner_id = learner_id

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )

    tools = [
        search_learning_content,
        get_learner_progress
    ]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are Evolyn, a friendly AI tutoring assistant named Evolyn.

Your role is to help learners study programming using:
- retrieved learning content
- learner progress
- weak areas
- personalized guidance

Use the available tools when needed:
- Use search_learning_content when the learner asks for an explanation or topic help.
- Use get_learner_progress when the learner asks about progress, weak areas, level, or current topic.

Keep your answers clear, supportive, and focused on learning.
Do not invent learner progress if it is not available.
"""
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False # True for debugging tool usage, False for clean production output.
    )

    return executor.invoke({
        "input": message
    })

if __name__ == "__main__":
    sample_answers = {
        "beginner": ["A", "B", "C", "D"],
        "intermediate": ["A", "B", "C", "D"],
        "advanced": ["A", "B", "C", "D"]
    }

    result = run_assessment_flow(
        learner_id="student_1",
        name="Njood",
        email="njood@example.com",
        path="python",
        goal="Learn Python and AI basics",
        user_answers=sample_answers
    )

    print("\n===== ASSESSMENT RESULTS =====")
    print("LEVEL:", result["level"])
    print("SCORES:", result["scores"])
    print("WEAK QUESTIONS:", len(result["wrong_questions"]))

    learning_path = result["learning_path"]

    print("\n===== LEARNING PLAN =====")

    new_plan = learning_path.get("new_plan", {})

    print("Plan Title:", new_plan.get("plan_title"))
    print("Current Topic:", new_plan.get("current_topic"))
    print("Recommended Next Step:", new_plan.get("recommended_next_step"))

    print("\n===== WEAK TOPICS =====")

    for topic in learning_path.get("weak_topics", []):
        print(
            f"- {topic['topic']} "
            f"({topic['mistake_count']} mistakes)"
        )
    
    print("\n===== LANGCHAIN TUTOR AGENT TEST =====")

    agent_response = run_tutor_agent(
        "Explain Python variables and check progress for student_1.",
        learner_id="student_1"
    )

    print(agent_response["output"])

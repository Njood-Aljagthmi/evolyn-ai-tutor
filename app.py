"""
app.py  —  AI Tutor
Run: streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "database"))

from src.agent.assessment_quiz import (
    generate_assessment_quiz,
    evaluate_assessment,
    determine_level,
    generate_questions,
)
from src.agent.memory_tool import update_memory
from src.agent.learning_plan import update_learning_path
from src.rag.vector_store import retrieve_knowledge

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Tutor", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .correct   { background:#d4edda; border-radius:8px; padding:10px; margin:4px 0; }
    .incorrect { background:#f8d7da; border-radius:8px; padding:10px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
DIFFICULTIES = ["beginner", "intermediate", "advanced"]


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "login",
        "learner_id": None,
        "name": "", "email": "", "path": "python",
        "level": None,
        "quiz": None,
        "answers": {"beginner": [], "intermediate": [], "advanced": []},
        "current_diff": "beginner",
        "current_q": 0,
        "weak_topics": [],
        "topic_status": {},
        "current_topic_name": None,
        "current_topic_diff": None,
        "explanation": None,
        "topic_quiz": None,
        "topic_answers": [],
        "topic_q_index": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def fetch_explanation(topic: str, difficulty: str) -> str:
    result = retrieve_knowledge(query=topic, language=st.session_state.path, level=difficulty, k=3)
    chunks = "\n\n".join(r["content"] for r in result["results"])
    prompt = f"""أنت مدرس برمجة ذكي. اشرح الموضوع التالي بأسلوب بسيط وواضح باللغة العربية.
استخدم أمثلة كود بسيطة. فقرتان أو ثلاث كافية.

الموضوع: {topic}
المستوى: {difficulty}

المحتوى المرجعي:
{chunks[:1500]}
"""
    return LLM.invoke(prompt).content


def fetch_topic_quiz(topic: str, difficulty: str):
    result = retrieve_knowledge(query=topic, language=st.session_state.path, level=difficulty, k=3)
    chunks = "\n\n".join(r["content"] for r in result["results"])
    return generate_questions(chunks, difficulty)[:3]


def score_quiz(quiz, answers) -> float:
    correct = sum(
        1 for q, a in zip(quiz, answers)
        if a.strip().upper() == q["correct_answer"].strip().upper()
    )
    return correct / len(quiz) if quiz else 0


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Login
# ─────────────────────────────────────────────────────────────────────────────
def page_login():
    st.title("🎓 AI Tutor")
    st.subheader("أهلاً! أدخلي بياناتك لتبدأي")

    with st.form("login"):
        name  = st.text_input("الاسم", placeholder="نجود")
        email = st.text_input("البريد", placeholder="njood@example.com")
        path  = st.selectbox("المسار", ["python"])
        go    = st.form_submit_button("ابدأي التقييم ←")

    if go:
        if not name or not email:
            st.error("أدخلي الاسم والبريد.")
            return
        st.session_state.update({
            "name": name, "email": email, "path": path,
            "learner_id": email.split("@")[0].replace(".", "_"),
        })
        with st.spinner("جاري تحضير الاختبار..."):
            st.session_state.quiz = generate_assessment_quiz(path)
        st.session_state.page = "assessment"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Assessment
# ─────────────────────────────────────────────────────────────────────────────
def page_assessment():
    answered = sum(len(st.session_state.answers[d]) for d in DIFFICULTIES)
    st.progress(answered / 12, text=f"السؤال {answered + 1} من 12")

    diff      = st.session_state.current_diff
    idx       = st.session_state.current_q
    questions = st.session_state.quiz[diff]

    if idx >= len(questions):
        next_i = DIFFICULTIES.index(diff) + 1
        if next_i < len(DIFFICULTIES):
            st.session_state.current_diff = DIFFICULTIES[next_i]
            st.session_state.current_q    = 0
            st.rerun()
        else:
            _finish_assessment()
            return

    q = questions[idx]
    level_label = {"beginner": "مبتدئ 🟢", "intermediate": "متوسط 🟡", "advanced": "متقدم 🔴"}
    st.caption(f"{level_label[diff]}  •  {q.get('topic','')}")
    st.markdown(f"### {q['question']}")

    choice = st.radio(
        "اختاري:",
        list(q["options"].keys()),
        format_func=lambda k: f"{k}. {q['options'][k]}",
        key=f"q_{diff}_{idx}",
    )

    if st.button("التالي ←"):
        st.session_state.answers[diff].append(choice)
        st.session_state.current_q += 1
        st.rerun()


def _finish_assessment():
    with st.spinner("جاري تحليل نتائجك وبناء خطتك..."):
        result = evaluate_assessment(st.session_state.quiz, st.session_state.answers)
        scores = result["scores"]
        level  = determine_level(scores["beginner"], scores["intermediate"], scores["advanced"])

        update_memory(
            learner_id=st.session_state.learner_id,
            name=st.session_state.name,
            email=st.session_state.email,
            skill_level=level,
            goal=f"Learn {st.session_state.path} and AI basics",
            completed_topic="assessment",
            current_topic="review_weak_areas",
            wrong_questions=result["wrong_questions"],
        )

        path_result = update_learning_path(
            learner_id=st.session_state.learner_id,
            name=st.session_state.name,
            email=st.session_state.email,
            skill_level=level,
            goal=f"Learn {st.session_state.path} and AI basics",
            wrong_questions=result["wrong_questions"],
            path=st.session_state.path,
        )

        weak   = path_result.get("weak_topics", [])
        status = {w["topic"]: ("active" if i == 0 else "locked") for i, w in enumerate(weak)}

        st.session_state.update({
            "level": level,
            "weak_topics": weak,
            "topic_status": status,
            "page": "learning_path",
        })
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Learning Path
# ─────────────────────────────────────────────────────────────────────────────
def page_learning_path():
    st.title("📚 خطتك التعليمية")
    st.caption(f"مرحباً {st.session_state.name} — اضغطي على الموضوع لتبدأي")

    weak   = st.session_state.weak_topics
    status = st.session_state.topic_status

    if not weak:
        st.success("🎉 ما في مواضيع ضعيفة — أحسنتِ!")
        return

    for i, w in enumerate(weak):
        topic = w["topic"]
        s     = status.get(topic, "locked")
        icon  = "✅" if s == "done" else ("📖" if s == "active" else "🔒")

        if s == "active":
            if st.button(f"{icon}  {topic.title()}", key=f"tp_{i}", use_container_width=True):
                st.session_state.update({
                    "current_topic_name": topic,
                    "current_topic_diff": w["difficulty"],
                    "explanation": None,
                    "topic_quiz": None,
                    "topic_answers": [],
                    "topic_q_index": 0,
                    "page": "topic_learn",
                })
                st.rerun()
        else:
            st.button(f"{icon}  {topic.title()}", key=f"tp_{i}",
                      disabled=True, use_container_width=True)

    if all(s == "done" for s in status.values()):
        st.balloons()
        st.success("🎉 أكملتِ جميع المواضيع!")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Topic Learn — شرح ثم كويز
# ─────────────────────────────────────────────────────────────────────────────
def page_topic_learn():
    topic = st.session_state.current_topic_name
    diff  = st.session_state.current_topic_diff

    st.title(f"📖 {topic.title()}")

    # الشرح
    if st.session_state.explanation is None:
        with st.spinner("الإيجنت يشرح لكِ..."):
            st.session_state.explanation = fetch_explanation(topic, diff)

    st.markdown(st.session_state.explanation)
    st.divider()

    # زر "فهمتُ"
    if st.session_state.topic_quiz is None:
        if st.button("✅ فهمتُ — ابدأي الاختبار"):
            with st.spinner("جاري تحضير الأسئلة..."):
                st.session_state.topic_quiz = fetch_topic_quiz(topic, diff)
            st.rerun()
        return

    # الكويز
    quiz  = st.session_state.topic_quiz
    q_idx = st.session_state.topic_q_index

    if q_idx >= len(quiz):
        _show_topic_result(topic, diff)
        return

    q = quiz[q_idx]
    st.subheader(f"سؤال {q_idx + 1} من {len(quiz)}")
    st.markdown(f"**{q['question']}**")

    choice = st.radio(
        "إجابتك:",
        list(q["options"].keys()),
        format_func=lambda k: f"{k}. {q['options'][k]}",
        key=f"tq_{q_idx}",
    )

    if st.button("التالي ←"):
        st.session_state.topic_answers.append(choice)
        st.session_state.topic_q_index += 1
        st.rerun()


def _show_topic_result(topic, diff):
    quiz    = st.session_state.topic_quiz
    answers = st.session_state.topic_answers
    score   = score_quiz(quiz, answers)
    passed  = score >= 0.6

    st.divider()

    if passed:
        st.success(f"🎉 أحسنتِ! {int(score*100)}% — اجتزتِ الموضوع!")

        # افتح الموضوع التالي
        weak   = st.session_state.weak_topics
        status = st.session_state.topic_status
        status[topic] = "done"
        curr_i = next((i for i, w in enumerate(weak) if w["topic"] == topic), None)
        if curr_i is not None and curr_i + 1 < len(weak):
            status[weak[curr_i + 1]["topic"]] = "active"
        st.session_state.topic_status = status

        update_memory(
            learner_id=st.session_state.learner_id,
            name=st.session_state.name,
            email=st.session_state.email,
            skill_level=st.session_state.level,
            goal=f"Learn {st.session_state.path} and AI basics",
            completed_topic=topic,
            current_topic=weak[curr_i + 1]["topic"] if curr_i + 1 < len(weak) else "completed",
        )

        if st.button("العودة للخطة ←"):
            st.session_state.page = "learning_path"
            st.rerun()

    else:
        st.error(f"❌ {int(score*100)}% — تحتاجين 60% للنجاح.")

        for q, a in zip(quiz, answers):
            if a.strip().upper() != q["correct_answer"].strip().upper():
                with st.expander(f"📌 {q['question'][:60]}..."):
                    for k, v in q.get("options", {}).items():
                        if k == q["correct_answer"]:
                            st.markdown(f'<div class="correct">✅ {k}. {v}</div>', unsafe_allow_html=True)
                        elif k == a:
                            st.markdown(f'<div class="incorrect">❌ {k}. {v} (إجابتك)</div>', unsafe_allow_html=True)
                        else:
                            st.write(f"{k}. {v}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 أعد الشرح"):
                st.session_state.update({
                    "explanation": None, "topic_quiz": None,
                    "topic_answers": [], "topic_q_index": 0,
                })
                st.rerun()
        with col2:
            if st.button("🔄 أعد الاختبار"):
                st.session_state.update({
                    "topic_quiz": None,
                    "topic_answers": [], "topic_q_index": 0,
                })
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "login":
    page_login()
elif page == "assessment":
    page_assessment()
elif page == "learning_path":
    page_learning_path()
elif page == "topic_learn":
    page_topic_learn()
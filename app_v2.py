"""
app_v2.py  —  AI Tutor (النسخة المحسّنة)
يستخدم: QuizService + ProgressService + generate_topics_for_level (learning plan)
Run: streamlit run app_v2.py
"""

import sys
import os
import json
from pathlib import Path

# ── Force UTF-8 on Windows to prevent UnicodeEncodeError from print() ──
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "database"))

# ── Services ──────────────────────────────────────────────
from src.services.quiz_service    import QuizService
from src.services.progress_service import ProgressService
from src.services.rag_service     import retrieve_knowledge_cached
from src.agent.assessment_quiz    import evaluate_assessment, determine_level
from src.agent.learning_plan      import update_learning_path, generate_topics_for_level
from src.agent.memory_tool        import update_memory
from db                           import (
    get_connection,
    initialize_learning_progress,
    initialize_topic_completion,
    update_learning_progress
)

# ─────────────────────────────────────────────────────────
st.set_page_config(page_title="🎓 AI Tutor", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; }
    .stApp { background: #0f1117; color: #e0e0e0; }
    .card  { background:#1a1d2e; border-radius:14px; padding:20px; margin:10px 0; border:1px solid #2d2d3d; }
    .correct   { background:#0d3321; border-left:4px solid #00e676; border-radius:8px; padding:10px; margin:4px 0; }
    .incorrect { background:#3b0d0d; border-left:4px solid #ff1744; border-radius:8px; padding:10px; margin:4px 0; }
    .topic-done   { background:#0d3321; border-radius:10px; padding:10px 16px; margin:6px 0; }
    .topic-active { background:#1a2d4a; border:1px solid #7c83fd; border-radius:10px; padding:10px 16px; margin:6px 0; }
    .topic-locked { background:#1a1d2e; border-radius:10px; padding:10px 16px; margin:6px 0; opacity:0.5; }
    .level-badge { display:inline-block; padding:4px 14px; border-radius:20px;
                   font-weight:700; font-size:0.85rem; }
    .badge-beginner     { background:#1a3a1a; color:#00e676; }
    .badge-intermediate { background:#2d2a00; color:#ffd740; }
    .badge-advanced     { background:#2d1a00; color:#ff6d00; }
</style>
""", unsafe_allow_html=True)

# ── Singletons ────────────────────────────────────────────
@st.cache_resource
def get_quiz_service():
    return QuizService()

@st.cache_resource
def get_progress_service():
    return ProgressService()

@st.cache_resource
def get_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

quiz_svc     = get_quiz_service()
progress_svc = get_progress_service()
llm          = get_llm()

DIFFICULTIES = ["beginner", "intermediate", "advanced"]

# ─────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page"             : "login",
        "learner_id"       : None,
        "name"             : "",
        "email"            : "",
        "subject"          : "python",
        "level"            : None,
        # Assessment
        "quiz"             : None,
        "answers"          : {"beginner": [], "intermediate": [], "advanced": []},
        "current_diff"     : "beginner",
        "current_q"        : 0,
        # Learning Plan
        "topics"           : [],        # list of {topic, difficulty, status}
        # Current topic
        "cur_topic"        : None,
        "cur_level"        : None,
        "explanation"      : None,
        "topic_quiz"       : None,
        "attempt_token"    : None,
        "topic_answers"    : [],
        "topic_q_idx"      : 0,
        "topic_result"     : None,
        # dashboard
        "dashboard_data"   : None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_state()

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def level_badge(level: str) -> str:
    cls = f"badge-{level}"
    labels = {"beginner": "مبتدئ 🟢", "intermediate": "متوسط 🟡",
              "advanced": "متقدم 🔴", "completed": "مكتمل ✅"}
    return f'<span class="level-badge {cls}">{labels.get(level, level)}</span>'


def fetch_explanation(topic: str, difficulty: str) -> str:
    result = retrieve_knowledge_cached(
        query=f"{st.session_state.subject} {topic}",
        language=st.session_state.subject,
        level=difficulty, k=3
    )
    chunks = "\n\n".join(r["content"] for r in result["results"])
    prompt = f"""أنت مدرس برمجة ذكي. اشرح الموضوع التالي بأسلوب بسيط وواضح باللغة العربية.
استخدم أمثلة كود بسيطة إن وجدت. فقرتان أو ثلاث كافية.

الموضوع: {topic}
المستوى: {difficulty}
اللغة: {st.session_state.subject}

المحتوى المرجعي:
{chunks[:1800]}
"""
    return llm.invoke(prompt).content


def _build_topics_from_plan(learner_id, subject, level, weak_topics_raw) -> list:
    """
    بناء قائمة المواضيع مع حالتها من learning_plan + topic_summary.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # جلب المواضيع من learning_plan
    cursor.execute("""
        SELECT recommended_next_step FROM learning_plan
        WHERE learner_id = ? AND subject = ? AND current_level = ?
        ORDER BY created_at DESC LIMIT 1
    """, (learner_id, subject, level))
    row = cursor.fetchone()

    topic_names = []
    if row and row["recommended_next_step"]:
        try:
            parsed = json.loads(row["recommended_next_step"])
            if isinstance(parsed, list):
                topic_names = parsed
        except Exception:
            pass

    if not topic_names:
        topic_names = generate_topics_for_level(subject, level)

    # جلب حالات topic_summary
    cursor.execute("""
        SELECT topic, rolling_average, completed FROM topic_summary
        WHERE learner_id = ? AND subject = ? AND level = ? AND status = 'active'
    """, (learner_id, subject, level))
    summaries = {r["topic"].lower(): r for r in cursor.fetchall()}
    conn.close()

    topics = []
    for i, t in enumerate(topic_names):
        summary = summaries.get(t.lower())
        if summary and summary["completed"] == 1:
            status = "done"
        elif summary:
            status = "active"
        elif i == 0:
            status = "active"
        else:
            prev = topic_names[i - 1]
            prev_s = summaries.get(prev.lower())
            status = "active" if (prev_s and prev_s["completed"] == 1) else "locked"
        topics.append({
            "topic": t,
            "difficulty": level,
            "status": status,
            "rolling_average": summary["rolling_average"] if summary else 0.0,
        })
    return topics


# ═══════════════════════════════════════════════════════════
# PAGE: Login
# ═══════════════════════════════════════════════════════════
def page_login():
    st.markdown('<div style="text-align:center;padding:30px 0 10px">'
                '<span style="font-size:3rem">🎓</span>'
                '<h1 style="color:#7c83fd;margin:0">المرشد الذكي للبرمجة</h1>'
                '<p style="color:#888">AI Adaptive Tutor</p>'
                '</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("login_form"):
            name    = st.text_input("الاسم الكامل", placeholder="نجود")
            email   = st.text_input("البريد الإلكتروني", placeholder="njood@example.com")
            subject = st.selectbox("اختاري المسار", ["python", "java"])
            go      = st.form_submit_button("ابدأي التقييم ← ", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if go:
        if not name or not email:
            st.error("أدخلي الاسم والبريد الإلكتروني.")
            return

        learner_id = email.replace(".", "_").replace("@", "_")
        st.session_state.update({
            "name": name, "email": email,
            "subject": subject, "learner_id": learner_id,
        })

        # إنشاء/جلب المستخدم من DB
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM learner_profile WHERE learner_id = ?", (learner_id,))
        user = cursor.fetchone()
        if not user:
            cursor.execute(
                "INSERT INTO learner_profile (learner_id, name, email, goal, skill_level) VALUES (?,?,?,?,?)",
                (learner_id, name, email, f"Learn {subject}", "beginner")
            )
            conn.commit()
        conn.close()

        # توليد الاختبار
        with st.spinner("⏳ جاري تحضير اختبار التقييم..."):
            quiz = quiz_svc.generate_assessment(subject)
            flat = [*quiz["beginner"], *quiz["intermediate"], *quiz["advanced"]]
            st.session_state.update({
                "quiz": quiz,
                "quiz_flat": flat,
                "answers": {"beginner": [], "intermediate": [], "advanced": []},
                "current_diff": "beginner",
                "current_q": 0,
                "page": "assessment",
            })
        st.rerun()


# ═══════════════════════════════════════════════════════════
# PAGE: Assessment
# ═══════════════════════════════════════════════════════════
def page_assessment():
    answered = sum(len(st.session_state.answers[d]) for d in DIFFICULTIES)
    total    = 12
    st.progress(answered / total, text=f"السؤال {answered + 1} من {total}")

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
    label_map = {"beginner": "مبتدئ 🟢", "intermediate": "متوسط 🟡", "advanced": "متقدم 🔴"}
    st.caption(f"{label_map[diff]}  •  {q.get('topic', '')}")
    st.markdown(f"### {q['question']}")

    choice = st.radio(
        "اختاري إجابتك:",
        list(q["options"].keys()),
        format_func=lambda k: f"**{k}.** {q['options'][k]}",
        key=f"q_{diff}_{idx}",
    )

    if st.button("التالي ←", use_container_width=True):
        st.session_state.answers[diff].append(choice)
        st.session_state.current_q += 1
        st.rerun()


def _finish_assessment():
    with st.spinner("⏳ جاري تحليل نتائجك وبناء خطتك التكيفية..."):
        quiz    = st.session_state.quiz
        answers = st.session_state.answers
        subject = st.session_state.subject
        lid     = st.session_state.learner_id

        result  = evaluate_assessment(quiz, answers)
        scores  = result["scores"]
        level   = determine_level(scores["beginner"], scores["intermediate"], scores["advanced"])
        pct     = {d: round(scores[d] / 4 * 100) for d in DIFFICULTIES}

        # ── بناء قائمة المواضيع الكاملة لمستوى المتعلم ──────────────
        # 1. مواضيع ضعف الاختبار (أولوية)
        weak_topics = result["wrong_questions"]
        weak_names = []
        seen = set()
        for w in weak_topics:
            t = w.get("topic", "").strip().lower()
            if t and t not in seen:
                weak_names.append(t)
                seen.add(t)

        # 2. كل مواضيع المستوى من الإيجنت
        level_topics = generate_topics_for_level(subject, level)

        # 3. دمج: نقاط الضعف أولاً ثم باقي مواضيع المستوى (بدون تكرار)
        combined = list(weak_names)
        for t in level_topics:
            if t.lower() not in seen:
                combined.append(t)
                seen.add(t.lower())

        # حفظ الخطة في DB
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assessment_results (learner_id, subject, beginner_score, intermediate_score, advanced_score, assigned_level)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lid, subject, pct["beginner"], pct["intermediate"], pct["advanced"], level))
        cursor.execute("UPDATE learner_profile SET skill_level=?, goal=? WHERE learner_id=?",
                       (level, f"Master {subject.upper()} programming", lid))

        # حفظ learning_plan بالمواضيع الكاملة
        cursor.execute("""
            INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lid, subject, level,
               f"Adaptive Plan — {level.title()}",
               combined[0] if combined else "start",
               json.dumps(combined)))

        conn.commit()
        conn.close()

        # Initialize learning progress and topic completion using helpers
        initialize_learning_progress(lid, subject, level, combined[0] if combined else "start")
        initialize_topic_completion(lid, subject, level, combined)
        update_learning_progress(lid, subject)

        # بناء قائمة UI من DB
        topics = _build_topics_from_plan(lid, subject, level, [])

        st.session_state.update({
            "level"     : level,
            "topics"    : topics,
            "page"      : "learning_path",
            "weak_names": weak_names,   # للعرض في الـ header
        })
    st.rerun()


# ═══════════════════════════════════════════════════════════
# PAGE: Learning Path
# ═══════════════════════════════════════════════════════════
def page_learning_path():
    lid     = st.session_state.learner_id
    subject = st.session_state.subject
    level   = st.session_state.level

    # ── إذا المستوى "completed" → اختيار مادة جديدة ──
    if level == "completed":
        st.markdown("""<div style='text-align:center;padding:40px 0'>
            <span style='font-size:3rem'>🏆</span>
            <h2 style='color:#ffd740'>أكملتِ المنهج كاملاً!</h2>
            <p style='color:#888'>يمكنكِ الآن اختيار مادة جديدة</p>
        </div>""", unsafe_allow_html=True)
        st.balloons()
        if st.button("📚 اختاري مادة جديدة", use_container_width=True, type="primary"):
            st.session_state.page = "select_subject"
            st.rerun()
        return

    # تحديث المواضيع دائماً من DB
    topics = _build_topics_from_plan(lid, subject, level, [])
    st.session_state.topics = topics

    # Header
    weak_names = st.session_state.get("weak_names", [])
    st.markdown(f"""
    <div class="card" style="display:flex;justify-content:space-between;align-items:center">
        <div>
            <h2 style="margin:0">📚 خطتك التعليمية — {subject.upper()}</h2>
            <p style="color:#888;margin:4px 0">مرحباً {st.session_state.name}</p>
        </div>
        <div>{level_badge(level)}</div>
    </div>
    """, unsafe_allow_html=True)

    # عرض نقاط الضعف من الاختبار (إن وجدت)
    if weak_names:
        with st.expander("⚠️ نقاط الضعف من الاختبار التقييمي (ستُدرَّس أولاً)"):
            for w in weak_names:
                st.write(f"• {w.title()}")

    if not topics:
        st.info("جاري تحميل المواضيع...")
        return

    # شريط التقدم
    done  = sum(1 for t in topics if t["status"] == "done")
    total = len(topics)
    if total:
        st.progress(done / total, text=f"✅ {done} من {total} موضوع مكتمل")

    st.markdown("---")

    for i, t in enumerate(topics):
        topic  = t["topic"]
        status = t["status"]
        avg    = t.get("rolling_average", 0.0)
        # تمييز نقاط الضعف بلون مختلف
        is_weak = topic.lower() in [w.lower() for w in weak_names]
        weak_tag = ' <span style="color:#ff6d00;font-size:0.75rem">[نقطة ضعف]</span>' if is_weak else ""

        if status == "done":
            st.markdown(
                f'<div class="topic-done">✅ <strong>{topic.title()}</strong>{weak_tag}  —  معدل: {avg:.0f}%</div>',
                unsafe_allow_html=True)

        elif status == "active":
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f'<div class="topic-active">📖 <strong>{topic.title()}</strong>{weak_tag}'
                    + (f'  —  آخر معدل: {avg:.0f}%' if avg > 0 else '') + '</div>',
                    unsafe_allow_html=True)
            with col2:
                if st.button("ابدأي", key=f"start_{i}", use_container_width=True):
                    st.session_state.update({
                        "cur_topic"    : topic,
                        "cur_level"    : level,   # ← مستوى المتعلم المحدد، ليس مستوى السؤال
                        "explanation"  : None,
                        "topic_quiz"   : None,
                        "attempt_token": None,
                        "topic_answers": [],
                        "topic_q_idx"  : 0,
                        "topic_result" : None,
                        "page"         : "topic_learn",
                    })
                    st.rerun()
        else:
            st.markdown(f'<div class="topic-locked">🔒 {topic.title()}{weak_tag}</div>',
                        unsafe_allow_html=True)

    # ── اكتمال المستوى ────────────────────────────────
    if done == total and total > 0:
        st.markdown("---")
        st.success(f"🎉 أكملتِ جميع مواضيع مستوى {level.title()}!")
        if st.button("🏆 التحقق من الترقية للمستوى التالي", use_container_width=True, type="primary"):
            with st.spinner("⏳ جاري التحقق من معدلاتك..."):
                check = progress_svc.check_level_progression(lid, subject, level)

            if check.get("status") == "promoted":
                new_level = check["new_level"]
                st.balloons()
                if new_level == "completed":
                    st.success("🏆 أكملتِ المنهج الكامل! مبروك!")
                    st.session_state.level = "completed"
                    st.rerun()
                else:
                    # توليد مواضيع المستوى الجديد وحفظها
                    with st.spinner(f"⏳ جاري تحضير مواضيع مستوى {new_level}..."):
                        new_topics = generate_topics_for_level(subject, new_level)
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (lid, subject, new_level,
                               f"Adaptive Plan — {new_level.title()}",
                               new_topics[0] if new_topics else "start",
                               json.dumps(new_topics)))
                        conn.commit()
                        conn.close()

                        # Initialize topics and learning progress for the new level
                        initialize_topic_completion(lid, subject, new_level, new_topics)
                        initialize_learning_progress(lid, subject, new_level, new_topics[0] if new_topics else "completed")
                        update_learning_progress(lid, subject)

                    st.session_state.level      = new_level
                    st.session_state.topics     = _build_topics_from_plan(lid, subject, new_level, [])
                    st.session_state.weak_names = []   # مواضيع الضعف تُصفّر عند الترقية
                    st.success(f"🎉 ترقية! الآن مستواكِ {new_level.title()}")
                    st.rerun()
            else:
                avg = check.get("level_average", 0)
                weak = check.get("weak_topics", [])
                st.warning(f"⚠️ معدلكِ {avg:.1f}% — تحتاجين 70% للترقية.")
                if weak:
                    st.info("راجعي هذه المواضيع: " + "، ".join(weak))

    st.markdown("---")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("📚 تغيير المادة", use_container_width=True):
            st.session_state.page = "select_subject"
            st.rerun()
    with col_r2:
        if st.button("🔄 إعادة الضبط", use_container_width=True):
            if st.session_state.get("confirm_reset"):
                progress_svc.soft_reset(lid, subject)
                for k in ["level", "topics", "quiz", "answers", "cur_topic", "explanation",
                          "topic_quiz", "topic_answers", "topic_result", "confirm_reset", "weak_names"]:
                    st.session_state.pop(k, None)
                st.session_state.page = "login"
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("اضغطي مرة ثانية للتأكيد")


# ═══════════════════════════════════════════════════════════
# PAGE: Select Subject (بعد إتمام مادة)
# ═══════════════════════════════════════════════════════════
def page_select_subject():
    lid  = st.session_state.learner_id
    name = st.session_state.name

    st.markdown(f"""<div style='text-align:center;padding:30px 0'>
        <span style='font-size:2.5rem'>📚</span>
        <h2 style='color:#7c83fd'>اختاري المادة التالية</h2>
        <p style='color:#888'>مرحباً {name} — اختاري المادة التي تريدين تعلمها</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    subjects = [
        ("python", "🐍", "Python", "برمجة عامة، بيانات، AI"),
        ("java", "☕", "Java", "تطوير تطبيقات، Android"),
    ]

    for idx, (subj, icon, label, desc) in enumerate(subjects):
        col = col1 if idx == 0 else col2
        with col:
            # فحص هل درست هذه المادة من قبل
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT current_level FROM learning_plan
                WHERE learner_id = ? AND subject = ?
                ORDER BY created_at DESC LIMIT 1
            """, (lid, subj))
            prev = cursor.fetchone()
            conn.close()

            if prev:
                badge = level_badge(prev["current_level"])
                st.markdown(
                    f'<div class="card" style="text-align:center">'
                    f'<div style="font-size:2.5rem">{icon}</div>'
                    f'<h3>{label}</h3><p style="color:#888">{desc}</p>'
                    f'<p>آخر مستوى: {badge}</p></div>',
                    unsafe_allow_html=True)
                btn_label = f"متابعة {label}"
            else:
                st.markdown(
                    f'<div class="card" style="text-align:center">'
                    f'<div style="font-size:2.5rem">{icon}</div>'
                    f'<h3>{label}</h3><p style="color:#888">{desc}</p>'
                    f'<p style="color:#555">لم تبدأي بعد</p></div>',
                    unsafe_allow_html=True)
                btn_label = f"ابدأي {label}"

            if st.button(btn_label, key=f"sel_{subj}", use_container_width=True):
                # استئناف أو بدء جديد
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT current_level FROM learning_plan
                    WHERE learner_id = ? AND subject = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (lid, subj))
                existing = cursor.fetchone()
                conn.close()

                st.session_state.subject    = subj
                st.session_state.weak_names = []

                if existing:
                    # استئناف من حيث توقفت
                    resume_level = existing["current_level"]
                    st.session_state.level  = resume_level
                    st.session_state.topics = _build_topics_from_plan(lid, subj, resume_level, [])
                    st.session_state.page   = "learning_path"
                else:
                    # مادة جديدة → اختبار تقييمي
                    with st.spinner("⏳ جاري تحضير اختبار التقييم..."):
                        quiz = quiz_svc.generate_assessment(subj)
                        st.session_state.update({
                            "quiz"        : quiz,
                            "answers"     : {d: [] for d in DIFFICULTIES},
                            "current_diff": "beginner",
                            "current_q"   : 0,
                            "page"        : "assessment",
                        })
                st.rerun()


# ═══════════════════════════════════════════════════════════
# PAGE: Topic Learn  (شرح ثم كويز)
# ═══════════════════════════════════════════════════════════
def page_topic_learn():
    topic   = st.session_state.cur_topic
    diff    = st.session_state.cur_level
    subject = st.session_state.subject
    lid     = st.session_state.learner_id

    if st.button("← العودة للخطة"):
        st.session_state.page = "learning_path"
        st.rerun()

    st.markdown(f"## 📖 {topic.title()}")
    st.markdown(level_badge(diff), unsafe_allow_html=True)
    st.markdown("---")

    # ── 1. شرح الموضوع ─────────────────────────────────
    if st.session_state.explanation is None:
        with st.spinner("🤖 الإيجنت يشرح لكِ..."):
            st.session_state.explanation = fetch_explanation(topic, diff)
        st.rerun()

    st.markdown(st.session_state.explanation)
    st.markdown("---")

    # ── 2. زر "فهمتُ" لبدء الكويز ──────────────────────
    if st.session_state.topic_quiz is None:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ فهمتُ — ابدأي الاختبار", use_container_width=True):
                with st.spinner("⏳ جاري تحضير الأسئلة..."):
                    res = quiz_svc.generate_topic_quiz(subject, diff, topic, bypass_cache=False)
                    st.session_state.topic_quiz    = res["questions"]
                    st.session_state.attempt_token = res["attempt_token"]
                    st.session_state.topic_answers = []
                    st.session_state.topic_q_idx   = 0
                st.rerun()
        with col2:
            if st.button("🔄 أعد الشرح", use_container_width=True):
                st.session_state.explanation = None
                st.rerun()
        return

    # ── 3. أسئلة الكويز ────────────────────────────────
    if st.session_state.topic_result is None:
        quiz  = st.session_state.topic_quiz
        q_idx = st.session_state.topic_q_idx

        if q_idx >= len(quiz):
            # تقديم الإجابات
            _submit_topic_quiz()
            return

        q = quiz[q_idx]
        st.subheader(f"سؤال {q_idx + 1} من {len(quiz)}")
        st.markdown(f"**{q['question']}**")

        choice = st.radio(
            "إجابتك:",
            list(q["options"].keys()),
            format_func=lambda k: f"**{k}.** {q['options'][k]}",
            key=f"tq_{q_idx}",
        )

        if st.button("التالي ←", use_container_width=True, key="quiz_next"):
            st.session_state.topic_answers.append(choice)
            st.session_state.topic_q_idx += 1
            st.rerun()
        return

    # ── 4. عرض النتيجة ─────────────────────────────────
    _show_topic_result()


def _submit_topic_quiz():
    with st.spinner("⏳ جاري تقييم إجاباتك..."):
        lid     = st.session_state.learner_id
        subject = st.session_state.subject
        diff    = st.session_state.cur_level
        topic   = st.session_state.cur_topic
        quiz    = st.session_state.topic_quiz
        answers = st.session_state.topic_answers
        token   = st.session_state.attempt_token

        # تحقق من التوكن وتقييم
        valid = quiz_svc.verify_and_consume_token(token, subject, diff, topic)
        eval_r = quiz_svc.evaluate_quiz_answers(quiz, answers)
        score  = eval_r["score"]

        if valid:
            stats = progress_svc.record_attempt(lid, subject, diff, topic, score, token)
        else:
            stats = {"attempt_count": 1, "rolling_average": score, "completed": score >= 70}

        # حفظ في quiz_history
        conn = get_connection()
        cursor = conn.cursor()
        for q, ans in zip(quiz, answers):
            cursor.execute("""
                INSERT INTO quiz_history (learner_id, subject, level, topic, question, learner_answer, correct_answer, score, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (lid, subject, diff, topic, q["question"], ans,
                  q["correct_answer"], score, eval_r["status"]))
        conn.commit()
        conn.close()

        st.session_state.topic_result = {
            "score"          : score,
            "status"         : eval_r["status"],
            "wrong_questions": eval_r["wrong_questions"],
            "attempt_count"  : stats.get("attempt_count", 1),
            "rolling_average": stats.get("rolling_average", score),
            "completed"      : stats.get("completed", False),
        }
    st.rerun()


def _show_topic_result():
    result = st.session_state.topic_result
    score  = result["score"]
    status = result["status"]
    topic  = st.session_state.cur_topic
    diff   = st.session_state.cur_level
    lid    = st.session_state.learner_id
    subject = st.session_state.subject

    st.markdown("---")
    st.subheader("📊 النتيجة")

    col1, col2, col3 = st.columns(3)
    col1.metric("الدرجة", f"{score:.0f}%")
    col2.metric("المحاولة", f"#{result['attempt_count']}")
    col3.metric("المعدل المتحرك", f"{result['rolling_average']:.0f}%")

    if status == "PASS" or result["completed"]:
        st.success("🎉 أحسنتِ! اجتزتِ الموضوع (معدل ≥ 70%)")

        # فتح الموضوع التالي
        topics = st.session_state.topics
        for i, t in enumerate(topics):
            if t["topic"].lower() == topic.lower():
                topics[i]["status"] = "done"
                topics[i]["rolling_average"] = result["rolling_average"]
                if i + 1 < len(topics) and topics[i + 1]["status"] == "locked":
                    topics[i + 1]["status"] = "active"
                break
        st.session_state.topics = topics

        if st.button("← العودة للخطة التعليمية", use_container_width=True):
            st.session_state.page = "learning_path"
            st.session_state.topic_result = None
            st.rerun()

    elif status == "RETRY":
        st.warning(f"⚠️ {score:.0f}% — تحتاجين 70% للنجاح. أعيدي المحاولة!")
        _show_wrong_questions(result["wrong_questions"])
        _retry_buttons(topic, diff, subject, lid)

    else:  # FAIL
        st.error(f"❌ {score:.0f}% — راجعي الشرح وأعيدي المحاولة.")
        _show_wrong_questions(result["wrong_questions"])
        _retry_buttons(topic, diff, subject, lid)


def _show_wrong_questions(wrong_qs):
    if not wrong_qs:
        return
    with st.expander("📌 مراجعة الأسئلة الخاطئة"):
        for q in wrong_qs:
            st.markdown(f"**{q['question']}**")
            for k, v in q.get("options", {}).items():
                if k == q["correct_answer"]:
                    st.markdown(f'<div class="correct">✅ {k}. {v}</div>', unsafe_allow_html=True)
                elif k == q.get("learner_answer"):
                    st.markdown(f'<div class="incorrect">❌ {k}. {v} (إجابتكِ)</div>', unsafe_allow_html=True)
                else:
                    st.write(f"{k}. {v}")
            st.divider()


def _retry_buttons(topic, diff, subject, lid):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 أعد الشرح", use_container_width=True):
            st.session_state.update({
                "explanation"  : None,
                "topic_quiz"   : None,
                "attempt_token": None,
                "topic_answers": [],
                "topic_q_idx"  : 0,
                "topic_result" : None,
            })
            st.rerun()
    with col2:
        if st.button("🔄 أعد الاختبار فقط", use_container_width=True):
            with st.spinner("⏳ جاري توليد أسئلة جديدة..."):
                res = quiz_svc.generate_topic_quiz(subject, diff, topic, bypass_cache=True)
                st.session_state.update({
                    "topic_quiz"   : res["questions"],
                    "attempt_token": res["attempt_token"],
                    "topic_answers": [],
                    "topic_q_idx"  : 0,
                    "topic_result" : None,
                })
            st.rerun()


# ═══════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════
page = st.session_state.page

if page == "login":
    page_login()
elif page == "assessment":
    page_assessment()
elif page == "learning_path":
    page_learning_path()
elif page == "topic_learn":
    page_topic_learn()
elif page == "select_subject":
    page_select_subject()

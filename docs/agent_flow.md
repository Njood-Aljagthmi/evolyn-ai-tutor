# Agent Flow

```text
Start
↓
Choose Learning Path
(Python / Java)

↓
Assessment Quiz

↓
Evaluate Assessment

↓
Agent Determines Starting Level
(Beginner / Intermediate / Advanced)

↓
Create Learning Plan

↓
Show Learning Plan

↓
Retrieve Knowledge (FAISS)

↓
Explain Current Topic

↓
Learning Quiz

↓
Evaluate Answer

↓
Update Memory

↓
Update Progress

↓
Agent Checks Topic Completion

├─ Not Completed
│  ↓
│  Review Topic
│  ↓
│  Learning Quiz Again
│
└─ Completed
   ↓
   Recommend Next Topic
   ↓
   Retrieve Knowledge (FAISS)

↓
Agent Checks Level Completion

├─ Level Not Completed
│  ↓
│  Continue Learning Current Level
│
└─ Level Completed
   ↓
   Agent Promotes User
   ↓
   Move to Next Level
   ↓
   Create New Learning Plan

↓
Agent Checks Course Completion

├─ Not Completed
│  ↓
│  Continue Learning
│
└─ Completed
   ↓
   Course Completed
   ↓
   End
```

---

# Assessment Quiz

## Quiz Structure

The assessment quiz is used to determine the learner's starting level in the selected learning path (Python or Java).

The quiz contains:

* 4 Beginner Questions
* 4 Intermediate Questions
* 4 Advanced Questions

**Total Questions:** 12

Each correct answer = 1 point.

Each incorrect answer = 0 points.

---

## Assessment Quiz Scoring Logic

### Score Calculation

The agent calculates three separate scores:

```text
Beginner Score / 4
Intermediate Score / 4
Advanced Score / 4
```

The learner must demonstrate mastery of lower levels before being promoted to higher levels.

---

### Level Determination

#### Beginner

Assigned when:

```text
Beginner Score < 3
```

or when the learner does not demonstrate sufficient understanding of beginner concepts.

---

#### Intermediate

Assigned when:

```text
Beginner Score >= 3
Intermediate Score >= 2
Advanced Score < 3
```

---

#### Advanced

Assigned when:

```text
Beginner Score >= 3
Intermediate Score >= 3
Advanced Score >= 3
```

---

### Examples

#### Example 1

```text
Beginner = 2/4
Intermediate = 1/4
Advanced = 0/4
```

Result:

```text
Beginner
```

#### Example 2

```text
Beginner = 4/4
Intermediate = 3/4
Advanced = 1/4
```

Result:

```text
Intermediate
```

#### Example 3

```text
Beginner = 4/4
Intermediate = 4/4
Advanced = 3/4
```

Result:

```text
Advanced
```

---

### Purpose

The assessment evaluates mastery at each difficulty level independently instead of relying only on the total score.

This ensures that learners cannot be promoted to advanced levels without demonstrating proficiency in prerequisite concepts.

---

# Implemented Workflow

The current implemented workflow is:

```text
Generate Assessment Quiz
↓
Retrieve content from FAISS
↓
Generate MCQ questions using GPT-4o-mini
↓
User answers the quiz
↓
Evaluate answers
↓
Determine learner level
↓
Save wrong answers using update_memory()
↓
Store weak areas in SQLite
↓
Retrieve learner progress using get_progress()
```

---

# Completed Implementation

* FAISS Vector Store was implemented and tested.
* retrieve_knowledge() retrieves relevant chunks by language and level.
* generate_assessment_quiz() generates 12 MCQ questions:

  * 4 Beginner
  * 4 Intermediate
  * 4 Advanced
* Questions are generated dynamically using GPT-4o-mini.
* Assessment content is retrieved from multiple topics per level.
* Each generated question contains:

  * question
  * options
  * correct_answer
  * difficulty
  * topic
* evaluate_assessment() calculates scores and returns wrong questions.
* determine_level() assigns the learner level.
* update_memory() stores wrong answers and weak areas in SQLite.
* get_progress() retrieves learner profile, quiz history, weak areas, and learning progress.
* Assessment Quiz and Memory System are fully integrated.

---

# Current Status

The Assessment + Memory workflow is working end-to-end as an MVP.

Current implemented flow:

```text
Assessment Quiz
↓
Evaluate Assessment
↓
Determine Level
↓
Update Memory
↓
Store Weak Areas
↓
Retrieve Progress
```


### 2️⃣ المستوى المتوسط (Intermediate)
**اسم الملف:** `python_intermediate_assessment.md`  
**المسار المفترض لوضعه:** `data/knowledge_base/python/intermediate/`

```markdown
# Python Intermediate Assessment Database

## 1. Quizzes
### Question 1
- **Type:** Multiple Choice
- **Question:** Which method is used to add an element to the end of a list?
  - A) `add()`
  - B) `insert()`
  - C) `append()`
  - D) `extend()`
- **Answer:** C

### Question 2
- **Type:** Multiple Choice
- **Question:** What does a Python Dictionary use to store data?
  - A) Index numbers
  - B) Key-Value pairs
  - C) Ordered sequences
  - D) Only unique values without keys
- **Answer:** B

---

## 2. Interview Questions
### Question 1: What are List Comprehensions and how do they work?
- **Answer:** List comprehensions provide a concise way to create lists in Python. They combine a `for` loop and an optional `if` condition inside square brackets into a single line. Example: `squared = [x**2 for x in range(5)]`.

---

## 3. Assignments
### Assignment 1: Unique Word Counter
- **Task:** Write a function that takes a string of text and uses a Python Dictionary to count the frequency of each unique word. Ignore case sensitivity.

---

## 4. Common Errors & Fixes
### Error 1: KeyError
- **Code with Error:**
  ```python
  student = {"name": "Sara", "age": 20}
  print(student["id"])
### 3️⃣ المستوى المتقدم (Advanced)
**اسم الملف:** `python_advanced_assessment.md`  
**المسار المفترض لوضعه:** `data/knowledge_base/python/advanced/`

```markdown
# Python Advanced Assessment Database

## 1. Quizzes
### Question 1
- **Type:** Multiple Choice
- **Question:** What is the purpose of the `__init__` method in a Python class?
  - A) To delete an object from memory
  - B) To initialize the attributes of an object upon creation
  - C) To speed up execution time
  - D) To import external libraries
- **Answer:** B

---

## 2. Interview Questions
### Question 1: Explain the concept of Decorators in Python.
- **Answer:** A decorator is a design pattern in Python that allows a user to add new functionality to an existing object (like a function or class) without modifying its structure. They are usually called with the `@decorator_name` syntax.

---

## 3. Assignments
### Assignment 1: Custom Context Manager
- **Task:** Create a custom context manager using a class with `__enter__` and `__exit__` methods that logs the execution time of any block of code running inside a `with` statement.

---

## 4. Common Errors & Fixes
### Error 1: TypeError (Mutable Default Arguments)
- **Code with Error:**
  ```python
  def add_item(item, items_list=[]):
      items_list.append(item)
      return items_list
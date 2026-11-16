# Python Beginner Assessment Database

## 1. Quizzes
### Question 1
- **Type:** Multiple Choice
- **Question:** Which of the following is a valid variable name in Python?
  - A) `2variable`
  - B) `my-variable`
  - C) `my_variable`
  - D) `class`
- **Answer:** C
- **Explanation:** Variable names cannot start with numbers, cannot contain hyphens, and cannot use reserved keywords like 'class'.

### Question 2
- **Type:** Multiple Choice
- **Question:** What is the output of `print(type(3.14))`?
  - A) `<class 'int'>`
  - B) `<class 'float'>`
  - C) `<class 'str'>`
  - D) `<class 'double'>`
- **Answer:** B

---

## 2. Interview Questions
### Question 1: What is the difference between a List and a Tuple in Python?
- **Answer:** Lists are mutable, meaning their elements can be changed or modified after creation, and they use square brackets `[]`. Tuples are immutable, meaning they cannot be changed after creation, and they use parentheses `()`.

---

## 3. Assignments
### Assignment 1: Even or Odd Checker
- **Task:** Write a Python program that asks the user for an integer number and checks whether it is Even or Odd using the modulus operator (`%`).
- **Expected Output:** "The number 7 is Odd." or "The number 4 is Even."

---

## 4. Common Errors & Fixes
### Error 1: IndentationError
- **Code with Error:**
  ```python
  def say_hello():
  print("Hello")


  
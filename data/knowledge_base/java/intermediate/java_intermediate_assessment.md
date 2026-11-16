```markdown
# Java Intermediate Assessment Database

## 1. Quizzes
### Question 1
- **Type:** Multiple Choice
- **Question:** Which statement is true about an ArrayList in Java?
  - A) It has a fixed size that cannot change.
  - B) It can dynamically grow and shrink in size.
  - C) It can only store primitive data types like int.
  - D) It does not allow duplicate elements.
- **Answer:** B

---

## 2. Interview Questions
### Question 1: What is Method Overloading vs Method Overriding?
- **Answer:** Overloading occurs when two or more methods in the same class have the same name but different parameters. Overriding occurs when a subclass redefines a method already existing in its parent class with the exact same signature.

---

## 3. Assignments
### Assignment 1: Inventory System using ArrayList
- **Task:** Create an inventory program where users can add, remove, and display product names stored dynamically inside an `ArrayList<String>`.

---

## 4. Common Errors & Fixes
### Error 1: NullPointerException (NPE)
- **Code with Error:**
  ```java
  String name = null;
  System.out.println(name.length());
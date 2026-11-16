```markdown
# Java Advanced Assessment Database

## 1. Quizzes
### Question 1
- **Type:** Multiple Choice
- **Question:** Which keyword is used to implement Inheritance in Java?
  - A) `implements`
  - B) `extends`
  - C) `inherits`
  - D) `super`
- **Answer:** B

---

## 2. Interview Questions
### Question 1: What is Polymorphism in Java?
- **Answer:** Polymorphism is the ability of an object to take on many forms. The most common use is when a parent class reference is used to point to a child class object (e.g., `Animal myDog = new Dog();`), allowing dynamic method execution at runtime.

---

## 3. Assignments
### Assignment 1: Shape Hierarchy (OOP)
- **Task:** Design an abstract class `Shape` with an abstract method `calculateArea()`. Create subclasses `Circle` and `Rectangle` that implement this method using OOP principles.

---

## 4. Common Errors & Fixes
### Error 1: ClassCastException
- **Code with Error:**
  ```java
  Object obj = new Integer(100);
  String str = (String) obj; // Throws Exception
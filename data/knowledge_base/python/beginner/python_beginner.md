# Python — Beginner Level

## Variables & Data Types
```python
age = 25
price = 19.99
name = "Alice"
is_active = True
nothing = None

# Type checking
print(type(age))      # <class 'int'>
print(type(name))     # <class 'str'>
```

## Strings
```python
s = "Hello, World!"
print(s.upper())        # HELLO, WORLD!
print(s.lower())        # hello, world!
print(s.replace("Hello", "Hi"))
print(s.split(","))     # ['Hello', ' World!']
print(len(s))           # 13
print(s[0:5])           # Hello
print(f"Name: {name}, Age: {age}")  # f-string
```

## Lists
```python
fruits = ["apple", "banana", "cherry"]
fruits.append("mango")
fruits.remove("banana")
fruits.insert(1, "grape")
print(fruits[0])        # apple
print(fruits[-1])       # last item
print(len(fruits))
for fruit in fruits:
    print(fruit)
squares = [x**2 for x in range(5)]
```

## Dictionaries
```python
student = {"name": "Alice", "age": 20, "grade": "A"}
print(student["name"])
student["email"] = "alice@example.com"
for key, value in student.items():
    print(f"{key}: {value}")
```

## Tuples & Sets
```python
point = (3, 4)          # tuple — immutable
colors = {"red", "blue", "green"}  # set — unique values
colors.add("yellow")
colors.discard("red")
```

## Functions
```python
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"

def add(*numbers):
    return sum(numbers)

result = greet("Alice")
print(add(1, 2, 3, 4))
```

## Conditionals & Loops
```python
age = 20
if age >= 18:
    print("Adult")
elif age >= 13:
    print("Teen")
else:
    print("Child")

for i in range(5):
    print(i)

i = 0
while i < 5:
    i += 1

# break / continue
for i in range(10):
    if i == 5: break
    if i % 2 == 0: continue
    print(i)
```

## Error Handling
```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
finally:
    print("Done")
```

## File I/O
```python
with open("file.txt", "w") as f:
    f.write("Hello\n")

with open("file.txt", "r") as f:
    content = f.read()
```

## Common Interview Questions — Beginner
Q: Difference between list and tuple?
A: List is mutable, tuple is immutable. Tuples are faster for fixed data.

Q: What is None in Python?
A: None represents the absence of a value, similar to null in other languages.

Q: What is indentation in Python?
A: Python uses indentation (spaces/tabs) instead of curly braces to define code blocks.

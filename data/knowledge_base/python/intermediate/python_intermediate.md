# Python — Intermediate Level

## OOP — Classes & Inheritance
```python
class Animal:
    species_count = 0  # class variable

    def __init__(self, name: str, species: str):
        self.name = name          # instance variable
        self.species = species
        Animal.species_count += 1

    def speak(self) -> str:
        return f"{self.name} makes a sound"

    def __str__(self):
        return f"{self.name} ({self.species})"

    def __repr__(self):
        return f"Animal(name={self.name!r})"

class Dog(Animal):
    def __init__(self, name: str):
        super().__init__(name, "Dog")

    def speak(self) -> str:  # method overriding
        return f"{self.name} says Woof!"

dog = Dog("Rex")
print(dog.speak())
print(isinstance(dog, Animal))   # True
print(issubclass(Dog, Animal))   # True
```

## Properties & Encapsulation
```python
class BankAccount:
    def __init__(self, balance: float):
        self._balance = balance   # protected

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = value

    @staticmethod
    def validate_amount(amount):
        return amount > 0

    @classmethod
    def create_empty(cls):
        return cls(0.0)
```

## Generators & Iterators
```python
# Generator function
def count_up(n):
    for i in range(n):
        yield i

# Generator expression
gen = (x**2 for x in range(10))

# Custom iterator
class CountDown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

for n in CountDown(5):
    print(n)
```

## Decorators
```python
import functools

def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Done: {result}")
        return result
    return wrapper

def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@log
@repeat(3)
def greet(name):
    return f"Hello, {name}!"
```

## Context Managers
```python
class FileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False  # don't suppress exceptions

with FileManager("data.txt", "w") as f:
    f.write("Hello")

# Using contextlib
from contextlib import contextmanager

@contextmanager
def timer():
    import time
    start = time.time()
    yield
    print(f"Elapsed: {time.time() - start:.2f}s")

with timer():
    sum(range(1000000))
```

## Lambda & Functional Programming
```python
double = lambda x: x * 2
add = lambda x, y: x + y

numbers = [3, 1, 4, 1, 5, 9, 2, 6]

# map / filter / reduce
doubled = list(map(lambda x: x * 2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))

from functools import reduce
total = reduce(lambda x, y: x + y, numbers)

# sorted with key
students = [("Alice", 90), ("Bob", 85), ("Charlie", 95)]
sorted_students = sorted(students, key=lambda x: x[1], reverse=True)
```

## Modules & Packages
```python
# math
import math
print(math.sqrt(16))
print(math.pi)

# datetime
from datetime import datetime, timedelta
now = datetime.now()
tomorrow = now + timedelta(days=1)
print(now.strftime("%Y-%m-%d"))

# os / pathlib
import os
from pathlib import Path

path = Path("data/files")
path.mkdir(parents=True, exist_ok=True)
files = list(Path(".").glob("*.py"))
```

## Regular Expressions
```python
import re

text = "My email is alice@example.com and bob@test.org"

# Find all emails
emails = re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)

# Match / Search
pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
date = pattern.search("Date: 2024-01-15")
if date:
    print(date.group())

# Replace
clean = re.sub(r'\s+', ' ', "too   many    spaces")
```

## Exception Handling — Advanced
```python
class AppError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

class ValidationError(AppError):
    pass

class DatabaseError(AppError):
    pass

def process(data):
    if not data:
        raise ValidationError("Data is empty", code=400)

try:
    process(None)
except ValidationError as e:
    print(f"Validation failed [{e.code}]: {e}")
except AppError as e:
    print(f"App error: {e}")
```

## Interview Questions — Intermediate
Q: What is the difference between @staticmethod and @classmethod?
A: @staticmethod doesn't receive any implicit argument. @classmethod receives the class (cls) as first argument and can access/modify class state.

Q: What is a generator and why use it?
A: A generator yields values one at a time using yield, saving memory by not storing all values at once. Good for large datasets.

Q: What is a decorator?
A: A function that wraps another function to extend its behavior without modifying it. Uses @syntax.

Q: What is the difference between deep copy and shallow copy?
A: Shallow copy copies only the top level. Deep copy copies all nested objects.
```python
import copy
original = [[1, 2], [3, 4]]
shallow = copy.copy(original)
deep = copy.deepcopy(original)
```

Q: What is __slots__?
A: Restricts instance attributes to save memory.
```python
class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

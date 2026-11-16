# Python — Advanced Level

## Async / Await (Asyncio)
```python
import asyncio

async def fetch_data(url: str) -> str:
    await asyncio.sleep(1)  # simulate I/O
    return f"Data from {url}"

async def main():
    # Run sequentially
    result1 = await fetch_data("url1")
    result2 = await fetch_data("url2")

    # Run concurrently
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    )
    return results

asyncio.run(main())
```

## Threading & Multiprocessing
```python
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Threading (good for I/O-bound)
def worker(name):
    print(f"Thread {name} running")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()

# Thread pool
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(worker, i) for i in range(10)]

# Multiprocessing (good for CPU-bound)
def cpu_task(n):
    return sum(i**2 for i in range(n))

with ProcessPoolExecutor() as executor:
    results = list(executor.map(cpu_task, [100000]*4))
```

## Metaclasses
```python
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.connection = "Connected"

db1 = Database()
db2 = Database()
print(db1 is db2)  # True
```

## Descriptors
```python
class TypedField:
    def __init__(self, field_type):
        self.field_type = field_type
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        if not isinstance(value, self.field_type):
            raise TypeError(f"{self.name} must be {self.field_type}")
        obj.__dict__[self.name] = value

class Person:
    name = TypedField(str)
    age = TypedField(int)

    def __init__(self, name, age):
        self.name = name
        self.age = age
```

## Design Patterns
```python
# Observer Pattern
class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args, **kwargs):
        for cb in self._listeners.get(event, []):
            cb(*args, **kwargs)

emitter = EventEmitter()
emitter.on("data", lambda x: print(f"Received: {x}"))
emitter.emit("data", 42)

# Factory Pattern
class ShapeFactory:
    @staticmethod
    def create(shape_type, **kwargs):
        shapes = {"circle": Circle, "rectangle": Rectangle}
        if shape_type not in shapes:
            raise ValueError(f"Unknown shape: {shape_type}")
        return shapes[shape_type](**kwargs)

# Strategy Pattern
from abc import ABC, abstractmethod

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list:
        pass

class BubbleSort(SortStrategy):
    def sort(self, data):
        data = data.copy()
        n = len(data)
        for i in range(n):
            for j in range(n - i - 1):
                if data[j] > data[j+1]:
                    data[j], data[j+1] = data[j+1], data[j]
        return data

class QuickSort(SortStrategy):
    def sort(self, data):
        if len(data) <= 1:
            return data
        pivot = data[len(data) // 2]
        left = [x for x in data if x < pivot]
        mid = [x for x in data if x == pivot]
        right = [x for x in data if x > pivot]
        return self.sort(left) + mid + self.sort(right)
```

## Memory Management
```python
import sys
import gc

# Object size
x = [1, 2, 3]
print(sys.getsizeof(x))

# Reference counting
import ctypes
def ref_count(obj):
    return ctypes.c_long.from_address(id(obj)).value

# Garbage collection
gc.collect()
print(gc.get_count())

# __del__
class Resource:
    def __init__(self, name):
        self.name = name
        print(f"Acquired {name}")

    def __del__(self):
        print(f"Released {self.name}")
```

## Type Hints & Protocols
```python
from typing import TypeVar, Generic, Protocol, runtime_checkable
from typing import Optional, Union, List, Dict, Tuple, Callable

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None: ...

def render(obj: Drawable) -> None:
    obj.draw()
```

## Interview Questions — Advanced
Q: What is the GIL and how does it affect performance?
A: The Global Interpreter Lock prevents multiple threads from executing Python bytecode simultaneously. For CPU-bound tasks, use multiprocessing. For I/O-bound tasks, threading or asyncio work well.

Q: What is the difference between threading and asyncio?
A: Threading uses OS threads — good for I/O-bound but has GIL overhead. Asyncio uses a single thread with an event loop — better for many concurrent I/O operations with less overhead.

Q: What is a metaclass?
A: A class whose instances are classes. It controls class creation. type is the default metaclass.

Q: What are descriptors?
A: Objects that define __get__, __set__, __delete__ to control attribute access. Properties are implemented using descriptors.

Q: How does Python manage memory?
A: Through reference counting + cyclic garbage collector. When reference count hits 0, memory is freed. gc.collect() handles circular references.

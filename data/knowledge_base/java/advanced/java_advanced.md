# Java — Advanced Level

## Multithreading & Concurrency
```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.concurrent.locks.*;

// Thread creation
Thread t1 = new Thread(() -> System.out.println("Thread running"));
t1.start();
t1.join();

// ExecutorService
ExecutorService executor = Executors.newFixedThreadPool(4);
Future<Integer> future = executor.submit(() -> {
    Thread.sleep(1000);
    return 42;
});
int result = future.get(); // blocks until done
executor.shutdown();

// CompletableFuture
CompletableFuture<String> cf = CompletableFuture
    .supplyAsync(() -> "Hello")
    .thenApply(s -> s + " World")
    .thenApply(String::toUpperCase);
System.out.println(cf.get());

// ReentrantLock
ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    // critical section
} finally {
    lock.unlock();
}

// AtomicInteger
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();
counter.compareAndSet(1, 2);
```

## Design Patterns
```java
// Singleton
public class DatabaseConnection {
    private static volatile DatabaseConnection instance;
    private DatabaseConnection() {}

    public static DatabaseConnection getInstance() {
        if (instance == null) {
            synchronized (DatabaseConnection.class) {
                if (instance == null) {
                    instance = new DatabaseConnection();
                }
            }
        }
        return instance;
    }
}

// Builder
public class Person {
    private final String name;
    private final int age;
    private final String email;

    private Person(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
    }

    public static class Builder {
        private String name;
        private int age;
        private String email;

        public Builder name(String name) { this.name = name; return this; }
        public Builder age(int age) { this.age = age; return this; }
        public Builder email(String email) { this.email = email; return this; }
        public Person build() { return new Person(this); }
    }
}

Person person = new Person.Builder()
    .name("Alice").age(30).email("alice@example.com").build();

// Observer
public interface Observer { void update(String event); }

public class EventBus {
    private Map<String, List<Observer>> listeners = new HashMap<>();

    public void subscribe(String event, Observer observer) {
        listeners.computeIfAbsent(event, k -> new ArrayList<>()).add(observer);
    }

    public void publish(String event) {
        listeners.getOrDefault(event, Collections.emptyList())
                 .forEach(o -> o.update(event));
    }
}
```

## JVM Internals & Memory
```java
// Memory areas:
// Heap: objects and arrays
// Stack: method calls, local variables
// Metaspace: class metadata (Java 8+)
// Code Cache: compiled native code

// Garbage Collection
System.gc(); // suggest GC (not guaranteed)

// Memory leaks — common causes:
// 1. Static collections growing unbounded
// 2. Listeners not removed
// 3. ThreadLocal not cleaned
// 4. Caches without eviction

// WeakReference — allows GC
WeakReference<Object> weakRef = new WeakReference<>(new Object());
Object obj = weakRef.get(); // null if GC'd

// SoftReference — cleared only when memory low
SoftReference<byte[]> cache = new SoftReference<>(new byte[1024]);
```

## Reflection & Annotations
```java
import java.lang.reflect.*;
import java.lang.annotation.*;

// Custom annotation
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Test {
    String description() default "";
    boolean enabled() default true;
}

// Using reflection
Class<?> clazz = String.class;
Method[] methods = clazz.getDeclaredMethods();
for (Method m : methods) {
    if (m.isAnnotationPresent(Test.class)) {
        Test ann = m.getAnnotation(Test.class);
        System.out.println(ann.description());
    }
}

// Dynamic proxy
interface Service { String process(String input); }

Service proxy = (Service) Proxy.newProxyInstance(
    Service.class.getClassLoader(),
    new Class[]{Service.class},
    (proxyObj, method, args) -> {
        System.out.println("Before: " + method.getName());
        return "Processed: " + args[0];
    }
);
```

## Java 8-17 Features
```java
// Records (Java 16+)
public record Point(int x, int y) {
    public double distance() {
        return Math.sqrt(x * x + y * y);
    }
}

// Sealed classes (Java 17)
public sealed class Shape permits Circle, Rectangle, Triangle {}
public final class Circle extends Shape { double radius; }

// Pattern matching (Java 16+)
Object obj = "Hello";
if (obj instanceof String s && s.length() > 3) {
    System.out.println(s.toUpperCase());
}

// Switch expressions (Java 14+)
String day = "MONDAY";
int numLetters = switch (day) {
    case "MONDAY", "FRIDAY", "SUNDAY" -> 6;
    case "TUESDAY" -> 7;
    default -> throw new IllegalArgumentException();
};

// Text blocks (Java 15+)
String json = """
    {
        "name": "Alice",
        "age": 30
    }
    """;
```

## Interview Questions — Advanced
Q: What is the difference between synchronized and ReentrantLock?
A: synchronized is simpler, built into Java. ReentrantLock offers tryLock(), timed lock, fairness policy, and explicit unlock — more flexible but more verbose.

Q: What is CompletableFuture vs Future?
A: Future is blocking — get() waits for result. CompletableFuture supports chaining (thenApply, thenCompose), combining futures, and non-blocking callbacks.

Q: What is the difference between heap and stack memory?
A: Stack stores method frames and local variables — LIFO, thread-specific, fast. Heap stores objects — shared across threads, managed by GC, slower.

Q: What is the volatile keyword?
A: Ensures visibility of changes to a variable across threads. Prevents CPU caching of the variable. Does NOT guarantee atomicity.

Q: What is a deadlock and how to prevent it?
A: Deadlock occurs when two threads each hold a lock the other needs. Prevention: always acquire locks in the same order, use tryLock with timeout, minimize lock scope.

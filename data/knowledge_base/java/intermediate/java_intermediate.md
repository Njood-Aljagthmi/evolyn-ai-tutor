# Java — Intermediate Level

## OOP — Full
```java
// Abstract class
public abstract class Shape {
    protected String color;

    public Shape(String color) {
        this.color = color;
    }

    public abstract double area();
    public abstract double perimeter();

    public void describe() {
        System.out.printf("Shape: %s, Area: %.2f%n",
            getClass().getSimpleName(), area());
    }
}

// Interface
public interface Drawable {
    void draw();
    default String getDescription() {
        return "A drawable shape";
    }
}

// Concrete class
public class Circle extends Shape implements Drawable {
    private double radius;

    public Circle(String color, double radius) {
        super(color);
        this.radius = radius;
    }

    @Override
    public double area() { return Math.PI * radius * radius; }

    @Override
    public double perimeter() { return 2 * Math.PI * radius; }

    @Override
    public void draw() { System.out.println("Drawing circle"); }
}
```

## Encapsulation & Access Modifiers
```java
public class BankAccount {
    private double balance;      // private
    protected String owner;      // protected
    String bankName;             // package-private
    public final String currency; // public

    public BankAccount(String owner, double initialBalance) {
        this.owner = owner;
        this.balance = initialBalance;
        this.currency = "USD";
    }

    public double getBalance() { return balance; }

    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Amount must be positive");
        balance += amount;
    }

    public void withdraw(double amount) {
        if (amount > balance) throw new IllegalStateException("Insufficient funds");
        balance -= amount;
    }
}
```

## Collections Framework
```java
import java.util.*;

// ArrayList
List<String> list = new ArrayList<>();
list.add("Apple"); list.add("Banana"); list.add("Cherry");
list.remove("Banana");
Collections.sort(list);
System.out.println(list.contains("Apple"));

// LinkedList
LinkedList<Integer> linked = new LinkedList<>();
linked.addFirst(1); linked.addLast(3); linked.add(1, 2);

// HashMap
Map<String, Integer> map = new HashMap<>();
map.put("Alice", 95); map.put("Bob", 87);
map.getOrDefault("Charlie", 0);
for (Map.Entry<String, Integer> e : map.entrySet()) {
    System.out.println(e.getKey() + ": " + e.getValue());
}

// TreeMap (sorted)
Map<String, Integer> sorted = new TreeMap<>(map);

// HashSet
Set<String> set = new HashSet<>();
set.add("Java"); set.add("Python"); set.add("Java"); // duplicate ignored

// PriorityQueue
PriorityQueue<Integer> pq = new PriorityQueue<>();
pq.offer(5); pq.offer(1); pq.offer(3);
while (!pq.isEmpty()) System.out.print(pq.poll() + " "); // 1 3 5
```

## Generics
```java
// Generic class
public class Pair<A, B> {
    private A first;
    private B second;

    public Pair(A first, B second) {
        this.first = first;
        this.second = second;
    }

    public A getFirst() { return first; }
    public B getSecond() { return second; }
}

// Generic method
public static <T extends Comparable<T>> T findMax(List<T> list) {
    return Collections.max(list);
}

// Bounded wildcards
public static double sumList(List<? extends Number> list) {
    return list.stream().mapToDouble(Number::doubleValue).sum();
}
```

## Lambda & Streams
```java
import java.util.*;
import java.util.stream.*;

List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

// filter + map + collect
List<Integer> result = numbers.stream()
    .filter(n -> n % 2 == 0)
    .map(n -> n * n)
    .collect(Collectors.toList());

// reduce
int sum = numbers.stream().reduce(0, Integer::sum);

// sorted
List<String> names = Arrays.asList("Charlie", "Alice", "Bob");
names.stream().sorted().forEach(System.out::println);

// groupingBy
Map<Boolean, List<Integer>> partitioned = numbers.stream()
    .collect(Collectors.partitioningBy(n -> n % 2 == 0));

// Optional
Optional<Integer> first = numbers.stream()
    .filter(n -> n > 5)
    .findFirst();
first.ifPresent(System.out::println);
```

## Functional Interfaces
```java
import java.util.function.*;

// Predicate
Predicate<String> isLong = s -> s.length() > 5;
System.out.println(isLong.test("Hello"));     // false
System.out.println(isLong.test("Hello World")); // true

// Function
Function<String, Integer> strLen = String::length;
System.out.println(strLen.apply("Hello")); // 5

// Consumer
Consumer<String> printer = System.out::println;
printer.accept("Hello!");

// Supplier
Supplier<Double> randomNum = Math::random;
System.out.println(randomNum.get());

// BiFunction
BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;
System.out.println(add.apply(3, 4)); // 7
```

## Exception Handling — Advanced
```java
// Custom exceptions
public class AppException extends RuntimeException {
    private final int errorCode;

    public AppException(String message, int errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    public int getErrorCode() { return errorCode; }
}

// Try-with-resources
try (BufferedReader br = new BufferedReader(new FileReader("file.txt"));
     PrintWriter pw = new PrintWriter("output.txt")) {
    String line;
    while ((line = br.readLine()) != null) {
        pw.println(line.toUpperCase());
    }
} catch (IOException e) {
    System.err.println("IO Error: " + e.getMessage());
}
```

## Interview Questions — Intermediate
Q: What is the difference between ArrayList and LinkedList?
A: ArrayList uses dynamic array — O(1) random access, O(n) insert/delete in middle. LinkedList uses nodes — O(1) insert/delete at ends, O(n) random access.

Q: What is the difference between HashMap and TreeMap?
A: HashMap is unordered, O(1) average operations. TreeMap is sorted by key, O(log n) operations.

Q: What is method overloading vs overriding?
A: Overloading = same method name, different parameters (compile-time). Overriding = subclass redefines parent method (runtime).

Q: What is the difference between abstract class and interface?
A: Abstract class can have constructors, fields, concrete methods — single inheritance. Interface (Java 8+) can have default methods — multiple implementation allowed.

Q: What is autoboxing?
A: Automatic conversion between primitives and wrapper classes. int ↔ Integer, double ↔ Double, etc.

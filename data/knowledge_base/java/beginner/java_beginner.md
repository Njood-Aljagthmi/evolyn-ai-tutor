# Java — Beginner Level

## Variables & Data Types
```java
// Primitive types
int age = 25;
double price = 19.99;
boolean isActive = true;
char grade = 'A';
long bigNumber = 9999999999L;
float temperature = 36.6f;

// String
String name = "Alice";
String greeting = "Hello, " + name + "!";
String formatted = String.format("Name: %s, Age: %d", name, age);

// Constants
final int MAX_SIZE = 100;
```

## Arrays
```java
int[] numbers = {1, 2, 3, 4, 5};
String[] names = new String[3];
names[0] = "Alice";

System.out.println(numbers.length);

for (int num : numbers) {
    System.out.println(num);
}

int[][] matrix = {{1, 2}, {3, 4}};
```

## Strings
```java
String s = "Hello, World!";
System.out.println(s.length());
System.out.println(s.toUpperCase());
System.out.println(s.toLowerCase());
System.out.println(s.substring(0, 5));
System.out.println(s.contains("World"));
System.out.println(s.replace("Hello", "Hi"));
System.out.println(s.trim());
String[] parts = s.split(", ");
```

## Control Flow
```java
int age = 20;
if (age >= 18) {
    System.out.println("Adult");
} else if (age >= 13) {
    System.out.println("Teen");
} else {
    System.out.println("Child");
}

// switch
int day = 3;
switch (day) {
    case 1: System.out.println("Monday"); break;
    case 2: System.out.println("Tuesday"); break;
    default: System.out.println("Other");
}

// for
for (int i = 0; i < 5; i++) {
    System.out.println(i);
}

// while
int i = 0;
while (i < 5) {
    System.out.println(i++);
}

// do-while
do {
    System.out.println(i);
    i++;
} while (i < 5);
```

## Methods
```java
public class Calculator {
    public static int add(int a, int b) {
        return a + b;
    }

    public static double divide(double a, double b) {
        if (b == 0) throw new ArithmeticException("Cannot divide by zero");
        return a / b;
    }
}
```

## Basic OOP
```java
public class Student {
    String name;
    int age;
    double gpa;

    public Student(String name, int age, double gpa) {
        this.name = name;
        this.age = age;
        this.gpa = gpa;
    }

    public void study() {
        System.out.println(name + " is studying");
    }

    @Override
    public String toString() {
        return name + " (GPA: " + gpa + ")";
    }
}
```

## Exception Handling
```java
try {
    int result = 10 / 0;
    String s = null;
    s.length();
} catch (ArithmeticException e) {
    System.out.println("Math error: " + e.getMessage());
} catch (NullPointerException e) {
    System.out.println("Null error: " + e.getMessage());
} finally {
    System.out.println("Always executes");
}
```

## Interview Questions — Beginner
Q: What is the difference between == and .equals() in Java?
A: == checks reference equality (same memory address). .equals() checks value equality. Always use .equals() for Strings.

Q: What is the difference between int and Integer?
A: int is a primitive type. Integer is a wrapper class (object). Integer can be null, int cannot.

Q: What is the main method signature in Java?
A: public static void main(String[] args) — it's the entry point of every Java application.

Q: What is a NullPointerException?
A: Thrown when you try to use a null reference as if it were an object (calling methods, accessing fields).

**Dynamic Array** – A Dynamic Array is a **data structure that automatically resizes itself when elements are added or removed, allowing flexible storage compared to a fixed-size array**.

It provides the same indexed access as a normal array but can grow or shrink during runtime.

- Stores elements in contiguous memory like a [[Array]]
- Automatically resizes when capacity is exceeded
- Allows efficient random access using indices
- Manages memory using reallocation and copying
- Commonly used in high-level [[Programming Languages]] (e.g., vector in C++, ArrayList in Java)
- Improves flexibility in [[Data Structures]] compared to static arrays

Dynamic arrays are a flexible version of arrays that adjust their size automatically during program execution.

**Examples:**
- C++ `std::vector`
- Java `ArrayList`
- Python `list` (internally dynamic array)
- JavaScript arrays

___
#### Data Structures Layer
Core structures used to organize, store, and manage data efficiently in programming and algorithms.

[[Array]]  
[[Linked List]]  
[[Stack]]  
[[Queue]]  
[[Tree]]  
[[Graph]]  
[[Hash Table]]

#### Memory Management Layer
How data structures interact with memory allocation, resizing, and storage optimization during program execution.

[[Heap Memory]]  
[[Stack Memory]]  
[[Memory Allocation]]  
[[Garbage Collection]]  
[[Pointer]]

#### Programming Languages Layer
Language-level implementations and built-in support for dynamic data structures used in software development.

[[C++]]  
[[Java]]  
[[Python]]  
[[JavaScript]]  
[[Rust]]

#### Performance & Algorithm Layer
Efficiency considerations when using dynamic arrays in terms of speed, resizing cost, and memory usage.

[[Time Complexity]]  
[[Space Complexity]]  
[[Amortized Analysis]]  
[[Big O Notation]]  
[[Algorithm Optimization]]

#### How System Works?

Initial Array → Add Elements → Capacity Full → Create New Larger Array → Copy Data → Continue Adding

In short, a dynamic array is a resizable data structure that allows efficient storage and access of elements while automatically managing memory when size changes.
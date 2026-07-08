**Concurrency Bug** – A **software defect that occurs when multiple processes** or threads access shared resources at the same time in an incorrect or unsynchronized way, leading to unpredictable or incorrect results**.

#### Why it happens?
Modern programs often run multiple tasks simultaneously using:

- [[Thread]]
- [[Process]]
- [[Parallel Computing]]

Problems occur when they share:

- [[Memory]]
- [[Data]]
- [[Variables]]
- Resources

Without proper coordination.

#### Common causes

- missing synchronization
- race conditions
- incorrect locking
- shared memory access conflicts
- timing issues

#### Simple analogy

Imagine:

- 2 people editing the same Google Doc
- both save at the same time
- one overwrites the other’s work

In short, a Concurrency Bug is a programming defect that happens when multiple threads or processes access shared resources at the same time without proper synchronization, causing unpredictable or incorrect behavior.

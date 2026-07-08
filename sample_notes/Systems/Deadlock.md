**[[Deadlock]]** – A deadlock is a **situation where two or more processes, threads, or systems wait for each other indefinitely because each one is holding a resource that another one needs**.

Classic computer behavior: extremely efficient at doing absolutely nothing.

#### How deadlock happens?

Imagine:

```
Process A → holds Resource 1 → waiting for Resource 2Process B → holds Resource 2 → waiting for Resource 1
```

Result:

```
Nobody proceeds
```

That is a deadlock.

#### Four conditions for deadlock (Coffman Conditions)

All four usually exist:

- **Mutual Exclusion** → resource cannot be shared
- **Hold and Wait** → process holds one resource while waiting for another
- **No Preemption** → resource cannot be forcibly taken away
- **Circular Wait** → processes wait in a cycle


#### Where deadlock appears

- [[Operating System]] process scheduling
- [[Concurrency]] and [[Multithreading]]
- [[Database]] transactions
- [[Distributed Systems]]
- [[Resource Allocation]]

In short, Deadlock is a condition where multiple processes or threads become permanently blocked because each is waiting for resources held by the others.
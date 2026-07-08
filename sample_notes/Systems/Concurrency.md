**Concurrency** – The **ability of a computer system to manage and make progress on multiple tasks during overlapping periods of time, even if they are not all executing at the exact same moment**.

**Important:**
- **Concurrency ≠ Parallelism**
- Concurrency = dealing with many tasks
- Parallelism = actually executing many tasks simultaneously

#### Why concurrency exists?

- improve responsiveness
- better resource usage
- support many users/processes
- increase throughput

#### Simple analogy

One chef:

```
Cook pasta
↓
Check oven
↓
Cut vegetables
↓
Return to pasta
```

Many tasks are progressing.

That is concurrency.

(Parallelism would be hiring more chefs. Humans solved CPU scaling by inventing coworkers.)

In short, Concurrency is the ability of a system to manage multiple tasks during overlapping periods of time by coordinating execution and resource usage efficiently.
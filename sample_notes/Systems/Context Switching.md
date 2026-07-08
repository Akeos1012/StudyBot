**Context Switching** – Context switching refers to the **process where the CPU switches from executing one process or task to another by saving the current state and loading the state of the next process**. This allows multiple programs to share a single CPU efficiently.

- Saves the current state of a running process (registers, program counter, memory state)
- Loads the saved state of another process to resume execution
- Enables multitasking in [[Operating System]]
- Managed by the [[CPU]] and [[Scheduler]]
- Occurs in [[Process Management]] and [[Thread]] handling
- Introduces slight overhead due to switching time

Context switching is a core operating system mechanism that enables efficient multitasking by rapidly switching the CPU between different processes.

#### Operating System Layer
The layer responsible for managing processes, scheduling, and CPU execution.

[[Operating System]]  
[[Kernel]]  
[[Process Management]]  
[[Thread]]  
[[Scheduler]]

#### CPU & Execution Layer
The hardware and execution components involved in switching tasks.

[[CPU]]  
[[Registers]]  
[[Cache Memory]]  
[[Instruction Cycle]]  
[[Memory Management]]

#### Performance Layer
Factors that affect efficiency and speed during task switching.

[[Latency]]  
[[Throughput]]  
[[CPU Utilization]]  
[[Overhead]]  
[[Parallel Processing]]

#### How System Works?
Process A State Saved → CPU Switch → Process B State Loaded → Execution Continues

In short, It defines **how a computer system manages multiple tasks at runtime**, which is exactly a systems-level behavior.
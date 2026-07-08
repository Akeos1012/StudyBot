**CPU** - Central Processing Unit is the main part of a [[Computer]] that <u>executes instructions and performs calculations.</u> It controls all operations by running instructions through a repeated process called the **Instruction Cycle (Fetch–Decode–Execute Cycle)**.

![[Pasted image 20260616222210.png|697]]

___
## How the CPU Works: [[Instruction Cycle]]

All CPU components work inside a repeating cycle:
### 1. [[Fetch]]
- Instruction is retrieved from memory
- Stored in registers (like the Instruction Register)
### 2. [[Decode]]
- Control Unit interprets the instruction
- Determines what operations are needed
### 3. [[Execute]]
- ALU performs computation or logic operation
### 4. [[Memory Access]]
- Data is read from or written to memory if needed
### 5. [[Write-Back]]
- Result is stored in registers or memory

*This cycle repeats billions of times per second.*

_________________________________________________________
### 1. [[ALU]]

The **ALU** is the computational engine of the CPU.

*All calculations in a program eventually pass through the ALU.*

___
### 2. [[Registers]]

Registers are the CPU’s **fastest internal memory**.

**They temporarily store:**
- Data being processed
- Instructions currently in execution
- Memory addresses

**Types of registers:**
- [[General-Purpose Registers]] → temporary working data
- [[Special-Purpose Registers]] → control execution (e.g., Program Counter)
- [[Vector Registers]] → parallel data processing (SIMD operations)

*Registers are grouped into a structure called the **register file**, which feeds data directly into the ALU.*

____ 
### 3. [[Control Unit]]

The Control Unit acts as the **orchestrator of the CPU**.

**It does:**
- Fetches instructions from memory
- Decodes instructions into signals
- Coordinates ALU, registers, and memory operations
- Controls execution timing

*Without it, the CPU would be a collection of disconnected hardware.*

___
### 4. [[Store Unit]]

**The Load/Store Unit manages movement of data between:**
- Registers inside the CPU
- External memory (RAM)

*It ensures the CPU always has the correct data available for execution.*

___
## Supporting CPU Subsystems

Modern CPUs also include performance and memory systems:

**[[Cache Memory]]** - A small, ultra-fast memory layer that stores frequently used data to reduce RAM access delays.

**[[Memory Management Unit (MMU)]]** - Handles memory translation and protects memory access between programs.

**[[Memory Controller]]** - Manages communication between CPU and RAM.

___
## Types of CPUs (Architecture Level)

**[[Single-Core CPU]]**
- One processing core
- Executes one instruction stream at a time

**[[Multi-Core CPU]]**
- Multiple independent cores in one chip
- Executes multiple tasks in parallel

**[[Multi-Threaded CPU]]**
- Each core handles multiple instruction threads
- Improves efficiency by reducing idle time

**[[Vector Processor]]**
- Executes the same operation on multiple data points simultaneously
- Used in graphics, AI, and scientific computing

___
## In Short

A CPU is a coordinated system of specialized components:
- [[ALU]] → computes
- [[Registers]] → store active data
- [[Control Unit]] → directs execution
- [[Store Unit]] → moves data
- [[Cache Memory]] → speeds up access
- [[MMU]] → manages memory safely

CPU = person doing work

*All of them work together inside the **Instruction Cycle**, turning code into real machine actions.*

_____
## Intel vs AMD (Consumer CPU Families)

Both [[Intel]] and [[AMD]] mostly use the **x86-64 instruction set**, meaning they can run the same operating systems and software. Their difference is mainly in **microarchitecture, efficiency, cache design, core organization, and performance goals.**

- **AMD** → often stronger value and gaming efficiency
- **Intel** → often strong mixed productivity and responsiveness
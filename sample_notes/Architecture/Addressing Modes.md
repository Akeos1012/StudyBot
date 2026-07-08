**Addressing Modes** – Addressing modes are **methods used by the CPU to specify how and where to access an operand (data) during instruction execution in memory or registers**.

- Determines how the [[CPU]] finds the data needed for an instruction
- Defines the location of operands in [[Memory]] or [[Registers]]
- Improves flexibility and efficiency in instruction execution
- Used in [[Computer Architecture]] and processor design
- Affects performance and instruction complexity
- Works closely with [[Instruction Set Architecture]]

Addressing modes describe different ways a CPU can access data when executing machine instructions.

---

### Types of Addressing Modes

- **Immediate Addressing** → data is directly inside the instruction
- **Register Addressing** → data is stored in a CPU register
- **Direct Addressing** → instruction contains memory address of data
- **Indirect Addressing** → address points to another address in memory
- **Indexed Addressing** → uses base address + offset for data location
- **Relative Addressing** → uses program counter + offset

**Examples:**
- Adding a constant value directly in an instruction (Immediate)
- Fetching data from a register (Register Addressing)
- Accessing array elements using index (Indexed Addressing)
- Jump instructions using relative position (Relative Addressing)

---

#### Physical electronics domain

Focuses on how data is physically stored and retrieved inside processor components.

[[CPU]]  
[[Registers]]  
[[Cache Memory]]  
[[Memory Controller]]  
[[System Bus]]

#### Circuit design & logic domain

Focuses on how instruction logic is designed to locate and access data efficiently.

[[Digital Circuit]]  
[[Instruction Set Architecture]]  
[[Computer Architecture]]  
[[Microarchitecture]]  
[[Control Unit]]

#### System control & execution domain

Focuses on how the processor manages instruction execution and data flow during runtime.

[[Operating System]]  
[[Process Management]]  
[[Memory Management]]  
[[Compiler]]  
[[Interrupts]]

#### How it works

Instruction → Addressing Mode Selection → Locate Operand → Fetch Data → Execute Operation

##### Simple analogy

Addressing modes are like:

choosing how you find a friend—sometimes they’re standing next to you, sometimes you look them up in a directory, and sometimes you follow directions step-by-step to reach them.

In short, addressing modes define how a CPU accesses data needed to execute instructions efficiently and flexibly.
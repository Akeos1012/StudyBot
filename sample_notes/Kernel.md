**[[Kernel]]** – The kernel is the **core component of an [[Operating System]] responsible for managing hardware resources and controlling communication between software and hardware**. It is the first major software component loaded during system startup and remains active while the system is running.

![[Pasted image 20260622191526.png]]

The kernel does not provide the visible interface of the operating system. Instead, it works behind the scenes by allocating resources, controlling execution, and acting as the protected layer between applications and physical hardware.

The kernel is the central control layer of the operating system that manages hardware and provides services for software to run.

- Controls access to [[CPU]] time
- Allocates and protects [[RAM]] usage
- Communicates with hardware through [[Device Driver]]
- Handles reading and writing operations
- Executes and schedules running programs
- Manages communication between applications and system resources

___
#### How it works?

User  
↓  
Application  
↓  
Operating System  
↓  
Kernel  
↓  
Hardware

___ 
#### Kernel Functions

**Process Management** – Handles the scheduling, coordination, and execution of running processes within the system.

**Memory Management** – Controls memory usage by allocating and freeing space, managing virtual memory, and enforcing memory protection and sharing between programs.

**Device Management** – Oversees communication with hardware devices by providing a standard interface and coordinating interaction through device drivers.

**File System Management** – Manages how files are created, accessed, stored, and organized, while providing a consistent interface for applications.

**Resource Management** – Allocates and distributes system resources such as CPU time, disk space, and network bandwidth efficiently among processes.

**Security and Access Control** – Enforces system protection rules by managing authentication, permissions, and user access rights.

**Inter-Process Communication** – Enables processes to exchange data and coordinate with each other using methods like shared memory and message passing.

___ 
#### Resource Management Layer

Controls and distributes system resources while maintaining stability.

- [[CPU]]
- Process
- [[Thread]]
- [[Memory Management]]
- [[Scheduler]]

#### Hardware Interaction Layer

Provides controlled communication between software and physical devices.

- [[Device Driver]]
- [[Input & Output (I & O)]]
- [[Interrupt]]
- [[System Call]]
- [[Hardware]]
#### Storage & System Access Layer

Manages access to stored information and system resources.

- [[File System]]
- [[Storage Devices]]
- [[Virtual Memory]]
- [[Permission Management]]
#### Protection & Execution Layer

Maintains system security, isolation, and controlled execution.

- [[Kernel Mode]]
- [[User Mode]]
- [[Context Switching]]
- [[Process Isolation]]
#### Kernel Design Layer

Represents different architectural approaches to kernel construction.

- [[Monolithic Kernel]]
- [[Microkernel]]
- [[Hybrid Kernel]]
- [[Modular Kernel]]

In short, the kernel is the core execution and control layer of an operating system that manages hardware resources, executes system operations, and provides a secure bridge between applications and physical devices.

reference: 

GeeksforGeeks. (2026, April 23). _Kernel in operating system_. GeeksforGeeks. https://www.geeksforgeeks.org/operating-systems/kernel-in-operating-system/
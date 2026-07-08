**Contiguous Memory** – Contiguous memory refers to a **memory allocation method where a program is assigned a single continuous block of memory addresses in RAM**, meaning all its data is stored in adjacent locations without gaps.

- Allocates memory in a single continuous block in [[RAM]]
- Used in [[Memory Management]] by the [[Operating System]]
- Improves access speed due to sequential memory locations
- Common in simple allocation systems and early OS designs
- Can lead to [[Memory Fragmentation]] when free space is broken into pieces
- Often compared with non-contiguous methods like paging and segmentation

Contiguous memory is a memory allocation approach where processes are stored in one continuous region of physical memory for simpler and faster access.

#### Operating System Layer
The system that controls how memory is assigned and used by processes.

[[Operating System]]  
[[Kernel]]  
[[Process Management]]  
[[Scheduler]]  
[[File System]]

#### Hardware Layer
The physical memory where contiguous blocks are stored.

[[RAM]]  
[[Cache Memory]]  
[[Memory Controller]]  
[[Storage Devices]]  
[[Registers]]

#### Performance Layer
Factors affected by how memory is organized and accessed.

[[Latency]]  
[[Throughput]]  
Access Time  
[[Fragmentation]]  
Efficiency
#### How System Works?

Process Request → OS Finds Continuous Block in [[RAM]] → Memory Allocated → Program Executes in Sequence

In short, contiguous memory is a [[Memory Allocation]] method where a program is stored in a single continuous block of RAM for efficient access and execution.
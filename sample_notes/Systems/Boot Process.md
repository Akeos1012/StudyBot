**[[Boot Process]]** – The boot process refers to the **sequence of steps a computer system follows when it is powered on to initialize hardware, load firmware, and start the operating system**. It is the critical startup routine that transitions the system from an off state to a fully functional operating state.

- Begins when the system is powered on and the [[CPU]] starts execution
- Initializes hardware components through [[BIOS]] or [[UEFI]] firmware
- Performs hardware checks known as [[POST]] (Power-On Self Test)
- Locates and loads the operating system from [[Storage Devices]]
- Transfers control from firmware to the [[Operating System]] kernel
- Sets up system memory, drivers, and essential services

The boot process is a fundamental system initialization procedure that ensures all hardware and software components are correctly prepared before the computer becomes usable.

#### Hardware Layer

The physical components involved in system startup and initialization.

[[Motherboard]]  
[[CPU]]  
[[RAM]]  
[[Storage Devices]]  
[[CMOS Battery]]

#### Firmware & Initialization Layer

The low-level software that controls system startup before the operating system loads.

[[BIOS]]  
[[UEFI]]  
[[Firmware]]  
[[POST]]  
[[Bootloader]]

#### Operating System Layer

The software system that takes control after initialization is complete.

[[Operating System]]  
[[Kernel]]  
[[System Drivers]]  
[[System Services]]  
[[File System]]

#### Architecture Layer

The structural design concepts that define how system startup is organized.

System Architecture  
[[Memory Hierarchy]]  
[[Instruction Set Architecture]]  
[[Interrupt Handling]]  
[[Hardware Abstraction Layer]]

#### How System Works?

Power On → [[CPU]] Initialization → [[BIOS/UEFI]] → [[POST]] → Bootloader → [[Operating System]] Loads → System Ready

In short, the boot process is the startup sequence that initializes hardware and loads the operating system when a computer is powered on.
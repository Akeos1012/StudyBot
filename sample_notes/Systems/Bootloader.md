**[[Bootloader]]** – A bootloader is a **small, specialized program that runs immediately after the system starts and is responsible for loading the operating system into memory and transferring control to it**. It acts as a bridge between firmware and the operating system during system startup.

- Executed after [[BIOS]] or [[UEFI]] completes initial hardware checks
- Loads the [[Operating System]] kernel into [[RAM]]
- Initializes basic system parameters needed for OS startup
- Can support multiple operating systems (boot selection)
- Stored in [[Storage Devices]] such as HDD, SSD, or flash memory
- Acts as the final step of the [[Boot Process]] before OS control begins

The bootloader is a critical low-level software component that ensures the operating system is correctly loaded and executed after the computer powers on.

---
#### Firmware & Startup Layer

The layer responsible for initiating system startup and preparing hardware for the operating system.

[[BIOS]]  
[[UEFI]]  
[[Boot Process]]  
[[Firmware]]  
[[POST]]

#### Operating System Layer

The layer that the bootloader loads and hands control over to.

[[Operating System]]  
[[Kernel]]  
[[System Drivers]]  
[[File System]]  
[[System Services]]

#### Memory & Execution Layer

The components involved in loading and executing system software.

[[RAM]]  
[[Memory Address]]  
[[Registers]]  
[[CPU]]  
[[Cache Memory]]

#### Storage Layer

The systems where bootloader code is stored before execution.

[[Storage Devices]]  
[[SSD]]  
[[HDD]]  
[[Flash Memory]]  
[[File System]]

#### How System Works?

Power On → [[BIOS]] → Bootloader → Load [[Operating System]] → System Ready

In short, a Bootloader is a small program that loads the operating system into memory after system startup and transfers control to it.
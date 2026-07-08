**Device Driver** – A device driver is a **special type of software that allows the operating system and applications to communicate with and control hardware devices** such as printers, graphics cards, keyboards, and storage devices.

Without drivers, the OS would basically stare at hardware like it’s ancient alien technology.

- Acts as a translator between [[Operating System]] and [[Hardware]]
- Controls and manages devices like printers, GPU, keyboard, mouse
- Ensures hardware works correctly with [[Software]] applications
- Installed per device (each hardware often needs its own driver)
- Helps the system recognize and use new hardware automatically
- Works inside the system’s [[Kernel]] or user-space depending on design

A device driver is system software that enables communication between the operating system and hardware devices.

#### System Software Layer
The core layer where drivers operate.

[[Operating System]]  
[[Kernel]]  
[[System Software]]  
[[Firmware]]  
[[BIOS]]

#### Hardware Layer
Devices controlled by drivers.

[[CPU]]  
[[GPU]]  
[[Printer]]  
[[Storage Devices]]  
[[Input Devices]]

#### Communication Layer
How software talks to hardware.

[[API]]  
[[System Calls]]  
[[Interrupts]]  
[[I & O Operations]]  
[[Memory Management]]

**Example:**
- Install printer → driver lets OS send print commands
- Plug GPU → driver enables graphics processing
- Connect USB → driver allows file access

#### How System Works?

Application → Operating System → Device Driver → Hardware → Output


In short, a program that enables communication between the operating system and hardware devices.
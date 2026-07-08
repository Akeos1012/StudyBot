Buffer overflow is a **software error that happens when a program writes more data into a fixed-size memory buffer than it can hold, causing extra data to overwrite adjacent memory**.


#### How it happens?

A buffer has a fixed size:

```
Buffer size = 8 bytes
```

But the program tries to store:

```
"123456789ABC"
```

Result:

- data spills outside the buffer
- overwrites nearby memory
- causes crashes or unexpected behavior

Buffer overflow can lead to:

- [[Software]] crashes
- corrupted [[Memory]]
- unpredictable program behavior
- serious Security vulnerabilities (even hacking attacks)

#### Where it appears

- [[Programming]] errors in memory handling
- low-level languages like C and C++
- [[Operating System]] memory management
- [[System Software]] and drivers
- [[Cybersecurity]] exploits

#### Simple analogy
It’s like:

- putting 10 liters of water into a 5-liter bottle
- the extra water spills everywhere
- and ruins whatever was next to it

Same goes to computers.


In short, Buffer Overflow is an error that occurs when a program writes more data into a fixed-size memory buffer than it can hold, causing memory corruption and potentially security vulnerabilities.
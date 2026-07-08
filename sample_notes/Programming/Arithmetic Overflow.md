**Arithmetic Overflow** – a **computing error that happens when a calculation produces a numeric value that is too large (or too small) to be stored in the available fixed-size memory space for that number**.

- [[Programming]] calculations
- [[CPU]] arithmetic operations
- [[Data Type]] limits (int, float)
- [[Algorithms]] with large numbers
- [[Memory]] constraints

**Example:**
You asked the computer to store a number it physically doesn’t have enough bits to hold.

#### How it happens
Computers store numbers using a fixed number of bits.

Example (8-bit system):

```
Max value = 255
```

Now try:

```
200 + 100 = 300
```

But 300 cannot fit in 8 bits → overflow occurs.

#### Simple analogy
It’s like pouring water into a cup:

- Cup = memory size
- Water = number
- Too much water = overflow

In short, Arithmetic Overflow is an error that occurs when a calculation produces a number too large or too small to be stored within the fixed size limit of a computer’s data type.
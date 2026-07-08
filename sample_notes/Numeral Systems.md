A writing system to express the number in a consistent manner. 
## **Binary to Decimal**

Example: 1011₂ --> decimal
Break it down: 

1 × 2³ = 8
0 × 2² = 0
1 × 2¹ = 2
1 × 2⁰ = 1

Add them:  
**8 + 0 + 2 + 1 = 11**

**Final Answer:**  
**1011₂ = 11₁₀**

_____________________________________________________________
## Decimal to Binary

*Note: The standard method is **repeated division by 2**, keeping track of remainders.*

Example: 13₁₀  --> Binary
Break it down, divide by 2 repeatedly:

- 13 ÷ 2 = 6 remainder **1**     
- 6 ÷ 2 = 3 remainder **0**       
- 3 ÷ 2 = 1 remainder **1**       
- 1 ÷ 2 = 0 remainder **1**       

Read the remainders from bottom to top. 

**Final Answer:** 
**13₁₀ = 1101₂**

**0** - 0000
**1** - 0001
**2** - 0010
**3** - 0011
**4** - 0100
**5** - 0101
**6** - 0110
**7** - 0111
**8** - 1000
**9** - 1001 

_____________________________________________________________
## Binary to Octal

*Note: Group into 3s (add leading zeros if needed)*
Example: 153₈ --> octal

Break it down, Group into 3s: 
1101011 → 001 101 011

Convert each group:
- 001 = 1
- 101 = 5
- 011 = 3

**Final Answer:**
**1101011₂ = 153₈**

_____________________________________________________________
## Octal to Binary

*Note: Replace each octal digit with 3-bit binary*
Example: 153₈ --> binary

Break it apart:
- 1 → 001
- 5 → 101
- 3 → 011

Now combine them:
153₈ = 001101011₂

You can remove leading zeros. 

**Final Answer:**
**153₈ = 1101011₂**

_____________________________________________________________
## Decimal to Octal

*Note: Divide by 8 repeatedly. Read remainders bottom to top.*
Example: 125₁₀ --> octal

Divide and record remainders: 
- 125 ÷ 8 = 15 remainder **5**
- 15 ÷ 8 = 1 remainder **7**
- 1 ÷ 8 = 0 remainder **1**

**Final Answer:**
**125₁₀ = 175₈**

_____________________________________________________________
## Octal to Decimal

*Note: Expand using powers of 8*
Example: 175₈ --> decimal 

Break it down: 
$1 \cdot 8^2 + 7 \cdot 8^1 + 5 \cdot 8^0$

Now compute:
- 1 × 64 = 64
- 7 × 8 = 56
- 5 × 1 = 5

Add them:  
64 + 56 + 5 = **125**

**Final Answer:**
**175₈ = 125₁₀**

_____________________________________________________________
## Binary to Hexadecimal

*Note: Group binary into sets of 4 (right to left)*
Example: 11010111₂ --> hexadecimal 

Group into 4 bits:
1101 0111

Convert each group:
- 1101 = D
- 0111 = 7

**Final Answer:**
**11010111₂ = D7₁₆**

_____________________________________________________________
## Decimal to Hexadecimal

*Note: Divide by 16 repeatedly. Read bottom to top*
Example: 254₁₀ --> hexadecimal 

Divide and track remainders:
- 254 ÷ 16 = 15 remainder **14**
- 15 ÷ 16 = 0 remainder **15**

Convert remainders:
- 14 = E
- 15 = F

**Final Answer:**
254₁₀ = FE₁₆

_____________________________________________________________
## Octal to Hexadecimal

*Note: Octal → Binary → Hex*
***Step 1:** Convert each octal digit to 3-bit binary*
***Step 2:** Group binary into 4-bit chunks*
***Step 3:** Convert each chunk to hex*

Example: 175₈ --> hexadecimal 

**Step 1: Octal → Binary**
1 → 001
7 → 111
5 → 101
175₈ = 001111101₂

**Step 2: Group into 4 bits (right to left)**
0011 1110 1

Add leading zeros:
0001 1111 1101

**Step 3: Convert to hex**
0001 = 1
1111 = F
1101 = D

**Final Answer:**
**175₈ = 1FD₁₆**

_____________________________________________________________
## Hexadecimal to Binary 

*Note: Replace each hex digit with 4-bit binary*
Example: D7₁₆ --> binary

Break it down:
- D = 13 = 1101
- 7 = 0111

**Final Answer:**
**D7₁₆ = 11010111₂**

_____________________________________________________________
## Hexadecimal to Decimal 

*Note: Expand using powers of 16*
Example: D7₁₆ --> decimal

Break it down:
$13 \cdot 16^1 + 7 \cdot 16^0$

Now compute:
- 13 × 16 = 208
- 7 × 1 = 7

Add them:  
208 + 7 = **215**

**Final Answer:**
**D7₁₆ = 215₁₀**
_____________________________________________________________
## Hexadecimal  to Octal

*Note: Hex → Binary → Octal*
***Step 1:** Convert each hex digit to 4-bit binary*
***Step 2:** Group binary into 3-bit chunks (right to left)*
***Step 3:** Convert each group to octal*

Example: D7₁₆ --> octal

**Step 1: Hex → Binary**
D = 1101
7 = 0111
D7₁₆ = 11010111₂

**Step 2: Group into 3 bits**
11010111 → 011 010 111
*(Add leading zero if needed)*

**Step 3: Convert to octal**
011 = 3
010 = 2
111 = 7

**Final Answer:**
**D7₁₆ = 327₈**

_____________________________________________________________
## Quick reference:

| Binary | Hex |
| ------ | --- |
| 0000   | 0   |
| 0001   | 1   |
| 0010   | 2   |
| 0011   | 3   |
| 0100   | 4   |
| 0101   | 5   |
| 0110   | 6   |
| 0111   | 7   |
| 1000   | 8   |
| 1001   | 9   |
| 1010   | A   |
| 1011   | B   |
| 1100   | C   |
| 1101   | D   |
| 1110   | E   |
| 1111   | F   |

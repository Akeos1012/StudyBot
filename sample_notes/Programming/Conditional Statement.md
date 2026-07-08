**Conditional Statement** – A **programming control structure that allows a program to make decisions by executing different blocks of code depending on whether a condition is true or false**. It is one of the core ways software behaves dynamically instead of running in a straight line.

#### How it Works?

A conditional statement checks a condition using **[[Boolean]] logic**:

- **True → run code A**
- **False → run code B**

---
#### Basic structure

```
IF condition is true:    
     do something    
ELSE:
     do something else
```

#### Simple If Statement

```
age = 18

if age >= 18:    
    print("You are allowed to vote")
```

#### What happens:

- Condition: `age >= 18`
- Result: True
- Output: `You are allowed to vote`

---
#### If–Else Statement

```
temperature = 30

if temperature > 35:    
    print("It's too hot")
else:    
    print("Weather is normal")
```

#### What happens:

- Condition is false (30 is not > 35)
- Program runs the `else` block

---
#### If – Else If – Else

```
score = 85

if score >= 90:    
    print("A grade")
elif score >= 75:    
    print("B grade")
else:    
    print("C grade")
```

#### What happens:

- 85 matches `score >= 75`
- Output: `B grade`

---
#### Real-life analogy

Think of it like a vending machine:

- If you press **A1 → Coke**
- If you press **B2 → Water**
- If nothing matches → “Invalid selection”

That’s conditional logic.

---
#### Where it is used

Conditional statements are everywhere in programming:

- login systems (password correct?)
- games (player health = 0?)
- apps (dark mode ON?)
- websites (user logged in?)

---
#### Related concepts

- [[Conditional Branching]] → the concept of decision paths
- [[Boolean]] → true/false logic
- [[Comparison Operation]] → checks like `>`, `<`, `==`
- [[Algorithms]] → step-by-step logic that uses conditions


In short, Conditional statement is a programming structure that allows a program to make decisions and execute different code depending on whether a condition is true or false.
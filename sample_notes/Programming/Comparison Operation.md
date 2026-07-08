**[[Comparison Operation]]** – A **basic programming and logic operation that compares two values and returns a Boolean result (True or False)**. It is used to make decisions in programs, algorithms, and conditions.

#### Common comparison operators

|Operator|Meaning|Example|
|---|---|---|
|`==`|equal to|`5 == 5 → True`|
|`!=`|not equal|`5 != 3 → True`|
|`>`|greater than|`10 > 3 → True`|
|`<`|less than|`2 < 8 → True`|
|`>=`|greater or equal|`5 >= 5 → True`|
|`<=`|less or equal|`4 <= 9 → True`|

#### Example 1: Simple comparison

```
x = 10
y = 5

print(x > y)
```

Output:

```
True
```

#### Example 2: Using equality

```
password = "1234"
if password == "1234":    
    print("Access granted")
```

Output:

```
Access granted
```

#### Example 3: Real decision making

```
age = 17
if age >= 18:    
    print("You can vote")
else:    
    print("You cannot vote")
```

Output:

```
You cannot vote
```

#### Where it is used?

Comparison operations are used everywhere in programming:

- login systems (password correct?)
- games (health > 0?)
- apps (user logged in?)
- algorithms (sorting numbers)
- AI decisions (confidence score > threshold?)

#### Related concepts

- [[Conditional Statement]] → uses comparisons to decide actions
- [[Boolean]] → result of comparisons (True/False)
- [[Algorithms]] → decision logic
- [[Operators]] → symbols like `>`, `<`, `==`

In short, a comparison operation is a programming operation that compares two values and returns True or False, used to control logic and decision-making in programs.
**Bohrbug** – A **type of software bug that is consistent and reproducible**, meaning it always appears when the same conditions are met, making it easier to detect and fix compared to unpredictable bugs.

Yes, it’s named after Niels Bohr, because unlike quantum chaos, this bug behaves nicely and _does the same annoying thing every time_.

- A stable and reproducible [[Bug]] in [[Software]]
- Happens under specific, repeatable conditions
- Easier to find using [[Debugger]] and Testing
- Often caused by clear logic errors in [[Programming]]
- Opposite of a [[Heisenbug]] (which disappears when you observe it)
- Common during Software Development and Debugging

A Bohrbug is a consistent software defect that can be reliably reproduced and fixed once identified.

___
#### How it happens?

A Bohrbug usually comes from **deterministic mistakes in programming**, such as:

#### 1. Logic mistakes in code

- wrong condition (`if x > 10` instead of `>= 10`)
- incorrect formula
- missing case in an algorithm

Same input → same wrong output → always reproducible

#### 2. Incorrect assumptions

- assuming input is always valid
- assuming values are never null
- assuming order of execution never changes

When reality disagrees, the bug _always shows up the same way_


#### 3. Deterministic execution flow

If the program always runs the same steps:

- same input
- same memory state
- same environment

 the bug triggers consistently

___
#### Simple analogy

- Bohrbug → predictable, like a broken switch that _always_ fails
- [[Heisenbug]] → shy bug that disappears when you look at it
- [[Mandelbug]] → chaotic bug caused by complex system interactions

In short, A Bohrbug is a consistent and reproducible software bug that appears under the same conditions every time, making it easier to detect and fix during debugging.
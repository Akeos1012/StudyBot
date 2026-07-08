\---

topic: Database

difficulty: beginner

tags: \[sql, dbms]

\---



\# Database Normalization



\## What is Normalization?

Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity.



\## First Normal Form (1NF)

\- Each table cell must contain a single value (atomic)

\- Each column must have a unique name

\- The order of rows and columns doesn't matter



\## Second Normal Form (2NF)

\- Must be in 1NF first

\- All non-key attributes must depend on the entire primary key



\## Third Normal Form (3NF)

\- Must be in 2NF first

\- No transitive dependencies (non-key attributes shouldn't depend on other non-key attributes)



\## Why Normalize?

\- Reduces data redundancy

\- Improves data integrity

\- Makes database more efficient


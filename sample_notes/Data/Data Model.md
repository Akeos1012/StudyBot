**Data Model** – A data model is a **structured representation that defines how data is organized, related, stored, and understood inside a system or database**. It acts like a blueprint that shows what data exists and how different pieces of information connect to each other.

- Defines the structure and relationships of [[Data]]
- Describes entities, attributes, and connections between them
- Used to design [[Database]] systems before implementation
- Helps maintain consistency and reduce data design errors
- Supports [[Data Integration]] and system interoperability
- Commonly represented using diagrams and schemas
- A data model is a **blueprint for organizing and defining relationships between data**.

A data model is a blueprint used to organize information and guide how data is stored, managed, and accessed in software systems.

#### Data Design Layer
Defines how information is structured.

[[Data]]  
[[Dataset]]  
[[Database]]  
[[Schema]]  
[[Data Structure]]
#### Database Layer
Systems that implement data models.

[[Database Management System]]  
[[Data Warehouse]]  
[[SQL]]  
[[NoSQL]] Database  
[[Data Mapping]]
#### Architecture Layer
How systems organize information.

[[System Design]]  
[[Data Integration]]  
[[Data Pipeline]]  
[[Distributed Systems]]  
[[Entity Relationship Diagram]]

#### Common Types of Data Models

- **Conceptual Model** → high-level business view
- **Logical Model** → defines entities and relationships
- **Physical Model** → actual database implementation

#### Example
An online store:

Customer
- CustomerID
- Name

Order
- OrderID
- CustomerID

Relationship:
One Customer → Many Orders


#### How System Works?

Requirements → Data Model → Database Design → Storage → Application Usage

In short, a Data Model is a blueprint that defines how data is structured and connected before it is stored and used inside databases and systems.
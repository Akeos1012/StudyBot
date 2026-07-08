**DevOps** – DevOps is a **set of practices and a culture that combines software development (Dev) and IT operations (Ops) to automate and improve the process of building, testing, deploying, and maintaining software systems continuously and efficiently**.

![[Pasted image 20260625154058.png]]

- Combines Software Development and [[IT Operations]]
- Uses automation for building, testing, and deploying software
- Relies on [[CI & CD]] pipelines for continuous integration and delivery
- Improves collaboration between developers and system administrators
- Uses [[Cloud Computing]] and infrastructure automation tools
- Focuses on reliability, scalability, and fast software delivery

DevOps is a methodology that integrates development and operations to automate and streamline software delivery and system management. **DevOps** works as a **continuous automated loop that connects software development and IT operations so code can be built, tested, deployed, and monitored repeatedly with minimal manual work**.

___
### How DevOps works step-by-step

#### 1. Code Development

Developers write code using [[Programming]] tools and push it to a shared repository ([[Version Control]] like Git).

---

#### 2. Continuous Integration (CI)
Every change triggers automation:

- Code is automatically built
- [[Unit Testing]] runs
- [[Bug]] checks happen early

Goal: catch errors immediately instead of later.

---

#### 3. Continuous Delivery / Deployment (CD)

If tests pass:

- Code is packaged
- Prepared for release
- Sometimes automatically deployed to production

This uses [[CI & CD]] pipelines.

---

#### 4. Infrastructure Setup
Applications are deployed using:

- [[Cloud Computing]]
- [[Server]] systems
- [[Containerization]] (Docker)
- [[Kubernetes]] orchestration

---

#### 5. Monitoring & Feedback
After deployment:

- [[Monitoring]] tracks performance
- [[Logging]] records system behavior
- [[Error Handling]] detects issues

Problems go back to developers → fix → redeploy.

#### How System Works?

Code → Build → Test → Deploy → Run → Monitor → Improve → repeat

In short, DevOps is a set of practices and tools used to automate software development, testing, deployment, and system operations
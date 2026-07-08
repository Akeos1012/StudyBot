**CI/CD** –  **(Continuous Integration and Continuous Delivery)** It is a **software development practice that automates the process of building, testing, and delivering code changes to users quickly and reliably**.

It is used to make software updates faster, safer, and more consistent by reducing manual steps in deployment.

- **Continuous Integration (CI)**: Developers frequently merge code into a shared repository, where it is automatically built and tested using tools like [[Version Control]] and automated testing systems
- **Continuous Delivery (CD)**: Code that passes tests is automatically prepared for release to production environments
- **Continuous Deployment (CD)**: Every validated change is automatically deployed to production without manual approval
- Uses [[Automation]] pipelines to reduce human error
- Common in [[DevOps]] and modern Software Development workflows
- Often runs on [[Cloud Computing]] platforms for scalability

CI/CD is a modern software engineering approach that streamlines code integration, testing, and deployment into an automated pipeline.

#### Continuous Integration (CI)

- Developers frequently merge code into a shared repository using [[Version Control]]
- Each code change is automatically built and tested
- Detects bugs and integration issues early
- Ensures code from multiple developers works together smoothly
- Uses automated testing and build systems
- Improves code quality and team collaboration
#### Continuous Delivery (CD)

- Code that passes CI tests is automatically prepared for release
- Ensures software is always in a deployable state
- Requires manual approval before production release
- Automates staging and release preparation steps
- Reduces deployment risks and errors
- Improves release consistency and reliability
#### Continuous Deployment (CD)

- Every tested and validated change is automatically deployed to production
- No manual approval required before release
- Fully automated release pipeline
- Enables rapid and continuous updates for users
- Relies heavily on [[Automation]] and [[Cloud Computing]]
- Requires strong testing to ensure stability

- **CI → Build + Test code automatically**
- **CD (Delivery) → Prepare release automatically**
- **CD (Deployment) → Release automatically to users**

In short, CI/CD is a software engineering pipeline that automates code integration, testing, and deployment to deliver faster and more reliable software updates.
# StudyBot

## Alpha Testing

StudyBot is currently in the Alpha Testing stage.

The application is functional and actively maintained. Alpha testing is intended to evaluate the application's features, reliability, usability, and overall behavior while development continues.

The project is expected to change during this stage. Features may be added, modified, improved, or removed as development and testing progress.

---

## About StudyBot

StudyBot is an AI-powered study companion designed to help students study using their own learning materials.

The project focuses on generating study questions from user-provided educational notes while keeping generated content grounded in the available source material.

---

## Important Features

### AI-Assisted Quiz Generation

StudyBot can generate quiz questions based on available study materials.

The system supports different question formats and generation methods intended to provide varied practice questions.

### Source-Grounded Questions

Questions are generated from the user's study materials rather than relying entirely on general AI knowledge.

The system is designed to reduce unsupported or invented information by validating generated questions against available source material.

### Question Validation

Generated questions go through validation checks before being accepted.

Validation is used to detect issues such as unsupported information, invalid question structures, duplicates, and other quality problems.

### Question Explanations

StudyBot can provide explanations for generated questions to help users understand why an answer is correct.

### Question Caching

Previously generated questions can be stored and reused when appropriate, reducing unnecessary regeneration.

### Study Material Support

StudyBot is designed to work with structured study notes and educational materials, allowing users to use their existing notes as a source for quiz generation.

### Configuration

Application settings can be managed through a centralized configuration system.

Environment variables can be used to override selected settings without modifying the application source code.

---

## Current Testing Status

StudyBot is currently undergoing Alpha Testing.

The application is functional, but it should not yet be considered a fully stable release.

Testing during this stage focuses on:

* Feature reliability
* Question quality
* Answer correctness
* Source grounding
* Validation accuracy
* Performance
* Error handling
* Usability
* Unexpected behavior

Issues discovered during testing may result in changes to the application's behavior.

---

## Known Limitations

StudyBot is still under active development.

Potential limitations include:

* Generated questions may occasionally require additional validation.
* Some study materials may not be suitable for automatic question generation.
* AI generation performance depends on the available hardware and configured model.
* Features and behavior may change during Alpha development.
* Some functionality may still be incomplete or experimental.

---

## Requirements

Before running StudyBot, ensure the required software and dependencies are installed.

Typical requirements include:

* Python 3.11 or compatible Python version
* A Python virtual environment
* Required Python packages
* Ollama for local AI model execution
* A compatible local language model

Refer to the project documentation and configuration files for the current setup requirements.

---

## Configuration

StudyBot supports environment-based configuration for selected settings.

Environment variables use the `STUDYBOT_` prefix to avoid conflicts with unrelated system or application variables.

A `.env` file may be used for local configuration.

Example:

```env
STUDYBOT_DEBUG=true
STUDYBOT_API_HOST=127.0.0.1
STUDYBOT_API_PORT=8000
STUDYBOT_API_RELOAD=true
STUDYBOT_LLM_MODEL=qwen2.5:3b
STUDYBOT_DB_PATH=analytics.db
```

The `.env` file should remain local and should not be committed to the repository.

---

## Running the Project

Activate the project's virtual environment and run the application using the project's current startup procedure.

For development and testing, refer to the project's existing setup instructions and test commands.

---

## Testing

The project includes automated tests for verifying application behavior.

The smoke test can be executed with:

```bash
python -m pytest tests/smoke/test_quick.py
```

A passing smoke test indicates that the primary quiz pipeline is functioning under the tested conditions.

---

## Alpha Testing Guidelines

Alpha testers are encouraged to:

1. Use StudyBot with different study materials.
2. Generate different types and quantities of questions.
3. Check whether generated answers are correct.
4. Check whether questions are supported by the provided study material.
5. Report crashes and unexpected behavior.
6. Report incorrect or misleading questions.
7. Report problems with explanations.
8. Report performance issues.
9. Provide feedback on usability.
10. Record the conditions under which an issue occurred.

When reporting an issue, include enough information to reproduce the problem whenever possible.

---

## Documentation

Project documentation will be expanded as development continues.

Documentation may include:

* Installation instructions
* Configuration instructions
* Usage instructions
* Feature documentation
* Testing procedures
* Troubleshooting
* Development notes
* Alpha testing information


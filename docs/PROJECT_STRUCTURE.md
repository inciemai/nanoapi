## Project Structure (No Code)

This document outlines the high-level layout of the NanoAPI Quiz Platform repository and the purpose of each directory/file. It intentionally avoids including any code.

### Repository Tree

```
.
├─ config.py                 # Centralized configuration loading (env vars, constants)
├─ run_services.py           # App/service bootstrap entrypoint
├─ requirements.txt          # Python dependencies
├─ README.md                 # Quickstart and top-level overview
├─ docs/                     # Documentation (architecture, API, guides)
│  ├─ api.md                 # REST API reference
│  ├─ PROJECT_STRUCTURE.md   # This file
│  └─ Project_Documentation.md  # Comprehensive product & tech documentation
├─ services/                 # Request handlers and business logic grouped by feature
│  ├─ create_quiz.py         # Create new quizzes (admin)
│  ├─ dashboard.py           # Admin dashboard metrics
│  ├─ decode_token.py        # Utility endpoint to decode JWT
│  ├─ delete_question.py     # Remove a question from a quiz (admin)
│  ├─ delete_quiz.py         # Delete quiz (admin)
│  ├─ get_all_quizzes_detailed.py # Full quiz details (diagnostics)
│  ├─ get_quiz.py            # Fetch a single quiz (without answers)
│  ├─ get_quizzes.py         # List quizzes
│  ├─ get_user.py            # Fetch a single user with derived stats
│  ├─ get_users.py           # List users (admin)
│  ├─ leaderboard.py         # Compute and return leaderboard
│  ├─ login.py               # Authenticate and issue JWT
│  ├─ quiz_info.py           # Per-user quiz attempt summaries
│  ├─ register.py            # User registration and validation
│  ├─ submit_quiz.py         # Submit and score quiz attempts
│  ├─ update_quiz.py         # Update quiz metadata/questions (admin)
│  └─ verify_token.py        # Verify token and return current user
└─ utils/                    # Shared utilities and helpers
   └─ auth.py                # JWT encode/decode, auth helpers
```

### Conventions

- Naming
  - Filenames are verbs or verb-phrases for request handlers (e.g., `create_quiz.py`).
  - Shared helpers live in `utils/` and are nouns for capabilities (e.g., `auth.py`).

- Responsibilities
  - `services/` contains request handling, validation, and orchestration of business rules.
  - `utils/` contains stateless helpers that are safe to reuse across services.
  - `config.py` is the single place to read environment variables and constants.

- Separation of Concerns
  - Data access and transformation should be encapsulated within the relevant service file.
  - Cross-cutting concerns (auth, pagination rules, error envelopes) should be implemented once in `utils/` and reused.

- Error Handling
  - Return consistent error envelopes and HTTP status codes as documented in `docs/api.md`.

- Security
  - All protected endpoints must validate Bearer JWTs via `utils/auth.py`.
  - Admin-only endpoints must enforce role checks consistently.

- Documentation
  - API changes: update `docs/api.md`.
  - Architectural or behavior changes: update `docs/Project_Documentation.md`.



    ## NanoAPI Quiz Platform — REST API Documentation

    This document describes the REST API exposed by the Quiz application.

    - Base URL: `http://localhost:5000`
    - Content-Type: `application/json`
    - Authentication: Bearer JWT in `Authorization: Bearer <token>` header for protected endpoints.

    ### Authentication Overview
    - Obtain JWT: `POST /login`
    - Include token in subsequent requests as `Authorization: Bearer <token>`
    - Token payload fields: `user_id`, `role`, `name`, `email`, `phone`, `school`, `iat`, `exp`
    - Roles: `admin`, `user`

    ### Health
    - GET `/health`
    - Public. Returns service and DB status.

    ---

    ### Auth
    1) POST `/login`
    - Public
    - Body:
    ```
    {
    "email": "admin" | "user@example.com",
    "password": "string"
    }
    ```
    - Notes: If `email` equals configured admin username, password is compared to admin password directly; otherwise, user login checks hashed password.
    - 200 Response:
    ```
    {
    "status": true,
    "message": "Login successful",
    "token": "<jwt>",
    "user": {
        "user_id": "string",
        "name": "string",
        "username": "email-or-admin",
        "phone": "string",
        "school": "string",
        "role": "admin|user"
    }
    }
    ```

    2) GET `/verify-token`
    - Protected (Bearer). Any authenticated user.
    - Returns current user info decoded from token.

    3) POST `/decode-token`
    - Public
    - Body:
    ```
    { "token": "<jwt>" }
    ```
    - 200 Response includes decoded user data and token times (`issued_at`, `expires_at`).

    ---

    ### Users
    1) POST `/register`
    - Public
    - Body:
    ```
    {
    "name": "string",
    "email_id": "string",
    "phone": "+91-0000000000",
    "password": "string",
    "confirm_password": "string",
    "school": "string"
    }
    ```
    - Rules: `email_id` must contain `@`; `phone` must match `+91-XXXXXXXXXX`; password must match confirm.
    - 201 Response returns created user basics and role (`admin` if admin creds, else `user`).

    2) GET `/users`
    - Protected (Bearer, admin)
    - Query params (either standard or positional):
    - `page` (default 1), `limit` (default 10, max 100)
    - 200 Response: `{ status: true, users: [ ...no password... ], pagination: { ... } }`

    3) GET `/user/{user_id}`
    - Protected (Bearer)
    - Path: `user_id` is Mongo ObjectId
    - 200 Response: `{ status: true, user: { ...derived fields... } }`
    - Adds: `total_questions`, `total_questions_attempted`, `rank`, `time_taken`, `score: { total_correct, total_questions }`, `is_quiz_attempted`

    ---

    ### Quizzes
    1) GET `/quizzes`
    - Public
    - Query: `created_by` (optional)
    - Returns list of quizzes without `correct_answer` in questions.

    2) GET `/quizzes/all`
    - Public
    - Query: `created_by` (optional)
    - Returns full quiz details including `correct_answer`. Intended for administrative/diagnostic use; no auth enforced in code.

    3) GET `/quiz/{quiz_id}`
    - Protected (Bearer)
    - Returns a single quiz without `correct_answer`; preserves `question_id`.

    4) POST `/quiz`
    - Protected (Bearer, admin)
    - Body:
    ```
    {
    "title": "string",
    "questions": [
        {
        "question": "string",
        "options": ["A", "B", ...],
        "correct_answer": "A"
        }
    ]
    }
    ```
    - Behavior: Generates `question_id` for each question. Response omits `correct_answer` for security.
    - 201 Response returns created quiz metadata and questions without answers.

    5) PUT `/quiz/{quiz_id}`
    - Protected (Bearer, admin)
    - Body (partial update accepted):
    ```
    {
    "title": "string?",
    "questions": [
        {
        "question_id": "string?",   // optional; auto-generated if missing
        "question": "string",
        "options": ["A","B",...],
        "correct_answer": "A"
        }
    ]
    }
    ```
    - Behavior: Appends provided questions to existing list; updates `title` if provided; updates `total_questions`, `updated_by`, `updated_at`.
    - 200 Response returns updated metadata and questions without answers.

    6) DELETE `/quiz/{quiz_id}`
    - Protected (Bearer, admin)
    - Deletes quiz; returns minimal info of deleted quiz.

    7) DELETE `/quiz/{quiz_id}/question/{question_id}`
    - Protected (Bearer, admin)
    - Removes one question by `question_id`. Cannot delete the last remaining question; returns 400 if attempted.

    8) POST `/quiz/{quiz_id}/submit`
    - Protected (Bearer)
    - Body:
    ```
    {
    "questions": [
        {
        "question_id": "string",
        "answer": "string",
        "answered": true,           // optional, default true
        "time_taken": 1.23          // seconds per question, optional
        }
    ]
    }
    ```
    - Behavior: Scores case-insensitively; sums `time_taken`; stores detailed result in `quiz_results` with `submitted_at`.
    - 200 Response returns `correct_answers`, `total_questions`, `total_answered_questions`, `time_taken`, and per-question correctness including `correct_answer`.

    ---

    ### Analytics and Admin Views
    1) GET `/dashboard`
    - Protected (Bearer, admin)
    - Returns counts and a top-10 leaderboard preview (ranked by average score desc, then time asc). Includes pagination metadata (fixed single page for preview).

    2) GET `/leaderboard`
    - Protected (Bearer, admin)
    - Query params (standard or positional): `page` (default 1), `limit` (default 10, max 100)
    - Returns full leaderboard with ranks and pagination. Users without attempts are included with zeroed stats.

    3) GET `/quiz_info/{user_id}`
    - Protected (Bearer)
    - Returns all quiz attempts for a user, each with per-question correctness and computed score percentage.

    ---

    ### Error Handling
    - Common structure: `{ "status": false, "error": "Message" }`
    - Status codes: 400 (validation), 401 (auth), 403 (admin required), 404 (not found), 500 (server/DB).

    ### Pagination Rules (where applicable)
    - Query params: `page`, `limit` (or positional like `?2&10`)
    - Defaults: `page=1`, `limit=10` (bounded to max 100)
    - Response object contains: `total_items`, `total_pages`, `current_page`, `per_page`, `has_next_page`, `has_prev_page`.

    ### Data Models (logical)
    - User: `{ _id, name, email, phone, password (hashed), role, school }`
    - Quiz: `{ _id, title, questions: [ { question_id, question, options[], correct_answer } ], created_by, created_at, total_questions, updated_by?, updated_at? }`
    - QuizResult: `{ quiz_id, user_id, correct_answers, total_questions, time_taken, submitted_at, questions: [ { question_id, options[], correct_answer, user_answer, is_correct } ] }`

    ### Curl Examples
    ```
    curl -X POST http://localhost:5000/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin","password":"admin123"}'

    curl -X GET http://localhost:5000/quizzes

    curl -X GET http://localhost:5000/quiz/<quiz_id> \
    -H "Authorization: Bearer <token>"

    curl -X POST http://localhost:5000/quiz \
    -H "Authorization: Bearer <admin_token>" \
    -H "Content-Type: application/json" \
    -d '{"title":"Sample","questions":[{"question":"Q?","options":["A","B"],"correct_answer":"A"}]}'
    ```

    ### Configuration
    - Environment variables (from `.env`):
    - `MONGO_URI` (required), `DB_NAME` (default `userdb`)
    - `JWT_SECRET_KEY` (required), `JWT_ALGORITHM` = `HS256`, `JWT_EXPIRATION_HOURS` = `8766`
    - `ADMIN_USERNAME` (default `admin`), `ADMIN_PASSWORD` (default `admin123`)

    ### Exporting to PDF (Windows)
    - Option A: VS Code/Cursor → Open `docs/api.md` → Print/Export to PDF.
    - Option B: Pandoc
    - Install Pandoc, then run:
        - `pandoc docs/api.md -o docs/api.pdf`
    - Option C: Chrome/Edge
    - Open the Markdown in a renderer (e.g., GitHub or Markdown preview), then Print → Save as PDF.



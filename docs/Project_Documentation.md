## NanoAPI Quiz Platform — Full Project Documentation (No Code)

This document provides a comprehensive, code-free overview of the Quiz Platform: vision, features, architecture, data model, security, operations, and maintenance. For the REST API details, see `docs/api.md`.

### 1) Product Overview
- Purpose: Enable administrators to create and manage quizzes, and users to take quizzes and receive instant scoring.
- Audience: Educational institutions, training teams, and anyone needing lightweight assessments.
- Key Outcomes:
  - Simple quiz authoring for admins
  - Reliable scoring and reporting
  - Secure user management with role-based access

### 2) Core Features
- User authentication with JWT
- Admin dashboard and leaderboard
- Quiz CRUD (create, update, delete)
- Taking quizzes and scoring
- Per-user attempt history and analytics

### 3) Architecture Overview
- Application Type: Lightweight REST API.
- Layers:
  - Routing/Services: Feature-oriented service files handling validation, orchestration, and responses.
  - Utilities: Shared concerns (authentication, validation helpers).
  - Configuration: Centralized environment-based settings.
- Data Store: MongoDB (document model fits quizzes and per-attempt results).
- Security: JWT-based authentication with role checks; passwords hashed server-side.

### 4) Request Flow (Typical)
1. Client sends HTTP request to an endpoint.
2. Authentication middleware/utility validates Bearer token (if required).
3. Service performs input validation and business logic.
4. Service queries/updates MongoDB.
5. Uniform success or error response is returned.

### 5) Data Model (Logical)
Note: Logical model only; refer to `docs/api.md` for field details.
- User: Identity fields, hashed password, role, and profile (e.g., school).
- Quiz: Title, list of questions, each question with options and a correct answer stored securely (not returned to non-admin consumers).
- QuizResult: Per-attempt record with user, quiz, answers, correctness, timing, and summary metrics.

### 6) Authentication and Authorization
- Login issues a JWT with standard claims and role.
- Protected endpoints require `Authorization: Bearer <token>`.
- Admin-only endpoints enforce role checks.
- Token validity and expiration are enforced; token payload includes role and user metadata.

### 7) API Summary
- Authentication: Login, verify token, decode token.
- Users: Register, list users (admin), get single user with derived stats.
- Quizzes: List, get single, create (admin), update (admin), delete (admin), delete question (admin), submit.
- Analytics: Dashboard (admin), leaderboard (admin), per-user quiz info.
- See `docs/api.md` for full request/response schemas and status codes.

### 8) Validation Rules (Highlights)
- Email must be valid; phone format `+91-XXXXXXXXXX`.
- Password confirmation required on registration.
- Quiz editing maintains/assigns `question_id` and prevents exposing correct answers to non-admin consumers.

### 9) Error Handling
- Consistent error envelope with appropriate HTTP status codes.
- Common statuses: 400 (validation), 401 (auth), 403 (admin required), 404 (not found), 409 (conflict), 500 (server/DB).

### 10) Configuration
- Managed via environment variables read in `config.py`.
- Typical variables: Mongo URI and DB name, JWT secret and algorithm, admin bootstrap credentials, token expiry.

### 11) Operations
- Startup: Configure environment, install dependencies, run the service entrypoint.
- Logging: Log authentication events, admin actions, and database errors with appropriate redaction of sensitive data.
- Monitoring: Basic health endpoint and DB connectivity checks.

### 12) Security and Privacy
- Passwords hashed; never log plaintext credentials or tokens.
- JWTs signed with a strong secret; rotate secrets and limit token lifetime.
- Admin role required for privileged actions; validate role at the boundary.
- Avoid exposing `correct_answer` in non-admin responses.

### 13) Performance Considerations
- Use selective projections to avoid returning large payloads (e.g., omit answers when listing quizzes).
- Index by common query keys (e.g., user_id, quiz_id) in MongoDB.
- Keep leaderboard computations efficient; cache summaries if needed at scale.

### 14) Testing Strategy (High-Level)
- Authentication: Token issuance, expiration, and role checks.
- Users: Registration validation and uniqueness.
- Quizzes: Create/update/delete flows, question ID management, answer redaction.
- Submissions: Scoring correctness, timing aggregation, and result recording.
- Analytics: Dashboard counts and leaderboard ordering.

### 15) Deployment Guidance
- Environment parity: Keep dev/staging/prod configuration patterns consistent.
- Secrets management: Use environment or a secret manager; never commit secrets.
- Observability: Enable access and application logs; monitor error rates and latency.
- Backup/Restore: Back up MongoDB regularly; test restores.

### 16) Maintenance
- Documentation hygiene: Update `docs/api.md` for endpoint changes and this document for behavioral or architectural updates.
- Dependency updates: Patch security vulnerabilities promptly; review major upgrades carefully.
- Data migrations: Plan and test schema evolution (e.g., new fields in quiz or results documents).

### 17) Glossary
- JWT: JSON Web Token used for stateless authentication.
- Admin: Role with elevated privileges to manage users/quizzes and access analytics.
- QuizResult: Stored outcome of a user’s quiz attempt with scoring and timing.

### 18) Changelog Template
- Version X.Y.Z (YYYY-MM-DD)
  - Added: …
  - Changed: …
  - Fixed: …
  - Removed: …

### 19) Related Documents
- API Reference: `docs/api.md`
- Project Structure: `docs/PROJECT_STRUCTURE.md`



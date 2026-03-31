# AGENTS.md - Animus Server

Guide for coding agents working in this repository.

## 1) Project Summary
- Project: `animus-server`
- Language: Python `>=3.13`
- Framework: FastAPI
- Dependency/env manager: `uv`
- Task runner: `poethepoet`
- DB: PostgreSQL + SQLAlchemy + Alembic
- Async/events: Inngest
- Quality tools: Ruff, BasedPyright, Pytest

## 2) Read Before Coding
For non-trivial changes (feature/refactor/bugfix), read in order:
1. `documentation/architecture.md`
2. `documentation/rules/rules.md`
3. `documentation/tooling.md`

Then read layer-specific rules under `documentation/rules/`.

Preferred MCP usage (when available):
- Atlassian MCP for Jira/Confluence context
- Context7 MCP for up-to-date library/framework docs
- Serena MCP for efficient code navigation/editing

## 3) Setup Commands
Install dependencies including dev:
```bash
uv sync --group dev
```
Create local env file:
```bash
cp .env.example .env
```
Install Node tooling for hooks/local CLI usage:
```bash
npm install
```

## 4) Build / Run / Lint / Typecheck / Test
Build note: there is no separate compile artifact step; validation commands are the quality gate.

Run API locally:
```bash
uv run dev
# or
uv run poe dev
```

Run Inngest local runtime:
```bash
uv run poe pubsub
```

DB commands:
```bash
uv run poe db:migrate "message"
uv run poe db:upgrade
uv run poe db:upgrade head
uv run poe db:downgrade -1
uv run poe db:seed
```

Quality commands:
```bash
uv run poe typecheck
uv run poe codecheck
uv run poe test
```

## 5) Single-Test Commands (Important)
Run one file:
```bash
uv run pytest -q tests/path/to/test_file.py
```
Run one test function:
```bash
uv run pytest -q tests/path/to/test_file.py::TestClassName::test_should_do_x_when_y
```
Run by keyword:
```bash
uv run pytest -q -k "keyword"
```
Run by layer:
```bash
uv run pytest -q tests/core
uv run pytest -q tests/rest/controllers
uv run pytest -q tests/pubsub/inngest/jobs
```

## 6) Architecture Boundaries
Main folders:
- `src/animus/core`: domain entities, DTOs, errors, interfaces, use cases
- `src/animus/rest`: controllers + request middlewares
- `src/animus/routers`: router composition
- `src/animus/pipes`: dependency providers (`Depends(...)`)
- `src/animus/database`: ORM models, mappers, repository implementations
- `src/animus/providers`: external integrations
- `src/animus/pubsub`: async jobs/event orchestration
- `src/animus/ai`: AI workflows/teams/toolkits

Hard rules:
- Keep controllers and jobs thin; business logic belongs in `UseCase`.
- Do not put ORM/SQL/session transaction logic in controllers.
- Keep `core` free of FastAPI/SQLAlchemy/Redis/Inngest/SDK dependencies.
- Contracts live in `core`; concrete implementations live outside `core`.

## 7) Code Style Guidelines
Imports (with blank line between groups):
1. Standard library
2. Third-party
3. First-party (`animus...`)

Formatting/linting:
- Ruff is authoritative.
- Max line length: `88`.
- Quote style: single quotes.
- Run `uv run poe codecheck` before finishing.

Types:
- BasedPyright strict mode is enabled.
- Add explicit type hints in new/changed code.
- Avoid `Any` unless truly necessary and justified.
- Keep interface and use case signatures precise.

Naming conventions:
- Prefer role suffixes: `*UseCase`, `*Dto`, `*Repository`, `*Provider`, `*Controller`, `*Event`, `*Error`.
- Test naming:
  - file: `test_<subject>.py`
  - class: `Test<Subject>`
  - method: `test_should_<result>_when_<condition>`

Error handling:
- Raise domain-specific errors in `core`.
- Translate domain errors at transport boundaries (REST layer).
- Avoid framework-specific exceptions inside `core`.

Testing conventions:
- Prefer Arrange / Act / Assert blocks.
- Use `create_autospec` for use case dependency mocks.
- REST tests validate HTTP contract (status + payload), not internals.
- PubSub tests validate event contract + observable side effects.

## 8) Commit and Hook Conventions
Husky + Commitlint are configured.

Allowed commit types:
- `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`

Commit subject must include Jira key pattern, example:
```text
feat(auth): ANM-123 add email verification retry
```

## 9) Cursor and Copilot Rules
Cursor rules check:
- `.cursor/rules/` not found
- `.cursorrules` not found

Copilot rules source: `.github/copilot-instructions.md`
- Review for: performance, security, concurrency, coupling, maintainability, duplication, test coverage, readability, typos/naming.
- Validate compliance with:
  - `documentation/rules/code-conventions-rules.md`
  - `documentation/rules/rules.md`
- If PR has linked issue, validate implementation against issue scope.
- Use this report format:
```text
**[OBRIGATÓRIO | SUGESTÃO]**
**Problema:** ...
**Impacto:** ...
**Sugestão:** ...
```

## 10) Suggested Agent Workflow
1. Read architecture + relevant rules.
2. Identify impacted layers and preserve boundaries.
3. Implement smallest viable change.
4. Run targeted tests first, broader tests after.
5. Run `typecheck` + `codecheck`.
6. Report: what changed, why, validations run, follow-up risks.

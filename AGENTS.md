# AGENTS.md

## Purpose
- This file is the operational guide for coding agents working in `animus-server`.
- Follow repository conventions first; if rules conflict, prefer explicit rules in `documentation/rules/`.

## Mandatory Reading Before Coding
- Read `documentation/architecture.md` for layer boundaries and data flow.
- Read `documentation/rules/rules.md` to choose the right rule files for the task.
- Read `documentation/tooling.md` for baseline commands.
- Product/domain context is in Confluence. Use Atlassian MCP to retrieve it.
- Primary link used by the team:
  - `https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/edit-v2/20480001?draftShareId=f6aa332c-e24a-4cb3-b1f9-a1c8358db1da`
- If that draft link is unavailable, use Atlassian search and read:
  - `Quadro Principal - ANIMUS`
  - `Requisitos do produto`

## MCP/Tooling Policy
- Use Serena MCP for codebase navigation and targeted code edits.
- Use Atlassian MCP for Jira/Confluence context.
- Use Context7 MCP for external library/framework/API docs.
- Prefer repository docs over assumptions.

## Project Snapshot
- Stack: Python 3.13+, FastAPI, SQLAlchemy, PostgreSQL, Redis, Inngest, Qdrant.
- Dependency/tooling: `uv`, Poe (`poethepoet`), Ruff, BasedPyright, Pytest.
- Main code: `src/animus/`; tests: `tests/`.
- Layered architecture (Clean + Hexagonal): core -> adapters/boundaries.
- Core contexts: `auth`, `intake`, `storage`, `notification`, `shared`.

## Architecture Rules (High Priority)
- Keep `core` pure: no FastAPI, ORM, SQL, request/session, SDK, env, or transport logic.
- Business rules belong in entities/structures/use cases, not controllers/pipes/jobs/repositories.
- `rest` controllers are thin adapters: validate, map input, call use case, return DTO/response.
- `routers` only compose routes (`register() -> APIRouter`), no business logic.
- `pipes` provide dependencies/guards, not full feature orchestration.
- `database` implements core interfaces and mapping only, no business rules.
- `pubsub` jobs orchestrate async flow and delegate to use cases.

## Environment Setup
- Install dependencies: `uv sync --group dev`
- Create env file: `cp .env.example .env`
- Start local infra (if needed): `docker compose up -d`
- Apply migrations: `uv run poe db:upgrade`
- Run API (dev): `uv run dev` (or `uv run poe dev`)

## Build, Lint, Typecheck, Test Commands
- Typecheck: `uv run poe typecheck`
- Lint/format check (with auto-fixes in lint step): `uv run poe codecheck`
- Full test suite: `uv run poe test`
- Build package: `uv build`

## Single-Test Execution (Important)
- Single test file:
  - `uv run pytest -q tests/path/test_file.py`
- Single test function:
  - `uv run pytest -q tests/path/test_file.py::TestClass::test_name`
- Pattern filtering:
  - `uv run pytest -q -k "pattern"`
- Keep test paths under `tests/` (configured in `pyproject.toml`).

## Useful Project Commands
- Run Inngest local dev: `uv run poe pubsub`
- New migration: `uv run poe db:migrate "message"`
- Downgrade migration: `uv run poe db:downgrade`
- Seed database: `uv run poe db:seed`
- Show current migration: `uv run poe db:current`

## CI Expectations
- CI order: branch validation -> typecheck -> codecheck -> tests -> build.
- A PR is expected to pass the same local sequence before review.
- `codecheck` must not leave diffs (`git diff --exit-code` in CI).

## Formatting and Imports
- Ruff config is authoritative (`pyproject.toml`).
- Line length: 88.
- Quote style: single quotes.
- Import order:
  1) Python standard library
  2) Third-party libraries
  3) First-party (`animus.*`)
- Separate import groups with one blank line.
- Keep files in `snake_case`; avoid unnecessary comments.

## Typing Guidelines
- Type checking mode is strict (BasedPyright/Pyright).
- Add explicit type hints to public functions/methods.
- Prefer concrete domain types/DTOs over untyped dicts.
- Avoid `Any` unless strictly necessary and justified.
- Keep interfaces/contracts in `core/interfaces` and implement them in adapters.

## Naming Conventions
- Use case classes: `*UseCase` with `execute(...)` entrypoint.
- DTO classes: `*Dto`.
- Repository interfaces: `*Repository`.
- Provider interfaces/implementations: `*Provider`.
- REST adapters: `*Controller` exposing `handle(router)`.
- Router classes: `*Router` exposing `register() -> APIRouter`.
- Dependency providers: `*Pipe`.
- Async handlers: `*Job`.
- Request body model in controllers should follow project pattern `_Body`.

## Error Handling Guidelines
- Use domain errors derived from `AppError` for business failures.
- Raise domain errors in use cases; do not encode HTTP concerns in core.
- Let global REST handlers map domain errors to HTTP responses.
- For repository lookup contracts, return `None` when contract expects it.
- Do not raise transport-specific errors inside database adapters.

## Testing Guidelines
- Framework: `pytest`.
- Keep tests in existing structure:
  - `tests/core/.../use_cases/`
  - `tests/rest/controllers/...`
  - `tests/pubsub/inngest/jobs/...`
- Use Arrange/Act/Assert structure with clear separation.
- Test naming: `test_should_<result>_when_<condition>`.
- Core use case tests should mock ports/interfaces (prefer `create_autospec`).
- REST tests should validate status code + payload contract with `TestClient`.
- Add at least one success and one failure path for new behavior.

## Commit and Message Rules
- Commit messages are validated by Husky + Commitlint.
- Allowed types: `build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test`.
- Required header pattern:
  - `<type>(<scope>)?: <PROJ-123> <english description>`
- Example:
  - `feat(auth): ANI-123 add google sign-in use case`

## Copilot Rules (from `.github/copilot-instructions.md`)
- For review tasks, read `AGENTS.md` first.
- If a PR has a linked issue, validate implementation against issue scope.
- Always check: performance, security, concurrency, coupling, maintainability,
  duplication, test coverage, readability, and naming/typos.
- Verify conformance with:
  - `documentation/rules/code-conventions-rules.md`
  - `documentation/rules/rules.md`
- Report findings using this template:
  - `**[OBRIGATORIO | SUGESTAO]**`
  - `**Problema:** ...`
  - `**Impacto:** ...`
  - `**Sugestao:** ...`
- Classification:
  - `OBRIGATORIO`: security/bugs/rule violations/scope divergence.
  - `SUGESTAO`: non-critical improvements.
- Avoid subjective style-only comments not backed by project rules.

## Cursor Rules
- No Cursor rules were found at `.cursor/rules/` or `.cursorrules` at the time
  this file was generated.
- If those files are added later, treat them as additional mandatory guidance.

## Agent Checklist Before Finishing
- Ran relevant validation commands for changed scope.
- Kept architectural boundaries intact.
- Updated/added tests when behavior changed.
- Ensured formatting, linting, and type checks pass locally.

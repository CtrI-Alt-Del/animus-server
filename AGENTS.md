# Animus Server Agent Guide

## Scope
- This file is for coding agents working inside `animus-server`.
- The source documentation is mostly in Portuguese; preserve the project's established terminology and naming.
- Prefer the smallest correct change that follows the existing layer boundaries.

## First Reads
- Read `documentation/architecture.md` before making non-trivial changes.
- Read `documentation/rules/rules.md` before editing code.
- Read `documentation/tooling.md` before running validation commands.
- Read `documentation/rules/code-conventions-rules.md` for any code change.
- Read only the layer-specific rule files that match the change you are making.
- Read `documentation/rules/core-layer-rules.md` for `src/animus/core/**`.
- Read `documentation/rules/rest-layer-rules.md` for `src/animus/rest/**`.
- Read `documentation/rules/routers-layers-rules.md` for `src/animus/routers/**`.
- Read `documentation/rules/pipes-layer-rules.md` for `src/animus/pipes/**`.
- Read `documentation/rules/database-layer-rules.md` for `src/animus/database/**`.
- Read `documentation/rules/pubsub-layer-rules.md` for `src/animus/pubsub/**`.
- Read `documentation/rules/ai-layer-rules.md` for `src/animus/ai/**`.
- Read `documentation/rules/testing-rules.md` plus the test-specific rule file before changing tests.

## Preferred MCPs And Tools
- Use Serena MCP for codebase navigation and symbol-aware inspection.
- Use Context7 MCP for library, framework, SDK, or external configuration documentation.
- Use Atlassian MCP for Jira and Confluence context.

## Repository Snapshot
- Stack: Python 3.13+, FastAPI, SQLAlchemy, PostgreSQL, Redis, Inngest, Pydantic, Ruff, BasedPyright, Pytest, Poe, uv.
- Architecture: Clean Architecture plus Hexagonal Architecture.
- Main code lives in `src/animus/`.
- Tests live in `tests/`.
- The `core` layer owns business rules, contracts, DTOs, entities, structures, errors, events, and use cases.
- The `rest` layer adapts HTTP requests to use cases.
- The `routers` layer is only for route composition.
- The `pipes` layer is only for dependency providers and reusable guards.
- The `database` layer implements persistence adapters and mappers.
- The `providers` layer implements infrastructure adapters.
- The `pubsub` layer orchestrates async/event-driven flows.

## Setup And Runtime Commands
```bash
uv sync --group dev
uv run poe dev
uv run poe pubsub
```

## Validation Commands
```bash
uv run poe typecheck
uv run poe codecheck
uv run poe test
uv build
```
- `uv run poe typecheck` runs `basedpyright` in strict mode.
- `uv run poe codecheck` runs `ruff check --fix src tests` and then `ruff format --check src tests`.
- `uv run poe codecheck` can modify files because of `--fix`.
- `uv run poe test` runs `pytest -s -x -vv`.
- CI order is `typecheck -> codecheck -> tests -> build`.
- The CI build command is `uv build`.

## Test Commands
```bash
uv run pytest -q tests/path/test_file.py
uv run pytest -q tests/path/test_file.py::TestClass::test_name
uv run pytest -q -k "pattern"
```
- Prefer direct `pytest` commands for focused debugging.
- `tests` is the configured test root.
- `pythonpath` includes `.` and `src`, so package imports from `animus` work in tests.
- For isolated lint/format work, you can also run `uv run ruff check --fix src tests`, `uv run ruff format src tests`, and `uv run ruff format --check src tests`.

## Code Style
- Use `uv`; do not use `pip` or `virtualenv` directly.
- Prefer existing Poe tasks for recurring workflows.
- Keep files, modules, functions, methods, variables, and JSON fields in `snake_case`.
- Keep classes in `PascalCase`.
- Follow the repo suffix conventions: `*UseCase`, `*Dto`, `*Repository`, `*Provider`, `*Controller`, `*Router`, `*Pipe`, `*Job`, `*Mapper`, `*Model`, `*Error`, `*Event`.
- Use explicit type hints throughout new code.
- BasedPyright is strict; avoid `Any` unless you truly cannot model the type.
- Ruff formatting rules include line length `88`, spaces for indentation, LF line endings, and single quotes.
- Group imports as standard library, third-party, then first-party, with blank lines between groups.
- Treat `animus` as first-party.
- Prefer absolute first-party imports.
- Keep public package exports stable in `__init__.py`.
- Update `__all__` when changing public module exports.
- Follow the existing decorator conventions for domain types such as `@entity`, `@structure`, `@dto`, and `@response`.

## Layer Conventions
- `UseCase` classes are the main application entry points and expose `execute(...)`.
- Do not import one concrete use case into another concrete use case.
- Share logic through domain objects, interfaces, or minimal duplicated orchestration when needed.
- `Controller` classes register endpoints through `handle(router)`.
- In REST controllers, the internal request body model should be named `_Body`.
- Routers expose `register() -> APIRouter` and only compose controllers or sub-routers.
- Pipes expose small static methods and should return `core` interfaces whenever possible.
- Repository implementations should be technology-explicit, such as `Sqlalchemy*Repository`.
- Mapper classes should use the `*Mapper` suffix.
- Jobs should use the `*Job` suffix and stay small.

## Architecture Boundaries
- Keep `core` pure.
- `core` must not depend on FastAPI, SQLAlchemy, Redis, Inngest, request objects, response objects, environment access, or infrastructure SDKs.
- Business rules belong in `core`, usually in entities, structures, and use cases.
- Controllers must be thin: validate, adapt, delegate, respond.
- Routers must not contain endpoint logic.
- Pipes must not become the main orchestration layer of a feature.
- Repositories must not contain business rules.
- Repositories must not expose ORM models outside the database layer.
- Repositories should respect the `core` interface contract exactly.
- If a repository contract expects `None` for missing data, return `None`; do not raise a domain error there.
- Database transaction ownership belongs to middleware or the outer execution scope, not to controllers or repositories.
- Do not call `commit()` or `rollback()` inside repositories unless the owning scope explicitly requires it.
- Publish domain events through the `Broker` interface, not directly through Inngest or Redis SDKs from `core` or controllers.
- Jobs are orchestration units, not business-rule containers.
- Jobs should be idempotent or safe for re-delivery.

## HTTP And Error Handling
- Prefer the flow `Schema/typed input -> DTO/domain type -> UseCase -> DTO/response`.
- Declare `status_code` and `response_model` explicitly on endpoints when applicable.
- Never return ORM models as API contracts.
- Raise domain errors from the `core` layer using the existing `AppError` hierarchy.
- Let the global REST error handler translate domain errors to HTTP responses.
- Existing mappings include `400`, `401`, `403`, `404`, and `409` for domain errors.
- Validation errors from request parsing should remain framework-handled unless the domain needs a specific `AppError`.

## Testing Conventions
- Keep test paths aligned with the layer under test.
- Core use case tests live under `tests/core/<context>/use_cases/`.
- REST controller tests live under `tests/rest/controllers/<context>/`.
- PubSub job tests live under `tests/pubsub/inngest/jobs/<context>/`.
- Use file names like `test_<subject>.py`.
- Use test classes like `Test<SubjectName>`.
- Use test names like `test_should_<result>_when_<condition>`.
- Structure tests with Arrange, Act, Assert blocks separated by blank lines.
- Use `pytest.fixture(autouse=True)` for shared use case setup when the existing test style does so.
- Use `create_autospec(..., instance=True)` for mocked ports in use case tests.
- In REST tests, prefer the shared `client: TestClient` fixture from `tests/conftest.py`.
- Use `auth_headers` for authenticated controller tests.
- Cover both success and failure paths.
- For new endpoints, include at least one success test and one validation/error test.
- Keep tests independent; do not rely on implicit state shared across tests.
- Mock only non-deterministic external boundaries when needed.

## Review Rules From Copilot Instructions
- No repo-local Cursor rules were found in `.cursor/rules/` or `.cursorrules`.
- Repo-local Copilot instructions exist in `.github/copilot-instructions.md`.
- Review for performance, security, concurrency, coupling, maintainability, duplication, missing tests, readability, and typos/inconsistent naming.
- Validate changes against `documentation/rules/code-conventions-rules.md` and `documentation/rules/rules.md`.
- Confirm the implementation matches the responsibilities of the layer being changed.
- Do not invent style rules that are not documented.
- Report findings with this structure:

```text
**[OBRIGATORIO | SUGESTAO]**
**Problema:** descricao clara e especifica
**Impacto:** consequencia real ou potencial
**Sugestao:** acao corretiva recomendada
```
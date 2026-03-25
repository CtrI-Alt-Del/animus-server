# Regras gerais para testes (animus-server)

Use este documento como indice rapido para escolher a estrategia de teste correta
no `animus-server` (Clean/Hexagonal: `core` puro, `rest` como borda HTTP e
`pubsub` como borda assincrona orientada a eventos).

## Tooling de testes

### Framework

- Ferramenta: `pytest`
- Comando padrao (task runner): `poe test` (executa `pytest -s -x -vv`)

### Configuracao

- Arquivo: `pyproject.toml` (secao `[tool.pytest.ini_options]`)
- Defaults relevantes do repo:
  - `testpaths = ["tests"]`
  - `pythonpath = [".", "src"]` (imports a partir de `animus` funcionam nos testes)
- Plugins usados no projeto:
  - `pytest-cov` (cobertura, quando habilitado)
  - `pytest-mock` (fixture `mocker`)

## Regra de leitura progressiva (qual doc ler)

### Use cases (core)

- Leia `documentation/rules/use-cases-testing-rules.md` antes de criar/alterar/revisar testes em `tests/core/**/use_cases/`.
- Use quando o alvo e regra de negocio em `src/animus/core/**` (mocks de ports/repositorios; foco em `use_case.execute(...)`).

### Controllers (REST)

- Leia `documentation/rules/controllers-testing-rules.md` antes de criar/alterar/revisar testes em `tests/rest/controllers/**`.
- Use quando o alvo e contrato HTTP (status code, payload, validacao de entrada, comportamento do endpoint).

### Jobs PubSub (Inngest)

- Leia `documentation/rules/pubsub-jobs-testing-rules.md` antes de criar/alterar/revisar testes em `tests/pubsub/inngest/jobs/**`.
- Use quando o alvo e um job assincrono em `src/animus/pubsub/inngest/jobs/**`, com foco no evento consumido, na orquestracao do runtime e no side effect observavel.

### Mudanca envolve mais de uma camada

- Leia primeiro o documento da regra mais interna (`use-cases-testing-rules.md`) e depois os das bordas impactadas (`controllers-testing-rules.md`, `pubsub-jobs-testing-rules.md`).
- Em PRs que adicionam endpoints, jobs e/ou use cases novos, releia todos os documentos aplicaveis antes de finalizar.

## Regras praticas do projeto

### Estrutura de pastas (estado atual)

- Testes de `core`: `tests/core/<contexto>/use_cases/` (unitarios, rapidos)
- Testes de `rest`: `tests/rest/controllers/<contexto>/` (contrato HTTP via `TestClient`)
- Testes de `pubsub`: `tests/pubsub/inngest/jobs/<contexto>/` (jobs assincronos via runtime do Inngest)
- Fakers: `tests/fakers/**` (massa de teste reutilizavel)

### AAA + intencao unica

- Mantenha Arrange / Act / Assert com separacao por linha em branco.
- Um teste deve validar uma unica regra/comportamento observavel.

### Banco de dados e infraestrutura em testes

- Dependencias externas nao deterministicas devem ser isoladas.
- Em testes REST, faca patch do registro do Inngest no setup para evitar side effects externos.
- Em testes de jobs PubSub, prefira runtime real do Inngest no ambiente de teste e mocke apenas o side effect externo final.
- Quando um teste depender de banco, container ou runtime auxiliar, centralize esse setup em fixtures reutilizaveis.

## Comandos rapidos (uso local)

- Rodar tudo: `poe test`
- Rodar um arquivo REST: `uv run pytest -q tests/rest/controllers/profiling/test_create_horse_controller.py`
- Rodar um arquivo PubSub: `uv run pytest -q tests/pubsub/inngest/jobs/auth/test_send_account_verification_email_job.py`
- Rodar um teste especifico: `uv run pytest -q -k "should_create"`

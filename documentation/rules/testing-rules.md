# Regras gerais para testes (animus-server)

Use este documento como indice rapido para escolher a estrategia de teste correta
no `animus-server` (Clean/Hexagonal: `core` puro, `rest` como borda HTTP).

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

### Mudanca envolve as duas camadas

- Leia primeiro `documentation/rules/use-cases-testing-rules.md` e depois `documentation/rules/controllers-testing-rules.md`.
- Em PRs que adicionam endpoints novos e/ou use cases novos, releia ambos antes de finalizar.

## Regras praticas do projeto

### Estrutura de pastas (estado atual)

- Testes de `core`: `tests/core/<contexto>/use_cases/` (unitarios, rapidos)
- Testes de `rest`: `tests/rest/controllers/<contexto>/` (contrato HTTP via `TestClient`)
- Fakers: `tests/fakers/**` (massa de teste reutilizavel)

### AAA + intencao unica

- Mantenha Arrange / Act / Assert com separacao por linha em branco.
- Um teste deve validar uma unica regra/comportamento observavel.

### Banco de dados em testes REST (como funciona aqui)

- No estado atual do bootstrap, o repositorio ainda nao possui fixture oficial de banco para REST.
- Ao introduzir testes REST com persistencia, implemente fixture dedicada em `tests/fixtures/database_fixtures.py` e documente o fluxo aqui.
- Consequencia: enquanto nao houver fixture de DB, mantenha os testes REST sem dependencia de sessao real.

### Publicacao/side effects em testes

- Dependencias externas nao deterministicas devem ser isoladas.
- Quando houver integracao com pubsub no app, faca patch no setup de testes para evitar side effects externos.

## Comandos rapidos (uso local)

- Rodar tudo: `poe test`
- Rodar um arquivo: `uv run pytest -q tests/rest/controllers/profiling/test_create_horse_controller.py`
- Rodar um teste especifico: `uv run pytest -q -k "should_create"`

---
description: Criar testes para core, rest e pubsub seguindo regras do repositorio
---

# Prompt: Criar testes (animus-server)

Objetivo: orientar a criacao de testes consistentes para o `animus-server`, cobrindo
regra de negocio (`core`), contrato HTTP (`rest`) e jobs assincronos (`pubsub`)
sem acoplar a infraestrutura no lugar errado.

Entrada:

- Codigo fonte a ser testado (use case em `src/animus/core/**`, controller/rota em
  `src/animus/rest/**`/`src/animus/routers/**`, job em
  `src/animus/pubsub/inngest/jobs/**`, ou estruturas de apoio).

---

## Diretrizes de execucao

### 1 Aderencia as regras do projeto (leitura progressiva)

- Sempre comece por `documentation/rules/testing-rules.md`.
- Se for use case (`core`): leia `documentation/rules/use-cases-testing-rules.md`.
- Se for controller (`rest`): leia `documentation/rules/controllers-testing-rules.md`.
- Se for job assincrono (`pubsub`/`inngest`): leia `documentation/rules/pubsub-jobs-testing-rules.md`.

### 2 Estrutura e nomenclatura

- Testes nao sao co-localizados no codigo fonte; ficam em `tests/`.
- Use cases (core):
  - caminho: `tests/core/<contexto>/use_cases/`
  - arquivo: `test_<nome_use_case>.py`
  - classe: `Test<UseCaseName>`
  - metodo: `test_should_<resultado>_when_<condicao>`
- Controllers (rest):
  - caminho: `tests/rest/controllers/<contexto>/`
  - arquivo: `test_<nome_controller>.py`
  - classe: `Test<ControllerName>`
  - metodo: `test_should_<resultado>_when_<condicao>`
- Jobs assincronos (pubsub/inngest):
  - caminho: `tests/pubsub/inngest/jobs/<contexto>/`
  - arquivo: `test_<nome_job>.py`
  - classe: `Test<JobName>`
  - metodo: `test_should_<resultado>_when_<condicao>`

### 3 Stack de testes

- Runner/framework: `pytest`
- Execucao padrao: `poe test` (usa `pytest -s -x -vv`)
- Mocking:
  - preferencia: `unittest.mock.create_autospec(<Interface>, instance=True)` (use cases)
  - fixture util: `mocker` (pytest-mock), quando fizer sentido
  - patch por `monkeypatch`, quando o alvo for side effect externo em job/pubsub
- REST client: `fastapi.testclient.TestClient` via fixture `client`
- Runtime de jobs Inngest: fixture `inngest_runtime`

### 4 Preparacao de dados (fakers)

- Reaproveite massa de teste em `tests/fakers/**`.
- Prefira dados explicitamente configurados quando forem parte da regra (evite aleatoriedade em asserts).

### 5 Estrategia por tipo de teste

- Use case (core):
  - foco: comportamento de negocio do metodo `execute(...)`
  - mocke apenas ports/repositorios (sem FastAPI, sem SQLAlchemy)
  - cubra no minimo um caminho feliz e um caminho de erro (excecao de dominio)
  - valide retorno + interacoes (ex.: `assert_called_once_with`)
- Controller (rest):
  - foco: contrato HTTP (rota/verbo, `status_code`, payload, validacao `422`)
  - exercite o app com `TestClient` usando fixtures `client` e `auth_headers` (quando autenticado)
  - evite acoplar a detalhes internos do use case
- Job assincrono (pubsub/inngest):
  - foco: contrato do evento consumido, orquestracao do runtime e side effect observavel
  - use `inngest_runtime` para publicar o evento no ambiente de teste
  - mocke apenas a fronteira externa final (ex.: provider de email)

### 6 Regras do repo que impactam testes REST e PubSub

- `tests/conftest.py` sobrescreve `Sqlalchemy.get_session` para controlar a sessao usada nos testes.
- Testes REST usam a fixture `client` e fazem patch de `InngestPubSub.register` para evitar efeitos colaterais externos.
- Testes de jobs Inngest usam `tests/fixtures/inngest_fixtures.py`, que sobe app + runtime de teste do Inngest.
- Testes que dependem de PostgreSQL ou runtime externo devem deixar isso explicito na fixture usada, nao no corpo do teste.

### 7 Qualidade

- Use Arrange / Act / Assert com separacao por linha em branco (sem comentarios).
- Cada teste deve ser independente (nao depender de ordem/estado de outro teste).
- Assert seja objetivo: valide campos chave e o contrato observavel.

---

## Workflow sugerido

1) Escolha o tipo: use case (`core`), controller (`rest`) ou job (`pubsub`) e leia as regras correspondentes.
2) Crie o arquivo de teste no caminho correto em `tests/`.
3) Escreva primeiro o caminho feliz, depois erro(s)/validacao quando aplicavel.
4) Rode localmente:

```bash
poe test
```

Ou apenas um arquivo:

```bash
uv run pytest -q tests/pubsub/inngest/jobs/auth/test_send_account_verification_email_job.py
```

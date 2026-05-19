---
title: ANI-95 - Endpoint para desarquivar analise
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYASAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-95?atlOrigin=eyJpIjoiZjU4N2Q0YWFjMjlkNDg3MTgxNWVhNjkyZjkzN2Q3NjgiLCJwIjoiaiJ9
status: closed
last_updated_at: 2026-05-13
---

# 1. Objetivo

Implementar o endpoint autenticado `PATCH /intake/analyses/{analysis_id}/unarchive` para desarquivar uma analise da conta do usuario, definindo `is_archived = false` de forma idempotente e retornando o `AnalysisDto` atualizado com `200 OK`. A implementacao deve criar o fluxo de dominio em `core`, expor a borda HTTP em `rest` e registrar o controller no router de `intake`, reutilizando o contrato atual de `AnalisysesRepository` e a entidade `Analysis`.

---

# 2. Escopo

## 2.1 In-scope

- Criar `UnarchiveAnalysisUseCase` para buscar a analise, validar ownership e persistir o desarquivamento.
- Adicionar o comportamento `Analysis.unarchive()` na entidade de dominio existente.
- Criar `UnarchiveAnalysisController` com rota `PATCH /intake/analyses/{analysis_id}/unarchive`.
- Registrar o controller em `AnalysesRouter`.
- Atualizar exports publicos de `core/intake/use_cases` e `rest/controllers/intake`.
- Reutilizar `AnalysisDto`, `AnalysisNotFoundError`, `AuthPipe.get_account_id_from_request()` e `DatabasePipe.get_analisyses_repository_from_request()`.
- Retornar `404` quando a analise nao existir ou pertencer a outra conta, conforme ANI-95.

## 2.2 Out-of-scope

- Criar endpoint de arquivamento singular.
- Alterar o endpoint existente de arquivamento em lote `PATCH /intake/analyses/archive`.
- Implementar desarquivamento em lote.
- Criar ou alterar schema de banco, models SQLAlchemy, mappers ou migrations.
- Alterar listagens, filtros, UI mobile ou area `Sem pasta` do RF 04.
- Publicar eventos assincronos, jobs Inngest ou mensagens WebSocket.

---

# 3. Requisitos

## 3.1 Funcionais

- `PATCH /intake/analyses/{analysis_id}/unarchive` deve exigir usuario autenticado via `Authorization: Bearer <token>`.
- Quando `analysis_id` existir e pertencer a conta autenticada, o sistema deve definir `Analysis.is_archived` como `Logical.create_false()`.
- O endpoint deve retornar `200` com `AnalysisDto` atualizado.
- A operacao deve ser idempotente: se a analise ja estiver desarquivada, o endpoint ainda deve retornar `200` com o `AnalysisDto` atual.
- Quando `analysis_id` nao existir, o fluxo deve levantar `AnalysisNotFoundError`.
- Quando `analysis_id` existir mas pertencer a outra conta, o fluxo deve levantar `AnalysisNotFoundError`, mantendo o contrato de `404` definido no ticket.

## 3.2 Nao funcionais

- **Seguranca:** o endpoint deve usar `AuthPipe.get_account_id_from_request()` para obter o `account_id` autenticado e nao aceitar `account_id` vindo do cliente.
- **Idempotencia:** `Analysis.unarchive()` deve sempre resultar em `is_archived = false`, sem alternar estado por inversao.
- **Compatibilidade retroativa:** a mudanca deve ser aditiva; nao deve alterar contratos existentes, payloads atuais ou schema de banco.
- **Transacao:** persistencia continua controlada pelo middleware de request; controller, use case e repositorio nao devem executar `commit` ou `rollback` manual.

---

# 4. O que ja existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) - entidade de dominio da analise; ja possui `archive()` que define `is_archived = Logical.create_true()` e deve receber o comportamento inverso `unarchive()`.
- **`AnalysisDto`** (`src/animus/core/intake/domain/entities/dtos/analysis_dto.py`) - contrato de saida ja usado como `response_model`, incluindo `is_archived: bool`.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) - erro de dominio traduzido para `404` pelo handler global.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) - port existente com `find_by_id(analysis_id: Id) -> Analysis | None` e `replace(analysis: Analysis) -> None`.
- **`ArchiveAnalysesUseCase`** (`src/animus/core/intake/use_cases/archive_analyses_use_case.py`) - referencia para validar ownership e persistir `analysis.archive()` em lote.
- **`GetAnalysisUseCase`** (`src/animus/core/intake/use_cases/get_analysis_use_case.py`) - referencia para fluxo singular com `account_id`, `analysis_id` e `AnalysisNotFoundError`.
- **`RenameAnalysisUseCase`** (`src/animus/core/intake/use_cases/rename_analysis_use_case.py`) - referencia para fluxo singular que altera a entidade e chama `AnalisysesRepository.replace(...)`.

## Database

- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) - implementa `replace(analysis)` e ja persiste `model.is_archived = analysis.is_archived.value`, portanto nao exige novo metodo ou alteracao de schema.

## Pipes

- **`AuthPipe.get_account_id_from_request()`** (`src/animus/pipes/auth_pipe.py`) - extrai e valida o `account_id` autenticado a partir do token de acesso.
- **`DatabasePipe.get_analisyses_repository_from_request()`** (`src/animus/pipes/database_pipe.py`) - fornece `AnalisysesRepository` usando a `Session` SQLAlchemy do request.

## REST

- **`ArchiveAnalysesController`** (`src/animus/rest/controllers/intake/archive_analyses_controller.py`) - registra `PATCH /analyses/archive` para arquivamento em lote; serve como referencia de wiring com `AuthPipe`, `DatabasePipe`, use case e `AnalysisDto`.
- **`GetAnalysisController`** (`src/animus/rest/controllers/intake/get_analysis_controller.py`) - referencia de endpoint singular com `analysis_id` em path param.
- **`RenameAnalysisController`** (`src/animus/rest/controllers/intake/rename_analysis_controller.py`) - referencia de `PATCH /analyses/{analysis_id}/...` com `status_code=200`, `response_model=AnalysisDto` e chamada ao use case por named params.
- **`AppErrorHandler.handle_not_found_error()`** (`src/animus/rest/handlers/app_error_handler.py`) - traduz `NotFoundError` para resposta HTTP `404`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) - compoe os controllers de analises e deve registrar o novo `UnarchiveAnalysisController`.
- **Exports de controllers** (`src/animus/rest/controllers/intake/__init__.py`) - agregador publico dos controllers de `intake`.
- **Exports de use cases** (`src/animus/core/intake/use_cases/__init__.py`) - agregador publico dos use cases de `intake`.

---

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/unarchive_analysis_use_case.py` (**novo arquivo**)
- **Classe:** `UnarchiveAnalysisUseCase`
- **Dependencias (ports injetados):** `analisyses_repository: AnalisysesRepository`
- **Metodo principal:** `execute(account_id: str, analysis_id: str) -> AnalysisDto` - desarquiva uma analise da conta autenticada e retorna o DTO atualizado.
- **Fluxo resumido:**
  - Normalizar `account_id` com `Id.create(account_id)`.
  - Normalizar `analysis_id` com `Id.create(analysis_id)`.
  - Buscar a analise com `AnalisysesRepository.find_by_id(normalized_analysis_id)`.
  - Levantar `AnalysisNotFoundError` se a analise nao existir ou se `analysis.account_id != normalized_account_id`.
  - Chamar `analysis.unarchive()`.
  - Persistir com `AnalisysesRepository.replace(analysis)`.
  - Retornar `analysis.dto`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/intake/unarchive_analysis_controller.py` (**novo arquivo**)
- **Classe:** `UnarchiveAnalysisController`
- **`*Body`:** **Nao aplicavel**; endpoint nao recebe body.
- **Metodo de registro:** `handle(router: APIRouter) -> None` - registra o endpoint no router recebido.
- **Metodo HTTP e path:** `PATCH /analyses/{analysis_id}/unarchive` dentro do `AnalysesRouter`, resultando em `PATCH /intake/analyses/{analysis_id}/unarchive`.
- **`status_code`:** `200`
- **`response_model`:** `AnalysisDto`
- **Dependencias injetadas via `Depends`:**
  - `account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)]`
  - `analisyses_repository: Annotated[AnalisysesRepository, Depends(DatabasePipe.get_analisyses_repository_from_request)]`
- **Fluxo:** `analysis_id` path param -> `AuthPipe` -> `DatabasePipe` -> `UnarchiveAnalysisUseCase.execute(account_id=account_id.value, analysis_id=analysis_id)` -> `AnalysisDto`.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/entities/analysis.py`
- **Mudanca:** adicionar `unarchive(self) -> None` na entidade `Analysis`.
- **Assinatura:** `unarchive(self) -> None` - define `self.is_archived = Logical.create_false()`.
- **Justificativa:** manter o comportamento de mudanca de estado dentro da entidade, simetrico a `archive()` e sem espalhar manipulacao de `Logical` no use case.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudanca:** importar e exportar `UnarchiveAnalysisUseCase`.
- **Justificativa:** preservar o padrao de exports publicos dos use cases de `intake`.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** importar e exportar `UnarchiveAnalysisController`.
- **Justificativa:** permitir que `AnalysesRouter` consuma o controller pelo agregador publico de controllers de `intake`.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudanca:** importar `UnarchiveAnalysisController` e chamar `UnarchiveAnalysisController.handle(router)`, preferencialmente proximo de `ArchiveAnalysesController.handle(router)`.
- **Justificativa:** anexar a nova rota ao router de analises sem colocar logica HTTP dentro da camada `routers`.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** criar `UnarchiveAnalysisUseCase` singular em vez de reaproveitar `ArchiveAnalysesUseCase`.
- **Alternativas consideradas:** adicionar parametro de acao ao use case de arquivamento em lote; criar um use case generico de toggle; criar desarquivamento em lote.
- **Motivo da escolha:** ANI-95 define endpoint singular e retorno `AnalysisDto`; um use case dedicado mantem o fluxo claro e evita acoplar operacoes com semanticas diferentes.
- **Impactos / trade-offs:** adiciona um arquivo novo pequeno, mas preserva legibilidade e evita alterar contrato existente.

- **Decisao:** reutilizar `AnalisysesRepository.replace(analysis)` em vez de criar metodo de repository como `unarchive(...)` ou `update(...)`.
- **Alternativas consideradas:** criar metodo especifico no port; alterar o repository concreto para update parcial.
- **Motivo da escolha:** `replace(...)` ja persiste `is_archived` e e usado pelos fluxos de alteracao de analise (`rename`, `archive`, `move_to_folder`).
- **Impactos / trade-offs:** evita mudar contratos de persistencia; mantem update de entidade completa como padrao atual.

- **Decisao:** retornar `404` para analise inexistente e para analise de outra conta usando `AnalysisNotFoundError`.
- **Alternativas consideradas:** usar `ForbiddenError` quando a analise pertence a outra conta.
- **Motivo da escolha:** o ticket exige `404` nos dois cenarios e esse padrao evita vazar existencia de recurso de outra conta.
- **Impactos / trade-offs:** o cliente nao consegue distinguir recurso inexistente de recurso sem ownership, por decisao de seguranca e contrato do ticket.

- **Decisao:** implementar `Analysis.unarchive()` com atribuicao explicita para `Logical.create_false()`.
- **Alternativas consideradas:** usar `self.is_archived.invert()` ou manipular `Logical.create_false()` diretamente no use case.
- **Motivo da escolha:** a operacao precisa ser idempotente; inverter estado quebraria a idempotencia quando a analise ja estivesse desarquivada.
- **Impactos / trade-offs:** mantem regra simples e local a entidade.

- **Decisao:** usar `execute(account_id: str, analysis_id: str) -> AnalysisDto`, mantendo `account_id` como primeiro parametro.
- **Alternativas consideradas:** seguir a ordem textual do ticket `execute(analysis_id: str, account_id: str) -> AnalysisDto`.
- **Motivo da escolha:** `GetAnalysisUseCase`, `RenameAnalysisUseCase` e `ArchiveAnalysesUseCase` usam `account_id` primeiro; o controller chamara por named params, eliminando ambiguidade pratica.
- **Impactos / trade-offs:** pequena divergencia de ordem em relacao ao texto do Jira, compensada por consistencia com a codebase.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
PATCH /intake/analyses/{analysis_id}/unarchive
  -> FastAPI middleware de request
  -> AnalysesRouter
  -> UnarchiveAnalysisController
  -> AuthPipe.get_account_id_from_request()
  -> DatabasePipe.get_analisyses_repository_from_request()
  -> UnarchiveAnalysisUseCase.execute(account_id, analysis_id)
  -> AnalisysesRepository.find_by_id(Id)
      -> None ou outra conta: AnalysisNotFoundError -> AppErrorHandler -> 404
  -> Analysis.unarchive()
  -> AnalisysesRepository.replace(Analysis)
  -> SqlalchemyAnalisysesRepository.replace(Analysis)
  -> PostgreSQL analyses.is_archived = false
  -> Analysis.dto
  -> 200 AnalysisDto
```

- **Fluxo assincrono:** **Nao aplicavel**; a feature nao publica eventos e nao consome jobs Inngest ou WebSocket.
- **Referencias:**
  - `src/animus/rest/controllers/intake/archive_analyses_controller.py`
  - `src/animus/core/intake/use_cases/archive_analyses_use_case.py`
  - `src/animus/rest/controllers/intake/get_analysis_controller.py`
  - `src/animus/core/intake/use_cases/get_analysis_use_case.py`
  - `src/animus/rest/controllers/intake/rename_analysis_controller.py`
  - `src/animus/core/intake/use_cases/rename_analysis_use_case.py`
  - `src/animus/core/intake/domain/entities/analysis.py`
  - `src/animus/core/intake/interfaces/analisyses_repository.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
  - `src/animus/routers/intake/analyses_router.py`

---

# 10. Pendencias / Duvidas

- **Descricao da pendencia:** o PRD RF 04 descreve armazenamento, organizacao e consulta de analises, mas nao detalha explicitamente arquivamento/desarquivamento; o comportamento de desarquivar vem do ticket ANI-95 e do estado `is_archived` ja existente na codebase.
- **Impacto na implementacao:** nao bloqueia a implementacao do endpoint porque o contrato do ticket e objetivo, mas pode deixar o PRD menos rastreavel para futuras alteracoes de biblioteca.
- **Acao sugerida:** validar com produto se o RF 04 deve ser atualizado para documentar `archive`/`unarchive` como parte da organizacao de analises.

- **Descricao da pendencia:** o ticket cita simetria com `PATCH /intake/analyses/{analysis_id}/archive`, porem a codebase mapeada possui `PATCH /intake/analyses/archive` em lote via `ArchiveAnalysesController`.
- **Impacto na implementacao:** nao bloqueia ANI-95, pois o novo endpoint singular esta explicitamente definido como `PATCH /intake/analyses/{analysis_id}/unarchive`; apenas impede tratar a simetria com archive como evidencia literal da rota existente.
- **Acao sugerida:** confirmar em refinamento se deve existir uma tarefa separada para endpoint singular de arquivamento ou se o arquivamento em lote atual e o contrato definitivo.

---

# 11. Restricoes

- O `core` deve permanecer puro: sem imports de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest`, `Request`, `Response`, `Session` ou `Env`.
- `UnarchiveAnalysisController` deve apenas adaptar HTTP, resolver dependencias e delegar ao use case.
- `AnalysesRouter` deve apenas compor controllers; nao deve conter validacao de transporte ou regra de negocio.
- Nao criar novo schema em `validation/`, pois o endpoint nao recebe body e retorna `AnalysisDto` ja existente.
- Nao alterar `AnalisysesRepository`, `SqlalchemyAnalisysesRepository` ou models SQLAlchemy, pois `replace(...)` ja cobre persistencia de `is_archived`.
- Nao adicionar migracao Alembic para ANI-95; a coluna `analyses.is_archived` ja existe e e mapeada.
- Manter resposta em `snake_case`, conforme contrato REST atual do projeto.

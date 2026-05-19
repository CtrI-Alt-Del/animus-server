---
title: Endpoints REST de pastas da biblioteca
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/17989633
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-65
status: open
last_updated_at: 2026-04-20
---

# 1. Objetivo

Entregar os 5 endpoints REST do modulo `library` para gerenciamento de pastas em `/library/folders`, cobrindo criacao, consulta por `id`, renomeacao, arquivamento e listagem paginada por cursor, com ownership por conta autenticada, persistencia SQLAlchemy em tabela propria de `folders`, contagem derivada de analises vinculadas e integracao ao `FastAPI` sem deslocar regra de negocio para `controllers`, `pipes` ou `repositories`.

---

# 2. Escopo

## 2.1 In-scope

- Criar os endpoints `POST /library/folders`, `GET /library/folders/{folder_id}`, `PATCH /library/folders/{folder_id}`, `PATCH /library/folders/{folder_id}/archive` e `GET /library/folders`.
- Criar os `use_cases` do contexto `library` para criar, obter, renomear, arquivar e listar pastas.
- Criar persistencia SQLAlchemy do agregado `Folder` com `model`, `mapper`, `repository` e migration de `folders`.
- Expor `FoldersRepository` via `DatabasePipe` e registrar o novo `LibraryRouter` no `app`.
- Reaproveitar `Folder`, `FolderDto`, `Id`, `Name`, `Logical`, `Integer` e `CursorPaginationResponse` ja existentes.
- Calcular `analysis_count` a partir de `analyses.folder_id` sem persistir contador duplicado na tabela `folders`.
- Manter a separacao do modulo HTTP em `rest/controllers/library/` e `routers/library/`, com prefixo publico `/library`.

## 2.2 Out-of-scope

- Exclusao de pasta e qualquer comportamento de mover analises para `Sem pasta`.
- Endpoint para mover analise entre pastas ou remover `folder_id` de uma analise existente.
- Listagem de analises dentro de uma pasta especifica.
- Busca textual de analises salvas, compartilhamento, exportacao ou operacoes em lote do RF 04 fora do escopo do ANI-65.
- Criacao de schemas reutilizaveis em `src/animus/validation/library/`; os corpos de entrada deste escopo sao exclusivos de cada controller.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /library/folders` deve receber `name`, criar uma pasta vinculada ao `account_id` autenticado e retornar `201` com `FolderDto`.
- `GET /library/folders/{folder_id}` deve retornar `200` com `FolderDto` da pasta solicitada.
- `PATCH /library/folders/{folder_id}` deve receber `name`, renomear a pasta e retornar `200` com `FolderDto` atualizado.
- `PATCH /library/folders/{folder_id}/archive` deve marcar `is_archived = true` e retornar `200` com `FolderDto` atualizado.
- `GET /library/folders` deve retornar `200` com `CursorPaginationResponse[FolderDto]`, suportando `cursor`, `limit` e `search` opcional.
- Todos os endpoints devem exigir autenticacao via `Bearer access token`.
- Endpoints com `folder_id` devem retornar `404` quando a pasta nao existir.
- Endpoints com `folder_id` devem retornar `403` quando a pasta existir, mas pertencer a outra conta.
- A listagem deve retornar apenas pastas ativas (`is_archived = false`).
- `analysis_count` deve refletir a quantidade de analises ativas (`analyses.is_archived = false`) associadas ao `folder_id` da pasta.

## 3.2 Nao funcionais

- **Seguranca:** todos os endpoints exigem autenticacao e ownership check por `account_id`.
- **Compatibilidade retroativa:** `Folder` e `FolderDto` existentes devem ser reaproveitados; nao deve surgir um contrato paralelo para pasta.
- **Compatibilidade retroativa:** `analysis_count` deve continuar exposto por `FolderDto`, mas sua origem passa a ser derivada de `analyses`, sem coluna redundante em `folders`.
- **Performance:** `GET /library/folders` e `GET /library/folders/{folder_id}` devem resolver `analysis_count` sem `N+1`; a contagem deve ser agregada em SQL.
- **Resiliencia:** transacao continua sob ownership do middleware de sessao SQLAlchemy; `repositories` nao fazem `commit()` nem `rollback()`.
- **Compatibilidade retroativa:** o novo modulo `/library` nao deve alterar contratos existentes de `/intake`, exceto pelo reuso consistente de `folder_id` como referencia de pasta.

---

# 4. Regras de Negocio e Invariantes

- Uma pasta pertence a exatamente uma conta via `account_id`.
- O nome da pasta e obrigatorio, nao pode ficar em branco apos `strip()` e deve respeitar limite maximo de `50` caracteres.
- `analysis_count` e derivado; a aplicacao nao deve persistir contador materializado em `folders`.
- Arquivar uma pasta significa apenas marcar `is_archived = true`; o ANI-65 nao remove registros nem move analises para `Sem pasta`.
- Apenas o dono da pasta pode consultar, renomear ou arquivar a pasta.
- A listagem principal de pastas deve ocultar pastas arquivadas.
- O endpoint de criacao sempre gera pasta nova com `is_archived = false` e `analysis_count = 0`.
- A ausencia da pasta e o acesso a pasta de outra conta devem ser diferenciados em `404` e `403`, respectivamente.

---

# 5. O que ja existe?

## Camada Core

- **`Folder`** (`src/animus/core/library/domain/entities/folder.py`) - entidade de dominio ja existente para pasta, com `name`, `account_id`, `analysis_count` e `is_archived`.
- **`FolderDto`** (`src/animus/core/library/domain/entities/dtos/folder_dto.py`) - DTO ja existente de pasta, usado como contrato de saida entre camadas.
- **`FoldersRepository`** (`src/animus/core/library/interfaces/folders_repository.py`) - port ja existente para persistencia/listagem de pastas, ainda incompleto para o fluxo do ANI-65.
- **`Name`**, **`Id`**, **`Integer`** e **`Logical`** (`src/animus/core/shared/domain/structures/`) - estruturas reutilizaveis para validacao e normalizacao.
- **`CursorPaginationResponse`** (`src/animus/core/shared/responses/cursor_pagination_response.py`) - resposta generica ja usada pelos endpoints paginados de `intake`.

## Camada Intake relacionada

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) - entidade ja integrada a `folder_id`, o que confirma o vinculo funcional entre analise e pasta.
- **`CreateAnalysisUseCase`** (`src/animus/core/intake/use_cases/create_analysis_use_case.py`) - referencia de caso de uso que ja aceita `folder_id` opcional na criacao de analise.
- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) - model SQLAlchemy com coluna `folder_id`, reutilizada para calcular `analysis_count`.
- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) - referencia de repository paginado com `CursorPaginationResponse`.

## Camada REST / Routers / Pipes

- **`CreateAnalysisController`** (`src/animus/rest/controllers/intake/create_analysis_controller.py`) - melhor referencia de `POST` simples com `_Body`, `AuthPipe` e `DatabasePipe`.
- **`ListAnalysesController`** (`src/animus/rest/controllers/intake/list_analyses_controller.py`) - referencia de listagem paginada por cursor usando `CursorPaginationResponse`.
- **`GetAnalysisController`** (`src/animus/rest/controllers/intake/get_analysis_controller.py`) - referencia de `GET` por `id` com `AuthPipe` e repasse direto para `UseCase`.
- **`RenameAnalysisController`** (`src/animus/rest/controllers/intake/rename_analysis_controller.py`) - referencia de `PATCH` com `_Body` contendo apenas `name`.
- **`ArchiveAnalysisController`** (`src/animus/rest/controllers/intake/archive_analysis_controller.py`) - referencia de arquivamento por endpoint dedicado.
- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) - referencia de router agregador por contexto.
- **`AuthPipe`** (`src/animus/pipes/auth_pipe.py`) - dependencia reutilizavel para extrair o `account_id` autenticado.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) - ponto atual de injecao de repositories SQLAlchemy por `Depends(...)`.
- **`IdSchema`** (`src/animus/validation/shared/id_schema.py`) - schema compartilhado para validar `ULID` em path params.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) - mapeia `NotFoundError` para `404` e `ForbiddenError` para `403`.

## Camada Database

- **`Model`** (`src/animus/database/sqlalchemy/models/model.py`) - base declarativa comum com `created_at` e `updated_at`.
- **`migrations/env.py`** - hoje importa apenas `models.auth` e `models.intake`; precisara conhecer o novo pacote `models.library` para metadata do Alembic.

## Lacunas identificadas

- Nao existe `use_cases/` no contexto `src/animus/core/library/`.
- Nao existe `rest/controllers/library/` nem `routers/library/`.
- Nao existe persistencia SQLAlchemy do contexto `library` em `models`, `mappers` ou `repositories`.
- Nao existe tabela `folders` nas migrations atuais.
- O `FoldersRepository` atual nao possui `find_by_id(...)` e sua `find_many(...)` ainda nao recebe `account_id`, o que impede ownership correto na listagem.
- `Folder.create(...)` ignora o `analysis_count` do DTO hoje e sempre zera o valor.

---

# 6. O que deve ser criado?

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/library/domain/errors/folder_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** quando `folder_id` nao existir nos fluxos de consulta, renomeacao ou arquivamento.

- **Localizacao:** `src/animus/core/library/domain/errors/__init__.py` (**novo arquivo**)
- **Classe base:** nao aplicavel
- **Motivo:** estabilizar exports publicos de erros do contexto `library`.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/library/use_cases/create_folder_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `FoldersRepository`
- **Metodo principal:** `execute(account_id: str, name: str) -> FolderDto` - cria uma nova pasta ativa para a conta autenticada e retorna o DTO com `id` gerado.
- **Fluxo resumido:** normalizar `account_id` -> montar `FolderDto(name, account_id, analysis_count=0, is_archived=False)` -> `Folder.create(...)` -> `FoldersRepository.add(...)` -> retornar `folder.dto`.

- **Localizacao:** `src/animus/core/library/use_cases/get_folder_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `FoldersRepository`
- **Metodo principal:** `execute(account_id: str, folder_id: str) -> FolderDto` - carrega a pasta por `id`, valida ownership e retorna o DTO.
- **Fluxo resumido:** normalizar `account_id` e `folder_id` -> `FoldersRepository.find_by_id(...)` -> `FolderNotFoundError` se ausente -> `ForbiddenError` se outra conta -> retornar `folder.dto`.

- **Localizacao:** `src/animus/core/library/use_cases/rename_folder_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `FoldersRepository`
- **Metodo principal:** `execute(account_id: str, folder_id: str, name: str) -> FolderDto` - renomeia a pasta apos validar ownership.
- **Fluxo resumido:** carregar pasta -> validar ownership -> `folder.rename(name)` -> `FoldersRepository.replace(folder)` -> retornar `folder.dto`.

- **Localizacao:** `src/animus/core/library/use_cases/archive_folder_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `FoldersRepository`
- **Metodo principal:** `execute(account_id: str, folder_id: str) -> FolderDto` - arquiva a pasta apos validar ownership.
- **Fluxo resumido:** carregar pasta -> validar ownership -> `folder.archive()` -> `FoldersRepository.replace(folder)` -> retornar `folder.dto`.

- **Localizacao:** `src/animus/core/library/use_cases/list_folders_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `FoldersRepository`
- **Metodo principal:** `execute(account_id: str, search: str, cursor: str | None, limit: int) -> CursorPaginationResponse[FolderDto]` - lista pastas ativas da conta com paginação por cursor.
- **Fluxo resumido:** validar `limit >= 1` -> normalizar `account_id`, `search`, `cursor` e `limit` -> `FoldersRepository.find_many(...)` -> mapear `Folder` para `FolderDto`.

- **Localizacao:** `src/animus/core/library/use_cases/__init__.py` (**novo arquivo**)
- **Dependencias (ports injetados):** nao aplicavel
- **Metodo principal:** nao aplicavel - exporta os `use_cases` publicos do contexto `library`.

## Camada Database (Models SQLAlchemy)

- **Localizacao:** `src/animus/database/sqlalchemy/models/library/folder_model.py` (**novo arquivo**)
- **Tabela:** `folders`
- **Colunas:** `id` (`String(26)`, `primary_key=True`), `name` (`String`, `nullable=False`), `account_id` (`String(26)`, `nullable=False`, `index=True`), `is_archived` (`Boolean`, `nullable=False`)
- **Relacionamentos:** nao aplicavel neste escopo; `analysis_count` sera derivado por agregacao sobre `analyses.folder_id`.

- **Localizacao:** `src/animus/database/sqlalchemy/models/library/__init__.py` (**novo arquivo**)
- **Tabela:** nao aplicavel
- **Colunas:** nao aplicavel
- **Relacionamentos:** nao aplicavel - exporta `FolderModel`.

## Camada Database (Mappers)

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/library/folder_mapper.py` (**novo arquivo**)
- **Metodos:**
- `to_entity(model: FolderModel, analysis_count: int = 0) -> Folder` - reconstrui a entidade de dominio usando o count agregado vindo da query.
- `to_model(entity: Folder) -> FolderModel` - cria o model ORM da pasta sem persistir `analysis_count`.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/library/__init__.py` (**novo arquivo**)
- **Metodos:** nao aplicavel - exporta `FolderMapper`.

## Camada Database (Repositorios)

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/library/sqlalchemy_folders_repository.py` (**novo arquivo**)
- **Interface implementada:** `FoldersRepository`
- **Dependencias:** `Session` SQLAlchemy, `FolderMapper`
- **Metodos:**
- `find_by_id(folder_id: Id) -> Folder | None` - busca a pasta por `id` com agregacao de `analysis_count` a partir de `AnalysisModel`.
- `find_many(account_id: Id, search: Text, cursor: Id | None, limit: Integer) -> CursorPaginationResponse[Folder]` - lista apenas pastas ativas da conta, filtra por `name ilike`, pagina por cursor e agrega `analysis_count` em SQL.
- `add(folder: Folder) -> None` - persiste a nova pasta.
- `add_many(folders: list[Folder]) -> None` - persiste varias pastas em lote.
- `replace(folder: Folder) -> None` - atualiza `name` e `is_archived` da pasta existente.

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/library/__init__.py` (**novo arquivo**)
- **Interface implementada:** nao aplicavel
- **Dependencias:** nao aplicavel
- **Metodos:** nao aplicavel - exporta `SqlalchemyFoldersRepository`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/library/create_folder_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body { name: str }` com validacoes `min_length=1` e `max_length=50`
- **Metodo HTTP e path:** `POST /library/folders`
- **`status_code`:** `201`
- **`response_model`:** `FolderDto`
- **Dependencias injetadas via `Depends`:** `AuthPipe.get_account_id_from_request`, `DatabasePipe.get_folders_repository_from_request`
- **Fluxo:** `_Body.name` -> `CreateFolderUseCase.execute(account_id=..., name=...)` -> resposta

- **Localizacao:** `src/animus/rest/controllers/library/get_folder_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `GET /library/folders/{folder_id}`
- **`status_code`:** `200`
- **`response_model`:** `FolderDto`
- **Dependencias injetadas via `Depends`:** `AuthPipe.get_account_id_from_request`, `DatabasePipe.get_folders_repository_from_request`
- **Fluxo:** `folder_id: IdSchema` -> `GetFolderUseCase.execute(account_id=..., folder_id=...)` -> resposta

- **Localizacao:** `src/animus/rest/controllers/library/rename_folder_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body { name: str }` com validacoes `min_length=1` e `max_length=50`
- **Metodo HTTP e path:** `PATCH /library/folders/{folder_id}`
- **`status_code`:** `200`
- **`response_model`:** `FolderDto`
- **Dependencias injetadas via `Depends`:** `AuthPipe.get_account_id_from_request`, `DatabasePipe.get_folders_repository_from_request`
- **Fluxo:** `folder_id: IdSchema` + `_Body.name` -> `RenameFolderUseCase.execute(...)` -> resposta

- **Localizacao:** `src/animus/rest/controllers/library/archive_folder_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `PATCH /library/folders/{folder_id}/archive`
- **`status_code`:** `200`
- **`response_model`:** `FolderDto`
- **Dependencias injetadas via `Depends`:** `AuthPipe.get_account_id_from_request`, `DatabasePipe.get_folders_repository_from_request`
- **Fluxo:** `folder_id: IdSchema` -> `ArchiveFolderUseCase.execute(account_id=..., folder_id=...)` -> resposta

- **Localizacao:** `src/animus/rest/controllers/library/list_folders_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `GET /library/folders`
- **`status_code`:** `200`
- **`response_model`:** `CursorPaginationResponse[FolderDto]`
- **Dependencias injetadas via `Depends`:** `AuthPipe.get_account_id_from_request`, `DatabasePipe.get_folders_repository_from_request`
- **Fluxo:** `limit`, `cursor`, `search` -> `ListFoldersUseCase.execute(...)` -> resposta

- **Localizacao:** `src/animus/rest/controllers/library/__init__.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** nao aplicavel
- **`status_code`:** nao aplicavel
- **`response_model`:** nao aplicavel
- **Dependencias injetadas via `Depends`:** nao aplicavel
- **Fluxo:** nao aplicavel - exporta os controllers do contexto `library`.

## Camada Routers

- **Localizacao:** `src/animus/routers/library/library_router.py` (**novo arquivo**)
- **Prefixo da rota:** `/library`
- **Controllers registrados:** `CreateFolderController`, `GetFolderController`, `RenameFolderController`, `ArchiveFolderController`, `ListFoldersController`

- **Localizacao:** `src/animus/routers/library/__init__.py` (**novo arquivo**)
- **Prefixo da rota:** nao aplicavel
- **Controllers registrados:** nao aplicavel - exporta `LibraryRouter`.

## Migrações Alembic

- **Localizacao:** `migrations/versions/` (**novo arquivo**)
- **Operacoes:** criar tabela `folders`; criar indice em `folders.account_id`; criar indice em `analyses.folder_id` para suportar agregacao de `analysis_count`.
- **Reversibilidade:** `downgrade` deve remover o indice novo de `analyses.folder_id` e depois dropar a tabela `folders`; nao ha perda de dados de `analyses`, apenas perda dos registros de pasta na reversao.

---

# 7. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/library/domain/entities/folder.py`
- **Mudanca:** fazer `Folder.create(...)` respeitar `dto.analysis_count` em vez de fixar `0`; adicionar `rename(name: str) -> None` e `archive() -> None`; concentrar a validacao do limite de `50` caracteres do nome da pasta no dominio.
- **Justificativa:** a entidade atual nao suporta renomeacao/arquivamento e hoje perde o `analysis_count` vindo do repository.

- **Arquivo:** `src/animus/core/library/interfaces/folders_repository.py`
- **Mudanca:** adicionar `find_by_id(folder_id: Id) -> Folder | None` e ajustar `find_many(...)` para receber `account_id: Id`.
- **Justificativa:** sem esses contratos nao e possivel implementar `GET/PATCH` por `folder_id` nem restringir a listagem ao dono da pasta.

## Camada Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
- **Mudanca:** marcar `folder_id` como indexado no model SQLAlchemy.
- **Justificativa:** a nova feature passa a agregar `analyses` por `folder_id` em leituras frequentes de `library`.

- **Arquivo:** `src/animus/database/sqlalchemy/models/__init__.py`
- **Mudanca:** incluir o pacote/model do contexto `library` nos exports/imports de metadata.
- **Justificativa:** manter descoberta consistente de models SQLAlchemy pelo restante da aplicacao.

- **Arquivo:** `migrations/env.py`
- **Mudanca:** importar `animus.database.sqlalchemy.models.library` junto dos pacotes `auth` e `intake`.
- **Justificativa:** permitir que o Alembic enxergue a nova tabela `folders` no `target_metadata`.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudanca:** adicionar `get_folders_repository_from_request(...) -> FoldersRepository` instanciando `SqlalchemyFoldersRepository` a partir da `Session` atual.
- **Justificativa:** os controllers do modulo `library` devem receber o repository via `Depends(...)`, seguindo o padrao do projeto.

## Camada Routers / App

- **Arquivo:** `src/animus/routers/__init__.py`
- **Mudanca:** exportar `LibraryRouter` junto aos routers ja existentes.
- **Justificativa:** estabilizar imports publicos do pacote `routers`.

- **Arquivo:** `src/animus/app.py`
- **Mudanca:** registrar `LibraryRouter.register()` no `FastAPIApp.register()`.
- **Justificativa:** expor a nova superficie HTTP `/library` na aplicacao.

> `src/animus/validation/shared/id_schema.py` permanece reutilizado sem alteracao. Schemas de entrada seguem locais aos controllers.

---

# 8. O que deve ser removido?

**Nao aplicavel**.

---

# 9. Decisoes Tecnicas e Trade-offs

- **Decisao:** manter ownership check em `GetFolderUseCase`, `RenameFolderUseCase` e `ArchiveFolderUseCase`, usando `FolderNotFoundError` para ausencia e `ForbiddenError` para pasta de outra conta.
- **Alternativas consideradas:** criar um `LibraryPipe` guard similar ao `IntakePipe`.
- **Motivo da escolha:** o modulo precisa apenas de um repository e um check simples de ownership; manter a regra no `core` evita um `pipe` novo que seria apenas pass-through.
- **Impactos / trade-offs:** ha pequena duplicacao do check em 3 `use_cases`, mas o fluxo permanece mais explicito e alinhado ao papel do `core`.

- **Decisao:** derivar `analysis_count` por query SQL sobre `analyses` em vez de persistir contador em `folders`.
- **Alternativas consideradas:** adicionar coluna materializada `analysis_count` em `folders`.
- **Motivo da escolha:** evita dupla escrita e risco de contador inconsistente quando analises forem movidas, arquivadas ou desarquivadas.
- **Impactos / trade-offs:** os `repositories` de leitura ficam mais complexos e exigem agregacao/indexacao em banco.

- **Decisao:** criar o modulo HTTP em `rest/controllers/library/` e `routers/library/` em vez de anexar endpoints ao contexto `intake`.
- **Alternativas consideradas:** expor tudo dentro de `IntakeRouter` por conveniencia.
- **Motivo da escolha:** o contrato publico do ticket e `/library`, e o `core` ja separa o conceito em `src/animus/core/library/`.
- **Impactos / trade-offs:** aumenta a quantidade de arquivos/pacotes, mas preserva fronteiras de contexto e facilita evolucao futura do modulo `library`.

- **Decisao:** nao criar arquivos novos em `src/animus/validation/` para este ANI-65.
- **Alternativas consideradas:** criar `validation/library/folder_body.py` ou schemas dedicados de resposta.
- **Motivo da escolha:** os corpos de entrada sao exclusivos de cada controller e o projeto ja usa `DTOs` do `core` como `response_model`; o unico schema compartilhado necessario e `IdSchema`, que ja existe.
- **Impactos / trade-offs:** as constraints de `name` aparecem em mais de um controller, mas continuam pequenas e locais.

- **Decisao:** tratar `PATCH /library/folders/{folder_id}/archive` como fonte de verdade do ANI-65 e deixar exclusao de pasta fora do escopo.
- **Alternativas consideradas:** implementar exclusao com movimentacao para `Sem pasta`, conforme o PRD geral do RF 04.
- **Motivo da escolha:** o ticket ANI-65 explicita `archive` com `is_archived`, e o dominio `Folder` ja possui `is_archived` como evidência de soft-delete.
- **Impactos / trade-offs:** a spec cobre o slice exato do ticket, mas o comportamento de exclusao real permanece para task futura.

---

# 10. Diagramas e Referencias

- **Fluxo de dados:**

```text
HTTP Request
-> FastAPI Router (/library)
-> Controller (library)
-> AuthPipe.get_account_id_from_request()
-> DatabasePipe.get_folders_repository_from_request()
-> Folder*UseCase.execute(...)
-> FoldersRepository (core port)
-> SqlalchemyFoldersRepository
-> folders table
-> aggregate COUNT on analyses.folder_id
-> FolderDto / CursorPaginationResponse[FolderDto]
-> JSON Response
```

- **Fluxo assíncrono:** Nao aplicavel.

- **Referencias:**
- `src/animus/rest/controllers/intake/create_analysis_controller.py`
- `src/animus/rest/controllers/intake/list_analyses_controller.py`
- `src/animus/rest/controllers/intake/get_analysis_controller.py`
- `src/animus/rest/controllers/intake/rename_analysis_controller.py`
- `src/animus/rest/controllers/intake/archive_analysis_controller.py`
- `src/animus/core/intake/use_cases/create_analysis_use_case.py`
- `src/animus/core/intake/use_cases/get_analysis_use_case.py`
- `src/animus/core/intake/use_cases/list_analyses_use_case.py`
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
- `src/animus/routers/intake/intake_router.py`
- `src/animus/pipes/database_pipe.py`
- `src/animus/pipes/auth_pipe.py`

---

# 11. Pendencias / Duvidas

- **Descricao da pendencia:** `POST /intake/analyses` ja aceita `folder_id`, mas hoje nao valida se a pasta existe nem se pertence a conta autenticada.
- **Impacto na implementacao:** apos a introducao de `folders`, clientes antigos ou chamadas manuais ainda podem gravar referencias invalidas em `analyses.folder_id`, afetando consistencia da biblioteca e de `analysis_count`.
- **Acao sugerida:** validar com arquitetura/produto se essa protecao deve entrar no ANI-65 ou virar follow-up dedicado para endurecer o fluxo de criacao/movimentacao de analises.

---
title: Endpoint de atualizacao de nome da conta do usuario
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AwACAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-38
status: closed
last_updated_at: 2026-03-31
---

# 1. Objetivo

Implementar no `animus-server` um endpoint autenticado para o proprio usuario atualizar apenas o campo `name` da sua conta, mantendo `email` imutavel, sem alteracao de senha nesta entrega e preservando o padrao arquitetural de controller fino com orquestracao de negocio no `UseCase` do contexto `auth`.

---

# 2. Escopo

## 2.1 In-scope

- Criar endpoint HTTP autenticado para atualizar somente o nome da conta do usuario logado.
- Criar `UpdateAccountUseCase` no `core/auth` com entrada por **named params**.
- Reaproveitar `AuthPipe` para resolver o `account_id` via token `Bearer`.
- Reaproveitar `AccountsRepository.find_by_id(...)` e `replace(...)` para persistencia.
- Retornar `AccountDto` atualizado como contrato de resposta do endpoint.

## 2.2 Out-of-scope

- Alteracao de senha (fluxo com `current_password` e `new_password`).
- Alteracao de e-mail.
- Alteracao de `is_active`, `is_verified` ou `social_accounts`.
- Mudancas em schema SQLAlchemy, migrations Alembic ou novas tabelas.
- Mudancas no fluxo de login, cadastro, verificacao OTP ou login social.

---

# 3. Requisitos

## 3.1 Funcionais

- Expor endpoint autenticado `PATCH /auth/account`.
- Receber body JSON com `name: str`.
- Identificar a conta a partir do token (`AuthPipe.get_account_id_from_request`).
- Validar o nome com a regra de dominio existente (`Name.create(...)`).
- Atualizar o nome da conta e persistir via `AccountsRepository.replace(...)`.
- Retornar `200` com `AccountDto` refletindo o novo `name`.

## 3.2 Nao funcionais

- **Seguranca:** endpoint exige autenticacao `Bearer`; nao aceita atualizar conta de terceiros.
- **Seguranca:** nao deve aceitar nem processar campos de senha neste endpoint.
- **Compatibilidade retroativa:** sem quebra nos endpoints de `auth` existentes; apenas adicao de nova rota.
- **Arquitetura:** controller deve permanecer fino, sem regra de negocio ou SQL direto.
- **Consistencia de dominio:** validacao de nome deve reutilizar `Name` do `core/shared`.

---

# 4. O que ja existe? (Obrigatorio)

## Core

- **`Account`** (`src/animus/core/auth/domain/entities/account.py`) - entidade de conta com `id`, `name`, `email`, `is_verified`, `is_active` e conversao para `AccountDto`.
- **`AccountDto`** (`src/animus/core/auth/domain/entities/dtos/account_dto.py`) - DTO de saida da conta; inclui `name`, `email`, `id`, `is_verified`, `is_active` e `social_accounts`.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) - port com `find_by_id(...)`, `find_by_email(...)`, `add(...)`, `add_many(...)` e `replace(...)`.
- **`SignInUseCase`** (`src/animus/core/auth/use_cases/sign_in_use_case.py`) - referencia de `UseCase` com entrada por named params e dependencias por interfaces.
- **`Name`** (`src/animus/core/shared/domain/structures/name.py`) - `Structure` de validacao do nome (minimo de 2 caracteres apos `strip`).

## Database

- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) - implementa `find_by_id(...)` e `replace(...)`; `replace(...)` ja atualiza `model.name`.
- **`AccountModel`** (`src/animus/database/sqlalchemy/models/auth/account_model.py`) - model da tabela `accounts` com coluna `name` existente.
- **`AccountMapper`** (`src/animus/database/sqlalchemy/mappers/auth/account_mapper.py`) - mapeamento dominio <-> ORM para conta.

## REST

- **`SignInController`** (`src/animus/rest/controllers/auth/sign_in_controller.py`) - referencia de controller fino no contexto `auth` com `_Body` local e `Depends(...)`.
- **`CreatePetitionController`** (`src/animus/rest/controllers/intake/create_petition_controller.py`) - referencia de endpoint autenticado que usa `AuthPipe.get_account_id_from_request`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) - tratamento central de erros de dominio (`400`, `401`, `403`, `404`, `409`).

## Routers

- **`AuthRouter`** (`src/animus/routers/auth/auth_router.py`) - agrega endpoints do modulo `auth` e registra controllers via `Controller.handle(router)`.

## Pipes

- **`AuthPipe`** (`src/animus/pipes/auth_pipe.py`) - resolve e valida `account_id` autenticado a partir do JWT.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) - provedor de `AccountsRepository` via sessao SQLAlchemy do request.

## Lacunas identificadas

- Nao existe `UpdateAccountUseCase` no contexto `auth`.
- Nao existe `UpdateAccountController` para atualizar perfil no backend.
- Nao existe rota de atualizacao de conta registrada no `AuthRouter`.
- Nao existe operacao de dominio explicita em `Account` para alterar nome (apenas atributos e metodos de ativacao/verificacao).

---

# 5. O que deve ser criado? (Depende da tarefa)

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/auth/use_cases/update_account_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`
- **Metodo principal:** `execute(account_id: str, name: str) -> AccountDto` - atualiza o nome da conta autenticada e retorna o DTO atualizado.
- **Fluxo resumido:** `Id.create(account_id)` -> `Name.create(name)` -> `AccountsRepository.find_by_id(...)` -> atualizar entidade -> `AccountsRepository.replace(...)` -> `AccountDto`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/auth/update_account_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body` com `name: str` definido no mesmo arquivo.
- **Metodo HTTP e path:** `PATCH /auth/account`
- **`status_code`:** `200`
- **`response_model`:** `AccountDto`
- **Dependencias injetadas via `Depends`:** `account_id` via `AuthPipe.get_account_id_from_request`; `AccountsRepository` via `DatabasePipe.get_accounts_repository_from_request`
- **Fluxo:** `_Body` -> `UpdateAccountUseCase.execute(account_id=..., name=...)` -> resposta `AccountDto`

---

# 6. O que deve ser modificado? (Depende da tarefa)

## Core

- **Arquivo:** `src/animus/core/auth/domain/entities/account.py`
- **Mudanca:** adicionar metodo de comportamento para atualizar nome da entidade (ex.: `rename(name: Name) -> None`).
- **Justificativa:** manter encapsulamento da entidade e evitar mutacao direta de atributo pelo `UseCase`.

- **Arquivo:** `src/animus/core/auth/use_cases/__init__.py`
- **Mudanca:** exportar `UpdateAccountUseCase`.
- **Justificativa:** manter API publica do pacote de use cases consistente com o padrao atual.

## REST

- **Arquivo:** `src/animus/rest/controllers/auth/__init__.py`
- **Mudanca:** exportar `UpdateAccountController`.
- **Justificativa:** manter imports publicos do contexto `auth` estaveis.

## Routers

- **Arquivo:** `src/animus/routers/auth/auth_router.py`
- **Mudanca:** registrar `UpdateAccountController` no router `auth`.
- **Justificativa:** expor o novo endpoint dentro do modulo de autenticacao/conta.

---

# 7. O que deve ser removido? (Depende da tarefa)

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs (Obrigatorio)

- **Decisao:** limitar o endpoint desta spec a atualizacao de `name`.
  - **Alternativas consideradas:** atualizar nome e senha no mesmo endpoint; criar endpoint exclusivo de senha junto.
  - **Motivo da escolha:** decisao explicita de escopo para ANI-38, reduzindo risco e complexidade.
  - **Impactos / trade-offs:** fluxo de senha fica pendente para spec separada.

- **Decisao:** usar `PATCH /auth/account` para alteracao parcial da conta autenticada.
  - **Alternativas consideradas:** `PUT /auth/account`; `PATCH /auth/profile`.
  - **Motivo da escolha:** semantica de update parcial e alinhamento com contexto `auth` existente.
  - **Impactos / trade-offs:** introduz o primeiro endpoint `PATCH` do projeto, exigindo manter consistencia futura.

- **Decisao:** identificar alvo de atualizacao pelo token (`AuthPipe`) e nao por `account_id` no path.
  - **Alternativas consideradas:** `PATCH /auth/accounts/{account_id}`.
  - **Motivo da escolha:** perfil de usuario unico no produto; evita superficie para atualizacao de terceiros.
  - **Impactos / trade-offs:** endpoint fica restrito ao contexto de "minha conta".

- **Decisao:** retornar `AccountDto` apos persistir a alteracao.
  - **Alternativas consideradas:** `204 No Content`.
  - **Motivo da escolha:** permite ao cliente atualizar estado local imediatamente com o payload canonico.
  - **Impactos / trade-offs:** resposta tem payload maior que `204`, mas melhora ergonomia do cliente.

- **Decisao:** manter validacao de nome no dominio via `Name.create(...)`.
  - **Alternativas consideradas:** validar apenas no `BaseModel` da borda HTTP.
  - **Motivo da escolha:** regra de negocio permanece no `core`, conforme arquitetura.
  - **Impactos / trade-offs:** pode haver dupla validacao (Pydantic + dominio), mas com consistencia entre camadas.

---

# 9. Diagramas e Referencias (Obrigatorio)

- **Fluxo de dados:**

```text
PATCH /auth/account
  -> FastAPI middleware stack
  -> AuthRouter
  -> UpdateAccountController
  -> AuthPipe.get_account_id_from_request
  -> DatabasePipe.get_accounts_repository_from_request
  -> UpdateAccountUseCase
       -> Id.create(account_id)
       -> Name.create(name)
       -> AccountsRepository.find_by_id(...)
       -> Account.rename(...)
       -> AccountsRepository.replace(...)
  -> 200 AccountDto
```

- **Fluxo assincrono (se aplicavel):** **Nao aplicavel**.

- **Referencias:**
  - `src/animus/rest/controllers/auth/sign_in_controller.py`
  - `src/animus/rest/controllers/intake/create_petition_controller.py`
  - `src/animus/core/auth/use_cases/sign_in_use_case.py`
  - `src/animus/core/auth/interfaces/accounts_repository.py`
  - `src/animus/core/auth/domain/entities/account.py`
  - `src/animus/core/auth/domain/entities/dtos/account_dto.py`
  - `src/animus/core/shared/domain/structures/name.py`
  - `src/animus/pipes/auth_pipe.py`
  - `src/animus/pipes/database_pipe.py`
  - `src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`
  - `src/animus/routers/auth/auth_router.py`

---

# 10. Pendencias / Duvidas (Quando aplicavel)

**Sem pendencias**.

---

## Restricoes (Obrigatorio)

- **Nao inclui testes automatizados nesta spec.**
- O `core` nao deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou detalhes de infraestrutura.
- Todos os caminhos citados existem no projeto ou estao marcados como **novo arquivo**.
- Nao inventa contratos sem evidencia no PRD e na codebase; esta spec reaproveita `AccountDto`, `AuthPipe` e `AccountsRepository` existentes.
- Qualquer extensao para troca de senha deve ser tratada em outra spec dedicada.
- Schemas de entrada `*Body` ficam no arquivo do controller (`update_account_controller.py`).

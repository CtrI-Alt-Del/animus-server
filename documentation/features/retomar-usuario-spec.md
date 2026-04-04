---
title: Endpoint para retornar conta do usuario autenticado
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/16908291/PRD+RF+01+Gerenciamento+de+sessao+do+usuario
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-54
status: closed
last_updated_at: 2026-04-04
---

# 1. Objetivo

Implementar o endpoint autenticado `GET /auth/account` no `animus-server` para retornar os dados da conta vinculada ao token de acesso do usuario logado, preservando o padrao arquitetural de `controller` fino, resolucao de identidade via `AuthPipe` e regra de negocio concentrada no `GetAccountUseCase`.

---

# 2. Escopo

## 2.1 In-scope

- Expor `GET /auth/account` no modulo `auth`.
- Resolver `account_id` a partir do `Authorization: Bearer <token>` via `AuthPipe.get_account_id_from_request(...)`.
- Buscar conta no `core` usando `GetAccountUseCase.execute(account_id: Id) -> AccountDto`.
- Retornar `200` com `AccountDto` completo (`id`, `name`, `email`, `password`, `is_verified`, `is_active`, `social_accounts`).
- Responder erro de autenticacao quando token invalido/ausente de conta autenticada.

## 2.2 Out-of-scope

- Atualizacao de perfil (`PATCH /auth/account`) ou alteracao de senha.
- Alteracao de email da conta.
- Cadastro, login, verificacao de email ou login social.
- Mudancas de schema SQLAlchemy, migrations Alembic ou novas tabelas.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint deve aceitar apenas usuarios autenticados com token `Bearer` valido.
- O `account_id` deve ser extraido do `sub` do JWT de acesso via `AuthPipe`.
- O endpoint deve consultar a conta usando `AccountsRepository.find_by_id(account_id)` dentro do `GetAccountUseCase`.
- O endpoint deve retornar `AccountDto` com os dados atuais da conta autenticada.
- Se o token for invalido, o endpoint deve retornar erro de autenticacao (`401`).
- Se o `sub` do token nao corresponder a uma conta existente na verificacao do `AuthPipe`, o endpoint deve retornar erro de autenticacao (`401`) com a mensagem de conta autenticada nao encontrada.
- Se a conta for encontrada, mas estiver inativa, o endpoint deve retornar erro de acesso negado (`403`) via `AccountInactiveError`.

## 3.2 Nao funcionais

- **Seguranca:** endpoint protegido por autenticacao obrigatoria; nao pode expor dados de outra conta.
- **Compatibilidade retroativa:** adicao de rota sem quebra de contratos existentes de `auth`.
- **Arquitetura:** regra de negocio no `UseCase`; `controller` apenas valida/adapta/delega.
- **Observabilidade:** erros de dominio devem continuar sendo mapeados pelo `AppErrorHandler` e registrados em log.
- **Performance:** fluxo sincrono com consultas pontuais por `account_id`, sem chamadas externas.

---

# 4. O que ja existe? (Obrigatorio)

## Core

- **`AccountDto`** (`src/animus/core/auth/domain/entities/dtos/account_dto.py`) — contrato de resposta reutilizado no endpoint.
- **`GetAccountUseCase`** (`src/animus/core/auth/use_cases/get_account_use_case.py`) — orquestra busca da conta e validacao de conta inativa.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) — port com `find_by_id(account_id: Id) -> Account | None`.
- **`AccountNotFoundError`** (`src/animus/core/auth/domain/errors/account_not_found_error.py`) — erro de dominio para conta nao encontrada no caso de uso.
- **`AccountInactiveError`** (`src/animus/core/auth/domain/errors/account_inactive_error.py`) — erro de dominio para conta desativada.

## Database

- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) — implementa `find_by_id(...)` convertendo `AccountModel` para entidade de dominio.

## REST

- **`GetAccountController`** (`src/animus/rest/controllers/auth/get_account_controller.py`) — endpoint `GET /auth/account` com `response_model=AccountDto`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — mapeamento global de `AuthError` (`401`), `ForbiddenError` (`403`) e `NotFoundError` (`404`).

## Pipes

- **`AuthPipe.get_account_id_from_request`** (`src/animus/pipes/auth_pipe.py`) — valida header/token, extrai `sub` e garante existencia da conta autenticada.
- **`DatabasePipe.get_accounts_repository_from_request`** (`src/animus/pipes/database_pipe.py`) — injeta `AccountsRepository` via `Session` por request.

## Routers

- **`AuthRouter`** (`src/animus/routers/auth/auth_router.py`) — composicao do modulo `auth` com registro do `GetAccountController`.

## Implementacoes analogas (referencia)

- **`UpdateAccountController`** (`src/animus/rest/controllers/auth/update_account_controller.py`) — padrao de endpoint autenticado no mesmo recurso `/auth/account`.
- **`CreateAnalysisController`** (`src/animus/rest/controllers/intake/create_analysis_controller.py`) — uso de `Depends(AuthPipe.get_account_id_from_request)` por `Id`.

## Fluxo de dados atual e ponto de extensao

- Fluxo principal ja identificado: `HTTP -> AuthRouter -> GetAccountController -> AuthPipe -> GetAccountUseCase -> AccountsRepository -> PostgreSQL -> AccountDto`.
- A feature estende o modulo `auth` apenas com leitura autenticada da conta atual, sem alterar o modelo relacional.

## Pontos de atencao

- O fluxo executa verificacao de conta no `AuthPipe` e nova consulta no `UseCase`; e intencional para manter precondicao de autenticacao e regra de estado inativo separadas.
- A resposta reutiliza `AccountDto` completo; qualquer mudanca nesse DTO afeta consumidores de `GET` e `PATCH` em `/auth/account`.

## Lacunas

- Nao foram encontradas lacunas tecnicas bloqueantes para implementar o endpoint com os contratos atuais.

---

# 5. O que deve ser criado? (Depende da tarefa)

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/auth/use_cases/get_account_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`
- **Metodo principal:** `execute(account_id: Id) -> AccountDto` — busca conta por ID, valida status e retorna DTO de saida.
- **Fluxo resumido:** `find_by_id` -> valida existencia -> valida conta ativa -> mapeia para `AccountDto`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/auth/get_account_controller.py` (**novo arquivo**)
- **Metodo HTTP e path:** `GET /auth/account`
- **`status_code`:** `200`
- **`response_model`:** `AccountDto`
- **Dependencias injetadas via `Depends`:** `AuthPipe.get_account_id_from_request`, `DatabasePipe.get_accounts_repository_from_request`
- **Fluxo:** `Depends(AuthPipe)` -> `GetAccountUseCase.execute(account_id)` -> `AccountDto`

---

# 6. O que deve ser modificado? (Depende da tarefa)

## Camada Core

- **Arquivo:** `src/animus/core/auth/use_cases/__init__.py`
- **Mudanca:** exportar `GetAccountUseCase` no `__all__`.
- **Justificativa:** manter API publica dos use cases de `auth` consistente para importacoes no `rest`.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/auth/__init__.py`
- **Mudanca:** exportar `GetAccountController` no `__all__`.
- **Justificativa:** padronizar composicao de controllers do modulo `auth`.

## Camada Routers

- **Arquivo:** `src/animus/routers/auth/auth_router.py`
- **Mudanca:** registrar `GetAccountController.handle(router)` no `AuthRouter.register()`.
- **Justificativa:** publicar o endpoint no roteamento principal de autenticacao.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/auth_pipe.py`
- **Mudanca:** garantir verificacao de existencia da conta autenticada apos extrair `sub` do token, levantando `AuthError` quando ausente.
- **Justificativa:** manter semantica de falha de autenticacao (`401`) para token com subject sem conta valida.

---

# 7. O que deve ser removido? (Depende da tarefa)

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs (Obrigatorio)

- **Decisao:** retornar `AccountDto` completo no `GET /auth/account`.
  - **Alternativas consideradas:** DTO reduzido com apenas `id`, `name`, `email`.
  - **Motivo da escolha:** reaproveita contrato ja existente no contexto `auth` e evita criar novo schema sem necessidade.
  - **Impactos / trade-offs:** payload maior, mas reduz duplicacao de contratos e mantem consistencia com endpoints correlatos.

- **Decisao:** tratar conta ausente derivada do token como falha de autenticacao (`401`) no `AuthPipe`.
  - **Alternativas consideradas:** devolver `404` na camada de use case.
  - **Motivo da escolha:** a conta e precondicao de autenticacao no fluxo atual; ausencia invalida o contexto autenticado.
  - **Impactos / trade-offs:** semantica HTTP fica orientada a auth; `404` fica reservado para consultas de recurso de dominio fora da precondicao de token.

- **Decisao:** manter `AccountInactiveError` no `GetAccountUseCase` mesmo com autenticacao valida.
  - **Alternativas consideradas:** ignorar status de ativacao e sempre retornar conta.
  - **Motivo da escolha:** reforca regra de negocio de conta desativada sem mover regra para o `controller`.
  - **Impactos / trade-offs:** adiciona uma validacao de dominio extra, com retorno `403` para casos especificos.

- **Decisao:** separar responsabilidades entre `AuthPipe` (auth/precondicao) e `GetAccountUseCase` (estado de negocio).
  - **Alternativas consideradas:** centralizar toda validacao em apenas uma camada.
  - **Motivo da escolha:** alinhamento com Clean/Hexagonal e controllers/pipes finos.
  - **Impactos / trade-offs:** duas consultas por `account_id` no caminho feliz, em troca de clareza de fronteira arquitetural.

---

# 9. Diagramas e Referencias (Obrigatorio)

- **Fluxo de dados:**

```text
GET /auth/account
  -> Middleware HTTP (sessao SQLAlchemy)
  -> AuthRouter
  -> GetAccountController
  -> AuthPipe.get_account_id_from_request
       -> JwtProvider.decode(access_token)
       -> AccountsRepository.find_by_id(account_id) [precondicao auth]
  -> GetAccountUseCase.execute(account_id)
       -> AccountsRepository.find_by_id(account_id) [regra de negocio]
       -> valida conta ativa
       -> monta AccountDto
  -> 200 JSON (AccountDto)
```

- **Fluxo assincrono (se aplicavel):** **Nao aplicavel**.

- **Referencias:**
  - `src/animus/rest/controllers/auth/get_account_controller.py`
  - `src/animus/core/auth/use_cases/get_account_use_case.py`
  - `src/animus/pipes/auth_pipe.py`
  - `src/animus/core/auth/interfaces/accounts_repository.py`
  - `src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`
  - `src/animus/routers/auth/auth_router.py`
  - `src/animus/rest/handlers/app_error_handler.py`

---

# 10. Pendencias / Duvidas (Quando aplicavel)

- **Descricao da pendencia:** O campo de requisito vinculado no Jira ANI-54 aponta para o PRD de RF 02, enquanto a descricao funcional da task corresponde ao RF 01.
- **Impacto na implementacao:** baixo impacto tecnico, mas gera risco de rastreabilidade documental incorreta entre task e requisito de produto.
- **Acao sugerida:** ajustar o link de requisito no Jira para o PRD de RF 01.

---

## Restricoes (Obrigatorio)

- **Nao inclui testes automatizados nesta spec.**
- O `core` permanece sem dependencia de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou detalhes de infraestrutura.
- Todos os caminhos citados existem no projeto ou estao explicitamente marcados como **novo arquivo**.
- Nenhum contrato foi inventado sem evidencia no PRD, Jira e codebase; a spec reutiliza `AccountDto`, `AuthPipe` e `AccountsRepository` existentes.
- Quando ha divergencia de requisito, ela fica registrada em **Pendencias / Duvidas** para ajuste de rastreabilidade.

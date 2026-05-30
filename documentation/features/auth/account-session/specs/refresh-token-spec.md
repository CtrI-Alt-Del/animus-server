---
title: Endpoint para renovação de sessão
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/16908291
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-124
status: closed
last_updated_at: 2026-05-29
---

# 1. Objetivo

Implementar o endpoint `POST /auth/refresh` para renovar a sessão do usuário a partir de um `refresh_token` válido, emitindo uma nova `SessionDto` com `access_token` e `refresh_token` atualizados. A solução deve validar o token via `JwtProvider.decode()`, rejeitar tokens inválidos, expirados ou que não sejam do tipo `refresh`, confirmar que a conta ainda existe, está verificada e ativa, e manter o `core` isolado de `FastAPI`, `SQLAlchemy` e detalhes de infraestrutura.

---

# 2. Escopo

## 2.1 In-scope

- Criar o `RefreshSessionUseCase` no contexto `auth`.
- Criar erro de domínio para `refresh_token` inválido, expirado, mal formado, sem `sub` ou com `type != "refresh"`.
- Criar controller HTTP `POST /auth/refresh` sem guard de autenticação por `Authorization`.
- Reutilizar `AccountsRepository` para localizar a conta pelo `sub` do token.
- Reutilizar `JwtProvider.decode()` para validar assinatura/expiração e ler claims.
- Reutilizar `JwtProvider.encode()` para emitir nova `SessionDto`.
- Registrar o controller no `AuthRouter`.
- Atualizar exports públicos de `core/auth/use_cases` e `rest/controllers/auth` quando aplicável.

## 2.2 Out-of-scope

- Alterar TTL de `access_token` ou `refresh_token`.
- Persistir refresh tokens no banco ou implementar revogação server-side.
- Implementar rotação com blacklist, token family ou detecção de replay.
- Alterar o contrato de `SessionDto`.
- Alterar login, cadastro, verificação de e-mail ou login com Google.
- Criar testes automatizados nesta spec.
- Criar migrations Alembic ou alterar models SQLAlchemy.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /auth/refresh` deve receber JSON `{ "refresh_token": "..." }`.
- Em caso de sucesso, deve retornar `200` com `SessionDto` contendo novo `access_token` e novo `refresh_token`.
- Deve retornar `401` quando o token estiver expirado, mal formado, com assinatura inválida, sem `sub`, sem `type` ou com `type != "refresh"`.
- Deve retornar `401` quando o `sub` do token não corresponder a uma conta existente.
- Deve retornar `403` quando `account.is_verified == False`.
- Deve retornar `403` quando `account.is_active == False`.
- O endpoint não deve exigir `Authorization: Bearer ...`, pois o token de renovação vem no body.

## 3.2 Não funcionais

- **Segurança:** aceitar somente tokens com claim `type == "refresh"`; tokens de acesso não podem renovar sessão.
- **Segurança:** manter validação de assinatura e expiração centralizada no `JwtProvider.decode()`.
- **Compatibilidade retroativa:** preservar `SessionDto` atual, com `access_token.value`, `access_token.expires_at`, `refresh_token.value` e `refresh_token.expires_at`.
- **Arquitetura:** manter `RefreshSessionUseCase` no `core` sem dependência de `FastAPI`, `SQLAlchemy`, `jose`, `Env` ou qualquer detalhe HTTP.
- **Idempotência:** múltiplas chamadas com o mesmo `refresh_token` válido podem emitir novas sessões sem alterar estado persistido.

---

# 4. O que já existe?

## Core

- **`SessionDto`** (`src/animus/core/auth/domain/structures/dtos/session_dto.py`) — contrato de resposta já usado por `sign-in`, `verify-email` e Google auth.
- **`TokenDto`** (`src/animus/core/auth/domain/structures/dtos/token_dto.py`) — estrutura dos tokens retornados em `SessionDto`.
- **`JwtProvider`** (`src/animus/core/auth/interfaces/jwt_provider.py`) — port com `encode(subject: Text) -> Session` e `decode(token: Text) -> dict[str, str]`.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) — port com `find_by_id(account_id: Id) -> Account | None`.
- **`SignInUseCase`** (`src/animus/core/auth/use_cases/sign_in_use_case.py`) — referência para emissão de `SessionDto` e validação de conta ativa/verificada.
- **`AccountNotVerifiedError`** (`src/animus/core/auth/domain/errors/account_not_verified_error.py`) — erro `ForbiddenError` mapeado para `403`.
- **`AccountInactiveError`** (`src/animus/core/auth/domain/errors/account_inactive_error.py`) — erro `ForbiddenError` mapeado para `403`.
- **`AuthError`** (`src/animus/core/shared/domain/errors/auth_error.py`) — classe base de erros mapeados para `401` por handler global.
- **`Text` e `Id`** (`src/animus/core/shared/domain/structures/`) — structures usadas para adaptar strings primitivas para ports do domínio.

## Providers

- **`JoseJwtProvider`** (`src/animus/providers/auth/jwt/jose/jose_jwt_provider.py`) — implementação concreta que gera claims `type: "access"` e `type: "refresh"`, aplica TTLs via `Env` e valida assinatura/expiração no `decode()`.

## REST

- **`SignInController`** (`src/animus/rest/controllers/auth/sign_in_controller.py`) — referência de controller com `_Body`, `response_model=SessionDto`, `Depends(DatabasePipe...)`, `Depends(ProvidersPipe...)` e chamada a `UseCase.execute(...)`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — mapeia `AuthError` para `401` e `ForbiddenError` para `403`.

## Routers

- **`AuthRouter`** (`src/animus/routers/auth/auth_router.py`) — composição do prefixo `/auth` e registro dos controllers de autenticação.

## Pipes

- **`DatabasePipe.get_accounts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provê `AccountsRepository` a partir da `Session` SQLAlchemy anexada ao request.
- **`ProvidersPipe.get_jwt_provider()`** (`src/animus/pipes/providers_pipe.py`) — provê `JwtProvider` concreto.
- **`AuthPipe.get_account_id_from_request(...)`** (`src/animus/pipes/auth_pipe.py`) — referência de validação de token `access`; não deve ser usado no refresh porque o endpoint recebe `refresh_token` no body e não no header.

## Database

- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) — implementação existente de `find_by_id(account_id: Id) -> Account | None`.
- **`AccountModel`** (`src/animus/database/sqlalchemy/models/auth/account_model.py`) — já possui `is_verified` e `is_active`, sem necessidade de alteração.
- **`AuthSeeder`** (`src/animus/database/sqlalchemy/seeders/auth_seeder.py`) — cria conta verificada para ambiente seedado; não precisa ser alterado.

---

# 5. O que deve ser criado?

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/auth/domain/errors/invalid_refresh_token_error.py` (**novo arquivo**)
- **Classe base:** `AuthError`
- **Classe:** `InvalidRefreshTokenError`
- **Motivo:** deve ser levantado quando o `refresh_token` for expirado, mal formado, inválido, não decodificável, sem `sub`, com `sub` inválido, com conta inexistente ou com `type != "refresh"`.
- **Mensagem:** usar mensagem genérica, por exemplo `Refresh token invalido`, sem diferenciar expiração, assinatura, formato ou conta inexistente.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/auth/use_cases/refresh_session_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AccountsRepository`, `JwtProvider`.
- **Método principal:** `execute(refresh_token: str) -> SessionDto` — valida o refresh token, verifica a conta e emite uma nova sessão.
- **Fluxo resumido:**
- Criar `Text` a partir de `refresh_token`.
- Chamar `jwt_provider.decode(token)` dentro de bloco que converte qualquer falha de decode para `InvalidRefreshTokenError`.
- Validar `payload.get("type") == "refresh"`; caso contrário, levantar `InvalidRefreshTokenError`.
- Obter `subject = payload.get("sub")`; se ausente, levantar `InvalidRefreshTokenError`.
- Criar `Id` a partir do `subject`; erros de validação devem virar `InvalidRefreshTokenError`.
- Buscar conta com `accounts_repository.find_by_id(account_id)`; se não existir, levantar `InvalidRefreshTokenError`.
- Se `account.is_verified.is_false`, levantar `AccountNotVerifiedError`.
- Se `account.is_active.is_false`, levantar `AccountInactiveError`.
- Retornar `jwt_provider.encode(Text.create(account.id.value)).dto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/auth/refresh_session_controller.py` (**novo arquivo**)
- **`_Body`:** schema Pydantic de entrada no mesmo arquivo do controller.
- **Campos do `_Body`:** `refresh_token: str`.
- **Método HTTP e path:** `POST /auth/refresh`.
- **`status_code`:** `200`.
- **`response_model`:** `SessionDto`.
- **Dependências injetadas via `Depends`:** `AccountsRepository` por `DatabasePipe.get_accounts_repository_from_request`, `JwtProvider` por `ProvidersPipe.get_jwt_provider`.
- **Fluxo:** `_Body.refresh_token` → named param `refresh_token=body.refresh_token` → `RefreshSessionUseCase.execute(...)` → `SessionDto`.
- **Observação:** não usar `AuthPipe.get_account_id_from_request(...)`, porque ele valida apenas `access_token` no header `Authorization`.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/auth/domain/errors/__init__.py`
- **Mudança:** exportar `InvalidRefreshTokenError` em import e `__all__`.
- **Justificativa:** manter o padrão de exports públicos para erros do contexto `auth`.

- **Arquivo:** `src/animus/core/auth/use_cases/__init__.py`
- **Mudança:** exportar `RefreshSessionUseCase` em import e `__all__`.
- **Justificativa:** permitir import consistente via `from animus.core.auth.use_cases import RefreshSessionUseCase`, seguindo `SignInUseCase`.

## REST

- **Arquivo:** `src/animus/rest/controllers/auth/__init__.py`
- **Mudança:** exportar `RefreshSessionController` em import e `__all__`.
- **Justificativa:** manter o padrão de registry centralizado de controllers de `auth`.

## Routers

- **Arquivo:** `src/animus/routers/auth/auth_router.py`
- **Mudança:** importar `RefreshSessionController` e chamar `RefreshSessionController.handle(router)` junto aos demais endpoints de autenticação.
- **Justificativa:** registrar `POST /auth/refresh` sob o prefixo existente `/auth`.

## Pipes

- **Não aplicável**. Os pipes existentes já fornecem `AccountsRepository` e `JwtProvider`.

## Database

- **Não aplicável**. O fluxo usa `AccountsRepository.find_by_id(...)` já implementado e não exige alteração de models, mappers, repositórios, seeders, arquivos persistidos ou paths gerados/consumidos.

## Providers

- **Não aplicável**. `JoseJwtProvider.decode(...)` e `JoseJwtProvider.encode(...)` já atendem ao contrato necessário.

## Validation

- **Não aplicável**. O body de entrada é exclusivo do controller e deve ficar como `_Body` em `refresh_session_controller.py`; a saída reutiliza `SessionDto` existente.

## Migrações Alembic

- **Não aplicável**. Não há alteração de schema de banco.

---

# 7. O que deve ser removido?

**Não aplicável**.

---

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** criar `RefreshSessionUseCase` dedicado.
- **Alternativas consideradas:** reaproveitar `SignInUseCase` ou validar token diretamente no controller.
- **Motivo da escolha:** o fluxo tem regra própria de domínio, não envolve senha e deve ficar no `core`, preservando controllers finos.
- **Impactos / trade-offs:** adiciona um arquivo novo, mas evita acoplamento HTTP e duplicação indevida com login.

- **Decisão:** criar `InvalidRefreshTokenError` baseado em `AuthError`.
- **Alternativas consideradas:** usar `InvalidCredentialsError` ou levantar `AuthError` diretamente no use case.
- **Motivo da escolha:** `InvalidCredentialsError` tem mensagem específica de e-mail/senha, inadequada para refresh; erro específico mantém semântica clara e ainda é mapeado para `401`.
- **Impactos / trade-offs:** adiciona uma classe pequena de erro, com mensagem genérica para não vazar detalhes do token.

- **Decisão:** tratar conta inexistente como `InvalidRefreshTokenError` e retornar `401`.
- **Alternativas consideradas:** usar `AccountNotFoundError` com `404`.
- **Motivo da escolha:** o Jira exige `401` se `AccountsRepository.find_by_id(decoded.sub)` não encontrar conta; também evita revelar existência de contas.
- **Impactos / trade-offs:** o consumidor recebe erro genérico de token inválido, não detalhe de conta removida/inexistente.

- **Decisão:** não criar novo pipe.
- **Alternativas consideradas:** criar `AuthPipe.get_refresh_payload_from_body(...)` ou pipe específico para refresh.
- **Motivo da escolha:** a validação do token refresh é o fluxo principal da feature e pertence ao use case; os pipes atuais já resolvem as dependências necessárias.
- **Impactos / trade-offs:** o controller instancia o use case como os demais controllers de `auth`, sem aumentar a superfície de DI.

- **Decisão:** não persistir nem revogar refresh tokens.
- **Alternativas consideradas:** tabela de sessões, blacklist em Redis ou rotação com token family.
- **Motivo da escolha:** PRD e Jira pedem renovação baseada em JWT stateless; não há contrato persistido existente para sessão.
- **Impactos / trade-offs:** chamadas repetidas com o mesmo refresh válido geram novas sessões até a expiração do token original; replay protection fica fora deste escopo.

---

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP Request
  POST /auth/refresh { refresh_token }
    -> Middleware SQLAlchemy por request
    -> AuthRouter (/auth)
    -> RefreshSessionController
    -> Depends(DatabasePipe.get_accounts_repository_from_request)
    -> Depends(ProvidersPipe.get_jwt_provider)
    -> RefreshSessionUseCase.execute(refresh_token)
    -> JwtProvider.decode(Text(refresh_token))
    -> AccountsRepository.find_by_id(Id(payload.sub))
    -> SqlalchemyAccountsRepository
    -> PostgreSQL accounts
    -> JwtProvider.encode(Text(account.id))
    -> SessionDto
    -> Response JSON 200
```

- **Fluxo assíncrono:** Não aplicável.

- **Referências:**
- `src/animus/core/auth/use_cases/sign_in_use_case.py` — padrão de use case que valida conta ativa/verificada e emite `SessionDto`.
- `src/animus/rest/controllers/auth/sign_in_controller.py` — padrão de controller com `_Body`, `Depends` e retorno `SessionDto`.
- `src/animus/routers/auth/auth_router.py` — ponto de registro dos controllers sob `/auth`.
- `src/animus/pipes/database_pipe.py` — provider do `AccountsRepository`.
- `src/animus/pipes/providers_pipe.py` — provider do `JwtProvider`.
- `src/animus/providers/auth/jwt/jose/jose_jwt_provider.py` — geração e decode dos tokens com claims `type`, `sub`, `iat` e `exp`.
- `src/animus/rest/handlers/app_error_handler.py` — mapeamento global de `AuthError` para `401` e `ForbiddenError` para `403`.
- `src/animus/core/auth/domain/errors/account_not_verified_error.py` — referência de erro `403` para conta não verificada.
- `src/animus/core/auth/domain/errors/account_inactive_error.py` — referência de erro `403` para conta inativa.

---

# 10. Pendências / Dúvidas

**Sem pendências**.

---

## Restrições

- **Não inclua testes automatizados na spec.**
- O `core` não deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou qualquer detalhe de infraestrutura.
- Todos os caminhos citados existem no projeto ou estão marcados como **novo arquivo**.
- Schemas `*Body` de entrada exclusivos de controller devem permanecer no arquivo do controller.
- O repasse ao `UseCase` deve usar named params, pois `refresh_token` é campo primitivo simples.

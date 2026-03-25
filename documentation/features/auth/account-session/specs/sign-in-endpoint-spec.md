---
title: Endpoint de sign-in com e-mail e senha
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AwACAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-34
status: closed
last_updated_at: 2026-03-24
---

# 1. Objetivo

Implementar o endpoint `POST /auth/sign-in` para autenticar contas manuais por e-mail e senha no `animus-server`, reutilizando `HashProvider` e `JwtProvider` ja existentes, mantendo o contrato de resposta em `SessionDto`, retornando erro generico para credenciais invalidas e bloqueando explicitamente contas nao verificadas ou inativas sem introduzir `DTO` de entrada no `core`.

---

# 2. Escopo

## 2.1 In-scope

- Criar o fluxo HTTP de `sign-in` por e-mail e senha em `auth`.
- Criar o `SignInUseCase` no `core` com entrada por **named parameters**.
- Criar erros de dominio especificos para `401` generico, `403` por e-mail nao confirmado e `403` por conta inativa.
- Estender o contrato de `AccountsRepository` para recuperar o `password_hash` persistido sem expor hash em `Account` ou `AccountDto`.
- Registrar o novo controller no `AuthRouter` e ajustar a traducao HTTP para suportar `403 Forbidden` mantendo o payload atual de erro.

## 2.2 Out-of-scope

- Login com Google e qualquer alteracao no fluxo `POST /auth/sign-up/google`.
- `refresh token`, renovacao de sessao, revoke de token ou logout.
- Reset de senha, edicao de perfil e exclusao de conta.
- Mudancas em `SessionDto`, `TokenDto` ou no formato de sucesso ja usado pelos providers atuais.
- Inclusao de campo `code` no payload de erro HTTP; o mobile vai diferenciar os casos por `status_code` + `message`.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /auth/sign-in` deve receber `email` e `password` no body JSON.
- O endpoint deve retornar `200` com `SessionDto`, contendo `access_token` e `refresh_token` com seus respectivos `expires_at`.
- Se o e-mail nao existir, a senha estiver incorreta ou a conta nao possuir `password_hash` persistido, o endpoint deve retornar `401` com mensagem generica de credenciais invalidas.
- Se a autenticacao por senha for valida e `account.is_verified == False`, o endpoint deve retornar `403` com mensagem especifica de e-mail nao confirmado.
- Se a autenticacao por senha for valida e `account.is_active == False`, o endpoint deve retornar `403` com mensagem especifica de conta desativada.
- O fluxo deve usar `HashProvider.verify()` para comparar a senha informada com o `password_hash` persistido e `JwtProvider.encode()` para emitir a sessao.

## 3.2 Nao funcionais

- **Seguranca:** o payload de erro para credenciais invalidas deve continuar generico (`401`) sem diferenciar e-mail inexistente, senha incorreta ou ausencia de `password_hash`.
- **Seguranca:** `password_hash` permanece restrito a `database`; ele nao deve entrar em `Account`, `AccountDto`, `SessionDto` ou resposta HTTP.
- **Seguranca:** a checagem de senha deve acontecer antes de `is_verified` e `is_active`, evitando revelar estado da conta quando a credencial estiver errada.
- **Compatibilidade retroativa:** o payload de erro deve permanecer no formato atual `{ "title": str, "message": str }`, sem novo campo `code`.
- **Compatibilidade retroativa:** o contrato de sucesso continua sendo `SessionDto`, reutilizando `TokenDto.expires_at` como `str` ISO-8601, conforme implementacao atual de `JoseJwtProvider`.

---

# 4. O que ja existe?

## Camada Core

- **`Account`** (`src/animus/core/auth/domain/entities/account.py`) — entidade de conta com `is_verified`, `is_active` e `password: Text | None`; nao carrega `password_hash`.
- **`AccountDto`** (`src/animus/core/auth/domain/entities/dtos/account_dto.py`) — DTO da conta usado entre camadas; mantem `password` opcional e nao representa hash persistido.
- **`Email`** (`src/animus/core/auth/domain/structures/email.py`) — `Structure` usada para normalizar e validar e-mail no dominio.
- **`Password`** (`src/animus/core/auth/domain/structures/password.py`) — `Structure` de senha forte usada no `sign-up`; serve de referencia para manter `sign-in` sem reintroduzir regra de cadastro no controller.
- **`Session` / `SessionDto` / `TokenDto`** (`src/animus/core/auth/domain/structures/session.py`, `src/animus/core/auth/domain/structures/dtos/session_dto.py`, `src/animus/core/auth/domain/structures/dtos/token_dto.py`) — contrato atual de sessao retornado pelos fluxos autenticados.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) — port de persistencia com `find_by_id()`, `find_by_email()` e `find_password_hash_by_email()`; expoe uma forma dedicada de recuperar `password_hash` sem acoplar hash na entidade de dominio.
- **`HashProvider`** (`src/animus/core/auth/interfaces/hash_provider.py`) — contrato para geracao e verificacao de hash; `verify(password: Text, hashed_password: Text) -> Logical` ja existe.
- **`JwtProvider`** (`src/animus/core/auth/interfaces/jwt_provider.py`) — contrato para emissao de `Session`; ja retorna o tipo de dominio necessario para o endpoint.
- **`SignUpUseCase`** (`src/animus/core/auth/use_cases/sign_up_use_case.py`) — referencia direta de orquestracao com portas injetadas e retorno de DTO.
- **`SignInWithGoogleUseCase`** (`src/animus/core/auth/use_cases/sign_in_with_google_use_case.py`) — referencia de fluxo autenticado que emite `SessionDto` usando `JwtProvider`.

## Camada Database

- **`AccountModel`** (`src/animus/database/sqlalchemy/models/auth/account_model.py`) — model ORM da tabela `accounts`; ja possui `password_hash` persistido e atualmente nullable para suportar contas do Google.
- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) — implementacao concreta do port de contas; ja consulta por e-mail e persiste contas manuais e sociais.
- **`AccountMapper`** (`src/animus/database/sqlalchemy/mappers/auth/account_mapper.py`) — reconstrui `Account` sem `password_hash`, reforcando que o hash nao pertence ao dominio.

## Camada REST

- **`SignUpController`** (`src/animus/rest/controllers/auth/sign_up_controller.py`) — referencia de controller fino com `_Body`, `Depends(...)` e repasse por **named parameters**.
- **`VerifyEmailController`** (`src/animus/rest/controllers/auth/verify_email_controller.py`) — referencia do padrao de composicao de dependencias no contexto `auth`.
- **`ResendVerificationEmailController`** (`src/animus/rest/controllers/auth/resend_verification_email_controller.py`) — referencia adicional de controller sem regra de negocio.
- **`SignInWithGoogleController`** (`src/animus/rest/controllers/auth/sign_in_with_google_controller.py`) — referencia de endpoint autenticado que retorna `SessionDto` sem camada `validation` dedicada.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — traduz hoje `400`, `401`, `404` e `409` para payload `{title, message}`; ainda nao cobre `ForbiddenError` com `403`.

## Camada Routers

- **`AuthRouter`** (`src/animus/routers/auth/auth_router.py`) — router agregador de `auth`; ja registra `sign-up`, verificacao de e-mail, reenvio e Google.

## Camada Providers

- **`Argon2idHashProvider`** (`src/animus/providers/auth/hash/argon2id_hash_provider.py`) — adapter concreto de `HashProvider`; sera reutilizado sem alteracao de contrato.
- **`JoseJwtProvider`** (`src/animus/providers/auth/jwt/jose/jose_jwt_provider.py`) — adapter concreto de `JwtProvider`; ja gera `Session` com `TokenDto` usando expiracao em formato ISO-8601.

## Lacunas identificadas na codebase

- Nao existe `SignInUseCase` para autenticacao por e-mail e senha.
- Nao existe `SignInController` para `POST /auth/sign-in`.
- Nao existem erros de dominio especificos para credenciais invalidas, conta nao verificada e conta inativa.
- O port `AccountsRepository` nao expoe hoje o `password_hash` persistido necessario para `HashProvider.verify()`.
- O `AppErrorHandler` ainda nao traduz `ForbiddenError` para `403`.

---

# 5. O que deve ser criado?

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/auth/domain/errors/invalid_credentials_error.py` (**novo arquivo**)
- **Classe base:** `AuthError`
- **Motivo:** usado quando o e-mail nao existe, a senha nao confere ou a conta nao possui `password_hash`; a mensagem deve ser `E-mail ou senha incorretos`.

- **Localizacao:** `src/animus/core/auth/domain/errors/account_not_verified_error.py` (**novo arquivo**)
- **Classe base:** `ForbiddenError`
- **Motivo:** usado quando a senha esta correta, mas `account.is_verified == False`; a mensagem deve ser `E-mail nao confirmado`.

- **Localizacao:** `src/animus/core/auth/domain/errors/account_inactive_error.py` (**novo arquivo**)
- **Classe base:** `ForbiddenError`
- **Motivo:** usado quando a senha esta correta, mas `account.is_active == False`; a mensagem deve ser `Conta desativada`.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/auth/use_cases/sign_in_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`, `HashProvider`, `JwtProvider`
- **Metodo principal:** `execute(email: str, password: str) -> SessionDto` — autentica uma conta manual por e-mail e senha e retorna a sessao emitida.
- **Fluxo resumido:** `Email.create(email)` -> `Text.create(password)` -> `AccountsRepository.find_by_email()` -> `AccountsRepository.find_password_hash_by_email()` -> `HashProvider.verify()` -> validar `is_verified` -> validar `is_active` -> `JwtProvider.encode(Text.create(account.id.value))` -> `SessionDto`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/auth/sign_in_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body` com `email: str` e `password: str` definidos no mesmo arquivo do controller.
- **Metodo HTTP e path:** `POST /auth/sign-in`
- **`status_code`:** `200`
- **`response_model`:** `SessionDto`
- **Dependencias injetadas via `Depends`:** `AccountsRepository` via `DatabasePipe`, `HashProvider` e `JwtProvider` via `ProvidersPipe`
- **Fluxo:** `_Body` -> controller instancia `SignInUseCase(...)` -> `use_case.execute(email=body.email, password=body.password)` -> `SessionDto`

---

# 6. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/auth/interfaces/accounts_repository.py`
- **Mudanca:** adicionar `find_password_hash_by_email(email: Email) -> Text | None` ao port.
- **Justificativa:** o `SignInUseCase` precisa acessar o hash persistido sem mover `password_hash` para `Account` nem quebrar a separacao entre dominio e persistencia.

- **Arquivo:** `src/animus/core/auth/domain/errors/__init__.py`
- **Mudanca:** exportar `InvalidCredentialsError`, `AccountNotVerifiedError` e `AccountInactiveError`.
- **Justificativa:** manter o contexto `auth` com imports publicos estaveis para os novos erros.

- **Arquivo:** `src/animus/core/auth/use_cases/__init__.py`
- **Mudanca:** exportar `SignInUseCase`.
- **Justificativa:** alinhar o pacote de `use_cases` ao padrao de exports publicos ja adotado.

## Camada Database (Repositorios)

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`
- **Mudanca:** implementar `find_password_hash_by_email(email: Email) -> Text | None`, lendo `AccountModel.password_hash` e retornando `None` quando a conta nao existir ou quando o hash estiver ausente.
- **Justificativa:** a camada `database` e o unico lugar autorizado a conhecer `password_hash`; retornar `None` permite ao `UseCase` colapsar tudo em `401` generico.

## Camada REST

- **Arquivo:** `src/animus/rest/handlers/app_error_handler.py`
- **Mudanca:** registrar `ForbiddenError` com `status_code=403`, preservando o payload atual `{title, message}`.
- **Justificativa:** o fluxo de `sign-in` precisa distinguir bloqueios por conta nao verificada ou inativa sem alterar o envelope de erro ja existente.

- **Arquivo:** `src/animus/rest/controllers/auth/__init__.py`
- **Mudanca:** exportar `SignInController`.
- **Justificativa:** manter a API publica do pacote `auth` consistente com os demais controllers.

## Camada Routers

- **Arquivo:** `src/animus/routers/auth/auth_router.py`
- **Mudanca:** registrar `SignInController` no router de `auth` com o mesmo padrao de composicao ja usado pelos endpoints existentes.
- **Justificativa:** expor o novo endpoint dentro da superficie HTTP ja consolidada do contexto `auth`.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** o `SignInUseCase` recebe **named parameters** (`email`, `password`) em vez de criar `SignInDto`.
  - **Alternativas consideradas:** criar um `DTO` de entrada no `core` apenas para `sign-in`.
  - **Motivo da escolha:** segue o padrao atual de `auth`, em que controllers simples repassam campos primitivos diretamente ao `UseCase`, como ja acontece em `SignUpController`.
  - **Impactos / trade-offs:** reduz um arquivo e uma conversao de borda, mas deixa a assinatura do `UseCase` mais acoplada ao par de campos especifico do endpoint.

- **Decisao:** manter `password_hash` fora de `Account` e de `AccountDto`, adicionando ao repositorio apenas o metodo `find_password_hash_by_email(...)`.
  - **Alternativas consideradas:** incluir hash em `Account`; criar uma entidade/DTO nova para credenciais; criar um metodo unico retornando `tuple[Account, Text | None]`.
  - **Motivo da escolha:** preserva a pureza do dominio atual e faz a menor mudanca necessaria no contrato de persistencia para autenticar por senha.
  - **Impactos / trade-offs:** o fluxo pode realizar duas leituras por e-mail no mesmo request (`find_by_email` + `find_password_hash_by_email`), em troca de um contrato mais simples e sem hash no dominio.

- **Decisao:** verificar a senha antes de checar `is_verified` e `is_active`.
  - **Alternativas consideradas:** validar status da conta logo apos localizar o e-mail.
  - **Motivo da escolha:** evita vazar estado da conta quando a credencial esta errada, mantendo o requisito de erro generico para falhas de autenticacao.
  - **Impactos / trade-offs:** um usuario com conta nao verificada ou inativa so recebe `403` depois de informar a senha correta.

- **Decisao:** manter o payload de erro somente com `title` e `message`, sem novo campo `code`.
  - **Alternativas consideradas:** evoluir `AppError` e `AppErrorHandler` para incluir `code` especifico por erro.
  - **Motivo da escolha:** decisao explicita desta spec para manter compatibilidade com o contrato HTTP atual e evitar uma mudanca transversal em todos os erros da aplicacao.
  - **Impactos / trade-offs:** o mobile passa a depender de `status_code` + `message` estavel para distinguir `401`, `403 e-mail nao confirmado` e `403 conta desativada`.

- **Decisao:** reutilizar `SessionDto` como `response_model` diretamente no controller.
  - **Alternativas consideradas:** criar schemas dedicados em `validation/` para `SessionResponse` e `TokenResponse`.
  - **Motivo da escolha:** o contexto `auth` ja retorna `SessionDto` em `SignInWithGoogleController`, e o documento de regras orienta usar `validation/` apenas para schemas compartilhados ou reutilizaveis entre multiplos controllers.
  - **Impactos / trade-offs:** o contrato HTTP fica fortemente alinhado ao DTO do `core`, mas preserva consistencia com a codebase atual e evita duplicacao de tipos.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /auth/sign-in
  -> FastAPIApp.register()
  -> AuthRouter
  -> SignInController
  -> DatabasePipe / ProvidersPipe
  -> SignInUseCase
       -> AccountsRepository.find_by_email()
       -> AccountsRepository.find_password_hash_by_email()
       -> HashProvider.verify()
       -> validar is_verified
       -> validar is_active
       -> JwtProvider.encode()
  -> 200 SessionDto
```

- **Fluxo assincrono:** **Nao aplicavel**.

- **Referencias:**
  - `src/animus/rest/controllers/auth/sign_up_controller.py`
  - `src/animus/core/auth/use_cases/sign_up_use_case.py`
  - `src/animus/rest/controllers/auth/sign_in_with_google_controller.py`
  - `src/animus/core/auth/use_cases/sign_in_with_google_use_case.py`
  - `src/animus/core/auth/interfaces/accounts_repository.py`
  - `src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`
  - `src/animus/providers/auth/hash/argon2id_hash_provider.py`
  - `src/animus/providers/auth/jwt/jose/jose_jwt_provider.py`
  - `src/animus/rest/handlers/app_error_handler.py`

---

# 10. Pendencias / Duvidas

**Sem pendencias**.

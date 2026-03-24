---
title: Endpoints de sign-up, verificacao e reenvio de e-mail
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AwACAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-35
status: closed
last_updated_at: 2026-03-19
---

# 1. Objetivo

Entregar o primeiro fluxo HTTP completo de `auth` no `animus-server`, cobrindo `POST /auth/sign-up`, `GET /auth/verify-email` e `POST /auth/resend-verification-email`, com persistencia SQLAlchemy de contas, hash de senha antes da escrita, emissao assicrona de `EmailVerificationRequestedEvent` via `Broker`, job Inngest para envio do e-mail de verificacao e composicao minima de `router`, `pipes`, `middleware`, `providers` e `app` para tornar o fluxo executavel ponta a ponta.

---

# 2. Escopo

## 2.1 In-scope

- Criar os tres endpoints HTTP do fluxo de cadastro e verificacao de conta.
- Criar os `use_cases`, erros de dominio e evento de dominio necessarios para o fluxo.
- Manter `password` em `Account` e `AccountDto` como campo opcional, usando `None` nos fluxos em que a senha nao deve ser exposta ou nao estiver carregada.
- Implementar persistencia de contas manuais em PostgreSQL com `accounts` table e `password_hash`.
- Criar o job Inngest que consome `EmailVerificationRequestedEvent` e delega o envio do e-mail.
- Criar o wiring minimo de `router`, `pipes`, `middleware`, `providers`, `app` e configuracao para o fluxo funcionar.
- Registrar o primeiro conjunto de handlers HTTP para `AppError` e subclasses usadas por `auth`.

## 2.2 Out-of-scope

- Login com e-mail/senha.
- Login com Google e persistencia de `social_accounts`.
- Reset de senha e edicao de perfil.
- Templates finais de e-mail e copy de UX.
- Qualquer fluxo de refresh de sessao alem do contrato atual de `SessionDto`.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /auth/sign-up` deve receber `name`, `email` e `password`.
- `POST /auth/sign-up` deve garantir e-mail unico, persistir a conta e publicar `EmailVerificationRequestedEvent`.
- `POST /auth/sign-up` deve gerar o token de verificacao de e-mail no proprio `UseCase` antes da publicacao do evento.
- `POST /auth/sign-up` deve retornar `201` com `AccountDto` e `password=None`.
- `GET /auth/verify-email` deve receber `token` via `Query`, validar autenticidade/expiracao, marcar a conta como verificada, invalidar o token com sucesso e retornar `200` com HTML de sucesso.
- `POST /auth/resend-verification-email` deve receber `email`, exigir conta existente e nao verificada, republicar `EmailVerificationRequestedEvent` e retornar `204` sem body.
- O envio do e-mail deve acontecer fora do request HTTP, via `Broker` + Inngest.
- `sign-up` e `resend-verification-email` devem publicar o mesmo `EmailVerificationRequestedEvent`, sempre com token ja gerado no fluxo sincrono.

## 3.2 Nao funcionais

- **Seguranca:** senha bruta nunca pode ser persistida nem exposta; apenas `password_hash` vai para a camada `database`.
- **Seguranca:** token de verificacao deve expirar em `1 hora`, conforme PRD.
- **Seguranca:** a sessao emitida em `verify-email` deve respeitar a janela funcional de `1 hora` descrita no PRD.
- **Idempotencia:** retries do job Inngest devem ser seguros via `step.run(...)`; reenvios explicitamente solicitados pelo endpoint devem gerar novo envio.
- **Compatibilidade retroativa:** a mudanca em `Account.password` / `AccountDto.password` para campo opcional e no port `AccountsRepository` deve ser aplicada de forma consistente em todos os imports/exportacoes publicas impactados.
- **Observabilidade:** o job deve usar o logger ja acoplado ao runtime do `uvicorn` pelo `InngestPubSub` para falhas do fluxo assicrono.

---

# 4. Regras de Negocio

- Nao e permitido cadastrar duas contas com o mesmo e-mail.
- Conta criada via `sign-up` nasce com `is_verified = False` e `is_active = True`.
- Nao aplicável.
- A senha deve ter pelo menos `8` caracteres, `1` letra maiuscula e `1` numero.
- O hash da senha e um detalhe de infraestrutura e nao faz parte de `Account` nem de `AccountDto`; o campo `password` do dominio representa apenas senha bruta em memoria, podendo ser `None` fora do fluxo de captura/autenticacao.
- Apenas token valido e nao expirado pode verificar a conta.
- Token de verificacao usado com sucesso em `verify-email` deve ser invalidado para impedir reuso.
- `resend-verification-email` nao pode reenviar e-mail para conta ja verificada.
- O efeito de envio de e-mail sempre acontece por evento de dominio; nenhum controller ou use case envia e-mail diretamente.
- O token de verificacao deve ser gerado tanto no `SignUpUseCase` quanto no `ResendVerificationEmailUseCase`; o job assincrono apenas entrega o e-mail com o token recebido no evento.
- O fluxo manual desta task nao persiste `social_accounts`; contas manuais devem ser reconstruidas com lista vazia.

---

# 5. O que ja existe?

## Camada Core

- **`Account`** (`src/animus/core/auth/domain/entities/account.py`) - entidade principal de conta; ja possui `verify()` e mantera `password` como atributo opcional.
- **`AccountDto`** (`src/animus/core/auth/domain/entities/dtos/account_dto.py`) - DTO atual da conta; sera ajustado para `password: str | None`.
- **`Email`** (`src/animus/core/auth/domain/structures/email.py`) - `Structure` usada para validacao de e-mail e conversoes no dominio.
- **`Session` / `SessionDto` / `TokenDto`** (`src/animus/core/auth/domain/structures/session.py`, `src/animus/core/auth/domain/structures/dtos/session_dto.py`, `src/animus/core/auth/domain/structures/dtos/token_dto.py`) - contrato de sessao no `verify-email`, com `SessionDto` composto por `TokenDto` em `access_token` e `refresh_token`.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) - port de persistencia da conta; sera estendido para receber o hash separadamente nas operacoes de escrita.
- **`HashProvider`**, **`EmailVerificationProvider`** e **`JwtProvider`** (`src/animus/core/auth/interfaces/hash_provider.py`, `src/animus/core/auth/interfaces/email_verification_provider.py`, `src/animus/core/auth/interfaces/jwt_provider.py`) - contratos centrais para hash, geracao/validacao/invalidacao de token de verificacao e emissao de sessao; o provider concreto de JWT desta feature deve ser implementado com `python-jose`.

## Camada Shared

- **`Broker`** (`src/animus/core/shared/interfaces/broker.py`) - port ja definido para publicacao de eventos.
- **`Event`** (`src/animus/core/shared/domain/abstracts/event.py`) - abstracao base de evento com serializacao por `payload_data`.
- **`AppError` e subclasses base** (`src/animus/core/shared/domain/errors/*.py`) - base para erros HTTP do fluxo (`ConflictError`, `NotFoundError`, `AuthError`, `ValidationError`).

## Camada App / PubSub

- **`FastAPIApp`** (`src/animus/app.py`) - composition root atual; hoje apenas instancia o `FastAPI` e ainda nao registra `router`, `middleware`, `handlers` nem `pubsub`.
- **`InngestBroker`** (`src/animus/pubsub/inngest/inngest_broker.py`) - adaptador ja adicionado localmente para publicar `Event` no Inngest via `send_sync`.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) - ponto de registro do Inngest ja adicionado localmente; precisa trocar placeholders e registrar jobs reais de `auth`.

## Camada Database

- **`model.py`** (`src/animus/database/sqlalchemy/models/model.py`) - arquivo base da camada SQLAlchemy existe, mas esta vazio.

## Camada REST / Routers / Pipes / Providers

- **Pacotes `auth` ja criados** (`src/animus/rest/controllers/auth/__init__.py`, `src/animus/routers/__init__.py`, `src/animus/pipes/__init__.py`, `src/animus/providers/__init__.py`) - o contexto agora usa subpastas de providers em `src/animus/providers/auth/` e `src/animus/providers/notification/`.

## Lacunas identificadas na codebase

- Nao foram encontrados `use_cases` de nenhum contexto em `src/animus/core/`.
- Nao foram encontrados controllers, routers, pipes ou middlewares analogos para copiar o wiring HTTP.
- Nao foram encontrados models, mappers ou repositories SQLAlchemy de `auth`; a camada `database/sqlalchemy/` ainda esta em estado inicial.
- O contrato `EmailSenderProvider` permanece no contexto `src/animus/core/notification/`, com implementacoes concretas organizadas em `src/animus/providers/notification/`.
- Nao foi encontrado scaffolding Alembic (`alembic.ini`, `migrations/env.py`, `migrations/versions/`).

---

# 6. O que deve ser criado?

## Camada Core (Entidades / Structures / DTOs)

- **Localizacao:** `src/animus/core/auth/domain/structures/password.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `value: str`
- **Metodos / factory:** `create(value: str) -> Password` - valida regra de forca minima da senha e retorna a structure para validacao de dominio; nao persiste nem expoe hash.

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/auth/domain/errors/account_already_exists_error.py` (**novo arquivo**)
- **Classe base:** `ConflictError`
- **Motivo:** quando `find_by_email()` encontra uma conta ja existente durante `sign-up`.

- **Localizacao:** `src/animus/core/auth/domain/errors/account_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** quando `AccountsRepository.find_by_id()` ou `find_by_email()` nao encontra a conta esperada.

- **Localizacao:** `src/animus/core/auth/domain/errors/account_already_verified_error.py` (**novo arquivo**)
- **Classe base:** `ConflictError`
- **Motivo:** quando `resend-verification-email` e solicitado para uma conta ja verificada.

- **Localizacao:** `src/animus/core/auth/domain/errors/invalid_email_verification_token_error.py` (**novo arquivo**)
- **Classe base:** `AuthError`
- **Motivo:** quando o token de verificacao for invalido, adulterado ou expirado.

- **Localizacao:** `src/animus/core/auth/domain/errors/__init__.py` (**novo arquivo**)
- **Classe base:** nao aplicavel
- **Motivo:** exportar publicamente os erros do contexto `auth`.

## Camada Core (Interfaces / Ports)

- **Localizacao:** `src/animus/core/notification/interfaces/email_sender_provider.py` (**novo arquivo**)
- **Metodos:** `send_account_verification_email(account_email: Email, verification_token: Text) -> None` - envia o e-mail de verificacao para a conta informada.

- **Localizacao:** `src/animus/core/notification/interfaces/__init__.py` (**novo arquivo**)
- **Metodos:** nao aplicavel - estabiliza os exports publicos do contexto `notification`.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/auth/use_cases/sign_up_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`, `HashProvider`, `EmailVerificationProvider`, `Broker`
- **Metodo principal:** `execute(name: str, email: str, password: str) -> AccountDto` - valida os dados de dominio, garante unicidade, persiste a conta com hash de senha, gera o token inicial de verificacao e publica o evento de envio de verificacao.
- **Fluxo resumido:** `Email.create` / `Name.create` / `Password.create` -> `AccountsRepository.find_by_email()` para detectar duplicidade -> `HashProvider.generate()` -> `AccountsRepository.add(account, password_hash)` -> `EmailVerificationProvider.generate_verification_token()` -> `Broker.publish(EmailVerificationRequestedEvent)` -> retornar `AccountDto` com `password=None`.

- **Localizacao:** `src/animus/core/auth/use_cases/verify_email_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`, `EmailVerificationProvider`, `JwtProvider`
- **Metodo principal:** `execute(token: str) -> SessionDto` - valida o token, marca a conta como verificada quando necessario, invalida o token usado e retorna a sessao autenticada.
- **Fluxo resumido:** `Text.create(token)` -> `EmailVerificationProvider.verify_verification_token()` -> `EmailVerificationProvider.decode_email_from_token()` -> `AccountsRepository.find_by_email()` -> `account.verify()` quando `is_verified` for `False` -> `AccountsRepository.replace()` -> `EmailVerificationProvider.invalidate_verification_token()` -> `JwtProvider.encode()` -> `Session.dto`.

- **Localizacao:** `src/animus/core/auth/use_cases/resend_verification_email_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`, `EmailVerificationProvider`, `Broker`
- **Metodo principal:** `execute(email: str) -> None` - gera um novo token de verificacao e publica o mesmo evento de envio usado no `sign-up`, apenas para contas existentes e ainda nao verificadas.
- **Fluxo resumido:** `Email.create(email)` -> `AccountsRepository.find_by_email()` -> validar `is_verified` -> `EmailVerificationProvider.generate_verification_token()` -> `Broker.publish(EmailVerificationRequestedEvent)`.

- **Localizacao:** `src/animus/core/auth/use_cases/__init__.py` (**novo arquivo**)
- **Dependencias (ports injetados):** nao aplicavel
- **Metodo principal:** nao aplicavel - exporta os `use_cases` do contexto.

## Camada PubSub (Eventos de Dominio)

- **Localizacao:** `src/animus/core/auth/domain/events/email_verification_requested_event.py` (**novo arquivo**)
- **`NAME`:** `auth/email-verification.requested`
- **Payload:** `account_email: str`, `account_email_verification_token: str`
- **Convencao de payload:** o payload do evento deve usar uma classe nomeada apenas como `_Payload`, implementada com `dataclasses.dataclass`, mantendo o evento enxuto e serializavel.
- **Construcao:** seguir o padrao de evento com `__init__(account_email: str, account_email_verification_token: str) -> None` que monta `_Payload` internamente e chama `super().__init__(EmailVerificationRequestedEvent.name, payload)`.

- **Localizacao:** `src/animus/core/auth/domain/events/__init__.py` (**novo arquivo**)
- **`NAME`:** nao aplicavel
- **Payload:** nao aplicavel

## Camada Database (Models SQLAlchemy)

- **Localizacao:** `src/animus/database/sqlalchemy/models/auth/account_model.py` (**novo arquivo**)
- **Tabela:** `accounts`
- **Colunas:** `id` (`String(26)`, `primary_key=True`), `name` (`String`, `nullable=False`), `email` (`String`, `nullable=False`, `unique=True`, `index=True`), `password_hash` (`String`, `nullable=False`), `is_verified` (`Boolean`, `nullable=False`, `default=False`), `is_active` (`Boolean`, `nullable=False`, `default=True`)
- **Relacionamentos:** nao aplicavel nesta task; `social_accounts` fica fora do schema inicial.

- **Localizacao:** `src/animus/database/sqlalchemy/models/auth/__init__.py` (**novo arquivo**)
- **Tabela:** nao aplicavel
- **Colunas:** nao aplicavel
- **Relacionamentos:** nao aplicavel

## Camada Database (Mappers)

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/auth/account_mapper.py` (**novo arquivo**)
- **Metodos:**
  - `to_entity(model: AccountModel) -> Account` - reconstrui `Account` com `password=None` e `social_accounts=[]` para contas manuais.
  - `to_model(account: Account, password_hash: Text) -> AccountModel` - cria o model ORM para insercao usando o hash ja gerado fora do dominio.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/auth/__init__.py` (**novo arquivo**)
- **Metodos:** nao aplicavel

## Camada Database (Repositórios)

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py` (**novo arquivo**)
- **Interface implementada:** `AccountsRepository`
- **Dependencias:** `Session` SQLAlchemy, `AccountMapper`
- **Metodos:**
  - `find_by_id(account_id: Id) -> Account` - busca a conta por ID ou lanca `AccountNotFoundError`.
  - `find_by_email(email: Email) -> Account` - busca a conta por e-mail ou lanca `AccountNotFoundError`.
  - `find_password_hash_by_email(email: Email) -> Text | None` - busca o hash de senha de uma conta manual pelo e-mail ou retorna `None` quando a conta nao possui hash.
  - `add(account: Account, password_hash: Text | None) -> None` - persiste uma nova conta com `password_hash` quando disponivel.
  - `add_many(accounts: list[tuple[Account, Text | None]]) -> None` - persiste varias contas com seus hashes quando disponiveis, mantendo o port coerente com a separacao entre entidade e hash.
  - `replace(account: Account) -> None` - atualiza `name`, `is_verified` e `is_active` sem alterar `password_hash`.

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/auth/__init__.py` (**novo arquivo**)
- **Interface implementada:** nao aplicavel
- **Dependencias:** nao aplicavel
- **Metodos:** nao aplicavel

## Camada REST (Handlers)

- **Localizacao:** `src/animus/rest/handlers/app_error_handler.py` (**novo arquivo**)
- **Tipo:** registrador de handlers FastAPI
- **Metodos:** `register(app: FastAPI) -> None` - traduz `ConflictError` para `409`, `NotFoundError` para `404`, `ValidationError` para `400` e `AuthError` para `401` com payload padrao baseado em `title` e `message`.

- **Localizacao:** `src/animus/rest/handlers/__init__.py` (**novo arquivo**)
- **Tipo:** nao aplicavel
- **Metodos:** nao aplicavel

## Camada REST (Middlewares)

- **Localizacao:** `src/animus/rest/middlewares/handle_sqlalchemy_session_middleware.py`
- **Tipo:** registrador de middleware FastAPI por request
- **Metodos:** `handle(app: FastAPI) -> None` - registra middleware HTTP que abre `Session`, anexa em `request.state.sqlalchemy_session`, faz `commit` em sucesso, `rollback` em excecao e fecha a sessao no `finally`.

- **Localizacao:** `src/animus/rest/middlewares/handle_inngest_client_middleware.py`
- **Tipo:** registrador de middleware FastAPI por request
- **Metodos:** `handle(app: FastAPI, inngest: Inngest) -> None` - registra middleware HTTP que anexa o client Inngest em `request.state.inngest_client` para uso dos pipes/controllers.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/auth/sign_up_controller.py` (**novo arquivo**)
- **`Body`:** `_Body` com `name: str`, `email: str`, `password: str`.
- **Metodo HTTP e path:** `POST /auth/sign-up`
- **`status_code`:** `201`
- **`response_model`:** `AccountDto`
- **Dependencias injetadas via `Depends`:** `AccountsRepository` via `DatabasePipe`, `HashProvider`, `EmailVerificationProvider` e `Broker` via pipes dedicados
- **Fluxo:** `_Body` -> controller instancia `SignUpUseCase(...)` com as dependencias resolvidas por `Depends` -> `use_case.execute(name=..., email=..., password=...)` -> `AccountDto`

- **Localizacao:** `src/animus/rest/controllers/auth/verify_email_controller.py` (**novo arquivo**)
- **`Body`:** nao aplicavel; `token` recebido via `Query`.
- **Metodo HTTP e path:** `GET /auth/verify-email`
- **`status_code`:** `200`
- **`response_model`:** nao aplicavel; retorno HTML via `HTMLResponse`.
- **Constante de resposta:** `src/animus/rest/controllers/auth/constants/verify_email_success_html.py` com template HTML de sucesso.
- **Dependencias injetadas via `Depends`:** `AccountsRepository` via `DatabasePipe`, `EmailVerificationProvider` e `JwtProvider` via pipes dedicados
- **Fluxo:** `token` (`Query`) -> controller instancia `VerifyEmailUseCase(...)` com as dependencias resolvidas por `Depends` -> `use_case.execute(token=...)` -> retorna `HTMLResponse` com conteúdo definido em constante.

- **Localizacao:** `src/animus/rest/controllers/auth/resend_verification_email_controller.py` (**novo arquivo**)
- **`Body`:** `ResendVerificationEmailBody` com `email: str`
- **Metodo HTTP e path:** `POST /auth/resend-verification-email`
- **`status_code`:** `204`
- **`response_model`:** nao aplicavel
- **Dependencias injetadas via `Depends`:** `AccountsRepository` via `DatabasePipe`, `EmailVerificationProvider` e `Broker` via pipes dedicados
- **Fluxo:** `ResendVerificationEmailBody` -> controller instancia `ResendVerificationEmailUseCase(...)` com as dependencias resolvidas por `Depends` -> `use_case.execute(email=...)` -> resposta vazia

## Camada Routers

- **Localizacao:** `src/animus/routers/auth/auth_router.py` (**novo arquivo**)
- **Prefixo da rota:** `/auth`
- **Controllers registrados:** `SignUpController`, `VerifyEmailController`, `ResendVerificationEmailController`
- **Metodo principal:** `register() -> APIRouter` - compoe o router do contexto `auth` e registra os controllers do modulo.

- **Localizacao:** `src/animus/routers/auth/__init__.py` (**novo arquivo**)
- **Prefixo da rota:** nao aplicavel
- **Controllers registrados:** nao aplicavel

## Camada Pipes

- **Localizacao:** `src/animus/pipes/database_pipe.py`
- **Metodo `Depends`:**
  - `get_sqlalchemy_session_from_request(request: Request) -> Session` - recupera a sessao aberta pelo middleware.
  - `get_accounts_repository_from_request(sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)]) -> AccountsRepository` - instancia `SqlalchemyAccountsRepository`.
- **Sessao SQLAlchemy:** obtida de `request.state.sqlalchemy_session`.

- **Localizacao:** `src/animus/pipes/providers_pipe.py` (**novo arquivo**)
- **Metodo `Depends`:**
  - `get_hash_provider() -> HashProvider` - provê `Argon2idHashProvider`.
  - `get_jwt_provider() -> JwtProvider` - provê `JoseJwtProvider`.
  - `get_email_verification_provider() -> EmailVerificationProvider` - provê `ItsdangerousEmailVerificationProvider`.
  - `get_email_sender_provider() -> EmailSenderProvider` - provê `ResendEmailSenderProvider`.
- **Sessao SQLAlchemy:** nao aplicavel.

- **Localizacao:** `src/animus/pipes/pubsub_pipe.py` (**novo arquivo**)
- **Metodo `Depends`:** `get_broker_from_request(request: Request) -> Broker` - monta `InngestBroker` a partir de `request.state.inngest_client`.
- **Sessao SQLAlchemy:** nao aplicavel.

## Camada Providers

- **Localizacao:** `src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `EmailSenderProvider`
- **Biblioteca/SDK utilizado:** `resend`
- **Metodos:**
  - `send_account_verification_email(account_email: Email, verification_token: Text) -> None` - envia e-mail transacional via `resend.Emails.send(...)`, usando template HTML em `src/animus/providers/notification/email_sender/constants/email_verification_html.py` para montar o corpo com `verification_url`.

- **Localizacao:** `src/animus/providers/notification/__init__.py` (**novo arquivo**)
- **Interface implementada (port):** nao aplicavel
- **Biblioteca/SDK utilizado:** nao aplicavel
- **Metodos:** nao aplicavel

- **Localizacao:** `src/animus/providers/auth/argon2id_hash_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `HashProvider`
- **Biblioteca/SDK utilizado:** `pwdlib[argon2]` com algoritmo `Argon2id`
- **Metodos:**
  - `generate(password: Text) -> Text` - gera o hash da senha para persistencia.
  - `verify(password: Text, hashed_password: Text) -> Logical` - compara senha bruta com hash persistido.

- **Localizacao:** `src/animus/providers/auth/jwt/jose/jose_jwt_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `JwtProvider`
- **Biblioteca/SDK utilizado:** `python-jose`
- **Metodos:**
  - `encode(subject: Text) -> Session` - gera os tokens da sessao usando o ID da conta como `subject` e retorna a estrutura de dominio.
  - `decode(token: Text) -> dict[str, str]` - decodifica um token emitido pelo provider.

- **Localizacao:** `src/animus/providers/auth/itsdangerous_email_verification_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `EmailVerificationProvider`
- **Biblioteca/SDK utilizado:** `itsdangerous`
- **Metodos:**
  - `generate_verification_token(account_email: Email) -> Text` - gera token assinado com expiração logica de `1 hora`.
  - `verify_verification_token(verification_token: Text) -> Logical` - valida assinatura e janela de expiração.
  - `decode_email_from_token(verification_token: Text) -> Email` - extrai o e-mail do payload assinado.
  - `invalidate_verification_token(verification_token: Text) -> None` - invalida token usado com sucesso no `verify-email` para evitar reuso.

- **Localizacao:** `src/animus/providers/auth/__init__.py` (**novo arquivo**)
- **Interface implementada (port):** nao aplicavel
- **Biblioteca/SDK utilizado:** nao aplicavel
- **Metodos:** nao aplicavel

## Camada PubSub (Jobs Inngest)

- **Localizacao:** `src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py` (**novo arquivo**)
- **Evento consumido:** `EmailVerificationRequestedEvent.name` com payload `account_email: str`, `account_email_verification_token: str`
- **Dependencias:** `EmailSenderProvider`
- **Metodo principal:** `handle(inngest: Inngest) -> Any` - registra a function do job no cliente Inngest e devolve o handler usado por `InngestPubSub`.
- **Normalizacao do payload:** o job deve reconstruir e normalizar o payload recebido para tipos de dominio usando uma classe `_Payload` antes de executar os passos do fluxo.
- **Passos (`step.run`):**
  - `normalize_payload` - converte o payload bruto recebido do Inngest em `_Payload` e reconstrui `Email` e `Text`.
  - `send_account_verification_email` - delega o envio ao provider de notificacao.
- **Idempotencia:** `step.run(...)` evita reexecucao duplicada do mesmo passo no mesmo job; eventos disparados por reenvio permanecem legitimos e devem gerar novo e-mail.

- **Localizacao:** `src/animus/pubsub/inngest/jobs/auth/__init__.py` (**novo arquivo**)
- **Evento consumido:** nao aplicavel
- **Dependencias:** nao aplicavel
- **Passos (`step.run`):** nao aplicavel
- **Idempotencia:** nao aplicavel

## Migracoes Alembic (se aplicavel)

- **Localizacao:** `alembic.ini` (**novo arquivo**), `migrations/env.py` (**novo arquivo**), `migrations/versions/<timestamp>_create_accounts_table.py` (**novo arquivo**)
- **Operacoes:** bootstrap minimo do Alembic e criacao da tabela `accounts` com `email` unico e `password_hash` obrigatorio.
- **Reversibilidade:** `downgrade` pode remover a tabela `accounts`; seguro apenas enquanto nao houver dependencia de dados em outros modulos.

---

# 7. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/auth/domain/entities/account.py`
- **Mudanca:** manter o atributo `password`, tornando-o opcional (`Text | None`), ajustar `create()` para aceitar DTO com `password` opcional e usar `None` em leituras de persistencia e respostas HTTP.
- **Justificativa:** o dominio continua podendo representar senha em memoria quando necessario, sem obrigar sua presenca em fluxos onde ela nao deve circular.

- **Arquivo:** `src/animus/core/auth/domain/entities/dtos/account_dto.py`
- **Mudanca:** tornar o campo `password` opcional (`str | None`) e retornar `None` nos fluxos HTTP desta feature.
- **Justificativa:** preserva compatibilidade estrutural do DTO sem expor senha ou hash na API.

- **Arquivo:** `src/animus/core/auth/interfaces/accounts_repository.py`
- **Mudanca:** alterar `add()` para `add(account: Account, password_hash: Text) -> None` e `add_many()` para `add_many(accounts: list[tuple[Account, Text]]) -> None`.
- **Justificativa:** o hash da senha deixa de fazer parte de `Account`, mas continua sendo necessario na persistencia.

- **Arquivo:** `src/animus/core/auth/interfaces/email_verification_provider.py`
- **Mudanca:** adicionar `invalidate_verification_token(verification_token: Text) -> None` ao contrato.
- **Justificativa:** permitir que o `VerifyEmailUseCase` invalide tokens usados com sucesso, evitando reuso.

- **Arquivo:** `src/animus/core/auth/domain/structures/__init__.py`
- **Mudanca:** exportar `Password`.
- **Justificativa:** estabilizar os imports publicos do contexto `auth`.

- **Arquivo:** `src/animus/core/auth/domain/structures/dtos/session_dto.py`
- **Mudanca:** trocar `access_token` e `refresh_token` de `str` para `TokenDto`.
- **Justificativa:** explicitar no contrato HTTP os metadados de expiracao de cada token da sessao.

- **Arquivo:** `src/animus/core/auth/domain/structures/session.py`
- **Mudanca:** ajustar `create(...)` para `create(dto: SessionDto) -> Session`, reconstruindo `Token` a partir de `TokenDto`.
- **Justificativa:** manter consistencia entre factory de dominio da sessao e o contrato DTO atualizado.

## Camada Database

- **Arquivo:** `src/animus/database/sqlalchemy/sqlalchemy.py`
- **Mudanca:** reutilizar `Sqlalchemy.get_session()` / `Sqlalchemy.session()` como bootstrap oficial de engine e sessao da aplicacao.
- **Justificativa:** o usuario ja adicionou o modulo base da infraestrutura SQLAlchemy, entao a implementacao deve se acoplar a ele em vez de criar outro bootstrap paralelo.

- **Arquivo:** `src/animus/database/sqlalchemy/models/model.py`
- **Mudanca:** definir a base declarativa (`DeclarativeBase`) compartilhada pela camada ORM.
- **Justificativa:** os novos models de `auth` precisam de uma base comum para metadata e migrations.

## Camada REST

- **Arquivo:** `src/animus/app.py`
- **Mudanca:** transformar `FastAPIApp.register()` no composition root real do servidor, registrando `AuthRouter`, `HandleSqlalchemySessionMiddleware.handle(app)`, handlers de erro, `InngestPubSub` e `HandleInngestClientMiddleware.handle(app, inngest)`.
- **Justificativa:** sem esse wiring os novos endpoints e jobs nao ficam expostos nem conseguem resolver dependencias.

- **Arquivo:** `src/animus/rest/controllers/auth/__init__.py`
- **Mudanca:** exportar os novos controllers de `auth`.
- **Justificativa:** estabilizar os imports publicos do pacote.

## Camada Routers

- **Arquivo:** `src/animus/routers/__init__.py`
- **Mudanca:** exportar `AuthRouter`.
- **Justificativa:** manter o pacote alinhado com a convencao de exports publicos.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudanca:** substituir o placeholder atual `get_horses_repository_from_request(...) -> HorsesRepository` por dependencias de `auth`, preservando `get_sqlalchemy_session_from_request(...)` e adicionando `get_accounts_repository_from_request(...) -> AccountsRepository`.
- **Justificativa:** o arquivo foi adicionado pelo usuario, mas ainda referencia um contexto alheio ao projeto atual e precisa ser alinhado com `auth`.

- **Arquivo:** `src/animus/pipes/__init__.py`
- **Mudanca:** exportar `DatabasePipe`, `ProvidersPipe` e `PubSubPipe`.
- **Justificativa:** reduzir imports acoplados a caminhos internos e seguir a regra de exports publicos.

## Camada Providers

- **Arquivo:** `src/animus/providers/__init__.py`
- **Mudanca:** exportar os providers concretos de `auth` e `notification`, incluindo `ResendEmailSenderProvider`, quando o pacote publico for consolidado.
- **Justificativa:** manter consistencia com a convencao do projeto.

- **Arquivo:** `src/animus/providers/auth/email_verification/itsdangerous_email_verification_provider.py`
- **Mudanca:** implementar `invalidate_verification_token(...)` e validar blacklist local ao verificar/decodificar token.
- **Justificativa:** alinhar o adapter concreto ao novo contrato de invalidacao do `EmailVerificationProvider`.

- **Arquivo:** `src/animus/constants/env.py`
- **Mudanca:** incluir os segredos/configuracoes necessarios para `JwtProvider`, `EmailVerificationProvider` e `ResendEmailSenderProvider`.
- **Justificativa:** os providers concretos de autenticacao precisam de configuracao centralizada e validada.

- **Arquivo:** `.env.example`
- **Mudanca:** documentar as novas variaveis de ambiente de autenticacao/verificacao e do `Resend`.
- **Justificativa:** manter o bootstrap local coerente com o novo wiring.

## Camada PubSub

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudanca:** remover placeholders herdados (`Equiny PubSub`), registrar o job de `auth` para `email-verification.requested`, parar de depender de `Env.INNGEST_SIGNING_KEY` inexistente e usar a configuracao padrao do SDK conforme ambiente.
- **Justificativa:** o arquivo local ja existe, mas ainda nao representa o contexto nem o bootstrap corretos do projeto.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/__init__.py`
- **Mudanca:** exportar o job de verificacao de conta.
- **Justificativa:** estabilizar imports do subpacote de jobs.

---

# 8. O que deve ser removido?

**Nao aplicavel**.

---

# 9. Decisoes Tecnicas e Trade-offs

- **Decisao:** manter `password` em `Account` e `AccountDto`, mas como campo opcional e com `None` nas respostas/leitura de persistencia.
  - **Alternativas consideradas:** remover completamente o campo do dominio; criar DTO HTTP separado sem tocar no dominio.
  - **Motivo da escolha:** preserva a forma atual da entidade/DTO com menor ruptura, mantendo seguranca ao nao expor senha ou hash no transporte HTTP.
  - **Impactos / trade-offs:** `AccountsRepository` continua recebendo o hash separadamente nas escritas, e implementacoes precisam garantir que leituras do banco sempre reconstruam `password=None`.

- **Decisao:** validar forca da senha em uma `Structure` nova (`Password`), mas continuar usando `Text` para o hash persistido.
  - **Alternativas consideradas:** regex direta no controller; regex direta no `UseCase`; introduzir `Password` tambem no port de hash.
  - **Motivo da escolha:** a regra de negocio da senha fica no `core`, mesmo com `Account.password` opcional, e o port de hash existente nao precisa ser quebrado.
  - **Impactos / trade-offs:** o `UseCase` faz uma pequena conversao adicional (`Password` -> `Text`) antes de chamar o provider.

- **Decisao:** reutilizar o mesmo evento para `sign-up` e `resend-verification-email`.
  - **Alternativas consideradas:** separar os eventos por fluxo; gerar token apenas no job consumidor.
  - **Motivo da escolha:** os dois fluxos podem publicar exatamente o mesmo contrato quando ambos geram o token no `UseCase`, reduzindo duplicacao de eventos e jobs.
  - **Impactos / trade-offs:** o `ResendVerificationEmailUseCase` ganha dependencia adicional de `EmailVerificationProvider`, mas o fluxo assincrono fica mais simples.

- **Decisao:** gerar o token inicial de verificacao no `SignUpUseCase`.
  - **Alternativas consideradas:** gerar token apenas no job assincrono; persistir token em banco antes da publicacao do evento.
  - **Motivo da escolha:** reduz ambiguidade no contrato do evento de conta criada e permite que o job apenas entregue o e-mail com o token ja decidido no fluxo de cadastro.
  - **Impactos / trade-offs:** `SignUpUseCase` e `ResendVerificationEmailUseCase` passam a depender de `EmailVerificationProvider`.

- **Decisao:** implementar `EmailSenderProvider` com `Resend`.
  - **Alternativas consideradas:** deixar o adapter indefinido na spec; usar SMTP direto; usar outro provedor transacional.
  - **Motivo da escolha:** a feature ja tem definicao explicita de provedor, e a SDK Python do `Resend` cobre o envio simples necessario para verificacao de conta.
  - **Impactos / trade-offs:** a implementacao passa a depender de configuracao adicional como `RESEND_API_KEY`, remetente padrao e possivel `ANIMUS_SERVER_URL` para compor o link de verificacao.

- **Decisao:** tratar `verify-email` como operacao idempotente quando a conta ja estiver verificada e o token ainda for valido.
  - **Alternativas consideradas:** lancar `AccountAlreadyVerifiedError` tambem no `verify-email`.
  - **Motivo da escolha:** o Jira nao exige erro para esse caso e o endpoint ja precisa devolver `SessionDto`; manter sucesso evita falha inutil em clique repetido no link.
  - **Impactos / trade-offs:** o mesmo token valido pode emitir nova sessao dentro da janela de expiracao; isso deve permanecer restrito a `1 hora`.

- **Decisao:** nao criar schema/persistencia de `social_accounts` nesta task.
  - **Alternativas consideradas:** abrir tabelas relacionais de contas sociais agora; adicionar coluna JSON apenas para antecipar o login Google.
  - **Motivo da escolha:** o escopo desta spec e exclusivamente o fluxo manual de cadastro/verificacao; antecipar Google aumentaria o tamanho da task sem evidencia funcional imediata.
  - **Impactos / trade-offs:** `SqlalchemyAccountsRepository` deve reconstruir contas manuais com `social_accounts=[]`, e a futura story de login Google precisara evoluir o schema.

- **Decisao:** registrar um handler global para `AppError` e subclasses junto com a feature.
  - **Alternativas consideradas:** deixar cada controller tratar excecoes manualmente; adiar o handler para uma task infra futura.
  - **Motivo da escolha:** o codigo atual nao possui traducao HTTP para erros de dominio, e os novos endpoints ja precisam de contratos de erro previsiveis.
  - **Impactos / trade-offs:** a PR desta feature passa a introduzir a infraestrutura minima de erro HTTP para futuras rotas.

---

# 10. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /auth/sign-up
  -> FastAPIApp.register()
  -> AuthRouter
  -> SignUpController
  -> DatabasePipe / ProvidersPipe / PubSubPipe
  -> SignUpUseCase (instanciado no controller)
       -> AccountsRepository.find_by_email()
       -> HashProvider.generate()
       -> AccountsRepository.add(account, password_hash)
       -> EmailVerificationProvider.generate_verification_token()
       -> Broker.publish(EmailVerificationRequestedEvent)
  -> 201 AccountDto

GET /auth/verify-email
  -> VerifyEmailController
  -> DatabasePipe / ProvidersPipe
  -> VerifyEmailUseCase (instanciado no controller)
       -> EmailVerificationProvider.verify_verification_token()
       -> EmailVerificationProvider.decode_email_from_token()
       -> AccountsRepository.find_by_email()
       -> account.verify() / AccountsRepository.replace()
       -> EmailVerificationProvider.invalidate_verification_token()
       -> JwtProvider.encode()
  -> 200 HTML (mensagem de sucesso)

POST /auth/resend-verification-email
  -> ResendVerificationEmailController
  -> DatabasePipe / ProvidersPipe / PubSubPipe
  -> ResendVerificationEmailUseCase (instanciado no controller)
       -> AccountsRepository.find_by_email()
       -> EmailVerificationProvider.generate_verification_token()
       -> Broker.publish(EmailVerificationRequestedEvent)
  -> 204 No Content
```

- **Fluxo assincrono:**

```text
SignUpUseCase / ResendVerificationEmailUseCase
  -> Broker.publish(EmailVerificationRequestedEvent)
  -> InngestBroker.send_sync(...)
  -> InngestPubSub (/api/inngest)
  -> SendAccountVerificationEmailJob
       -> step.run("normalize_payload")
       -> step.run("send_account_verification_email")
  -> EmailSenderProvider
  -> e-mail de verificacao entregue ao usuario
```

- **Referencias:**
  - `src/animus/core/auth/domain/entities/account.py`
  - `src/animus/core/auth/interfaces/accounts_repository.py`
  - `src/animus/core/auth/interfaces/email_verification_provider.py`
  - `src/animus/core/auth/interfaces/jwt_provider.py`
  - `src/animus/core/shared/domain/abstracts/event.py`
  - `src/animus/pubsub/inngest/inngest_broker.py`
  - `src/animus/pubsub/inngest/inngest_pubsub.py`
  - `src/animus/app.py`

---

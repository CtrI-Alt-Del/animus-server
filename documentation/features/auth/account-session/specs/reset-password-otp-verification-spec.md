---
title: Refatoracao do reset de senha para OTP com contexto temporario
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/anm/pages/16908291/PRD+RF+01+Gerenciamento+de+sess+o+do+usu+rio
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-70
status: open
last_updated_at: 2026-04-13
---

# 1. Objetivo

Migrar o fluxo de redefinicao de senha do `animus-server` do modelo legado por link/token para um fluxo por `OTP` numerico com cache temporario, sem enumeracao de e-mails e com contexto opaco de reset apos a verificacao bem-sucedida. Tecnicamente, a entrega substitui `GET /auth/password/verify-reset-token` por novos endpoints `POST` para reenvio e verificacao do `OTP`, evolui os `use_cases` e eventos de `auth` para gerar e validar o codigo no `core`, reaproveita `CacheProvider`, `OtpProvider`, `Broker` e o job Inngest existente para envio de e-mail, e altera o reset final para consumir um `reset_context` temporario em vez de `account_id` enviado pelo cliente.

---

# 2. Escopo

## 2.1 In-scope

- Evoluir `POST /auth/password/forgot` para gerar e persistir `OTP` de reset quando a conta existir, mantendo resposta silenciosa.
- Criar `POST /auth/password/resend-reset-otp` com validacao de cooldown e republicacao do envio sem enumeracao de conta.
- Criar `POST /auth/password/verify-reset-otp` com `email + otp`, validacao em cache, controle de tentativas e emissao de `ResetPasswordContextDto`.
- Alterar `POST /auth/password/reset` para receber `reset_context` opaco e resolver internamente a conta autorizada.
- Reaproveitar `PasswordResetRequestEvent` e `SendPasswordResetEmailJob`, mudando o payload para `OTP` em vez de token/link.
- Remover o endpoint legado `GET /auth/password/verify-reset-token`, o `VerifyResetTokenUseCase` e o acoplamento do reset com `EmailVerificationProvider`.
- Atualizar `CacheKeys`, configuracao de ambiente e template de e-mail para o novo fluxo.

## 2.2 Out-of-scope

- Alterar `POST /auth/sign-in`, `POST /auth/sign-up`, `POST /auth/verify-email` ou login com Google.
- Criar coluna, tabela ou migration Alembic para persistir `OTP` ou `reset_context` em PostgreSQL.
- Introduzir `validation` compartilhada para os novos endpoints; os `*Body` permanecem nos controllers, seguindo o padrao atual de `auth`.
- Refatorar o contrato geral de `AccountsRepository.replace(...)` alem do necessario para o reset final.
- Alterar UX mobile, countdown visual, navegacao de telas ou copy final do aplicativo alem do contrato HTTP necessario.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /auth/password/forgot` deve receber `email: str` e continuar retornando `204` sem revelar se a conta existe.
- Quando a conta existir em `POST /auth/password/forgot`, o backend deve gerar um `OTP` de 6 digitos, salvar o codigo no cache com TTL proprio do reset, reinicializar o contador de tentativas e publicar `PasswordResetRequestEvent` com `account_email` e `account_email_otp`.
- `POST /auth/password/resend-reset-otp` deve receber `email: str`, validar cooldown antes de emitir novo codigo e manter a mesma semantica silenciosa de `204` para conta existente ou inexistente.
- Quando o cooldown permitir e a conta existir, `POST /auth/password/resend-reset-otp` deve regerar o `OTP`, sobrescrever o codigo anterior, reinicializar tentativas, renovar o cooldown e republicar o evento de envio.
- `POST /auth/password/verify-reset-otp` deve receber body JSON com `email: str` e `otp: str`.
- `POST /auth/password/verify-reset-otp` deve validar formato do `OTP`, existencia do codigo no cache, expiracao implicita por TTL e tentativas restantes antes de liberar o reset.
- Em `OTP` divergente, o backend deve decrementar o contador de tentativas e responder com erro de dominio unico para codigo invalido ou expirado.
- Em `OTP` valido, o backend deve invalidar o `OTP`, invalidar o contador de tentativas, criar um `reset_context` opaco de uso unico, armazenar esse contexto em cache com TTL proprio e retornar `200` com `ResetPasswordContextDto`.
- `POST /auth/password/reset` deve receber `reset_context: str` e `new_password: str`.
- `POST /auth/password/reset` deve resolver a conta a partir do `reset_context` armazenado, validar a nova senha com as mesmas regras de `Password.create(...)`, aplicar `HashProvider.generate(...)`, persistir a nova senha e invalidar o `reset_context` apos sucesso.
- Nenhum endpoint do fluxo de reset deve expor `account_id` cru ao cliente.
- O envio de e-mail de reset deve continuar assincrono via `Broker` + Inngest.

## 3.2 Nao funcionais

- **Seguranca:** `OTP` deve ter exatamente `6` digitos numericos e ser gerado por `OtpProvider`, como ja ocorre no fluxo de verificacao de e-mail.
- **Seguranca:** `forgot` e `resend-reset-otp` devem preservar anti-enumeracao de e-mail, sempre respondendo `204` sem diferenciar conta inexistente, conta existente ou cooldown ativo.
- **Seguranca:** `OTP` e `reset_context` devem ser de uso unico; apos sucesso em `verify-reset-otp` e `reset`, as chaves temporarias associadas devem ser removidas.
- **Seguranca:** `reset_context` deve ser opaco para o cliente e nao pode carregar `account_id` em texto claro no payload HTTP de resposta alem do proprio contexto.
- **Resiliencia:** retries do `SendPasswordResetEmailJob` nao podem regerar `OTP` nem `reset_context`; o job apenas entrega o e-mail com o payload ja publicado.
- **Compatibilidade retroativa:** esta task quebra o contrato legado de `GET /auth/password/verify-reset-token?token=...` e tambem o body atual de `POST /auth/password/reset`, que hoje recebe `account_id`; clientes precisam migrar para `verify-reset-otp` + `reset_context`.
- **Compatibilidade retroativa:** o schema SQLAlchemy da tabela `accounts` permanece inalterado; toda informacao temporaria do reset fica em cache.
- **Observabilidade:** o fluxo assincrono continua centralizado no `InngestPubSub` atual, sem novo runtime de eventos.
- **Configuracao:** TTL do `OTP`, TTL do `reset_context` e cooldown de reenvio devem ser lidos de configuracao de ambiente dedicada, nao hardcoded no controller ou job.

---

# 4. Regras de Negocio e Invariantes

- Nao e permitido enumerar e-mails no fluxo de reset; `forgot` e `resend-reset-otp` continuam silenciosos para conta existente ou inexistente.
- O `OTP` de reset e sempre temporario e de uso unico.
- O `OTP` mais recente invalida o anterior para o mesmo e-mail.
- O contador de tentativas e associado ao e-mail do reset e deve ser reiniciado quando um novo `OTP` e emitido.
- Quando o numero de tentativas restantes atingir `0`, novas verificacoes com aquele `OTP` devem falhar ate que um novo codigo seja emitido.
- O cooldown de reenvio impede emissao de um novo `OTP` antes do intervalo definido pelo produto; durante esse periodo o endpoint continua silencioso.
- A verificacao bem-sucedida do `OTP` nao redefine a senha diretamente; ela apenas libera um `reset_context` temporario para a etapa final.
- O `reset_context` nao pode revelar `account_id` ao cliente e deve ser invalidado apos uso bem-sucedido.
- A nova senha deve obedecer as regras ja existentes de `Password.create(...)`.
- O envio de e-mail continua sendo side effect assincrono; nenhum controller ou `use_case` envia e-mail diretamente.

---

# 5. O que ja existe?

## Camada Core

- **`ForgotPasswordUseCase`** (`src/animus/core/auth/use_cases/forgot_password_use_case.py`) - hoje apenas valida `email`, busca a conta e publica `PasswordResetRequestEvent` sem cache nem `OTP`; sera o ponto principal de extensao do fluxo inicial.
- **`ResetPasswordUseCase`** (`src/animus/core/auth/use_cases/reset_password_use_case.py`) - hoje recebe `account_id` diretamente do cliente e aplica `HashProvider`; precisa trocar o contrato para `reset_context`.
- **`VerifyResetTokenUseCase`** (`src/animus/core/auth/use_cases/verify_reset_token_use_case.py`) - fluxo legado baseado em token assinado por `EmailVerificationProvider`; sera removido.
- **`VerifyEmailUseCase`** (`src/animus/core/auth/use_cases/verify_email_use_case.py`) - referencia direta para validacao de `OTP`, decremento de tentativas, limpeza de cache e erro unico em caso de codigo invalido/expirado.
- **`ResendVerificationEmailUseCase`** (`src/animus/core/auth/use_cases/resend_verification_email_use_case.py`) - referencia direta para regeracao de `OTP`, reset de tentativas e republicacao de evento.
- **`Otp`** (`src/animus/core/auth/domain/structures/otp.py`) - `Structure` pronta para validar `OTP` numerico de 6 digitos e expor `MAX_VERIFICATION_ATTEMPTS`.
- **`Password`** (`src/animus/core/auth/domain/structures/password.py`) - `Structure` existente para validar regra de forca da nova senha.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) - port atual com `find_by_id(...)`, `find_by_email(...)`, `find_password_hash_by_email(...)`, `add(...)`, `add_many(...)` e `replace(...)`; suficiente para o fluxo, sem exigir persistencia nova.
- **`PasswordResetRequestEvent`** (`src/animus/core/auth/domain/events/password_reset_request_event.py`) - evento ja existente para envio de reset; hoje carrega apenas `account_email`.

## Camada Core Shared

- **`CacheProvider`** (`src/animus/core/shared/interfaces/cache_provider.py`) - contrato ja consolidado com `get`, `set`, `set_with_ttl` e `delete`; e o adaptador correto para guardar `OTP`, tentativas, cooldown e `reset_context` sem acoplar o `core` ao Redis.
- **`Ttl`** (`src/animus/core/shared/domain/structures/ttl.py`) - `Structure` tipada para TTL ja usada no fluxo de verificacao de e-mail.
- **`Id`** (`src/animus/core/shared/domain/structures/id.py`) - gera `ULID` opaco quando chamado sem argumento; pode ser reaproveitado para produzir o valor do `reset_context` sem criar provider novo.
- **`Broker`** (`src/animus/core/shared/interfaces/broker.py`) - port existente para publicacao de eventos de dominio.

## Camada REST

- **`ForgotPasswordController`** (`src/animus/rest/controllers/auth/forgot_password_controller.py`) - endpoint atual `POST /auth/password/forgot` com `_Body(email: str)` e `204`; sera estendido para injetar `OtpProvider` e `CacheProvider`.
- **`ResetPasswordController`** (`src/animus/rest/controllers/auth/reset_password_controller.py`) - endpoint atual `POST /auth/password/reset` com `_Body(account_id: str, new_password: str)`; precisa trocar o body para `reset_context`.
- **`VerifyResetTokenController`** (`src/animus/rest/controllers/auth/verify_reset_token_controller.py`) - endpoint legado `GET /auth/password/verify-reset-token`; sera removido.
- **`VerifyEmailController`** (`src/animus/rest/controllers/auth/verify_email_controller.py`) - referencia direta de controller fino com `_Body(email, otp)` e `response_model=SessionDto`.

## Camada Routers

- **`AuthRouter`** (`src/animus/routers/auth/auth_router.py`) - composicao atual das rotas de `auth`; ainda registra `VerifyResetTokenController` e ainda nao registra endpoints especificos de `resend-reset-otp` e `verify-reset-otp`.

## Camada Pipes

- **`ProvidersPipe`** (`src/animus/pipes/providers_pipe.py`) - ja entrega `HashProvider`, `JwtProvider`, `CacheProvider`, `OtpProvider` e `EmailSenderProvider`; ainda expoe `get_email_verification_provider()` por causa do fluxo legado.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) - ja entrega `AccountsRepository` para os controllers de `auth`.
- **`PubSubPipe`** (`src/animus/pipes/pubsub_pipe.py`) - ja entrega `Broker` para publicacao do evento de reset.

## Camada Providers

- **`RedisCacheProvider`** (`src/animus/providers/shared/cache/redis/redis_cache_provider.py`) - implementacao concreta ja pronta para `get`, `set`, `set_with_ttl` e `delete` no Redis.
- **`ResendEmailSenderProvider`** (`src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py`) - hoje envia e-mail de reset montando link para `GET /auth/password/verify-reset-token?token=...`; precisa migrar para `OTP`.
- **`ItsdangerousEmailVerificationProvider`** (`src/animus/providers/auth/email_verification/itsdangerous_email_provider.py`) - provider legado de token assinado, hoje usado apenas pelo reset por link.

## Camada PubSub

- **`SendPasswordResetEmailJob`** (`src/animus/pubsub/inngest/jobs/auth/send_password_reset_email_job.py`) - job atual do reset, mas ainda gera token dentro do job via `EmailVerificationProvider`; precisa passar a apenas consumir `account_email` e `account_email_otp`.
- **`SendPasswordResetEmailUseCase`** (`src/animus/core/notification/use_cases/send_password_reset_email_use_case.py`) - hoje gera token assinado e repassa ao provider de e-mail; precisa receber `OTP` pronto.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) - wiring atual do job que deve ser mantido.

## Camada Database

- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) - repositorio concreto atual para leitura e escrita de conta; o reset final continua reaproveitando `find_by_id(...)` e `replace(...)`.
- **`AccountModel`** (`src/animus/database/sqlalchemy/models/auth/account_model.py`) - model atual da tabela `accounts` com `password_hash`; nao exige alteracao de schema.
- **`AccountMapper`** (`src/animus/database/sqlalchemy/mappers/auth/account_mapper.py`) - mapper atual de conta; nao precisa de extensao para esta task.

## Configuracao

- **`CacheKeys`** (`src/animus/constants/cache_keys.py`) - hoje centraliza apenas chaves de verificacao de e-mail; faltam chaves dedicadas ao reset de senha.
- **`Env`** (`src/animus/constants/env.py`) - hoje ainda mantem configuracoes do fluxo legado por token e nao tem configuracao dedicada para TTL/cooldown do reset por `OTP`.
- **`.env.example`** (`.env.example`) - ainda documenta variaveis do fluxo legado por token e nao documenta as novas variaveis dedicadas ao reset via `OTP`.

---

# 6. O que deve ser criado?

## Camada Core (DTOs)

- **Localizacao:** `src/animus/core/auth/domain/structures/dtos/reset_password_context_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `reset_context: str`
- **Metodos / factory:** nao aplicavel - DTO minimo para devolver o contexto temporario liberado apos a verificacao do `OTP`.

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/auth/domain/errors/invalid_reset_password_otp_error.py` (**novo arquivo**)
- **Classe base:** `AuthError`
- **Motivo:** quando o `OTP` informado para reset for invalido, expirado, corrompido ou quando as tentativas restantes tiverem sido esgotadas.

- **Localizacao:** `src/animus/core/auth/domain/errors/invalid_reset_password_context_error.py` (**novo arquivo**)
- **Classe base:** `AuthError`
- **Motivo:** quando o `reset_context` estiver ausente, expirado, corrompido ou ja tiver sido consumido.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/auth/use_cases/resend_reset_password_otp_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`, `OtpProvider`, `CacheProvider`, `Broker`, `Ttl` de cooldown e `Ttl` do `OTP`
- **Metodo principal:** `execute(email: str) -> None` - valida o e-mail, mantem semantica silenciosa, respeita cooldown e, quando aplicavel, regenera o `OTP`, renova o estado temporario e republica o evento.
- **Fluxo resumido:** `Email.create(...)` -> `AccountsRepository.find_by_email(...)` -> retorno silencioso se conta inexistente -> checar chave de cooldown -> retorno silencioso se cooldown ativo -> `OtpProvider.generate()` -> `CacheProvider.set_with_ttl(...)` para `OTP` -> `CacheProvider.set(...)` para tentativas -> `CacheProvider.set_with_ttl(...)` para cooldown -> `Broker.publish(PasswordResetRequestEvent(...))`.

- **Localizacao:** `src/animus/core/auth/use_cases/verify_reset_password_otp_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AccountsRepository`, `CacheProvider`, `Ttl` do `reset_context`
- **Metodo principal:** `execute(email: str, otp: str) -> ResetPasswordContextDto` - valida `OTP` de reset em cache, decrementa tentativas quando necessario e, em sucesso, cria o contexto temporario de reset de uso unico.
- **Fluxo resumido:** `Email.create(...)` / `Otp.create(...)` -> ler tentativas -> bloquear em `0` -> ler `OTP` armazenado -> decrementar tentativas em divergencia -> buscar conta por e-mail -> gerar `reset_context = Id.create().value` -> `CacheProvider.set_with_ttl(...)` mapeando contexto para `account_id` -> apagar chaves de `OTP`, tentativas e cooldown -> retornar `ResetPasswordContextDto`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/auth/resend_reset_password_otp_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body` com `email: str`
- **Metodo HTTP e path:** `POST /auth/password/resend-reset-otp`
- **`status_code`:** `204`
- **`response_model`:** nao aplicavel
- **Dependencias injetadas via `Depends`:** `AccountsRepository` via `DatabasePipe`, `OtpProvider` e `CacheProvider` via `ProvidersPipe`, `Broker` via `PubSubPipe`
- **Fluxo:** `_Body` -> `ResendResetPasswordOtpUseCase.execute(email=body.email)` -> sem body de resposta.

- **Localizacao:** `src/animus/rest/controllers/auth/verify_reset_password_otp_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body` com `email: str` e `otp: str`
- **Metodo HTTP e path:** `POST /auth/password/verify-reset-otp`
- **`status_code`:** `200`
- **`response_model`:** `ResetPasswordContextDto`
- **Dependencias injetadas via `Depends`:** `AccountsRepository` via `DatabasePipe`, `CacheProvider` via `ProvidersPipe`
- **Fluxo:** `_Body` -> `VerifyResetPasswordOtpUseCase.execute(email=body.email, otp=body.otp)` -> `ResetPasswordContextDto`.

---

# 7. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/auth/use_cases/forgot_password_use_case.py`
- **Mudanca:** adicionar dependencias de `OtpProvider`, `CacheProvider`, `Ttl` do `OTP` e `Ttl` do cooldown; gerar `OTP`, persistir `OTP`/tentativas/cooldown em cache e publicar `PasswordResetRequestEvent(account_email=..., account_email_otp=...)`; manter retorno silencioso quando a conta nao existir.
- **Justificativa:** o `OTP` deve nascer no fluxo sincrono do `core`, nao no job, e o endpoint nao pode enumerar e-mails.

- **Arquivo:** `src/animus/core/auth/use_cases/reset_password_use_case.py`
- **Mudanca:** trocar assinatura para `execute(reset_context: str, new_password: str) -> None`, remover dependencia de `account_id` vindo do cliente, adicionar `CacheProvider`, resolver `account_id` a partir do contexto salvo em cache, validar `Password.create(new_password)`, gerar hash com `HashProvider` e invalidar o `reset_context` apos sucesso.
- **Justificativa:** o reset final precisa depender de um contexto temporario emitido apos a verificacao do `OTP`, e nao de um identificador arbitrario informado pelo cliente.

- **Arquivo:** `src/animus/core/auth/domain/events/password_reset_request_event.py`
- **Mudanca:** alterar o payload para carregar `account_email: str` e `account_email_otp: str`, ajustando `__init__(account_email: str, account_email_otp: str) -> None`.
- **Justificativa:** o job de envio deve consumir o `OTP` pronto, sem gerar token proprio.

- **Arquivo:** `src/animus/core/auth/domain/errors/__init__.py`
- **Mudanca:** exportar `InvalidResetPasswordOtpError` e `InvalidResetPasswordContextError`.
- **Justificativa:** manter a API publica do contexto `auth` coerente com os novos erros de dominio.

- **Arquivo:** `src/animus/core/auth/domain/structures/dtos/__init__.py`
- **Mudanca:** exportar `ResetPasswordContextDto`.
- **Justificativa:** estabilizar o import do novo DTO de saida, seguindo o padrao ja usado por `SessionDto`.

- **Arquivo:** `src/animus/core/auth/use_cases/__init__.py`
- **Mudanca:** exportar `ResendResetPasswordOtpUseCase` e `VerifyResetPasswordOtpUseCase`, e remover `VerifyResetTokenUseCase` dos exports publicos.
- **Justificativa:** manter o pacote de `use_cases` alinhado ao fluxo suportado pela aplicacao.

## Camada Core Notification

- **Arquivo:** `src/animus/core/notification/interfaces/email_sender_provider.py`
- **Mudanca:** alterar o contrato para `send_password_reset_email(account_email: Email, otp: Otp) -> None`.
- **Justificativa:** o provider de e-mail deixa de enviar link/token e passa a enviar `OTP` textual.

- **Arquivo:** `src/animus/core/notification/use_cases/send_password_reset_email_use_case.py`
- **Mudanca:** remover a dependencia de `EmailVerificationProvider`, trocar a assinatura para `execute(account_email: str, otp: str) -> None` e converter ambos para `Email.create(...)` e `Otp.create(...)` antes de repassar ao provider.
- **Justificativa:** o `use_case` de notificacao passa a ser apenas um adaptador do payload para o provider de e-mail.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/auth/forgot_password_controller.py`
- **Mudanca:** adicionar injecoes de `OtpProvider` e `CacheProvider` e atualizar a instancia do `ForgotPasswordUseCase` com os TTLs dedicados ao reset.
- **Justificativa:** o controller continua fino, mas precisa montar o novo conjunto de dependencias do fluxo.

- **Arquivo:** `src/animus/rest/controllers/auth/reset_password_controller.py`
- **Mudanca:** substituir `_Body(account_id: str, new_password: str)` por `_Body(reset_context: str, new_password: str)`, injetar `CacheProvider` e chamar `ResetPasswordUseCase.execute(reset_context=..., new_password=...)`.
- **Justificativa:** o contrato HTTP final precisa refletir o contexto temporario emitido apos `verify-reset-otp`.

## Camada Routers

- **Arquivo:** `src/animus/routers/auth/auth_router.py`
- **Mudanca:** remover o registro de `VerifyResetTokenController`, registrar `ResendResetPasswordOtpController` e `VerifyResetPasswordOtpController`, preservando o prefixo `/auth`.
- **Justificativa:** a superficie HTTP suportada por `auth` muda do fluxo legado por token para o fluxo novo por `OTP`.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/providers_pipe.py`
- **Mudanca:** remover `get_email_verification_provider()` e manter `get_cache_provider()` / `get_otp_provider()` como fontes oficiais do fluxo de reset.
- **Justificativa:** o reset deixa de depender do provider legado de token assinado.

## Camada Providers

- **Arquivo:** `src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py`
- **Mudanca:** alterar `send_password_reset_email(...)` para receber `Otp`, remover a montagem de `reset_link` e preencher o template com `{{OTP_CODE}}`.
- **Justificativa:** o e-mail de reset passa a instruir o usuario a digitar o codigo no app, e nao clicar em link.

- **Arquivo:** `src/animus/providers/notification/email_sender/constants/reset_password_email_template.py`
- **Mudanca:** substituir o placeholder e a copy orientada a link por uma versao orientada a `OTP` numerico.
- **Justificativa:** alinhar o conteudo do e-mail ao novo fluxo do backend.

## Camada PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/auth/send_password_reset_email_job.py`
- **Mudanca:** ajustar o payload normalizado para `account_email` e `account_email_otp`, remover a dependencia de `ItsdangerousEmailVerificationProvider` e fazer o job apenas chamar `SendPasswordResetEmailUseCase.execute(account_email=..., otp=...)`.
- **Justificativa:** o job deve continuar idempotente e restrito a orquestrar envio, sem gerar `OTP` nem token.

## Configuracao

- **Arquivo:** `src/animus/constants/cache_keys.py`
- **Mudanca:** adicionar APIs explicitas para as chaves temporarias do reset, incluindo `OTP`, tentativas, cooldown e `reset_context`.
- **Justificativa:** evitar string literals duplicadas entre `use_cases` e manter consistencia com o padrao ja usado em verificacao de e-mail.

- **Arquivo:** `src/animus/constants/env.py`
- **Mudanca:** remover as configuracoes do fluxo legado por token (`EMAIL_VERIFICATION_SECRET_KEY`, `EMAIL_VERIFICATION_SALT`, `EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS`) e adicionar configuracoes dedicadas ao reset por `OTP`, como `RESET_PASSWORD_OTP_TTL_SECONDS`, `RESET_PASSWORD_OTP_RESEND_COOLDOWN_SECONDS` e `RESET_PASSWORD_CONTEXT_TTL_SECONDS`.
- **Justificativa:** o novo fluxo depende de cache temporario e nao mais de token assinado por link.

- **Arquivo:** `.env.example`
- **Mudanca:** documentar as novas variaveis de reset via `OTP` e remover as variaveis do fluxo legado por token que ficarem sem uso.
- **Justificativa:** manter o bootstrap local coerente com o comportamento suportado pela aplicacao.

---

# 8. O que deve ser removido?

## Camada Core

- **Arquivo:** `src/animus/core/auth/use_cases/verify_reset_token_use_case.py`
- **Motivo da remocao:** o fluxo legado de validacao por token assinado deixa de existir na aplicacao.
- **Impacto esperado:** atualizar imports e exports em `src/animus/core/auth/use_cases/__init__.py` e remover qualquer referencia restante ao fluxo legado.

- **Arquivo:** `src/animus/core/auth/interfaces/email_verification_provider.py`
- **Motivo da remocao:** apos a migracao completa do reset para `OTP`, nao resta uso real do contrato de token assinado na codebase atual.
- **Impacto esperado:** remover referencias em `ProvidersPipe`, job de reset, provider itsdangerous e qualquer import residual.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/auth/verify_reset_token_controller.py`
- **Motivo da remocao:** o endpoint `GET /auth/password/verify-reset-token` sai da superficie HTTP suportada.
- **Impacto esperado:** atualizar `AuthRouter` e remover consumidores do contrato legado.

## Camada Providers

- **Arquivo:** `src/animus/providers/auth/email_verification/itsdangerous_email_provider.py`
- **Motivo da remocao:** o provider itsdangerous deixa de ter consumidor apos a remocao do reset por link.
- **Impacto esperado:** eliminar dependencias de `Env` e imports relacionados ao token legado.

> Se a pasta `src/animus/providers/auth/email_verification/` ficar vazia apos a remocao, a limpeza estrutural pode ser feita na mesma implementacao.

---

# 9. Decisoes Tecnicas e Trade-offs

- **Decisao:** gerar `reset_context` com `Id.create().value` e persisti-lo em `CacheProvider`, em vez de criar novo provider de token assinado.
- **Alternativas consideradas:** reaproveitar `EmailVerificationProvider`; criar um provider novo dedicado para contexto assinado.
- **Motivo da escolha:** `Id` ja existe no `core`, produz valor opaco e evita manter o acoplamento do reset a tokens assinados, respeitando a direcao de dependencias.
- **Impactos / trade-offs:** o contexto passa a depender de cache para validacao e expiracao; isso reduz escopo e complexidade, mas o valor deixa de ser auto-contido fora do Redis.

- **Decisao:** manter `forgot` e `resend-reset-otp` silenciosos com `204` mesmo para e-mail inexistente ou cooldown ativo.
- **Alternativas consideradas:** retornar erro explicito de cooldown (`409` ou `429`) em `resend-reset-otp`.
- **Motivo da escolha:** preservar o requisito de anti-enumeracao do ticket e do PRD, evitando qualquer sinal externo sobre a existencia da conta.
- **Impactos / trade-offs:** o backend nao comunica ao cliente se o cooldown bloqueou o reenvio; o app precisa continuar controlando o countdown na borda.

- **Decisao:** reaproveitar `PasswordResetRequestEvent` e `SendPasswordResetEmailJob`, alterando apenas o payload de token para `OTP`.
- **Alternativas consideradas:** criar evento e job novos com nome especifico de `reset-password-otp`.
- **Motivo da escolha:** a responsabilidade do evento continua a mesma - solicitar envio de e-mail de reset - e a menor mudanca correta preserva wiring existente no `InngestPubSub`.
- **Impactos / trade-offs:** o nome do evento permanece generico para reset, mas o payload muda e exige atualizacao sincronizada do consumidor.

- **Decisao:** reutilizar o contrato atual `AccountsRepository.replace(account)` no reset final, sem introduzir novo metodo especifico de troca de senha nesta task.
- **Alternativas consideradas:** criar `update_password(...)` ou alterar a assinatura de `replace(...)` para receber `password_hash` separado.
- **Motivo da escolha:** reduzir escopo da refatoracao ao necessario para ANI-70 e manter consistencia com o comportamento atual do repositorio concreto.
- **Impactos / trade-offs:** a implementacao continua dependendo do comportamento atual de `SqlalchemyAccountsRepository.replace(...)` para escrever `password_hash` a partir de `account.password`; isso merece revisita futura se o contexto `auth` passar por refactor maior.

---

# 10. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /auth/password/forgot
  -> AuthRouter
  -> ForgotPasswordController
  -> ForgotPasswordUseCase
  -> AccountsRepository.find_by_email(email)
  -> CacheProvider.set_with_ttl(reset_otp)
  -> CacheProvider.set(reset_otp_attempts)
  -> CacheProvider.set_with_ttl(reset_otp_cooldown)
  -> Broker.publish(PasswordResetRequestEvent)
  -> HTTP 204

POST /auth/password/verify-reset-otp
  -> AuthRouter
  -> VerifyResetPasswordOtpController
  -> VerifyResetPasswordOtpUseCase
  -> CacheProvider.get(reset_otp_attempts)
  -> CacheProvider.get(reset_otp)
  -> AccountsRepository.find_by_email(email)
  -> CacheProvider.set_with_ttl(reset_context -> account_id)
  -> CacheProvider.delete(reset_otp / attempts / cooldown)
  -> HTTP 200 ResetPasswordContextDto

POST /auth/password/reset
  -> AuthRouter
  -> ResetPasswordController
  -> ResetPasswordUseCase
  -> CacheProvider.get(reset_context)
  -> AccountsRepository.find_by_id(account_id)
  -> Password.create(new_password)
  -> HashProvider.generate(new_password)
  -> AccountsRepository.replace(account)
  -> CacheProvider.delete(reset_context)
  -> HTTP 200
```

- **Fluxo assincrono:**

```text
ForgotPasswordUseCase / ResendResetPasswordOtpUseCase
  -> Broker.publish(PasswordResetRequestEvent)
  -> InngestBroker
  -> SendPasswordResetEmailJob
  -> SendPasswordResetEmailUseCase
  -> EmailSenderProvider.send_password_reset_email(account_email, otp)
  -> Resend API
```

- **Referencias:**
  - `src/animus/core/auth/use_cases/verify_email_use_case.py`
  - `src/animus/core/auth/use_cases/resend_verification_email_use_case.py`
  - `src/animus/core/auth/use_cases/sign_up_use_case.py`
  - `src/animus/rest/controllers/auth/verify_email_controller.py`
  - `src/animus/rest/controllers/auth/forgot_password_controller.py`
  - `src/animus/rest/controllers/auth/reset_password_controller.py`
  - `src/animus/routers/auth/auth_router.py`
  - `src/animus/pubsub/inngest/jobs/auth/send_password_reset_email_job.py`
  - `src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py`
  - `src/animus/providers/shared/cache/redis/redis_cache_provider.py`

---

# 11. Pendencias / Duvidas

- **Descricao da pendencia:** o PRD em Confluence ainda descreve redefinicao de senha por link/deep link, enquanto o ticket `ANI-70` detalha a migracao completa para `OTP`.
- **Impacto na implementacao:** a spec desta task precisa se apoiar no ticket como fonte de verdade funcional, mesmo com o PRD geral desatualizado para este subfluxo.
- **Acao sugerida:** alinhar o PRD em Confluence apos a entrega da spec para remover a divergencia documental. Confirmacao do usuario nesta sessao: usar `ANI-70` como fonte principal.

- **Descricao da pendencia:** o ticket exige cooldown e expiracoes para `OTP` e `reset_context`, mas nao fixa valores numericos para `RESET_PASSWORD_OTP_TTL_SECONDS`, `RESET_PASSWORD_OTP_RESEND_COOLDOWN_SECONDS` e `RESET_PASSWORD_CONTEXT_TTL_SECONDS`.
- **Impacto na implementacao:** o wiring tecnico pode ser implementado imediatamente, mas os valores finais de produto precisam ser definidos para evitar defaults arbitrarios no backend.
- **Acao sugerida:** validar com produto/arquitetura os valores finais antes da implementacao ou registrar explicitamente esses valores no proprio ticket/PRD.

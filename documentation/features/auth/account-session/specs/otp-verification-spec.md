---
title: Verificacao de e-mail por OTP no Redis
prd: ../prd.md
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-57
status: closed
last_updated_at: 2026-03-25
---

# 1. Objetivo

Substituir o fluxo atual de verificacao de e-mail baseado em link com token assinado por um fluxo de OTP numerico de 6 digitos armazenado no Redis com TTL de 1 hora, fazendo com que `POST /auth/verify-email` passe a receber `email` e `otp`, que `sign-up` e `resend-verification-email` gerem o OTP no proprio `UseCase`, persistam esse valor temporario via `CacheProvider` e publiquem o evento de envio, e que o job assincrono apenas entregue o codigo por e-mail em HTML, preservando a emissao de `SessionDto` apos a confirmacao da conta.

---

# 2. Escopo

## 2.1 In-scope

- Refatorar `VerifyEmailUseCase` e `VerifyEmailController` para verificacao por `email + otp`.
- Introduzir o contrato `OtpProvider` no `core/shared`, criar uma `Structure` de TTL em `shared` e evoluir `CacheProvider` com `set_with_ttl(...)`.
- Criar adaptadores concretos para gerar OTP e persistir/consultar valores no Redis.
- Ajustar `SignUpUseCase`, `ResendVerificationEmailUseCase`, `VerifyEmailUseCase`, `EmailVerificationRequestedEvent` e `SendAccountVerificationEmailJob` para que o OTP seja gerado e persistido nos `use_cases`, e o job apenas envie o e-mail.
- Alterar o envio de e-mail de verificacao para HTML contendo o codigo OTP.
- Remover o fluxo HTTP/HTML baseado em link de verificacao e os artefatos de token que ficarem sem uso na codebase.
- Atualizar configuracao e dependencias minimas necessarias para Redis.

## 2.2 Out-of-scope

- Alterar o fluxo de `POST /auth/sign-in` por e-mail e senha.
- Alterar login com Google, `refresh token`, logout ou gestao de sessao alem do contrato atual de `SessionDto`.
- Introduzir coluna nova em banco, migration Alembic ou persistencia de OTP em PostgreSQL.
- Implementar reset de senha; se esse fluxo vier a precisar de token de e-mail no futuro, ele deve ter contrato proprio.
- Alterar o broker, o router `auth` ou o formato base do payload de erro HTTP alem do necessario para o novo endpoint.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /auth/verify-email` deve receber body JSON com `email: str` e `otp: str`.
- O endpoint deve buscar o OTP esperado em `CacheProvider.get("auth:email_verification:{email}")`.
- Se a chave nao existir ou se o valor nao coincidir com o OTP informado, o fluxo deve lancar `InvalidEmailVerificationTokenError`.
- Em caso de sucesso, o fluxo deve localizar a conta por e-mail, executar `account.verify()` quando `is_verified == False`, persistir a alteracao e remover a chave do cache com `CacheProvider.delete(...)`.
- `POST /auth/verify-email` deve retornar `200` com `SessionDto` emitido por `JwtProvider.encode(...)`.
- `POST /auth/sign-up` e `POST /auth/resend-verification-email` devem gerar um `Otp` no `UseCase`, persisti-lo em `CacheProvider.set_with_ttl(...)` e publicar `EmailVerificationRequestedEvent` contendo `account_email` e `account_email_otp`.
- `SendAccountVerificationEmailJob` deve apenas enviar por e-mail o OTP ja recebido no evento, em HTML.
- `POST /auth/resend-verification-email` deve sobrescrever a mesma chave de cache e reiniciar o TTL ao gerar um novo OTP.

## 3.2 Nao funcionais

- **Seguranca:** o OTP deve ter exatamente `6` digitos numericos e ser gerado com fonte criptograficamente segura.
- **Seguranca:** o erro de verificacao deve continuar colapsando os casos de OTP ausente, expirado ou divergente em uma unica resposta de dominio.
- **Seguranca:** o OTP deve ser de uso unico; apos sucesso, a chave precisa ser removida antes do retorno da resposta HTTP.
- **Idempotencia:** o job Inngest deve usar `step.run(...)` apenas para normalizacao e envio, sem regenerar OTP em reexecucoes do mesmo evento.
- **Compatibilidade retroativa:** esta task quebra o contrato HTTP atual de `GET /auth/verify-email?token=...` com retorno HTML para `POST /auth/verify-email` com body JSON e retorno `SessionDto`; consumidores precisam ser atualizados junto com o backend.
- **Compatibilidade retroativa:** a tabela `accounts` e o schema SQLAlchemy permanecem inalterados; nenhum dado de OTP vai para PostgreSQL.
- **Observabilidade:** o job continua executando dentro do `InngestPubSub` registrado com logger do `uvicorn`, sem introduzir canal paralelo de envio.

---

# 4. O que ja existe?

## Camada Core

- **`Otp`** (`src/animus/core/auth/domain/structures/otp.py`) — `Structure` ja pronta para validar OTP com exatamente 6 digitos; hoje ainda nao participa de nenhum fluxo.
- **`VerifyEmailUseCase`** (`src/animus/core/auth/use_cases/verify_email_use_case.py`) — fluxo atual baseado em `token`, `EmailVerificationProvider` e retorno de `SessionDto`; serve de referencia para manter a verificacao e a emissao de sessao no `core`.
- **`SignUpUseCase`** (`src/animus/core/auth/use_cases/sign_up_use_case.py`) — fluxo atual que gera token de verificacao no request sincrono e publica `EmailVerificationRequestedEvent`; sera a principal referencia para manter a geracao do novo OTP no `core`.
- **`ResendVerificationEmailUseCase`** (`src/animus/core/auth/use_cases/resend_verification_email_use_case.py`) — fluxo atual que tambem gera token no request antes de publicar o evento; sera ajustado para gerar novo `Otp` e sobrescrever o valor no cache ainda no fluxo sincrono.
- **`EmailVerificationRequestedEvent`** (`src/animus/core/auth/domain/events/email_verification_requested_event.py`) — evento de dominio ja consolidado para disparar o envio de verificacao; hoje carrega `account_email` e `account_email_verification_token`.
- **`InvalidEmailVerificationTokenError`** (`src/animus/core/auth/domain/errors/invalid_email_verification_token_error.py`) — erro de dominio ja mapeado para `401`, mas com mensagem orientada a token/link.
- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) — port que ja oferece `find_by_email(...)` e `replace(...)`, suficientes para o fluxo de verificacao apos a validacao do OTP.
- **`JwtProvider`** (`src/animus/core/auth/interfaces/jwt_provider.py`) e **`SessionDto`** (`src/animus/core/auth/domain/structures/dtos/session_dto.py`) — contrato atual de sessao que deve ser preservado no retorno de sucesso.

## Camada Core Shared

- **`CacheProvider`** (`src/animus/core/shared/interfaces/cache_provider.py`) — contrato existente com `get`, `set` e `delete`; falta suporte explicito a TTL e hoje ainda trabalha com `str | None`, nao com `Text | None`.
- **`Broker`** (`src/animus/core/shared/interfaces/broker.py`) — port atual para publicar `EmailVerificationRequestedEvent` sem acoplar o `core` ao SDK do Inngest.
- **Lacuna identificada:** nao existe uma `Structure` compartilhada para representar TTL de forma tipada no dominio; hoje o tempo de expiracao so aparece como `int` solto em configuracao e contratos.
- **Lacuna identificada:** nao existe `OtpProvider` no `core/shared`, apesar de a task exigir uma abstracao especifica para geracao de codigos.

## Camada REST

- **`VerifyEmailController`** (`src/animus/rest/controllers/auth/verify_email_controller.py`) — endpoint atual `GET /auth/verify-email` com `token` via `Query`; executa o `UseCase`, ignora o `SessionDto` retornado e responde com HTML estatico.
- **`SignUpController`** (`src/animus/rest/controllers/auth/sign_up_controller.py`) — referencia de controller fino que usa `_Body`, `Depends(...)` e `named params`.
- **`ResendVerificationEmailController`** (`src/animus/rest/controllers/auth/resend_verification_email_controller.py`) — referencia do fluxo HTTP que continuara retornando `204`, mas deixara de depender de `EmailVerificationProvider`.
- **`SignInController`** (`src/animus/rest/controllers/auth/sign_in_controller.py`) — referencia direta para endpoint que recebe body JSON e retorna `SessionDto` sem camada `validation` dedicada.

## Camada Pipes

- **`ProvidersPipe`** (`src/animus/pipes/providers_pipe.py`) — hoje resolve `HashProvider`, `JwtProvider`, `EmailVerificationProvider`, `EmailSenderProvider` e `GoogleOAuthProvider`; sera o ponto natural para adicionar `CacheProvider` e `OtpProvider` e retirar o provider legado de verificacao por token.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — ja entrega `AccountsRepository` via `Depends(...)` e nao precisa mudar de responsabilidade.
- **`PubSubPipe`** (`src/animus/pipes/pubsub_pipe.py`) — ja entrega `Broker` para os controllers de `auth` e continua sendo a referencia para o fluxo assincrono.

## Camada PubSub

- **`SendAccountVerificationEmailJob`** (`src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py`) — job atual que recebe o evento, normaliza `account_email` e `account_email_verification_token` e delega o envio do e-mail; servira de referencia para o modelo futuro em que o job apenas consome `account_email` e `account_email_otp`.
- **`InngestBroker`** (`src/animus/pubsub/inngest/inngest_broker.py`) — adaptador atual de publicacao de eventos de dominio; nao precisa mudar de contrato.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) — wiring atual do job, que deve permanecer reaproveitado.

## Camada Providers

- **`ItsdangerousEmailVerificationProvider`** (`src/animus/providers/auth/email_verification/itsdangerous_email_verification_provider.py`) — adaptador atual de token assinado; apos a refatoracao, nao ha outro uso conhecido na codebase.
- **`ResendEmailSenderProvider`** (`src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py`) — provider atual que monta link HTML e texto apontando para `GET /auth/verify-email?token=...`; serve de referencia para manter a integracao com `resend`, mas precisa trocar o conteudo da mensagem e passar a receber `structures` em vez de primitivos.
- **Lacunas identificadas:** nao existe implementacao concreta de `CacheProvider`, nao existe provider concreto para OTP e nao foi encontrado codigo de Redis/Upstash em `src/animus/`.

## Configuracao e dependencias

- **`src/animus/constants/cache_keys.py`** — centraliza o formato das chaves de cache da aplicacao; deve ser reutilizado para montar a chave de OTP de verificacao de e-mail sem duplicar string literals.
- **`src/animus/constants/env.py`** — hoje concentra segredos e TTL do fluxo legado de token (`EMAIL_VERIFICATION_SECRET_KEY`, `EMAIL_VERIFICATION_SALT`, `EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS`); nao possui configuracao de Redis.
- **`.env.example`** — documenta apenas as variaveis do fluxo legado por token e nao traz `REDIS_URL` nem uma constante dedicada ao TTL do OTP.
- **`pyproject.toml`** — nao possui dependencia de cliente Redis; isso e uma lacuna tecnica direta para a implementacao do cache.

---

# 5. O que deve ser criado?

## Camada Core (Structures)

- **Localizacao:** `src/animus/core/shared/domain/structures/ttl.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `seconds: int`
- **Metodos / factory:**
  - `create(seconds: int) -> Ttl` — valida e cria uma representacao tipada de TTL em segundos para uso em contratos de cache e configuracao de expiracao.
  - `dto -> int` — devolve o valor normalizado em segundos para adaptadores de infraestrutura.

## Camada Core (Interfaces / Ports)

- **Localizacao:** `src/animus/core/shared/interfaces/otp_provider.py` (**novo arquivo**)
- **Metodos:**
  - `generate() -> Otp` — gera um codigo numerico aleatorio de 6 digitos e devolve a `Structure` de dominio validada.

## Camada Providers

- **Localizacao:** `src/animus/providers/auth/otp/secrets/secrets_otp_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `OtpProvider`
- **Biblioteca/SDK utilizado:** `secrets` da standard library
- **Metodos:**
  - `generate() -> Otp` — gera OTP numerico de 6 digitos usando fonte criptograficamente segura e devolve `Otp.create(...)`.

- **Localizacao:** `src/animus/providers/shared/cache/redis/redis_cache_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `CacheProvider`
- **Biblioteca/SDK utilizado:** `redis-py`
- **Dependencias:** conexao `redis.Redis` configurada com `decode_responses=True`
- **Metodos:**
  - `get(key: str) -> Text | None` — recupera valor textual da chave, convertendo para `Text`, ou `None` quando ausente.
  - `set(key: str, value: Text) -> None` — preserva o contrato atual de escrita sem expiracao usando `Text` como valor de entrada.
  - `set_with_ttl(key: str, value: Text, ttl: Ttl) -> None` — grava o valor com TTL em segundos usando a operacao nativa do Redis.
  - `delete(key: str) -> None` — remove a chave do cache.

---

# 6. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/auth/use_cases/verify_email_use_case.py`
- **Mudanca:** trocar a dependencia de `EmailVerificationProvider` por `CacheProvider`, alterar a assinatura para `execute(email: str, otp: str) -> SessionDto`, validar `Email.create(email)` + `Otp.create(otp)` antes de consultar o cache e comparar `Otp` informado com o valor retornado por `CacheProvider.get(...)` convertido para `Otp`.
- **Justificativa:** o fluxo deixa de verificar link assinado e passa a comparar um codigo armazenado no Redis, mantendo a verificacao da conta e a emissao de sessao no `core`.

- **Arquivo:** `src/animus/core/auth/use_cases/sign_up_use_case.py`
- **Mudanca:** remover a dependencia de `EmailVerificationProvider`, adicionar dependencias de `OtpProvider` e `CacheProvider`, criar `ttl = Ttl.create(...)`, gerar `otp = otp_provider.generate()`, persistir `CacheProvider.set_with_ttl(...)` e publicar `EmailVerificationRequestedEvent(account_email=..., account_email_otp=...)`.
- **Justificativa:** o OTP deve nascer no `core`, nao no job, e o `UseCase` continua sendo o orquestrador do fluxo sincrono.

- **Arquivo:** `src/animus/core/auth/use_cases/resend_verification_email_use_case.py`
- **Mudanca:** remover a dependencia de `EmailVerificationProvider`, adicionar dependencias de `OtpProvider` e `CacheProvider`, criar `ttl = Ttl.create(...)`, gerar novo `Otp`, sobrescrever a chave de cache com TTL renovado e republicar o evento com `account_email` e `account_email_otp`.
- **Justificativa:** o reenvio precisa controlar a renovacao do codigo ainda no fluxo sincrono e manter o job apenas como entregador da notificacao.

- **Arquivo:** `src/animus/core/auth/domain/events/email_verification_requested_event.py`
- **Mudanca:** substituir `account_email_verification_token` por `account_email_otp` no payload e ajustar `__init__(account_email: str, account_email_otp: str) -> None`.
- **Justificativa:** o evento continua transportando o dado necessario para o envio do e-mail, mas agora com OTP gerado no `UseCase`.

- **Arquivo:** `src/animus/core/auth/domain/errors/invalid_email_verification_token_error.py`
- **Mudanca:** manter a classe, mas atualizar a mensagem para refletir codigo/OTP invalido ou expirado.
- **Justificativa:** preserva o mapeamento de erro ja consolidado na aplicacao sem manter copy orientada a link.

- **Arquivo:** `src/animus/core/notification/interfaces/email_sender_provider.py`
- **Mudanca:** alterar o contrato para `send_account_verification_email(account_email: Email, otp: Otp) -> None`.
- **Justificativa:** o provider de e-mail deixa de receber um link/token e passa a enviar um codigo textual.

- **Arquivo:** `src/animus/core/notification/use_cases/send_account_verification_email_use_case.py`
- **Mudanca:** alterar a assinatura para `execute(account_email: str, otp: str) -> None`, convertendo para `Email.create(...)` e `Otp.create(...)` antes de repassar ao provider.
- **Justificativa:** manter a orquestracao atual do contexto `notification`, mas alinhada ao novo contrato de envio.

## Camada Core Shared

- **Arquivo:** `src/animus/core/shared/interfaces/cache_provider.py`
- **Mudanca:** alterar o contrato para `get(key: str) -> Text | None`, `set(key: str, value: Text) -> None` e adicionar `set_with_ttl(key: str, value: Text, ttl: Ttl) -> None`.
- **Justificativa:** a task exige persistencia temporaria do OTP; o contrato atual nao suporta expiracao.

- **Arquivo:** `src/animus/core/shared/interfaces/__init__.py`
- **Mudanca:** exportar `CacheProvider` e `OtpProvider` junto de `Broker`.
- **Justificativa:** manter imports publicos estaveis para contratos compartilhados que passam a ser usados por `use_cases`, `pipes` e providers.

- **Arquivo:** `src/animus/core/auth/interfaces/__init__.py`
- **Mudanca:** remover o export de `EmailVerificationProvider` apos a eliminacao do contrato legado.
- **Justificativa:** evitar API publica apontando para uma interface sem uso no contexto `auth`.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/auth/verify_email_controller.py`
- **Mudanca:** trocar `GET` por `POST`, substituir `token: Query` por `_Body(email: str, otp: str)`, mudar `response_class=HTMLResponse` para `response_model=SessionDto` e injetar `CacheProvider` via `Depends(ProvidersPipe.get_cache_provider)`.
- **Justificativa:** o endpoint passa a ser consumido pelo app mobile com digitacao manual do codigo, sem HTML nem deep link.

- **Arquivo:** `src/animus/rest/controllers/auth/sign_up_controller.py`
- **Mudanca:** remover a injecao de `EmailVerificationProvider` e adicionar injecoes de `OtpProvider` e `CacheProvider` para a instancia do `SignUpUseCase`.
- **Justificativa:** o `UseCase` deixa de depender desse port.

- **Arquivo:** `src/animus/rest/controllers/auth/resend_verification_email_controller.py`
- **Mudanca:** remover a injecao de `EmailVerificationProvider` e adicionar `OtpProvider` e `CacheProvider` para instanciar `ResendVerificationEmailUseCase`.
- **Justificativa:** o reenvio continua fino, mas a geracao e persistencia do OTP passam a acontecer no `UseCase`.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/providers_pipe.py`
- **Mudanca:** remover `get_email_verification_provider()`, adicionar `get_cache_provider() -> CacheProvider` e `get_otp_provider() -> OtpProvider`, mantendo os demais providers atuais e retornando contratos tipados por `Text` / `Otp` nas assinaturas dos adapters.
- **Justificativa:** centraliza o wiring das novas dependencias de infraestrutura e elimina o adaptador legado de token do fluxo HTTP.

## Camada Providers

- **Arquivo:** `src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py`
- **Mudanca:** remover a montagem de `verification_url`, trocar o HTML dedicado baseado em link por um template HTML com o codigo OTP, recebendo `Email` e `Otp` como parametros tipados.
- **Justificativa:** o usuario agora confirma a conta digitando o codigo no app, sem navegar para uma pagina web.

- **Arquivo:** `src/animus/constants/env.py`
- **Mudanca:** remover as configuracoes do token legado (`EMAIL_VERIFICATION_SECRET_KEY`, `EMAIL_VERIFICATION_SALT`, `EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS`) e adicionar configuracao minima de Redis (`REDIS_URL`) e TTL do OTP (`EMAIL_VERIFICATION_OTP_TTL_SECONDS`).
- **Justificativa:** o novo fluxo depende de cache e deixa de depender de segredo/salt para assinatura de link.

- **Arquivo:** `src/animus/constants/cache_keys.py`
- **Mudanca:** adicionar ou consolidar uma API explicita para a chave de OTP de verificacao de e-mail, por exemplo `email_verification_otp(email: str) -> str`.
- **Justificativa:** evitar string literals duplicadas e garantir consistencia entre geracao, reenvio e verificacao do OTP.

- **Arquivo:** `.env.example`
- **Mudanca:** refletir as novas variaveis de ambiente de Redis/TTL e remover as do fluxo legado de token.
- **Justificativa:** manter o bootstrap local coerente com a implementacao planejada.

- **Arquivo:** `pyproject.toml`
- **Mudanca:** adicionar a dependencia do cliente Redis Python.
- **Justificativa:** a codebase nao possui hoje nenhuma biblioteca capaz de implementar `CacheProvider` com Redis.

## Camada PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py`
- **Mudanca:** ajustar o payload normalizado para conter `account_email` e `account_email_otp`, remover os passos de geracao/persistencia do OTP e manter apenas normalizacao + envio do e-mail.
- **Justificativa:** a responsabilidade de gerar e persistir o codigo permanece no `core`; o job fica restrito a orquestrar o envio.

---

# 7. O que deve ser removido?

## Camada Core

- **Arquivo:** `src/animus/core/auth/interfaces/email_verification_provider.py`
- **Motivo da remocao:** apos a migracao para OTP em Redis com geracao no `core`, nao restam usos ativos do contrato de token assinado na codebase atual.
- **Impacto esperado:** atualizar imports e exports em `src/animus/core/auth/interfaces/__init__.py`, `src/animus/pipes/providers_pipe.py` e qualquer arquivo que ainda referencie o provider legado.

## Camada Providers

- **Arquivo:** `src/animus/providers/auth/email_verification/itsdangerous_email_verification_provider.py`
- **Motivo da remocao:** o adaptador implementa exclusivamente o fluxo legado de token assinado, que deixa de existir nesta feature.
- **Impacto esperado:** remover o export correspondente em `src/animus/providers/auth/__init__.py` e a dependencia de `itsdangerous` do wiring deste fluxo.

- **Arquivo:** `src/animus/providers/notification/email_sender/constants/email_verification_html.py`
- **Motivo da remocao:** o e-mail deixa de conter CTA HTML com link e passa a conter um template HTML com o codigo OTP.
- **Impacto esperado:** simplificar `ResendEmailSenderProvider` e eliminar a constante HTML hoje usada apenas por esse provider.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/auth/constants/verify_email_success_html.py`
- **Motivo da remocao:** `POST /auth/verify-email` passa a retornar `SessionDto`; nao existe mais pagina HTML de confirmacao.
- **Impacto esperado:** remover tambem o import e qualquer referencia em `src/animus/rest/controllers/auth/verify_email_controller.py`.

- **Arquivo:** `src/animus/rest/controllers/auth/constants/__init__.py`
- **Motivo da remocao:** o pacote fica sem responsabilidade apos a exclusao do HTML de sucesso.
- **Impacto esperado:** limpar imports do subpacote `constants` no contexto `auth`.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** gerar o OTP dentro de `SignUpUseCase` e `ResendVerificationEmailUseCase`, e nao em `SendAccountVerificationEmailJob`.
  - **Alternativas consideradas:** gerar o OTP no job; gerar o OTP no controller.
  - **Motivo da escolha:** mantem a decisao e a persistencia do codigo dentro do `core`, deixa o job sem responsabilidade de negocio e segue sua diretriz de que o OTP deve nascer nos `use_cases`.
  - **Impactos / trade-offs:** o request sincrono passa a depender do cache para concluir o fluxo, mas o evento publicado fica completo para o envio assicrono.

- **Decisao:** manter o nome `EmailVerificationRequestedEvent`, mas trocar o payload para `account_email` + `account_email_otp`.
  - **Alternativas consideradas:** criar um novo evento especifico para OTP; reduzir o payload para apenas o e-mail e deixar o job gerar o codigo.
  - **Motivo da escolha:** o fato de dominio continua sendo o mesmo e o evento segue carregando o dado exato que o job precisa para enviar a notificacao.
  - **Impactos / trade-offs:** o payload volta a transportar dado sensivel de curta duracao, mas elimina duplicacao de geracao entre fluxo sincrono e assicrono.

- **Decisao:** evoluir `CacheProvider` com `set_with_ttl(...)`, usar `Text` como contrato de valor e `Ttl` como contrato tipado de expiracao.
  - **Alternativas consideradas:** sobrescrever semanticamente `set` para aceitar expiracao opcional; fazer o job falar diretamente com o cliente Redis.
  - **Motivo da escolha:** deixa o contrato explicito no `core/shared`, preserva o principio de ports and adapters e reforca que providers devem operar com `structures` do dominio em vez de `str` ou `int` soltos.
  - **Impactos / trade-offs:** aumenta a superficie da interface compartilhada e exige pequenas conversoes no adapter Redis.

- **Decisao:** remover `EmailVerificationProvider` e o adapter `itsdangerous` nesta task.
  - **Alternativas consideradas:** manter o codigo legado sem uso aguardando futuras features como reset de senha.
  - **Motivo da escolha:** a pesquisa na codebase nao encontrou outro fluxo ativo que dependa desse contrato, e mantelo sem uso adicionaria ruido e custo de manutencao.
  - **Impactos / trade-offs:** uma futura feature de reset de senha precisara definir seu proprio contrato/adaptador em vez de reaproveitar o legado implicitamente.

- **Decisao:** preservar `InvalidEmailVerificationTokenError` como classe de dominio, mudando apenas a mensagem.
  - **Alternativas consideradas:** renomear para `InvalidEmailVerificationOtpError`.
  - **Motivo da escolha:** minimiza churn em imports, handlers e testes existentes, enquanto o significado funcional do erro continua sendo "credencial de verificacao de e-mail invalida".
  - **Impactos / trade-offs:** o nome interno continua mencionando `token`, embora o transporte passe a ser OTP.

- **Decisao:** adicionar um adapter Redis dedicado e registrar a dependencia em `pyproject.toml`.
  - **Alternativas consideradas:** falar com Upstash por HTTP diretamente; armazenar OTP em PostgreSQL; usar `request.state` sem port dedicado.
  - **Motivo da escolha:** o Jira exige Redis com TTL e cita operacao equivalente a `setex`; alem disso, a arquitetura ja define Redis como tecnologia da stack.
  - **Impactos / trade-offs:** a feature passa a depender de configuracao adicional de Redis em ambiente local e remoto.

- **Decisao:** reutilizar `src/animus/constants/cache_keys.py` para montar a chave `auth:email_verification:{email}`.
  - **Alternativas consideradas:** manter a chave inline nos `use_cases`; encapsular a string apenas no adapter Redis.
  - **Motivo da escolha:** a constante ja existe, reduz duplicacao e deixa o formato da chave consistente em todos os pontos do fluxo.
  - **Impactos / trade-offs:** o formato da chave passa a ficar acoplado a um modulo compartilhado de constantes da aplicacao, o que e aceitavel para esse detalhe transversal.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /auth/verify-email
  -> AuthRouter
  -> VerifyEmailController
  -> DatabasePipe / ProvidersPipe
  -> VerifyEmailUseCase.execute(email, otp)
       -> Email.create(...)
       -> Otp.create(...)
        -> CacheProvider.get("auth:email_verification:{email}") -> Text | None
       -> Otp.create(valor_persistido)
       -> comparar otp informado x otp persistido
       -> AccountsRepository.find_by_email(...)
       -> account.verify()
       -> AccountsRepository.replace(account)
        -> CacheProvider.delete("auth:email_verification:{email}")
       -> JwtProvider.encode(account.id)
  -> 200 SessionDto
```

- **Fluxo assincrono:**

```text
POST /auth/sign-up | POST /auth/resend-verification-email
  -> SignUpUseCase / ResendVerificationEmailUseCase
  -> OtpProvider.generate()
  -> Ttl.create(3600)
  -> CacheProvider.set_with_ttl(key, Text.create(otp.value), ttl)
  -> Broker.publish(EmailVerificationRequestedEvent(account_email, account_email_otp))
  -> InngestBroker.send_sync(...)
  -> InngestPubSub
  -> SendAccountVerificationEmailJob
       -> step.run("normalize_payload")
       -> step.run("send_account_verification_email")
             -> SendAccountVerificationEmailUseCase
             -> EmailSenderProvider.send_account_verification_email(account_email, otp)
  -> usuario recebe codigo OTP por e-mail
```

- **Referencias:**
  - `src/animus/core/auth/use_cases/verify_email_use_case.py`
  - `src/animus/core/auth/use_cases/sign_up_use_case.py`
  - `src/animus/core/auth/use_cases/resend_verification_email_use_case.py`
  - `src/animus/core/auth/domain/structures/otp.py`
  - `src/animus/core/shared/interfaces/cache_provider.py`
  - `src/animus/constants/cache_keys.py`
  - `src/animus/rest/controllers/auth/verify_email_controller.py`
  - `src/animus/rest/controllers/auth/sign_in_controller.py`
  - `src/animus/pipes/providers_pipe.py`
  - `src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py`
  - `src/animus/providers/notification/email_sender/resend/resend_email_sender_provider.py`

---

# 10. Pendencias / Duvidas

**Sem pendencias**.

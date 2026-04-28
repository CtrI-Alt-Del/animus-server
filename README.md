# <h1 align="center">Animus Server</h1>

Backend da plataforma **Animus**, uma aplicacao de analise de precedentes juridicos que transforma peticoes iniciais em insumos objetivos para advogados e juizes. Este servico foi desenvolvido em **Python** com **FastAPI**, com foco em regras de negocio desacopladas, arquitetura em camadas e integracoes robustas para autenticacao, processamento com IA, armazenamento de analises e notificacoes assincronas.

## 🚀 Visao Geral

O Animus Server sustenta os principais fluxos do produto:

- **Auth e identidade:** cadastro, login, gestao de perfil e recuperacao de senha.
- **Intake juridico:** upload de peticoes em PDF ou DOCX para extracao, resumacao e analise de precedentes com IA.
- **Analise de precedentes:** classificacao de aplicabilidade, sintese explicativa e apoio a decisao processual.
- **Storage e historico:** persistencia, organizacao, consulta e exportacao de analises anteriores.
- **Notificacoes assicronas:** eventos de conclusao de analise e outros fluxos desacoplados.

## 🛠 Tech Stack

O projeto utiliza uma stack moderna para API, persistencia, processamento e mensageria:

- **Linguagem:** [Python](https://www.python.org/) 3.13+
- **Framework HTTP:** [FastAPI](https://fastapi.tiangolo.com/)
- **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
- **ORM e Persistencia:** [SQLAlchemy](https://www.sqlalchemy.org/) + [PostgreSQL](https://www.postgresql.org/)
- **Migracoes:** [Alembic](https://alembic.sqlalchemy.org/)
- **Jobs/Eventos:** [Inngest](https://www.inngest.com/)
- **IA e orquestracao:** [Agno](https://www.agno.com/)
- **Validacao e configuracao:** [Pydantic](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Autenticacao e seguranca:** [PyJWT](https://pyjwt.readthedocs.io/) + [pwdlib](https://frankie567.github.io/pwdlib/)
- **Tooling:** [uv](https://github.com/astral-sh/uv), [Poe the Poet](https://github.com/nat-n/poethepoet), [Ruff](https://docs.astral.sh/ruff/), [BasedPyright](https://docs.basedpyright.com/), [Pytest](https://docs.pytest.org/)

## 🏗 Arquitetura

O projeto segue uma arquitetura em camadas inspirada em **Clean Architecture** e **Hexagonal Architecture (Ports and Adapters)**.

### Estrutura de Camadas

- **Core (`src/animus/core/`)**: entidades, DTOs, erros de dominio, interfaces e use cases.
- **Rest (`src/animus/rest/`)**: controllers HTTP e middlewares de request.
- **Routers (`src/animus/routers/`)**: composicao e registro de rotas por contexto.
- **Pipes (`src/animus/pipes/`)**: providers de dependencia para `Depends(...)`.
- **Validation (`src/animus/validation/`)**: schemas e conversao request/response.
- **Database (`src/animus/database/`)**: models, mappers e repositorios SQLAlchemy.
- **Providers (`src/animus/providers/`)**: adaptadores externos e servicos de infraestrutura.
- **PubSub (`src/animus/pubsub/`)**: orquestracao assincrona por eventos com Inngest.
- **AI (`src/animus/ai/`)**: integracoes e orquestracao dos fluxos de inteligencia artificial.

Para detalhes tecnicos, consulte a [Documentacao de Arquitetura](documentation/architecture.md).

## 📂 Estrutura do Projeto

```bash
src/animus/
├── app.py
├── ai/
├── constants/
├── core/
├── database/
├── pipes/
├── providers/
├── pubsub/
├── rest/
├── routers/
└── validation/
```

## ⚙️ Configuracao e Instalacao

### Pre-requisitos

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- PostgreSQL local ou acessivel via `DATABASE_URL`
- Node.js/npm apenas se voce for executar o ambiente local do Inngest

### Passo a passo

1. **Clone o repositorio:**

   ```bash
   git clone <url-do-repositorio>
   cd animus-server
   ```

2. **Configure as variaveis de ambiente:**

   ```bash
   cp .env.example .env
   ```

   Preencha os valores necessarios no arquivo `.env`.
   Consulte a secao `Variaveis de Ambiente` abaixo para o detalhamento completo de cada chave.

3. **Instale as dependencias do projeto:**

   ```bash
   uv sync
   ```

   O `uv sync` cria/atualiza automaticamente o ambiente virtual local em `.venv`.
   Se quiser ativar manualmente no shell:

   ```bash
   source .venv/bin/activate
   ```

4. **Prepare o banco de dados:**

   Crie a base configurada em `DATABASE_URL` e depois aplique as migracoes:

   ```bash
   uv run poe db:upgrade
   ```

5. **Execute a API em desenvolvimento:**

   ```bash
   uv run poe dev
   ```

6. **(Opcional) Execute o ambiente local de eventos:**

   ```bash
   uv run poe pubsub
   ```

7. **(Opcional) Popule dados de desenvolvimento:**

   ```bash
   uv run poe db:seed
   ```

### Infra local com Docker Compose

Para subir os servicos locais (PostgreSQL, Redis, Qdrant, Inngest e emulador de GCS):

```bash
docker compose up -d
```

Para derrubar os servicos:

```bash
docker compose down
```

## 🔐 Variaveis de Ambiente

### Minimo para rodar local

- Obrigatorias para o fluxo principal local: `MODE`, `DATABASE_URL`, `JWT_SECRET_KEY`, `REDIS_URL`, `QDRANT_URL`, `GCS_BUCKET_NAME`, `GCS_EMULATOR_HOST`.
- Recomendadas para testar IA/end-to-end: `OPENAI_API_KEY` e/ou `GEMINI_API_KEY`, `INNGEST_SIGNING_KEY`, `RESEND_API_KEY`, `RESEND_SENDER_EMAIL`.

### Produção

- Em `prod`, nao use `GCS_EMULATOR_HOST`; use bucket real no GCS.
- Mantenha segredos (`*_KEY`, `*_SECRET`, credenciais e URLs com auth) em gerenciador de segredos.

## 📦 CD de Imagem Docker e Cloud Run

O repositorio possui um workflow de CD dedicado para publicar a imagem Docker no Google Artifact Registry e atualizar o servico no Google Cloud Run.

### Gatilhos

- Push em `main`: publica imagem de `staging` e faz deploy no Cloud Run.
- Push em `production`: publica imagem de `prod` e faz deploy no Cloud Run.
- O CD so roda quando o workflow `Continuous Integration` termina com sucesso para o mesmo push.

### Tags publicadas

- `main`:
  - `staging`
  - `staging-<sha-curto>`
- `production`:
  - `prod`
  - `prod-<sha-curto>`
  - `latest`

### Deploy no Cloud Run

- `main`: faz deploy da imagem `staging-<sha-curto>` no servico configurado para `staging`.
- `production`: faz deploy da imagem `prod-<sha-curto>` no servico configurado para `production`.
- O deploy usa uma tag imutavel por commit para garantir rastreabilidade da revisao publicada.

### Variaveis do GitHub Actions

Configure estas variaveis em `Settings > Secrets and variables > Actions` ou nos `Environments` correspondentes:

- `GCP_PROJECT_ID`: ID do projeto GCP.
- `GCP_ARTIFACT_REGISTRY_REGION`: regiao do Artifact Registry, ex. `southamerica-east1`.
- `GCP_ARTIFACT_REGISTRY_REPOSITORY`: nome do repositorio Docker no Artifact Registry.
- `GCP_CLOUD_RUN_REGION`: regiao do servico Cloud Run, ex. `southamerica-east1`.
- `GCP_CLOUD_RUN_SERVICE`: nome do servico Cloud Run que recebera o deploy.
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: resource name completo do provider, ex. `projects/123456789/locations/global/workloadIdentityPools/github/providers/animus-server`.
- `GCP_SERVICE_ACCOUNT_EMAIL`: email da service account usada pelo GitHub Actions.
- `IMAGE_NAME`: opcional; nome da imagem. Padrao: `animus-server`.

### Configuracao recomendada no GCP

Use `Workload Identity Federation` em vez de chave JSON fixa.

1. Habilite as APIs do Artifact Registry e Cloud Run no projeto.
2. Crie um repositorio Docker no Artifact Registry.
3. Crie uma service account para o GitHub Actions.
4. Conceda a essa service account ao menos `roles/artifactregistry.writer`.
5. Conceda tambem `roles/run.admin` para atualizar o Cloud Run.
6. Conceda `roles/iam.serviceAccountUser` na service account de runtime usada pelo Cloud Run, quando aplicavel.
7. Crie um `Workload Identity Pool` para GitHub Actions.
8. Crie um `OIDC Provider` com issuer `https://token.actions.githubusercontent.com`.
9. Restrinja o provider ao owner/repositorio corretos.
10. Permita que o repositorio GitHub impersonifique a service account com `roles/iam.workloadIdentityUser`.

### Exemplo de destino da imagem

```text
southamerica-east1-docker.pkg.dev/<project-id>/<repository>/animus-server:staging
southamerica-east1-docker.pkg.dev/<project-id>/<repository>/animus-server:prod
```

### Detalhamento por variavel

- `HOST`
  - O que e: host onde a API vai escutar localmente.
  - Como obter: defina manualmente (`127.0.0.1` para desenvolvimento local).

- `PORT`
  - O que e: porta HTTP da API.
  - Como obter: defina manualmente (`8080` no ambiente local).

- `ANIMUS_SERVER_URL`
  - O que e: URL publica/base da API usada em fluxos que precisam de callback/link absoluto.
  - Como obter: local `http://localhost:8080`; em cloud, use a URL publica do servico.

- `MODE`
  - O que e: modo de execucao (`dev`, `stg`, `prod`).
  - Como obter: defina conforme ambiente de deploy.

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - O que e: dados auxiliares para ambiente local de banco.
  - Como obter: defina manualmente para o banco local (ou os valores do seu container/servico PostgreSQL).

- `DATABASE_URL`
  - O que e: string de conexao principal do PostgreSQL.
  - Como obter: no formato `postgresql://<user>:<password>@<host>:<port>/<db>`.
    - Local: use os valores do seu Postgres local.
    - Gerenciado (ex.: Supabase): copie a connection string no painel do provider.

- `GCS_BUCKET_NAME`
  - O que e: nome do bucket usado para arquivos.
  - Como obter:
    - Local (emulador): defina um nome fixo, ex. `animus`.
    - Producao: crie bucket no Google Cloud Storage e use o nome exato.

- `GCS_EMULATOR_HOST`
  - O que e: endpoint do emulador de storage.
  - Como obter: em dev local, use algo como `http://localhost:4443`.
    - Importante: essa variavel so deve ser usada com `MODE=dev`.

- `GEMINI_API_KEY`
  - O que e: chave da API Gemini (Google AI Studio).
  - Como obter: gere em Google AI Studio e copie para o `.env`.

- `OPENAI_API_KEY`
  - O que e: chave da API OpenAI.
  - Como obter: gere no painel da OpenAI e copie para o `.env`.

- `GOOGLE_CLIENT_ID`
  - O que e: client id OAuth usado no login com Google.
  - Como obter: crie credencial OAuth 2.0 no Google Cloud Console (tipo Web application) e copie o Client ID.

- `PANGEA_SERVICE_URL`
  - O que e: URL base do servico Pangea consumido pelo backend.
  - Como obter: usar a URL oficial do ambiente alvo; em geral manter `https://pangeabnp.pdpj.jus.br`.

- `QDRANT_URL`
  - O que e: endpoint HTTP do Qdrant.
  - Como obter:
    - Local: `http://localhost:6333`.
    - Cloud: copie a URL/endpoint do cluster Qdrant.

- `INNGEST_DEV`
  - O que e: flag para modo de desenvolvimento do Inngest.
  - Como obter: use `1` localmente; em ambientes nao-dev normalmente remova/ajuste conforme configuracao do Inngest.

- `INNGEST_SIGNING_KEY`
  - O que e: chave de assinatura/validacao de eventos Inngest.
  - Como obter: copie no dashboard/projeto do Inngest (environment keys).

- `JWT_SECRET_KEY`
  - O que e: segredo usado para assinar tokens JWT.
  - Como obter: gere uma string aleatoria forte (ex.: 32+ bytes) e armazene em cofre de segredos.

- `JWT_ALGORITHM`
  - O que e: algoritmo de assinatura JWT.
  - Como obter: definir manualmente (`HS256` padrao do projeto).

- `JWT_ACCESS_TOKEN_EXPIRATION_SECONDS`
  - O que e: expiracao do access token em segundos.
  - Como obter: definir manualmente (ex.: `3600`).

- `JWT_REFRESH_TOKEN_EXPIRATION_SECONDS`
  - O que e: expiracao do refresh token em segundos.
  - Como obter: definir manualmente (ex.: `86400`).

- `REDIS_URL`
  - O que e: URL de conexao ao Redis.
  - Como obter:
    - Local: `redis://localhost:6379/0`.
    - Gerenciado (ex.: Upstash): copie endpoint e credenciais no painel do provider.

- `EMAIL_VERIFICATION_OTP_TTL_SECONDS`
  - O que e: tempo de vida do OTP de verificacao de email (em segundos).
  - Como obter: definir manualmente entre 60 e 86400 (padrao recomendado: `3600`).

- `RESEND_API_KEY`
  - O que e: chave da API Resend para envio de emails.
  - Como obter: gere no dashboard da Resend.

- `RESEND_SENDER_EMAIL`
  - O que e: remetente dos emails transacionais.
  - Como obter: use um endereco de dominio verificado na Resend.

## 📖 Dominios do Produto

Com base na documentacao funcional, os modulos centrais do produto sao:

- **Auth:** identidade do usuario, login com email/senha ou Google, perfil e recuperacao de senha.
- **Intake:** recebimento da peticao inicial, extracao de informacoes e busca de precedentes juridicos relevantes.
- **Storage:** historico, organizacao em pastas, nomeacao e exportacao das analises.
- **Notification:** comunicacao assincrona quando uma analise e concluida ou um relatorio e gerado.

O sistema e uma ferramenta de apoio a decisao. A interpretacao final e a escolha do precedente continuam sob responsabilidade do usuario.

## 📖 Documentacao

Os principais documentos do projeto estao em `documentation/`:

- [Arquitetura e Decisoes Tecnicas](documentation/architecture.md)
- [Regras e Convencoes por Camada](documentation/rules/rules.md)

## 🧪 Testes e Qualidade

Execute os comandos abaixo para validar o projeto:

```bash
uv run poe test
uv run poe typecheck
uv run poe codecheck
```

## 📝 Licenca

Este projeto esta licenciado sob a licenca [MIT](LICENSE).

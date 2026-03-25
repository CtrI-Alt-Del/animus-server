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
- Node.js/npm apenas se voce for executar o ambiente local do Inngest ou executar alterações no código

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

3. **Instale as dependencias do projeto:**

   ```bash
   uv sync
   ```

   #### Apenas se for desenvolver

   ```bash
   npm i
   ```

4. **Prepare o banco de dados:**

   Crie a base configurada em `DATABASE_URL` e depois aplique as migracoes:

   ```bash
   uv run poe db:upgrade
   ```

5. **Execute a API em desenvolvimento:**

   ```bash
   uv run dev
   ```

6. **(Opcional) Execute o ambiente local de eventos:**

   ```bash
   uv run poe pubsub
   ```

7. **(Opcional) Popule dados de desenvolvimento:**

   ```bash
   uv run poe db:seed
   ```

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

---
description: Atualizar documento de arquitetura conforme mudancas reais do servidor
---

# Prompt: Atualizar documento de arquitetura (equiny-server)

Objetivo: manter `documentation/architecture.md` sincronizado com a realidade do
`equiny-server` (Clean Architecture + Hexagonal/Ports and Adapters), incluindo
camadas, responsabilidades, stack e estrutura de diretorios.

Entradas:

1) PRDs/Specs relevantes (quando existirem) e decisoes tecnicas recentes.
2) Regras do projeto (substitui "guidelines"):
   - indice: `documentation/rules/rules.md`
   - por camada: `documentation/rules/*-rules.md`
3) Mudancas significativas no codigo (novas camadas, refactors, novos modulos).
4) O arquivo atual: `documentation/architecture.md`.

Diretrizes de execucao:

1) Analise de impacto

- Produto: o PRD pode introduzir novos contextos/modulos (ex.: `matching`, `messaging`, `discovery`).
- Regras: verifique se novas regras mudam limites arquiteturais ou convencoes.
- Codigo: confirme se a estrutura real segue os limites (dependencia aponta para dentro).

2) Atualizacao das secoes criticas em `documentation/architecture.md`

- Visao geral: reafirme Clean/Hex e descreva o por que da separacao.
- Stack: mantenha alinhado ao `pyproject.toml` (Python/FastAPI/SQLAlchemy/uv/pytest/ruff/pyright/poe).
- Estrutura de diretorios: sincronize com `src/equiny/**` (core/database/rest/routers/validation/middlewares).
- Camadas e responsabilidades:
  - `core`: entidades, use cases, ports, erros de dominio; sem FastAPI/SQLAlchemy/HTTP/env.
  - `database`: models/mappers/repositorios; sem regra de negocio.
  - `rest`/`routers`: contrato HTTP, validacao, adaptacao; controller fino.
  - `validation`: DTOs/Pydantic; contrato de entrada/saida.
- Fluxo de request: atualize se houver novo middleware, DI ou alteracao no ciclo transacional.
- Inversao de dependencia: mostre como ports sao definidos no `core` e implementados em `database` e injetados em `rest`.

3) Validacao de consistencia

- Exemplos e nomes: devem refletir o codigo real do repo (nomes de pacotes, pastas, comandos).
- Diagramas ASCII: atualize apenas quando houver mudanca relevante (sem especular).
- Nao introduza camadas inexistentes (ex.: UI) no `equiny-server`.

Saida esperada:

- `documentation/architecture.md` atualizado, com mudancas rastreaveis (o que mudou e por que).

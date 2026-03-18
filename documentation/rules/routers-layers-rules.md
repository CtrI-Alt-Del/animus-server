# Regras da Camada Routers

> 💡 Use este documento ao criar ou revisar composicao de rotas HTTP em `src/animus/routers/`.

## Visao Geral

### Resumo da camada

| Aspecto | Diretriz |
|---|---|
| **Objetivo** | Compor a superficie de entrada HTTP da aplicacao. |
| **Papel arquitetural** | Organizar modulos, `prefix`, `tags` e hierarquia de rotas. |
| **Entrada principal** | `Controllers` vindos de `rest`. |
| **Saida principal** | Instancias de `APIRouter` prontas para o `app`. |

### Responsabilidades principais

- Agrupar endpoints por modulo e contexto funcional.
- Definir `prefix`, `tags` e inclusao de sub-routers.
- Registrar `controllers` da camada `rest` e entregar routers prontos para o `composition root`.

### Limites da camada

- `routers` deve priorizar composicao e organizacao, nao implementacao de regra de negocio.
- Routers HTTP nao devem conhecer `ORM`, `session`, providers ou detalhes de persistencia.
- O fluxo de `WebSocket` fica fisicamente em `src/animus/routers/`, mas segue regras adicionais de `documentation/rules/websocket-layer-rules.md`.

> 💡 Regra pratica: **`Router = composicao`** e **`Controller = endpoint`**.

## Estrutura de Diretorios Globais

### Mapa de pastas relevantes

| Caminho | Responsabilidade |
|---|---|
| `src/animus/routers/` | Ponto de composicao dos routers publicos da aplicacao. |
| `src/animus/routers/<context>/` | Routers HTTP agrupados por contexto, como `auth`, `profiling`, `conversation`, `matching`, `storage` e `docs`. |

### Regras de organizacao e nomeacao

- Cada contexto deve ter um router agregador e, quando fizer sentido, sub-routers por recurso.
- Routers devem seguir convencao `*Router` com metodo estatico `register() -> APIRouter`.
- Sub-routers devem existir para modularizar recursos, nao para repetir logica de endpoint.
- Nao especificar arquivos especificos, pois isso muda constantemente.

## Glossario arquitetural da camada

| Termo | Definicao |
|---|---|
| `Router` | Unidade de composicao que monta um conjunto de rotas e devolve `APIRouter`. |
| `Module Router` | Router principal de um contexto, responsavel por `prefix`, `tags` e sub-routers. |
| `Sub-router` | Router subordinado usado para separar recursos internos do mesmo modulo. |
| `register()` | Metodo padrao que cria o router, registra `controllers` e devolve a instancia final. |
| `include_router(...)` | Mecanismo de composicao do `FastAPI` para montar hierarquia de rotas. |

## Padroes de Projeto

### Padroes arquiteturais aceitos

- **`Router as Composition Unit`** para separar organizacao de modulo da implementacao de endpoint.
- **`Hierarchical Routing`** para decompor recursos por contexto e subcontexto.
- **`Explicit Registration`** para concentrar a montagem final no `composition root`.

### Como aplicar os padroes

- Um router de contexto deve criar `APIRouter`, definir `prefix` e `tags`, registrar `controllers` e incluir sub-routers quando necessario.
- Routers devem importar `controllers` da camada `rest` e registrar endpoints via `Controller.handle(router)`.
- O `app` deve incluir apenas routers prontos, mantendo a montagem global clara em um unico lugar.

### Quando evitar

- Nao criar sub-router quando isso apenas adiciona profundidade artificial.
- Nao transformar router em endpoint; se existir logica de transporte ou de negocio, ela pertence a `rest`.
- Nao espalhar inclusao global de routers em varios arquivos quando o `composition root` ja resolve o acoplamento.

## Regras de Integracao com Outras Camadas

### Mapa de integracao

| Camada | Como integra com `routers` | Regra |
|---|---|---|
| `rest` | Fornece `controllers` registrados via `handle(router)` | Router apenas compoe. |
| `app` | Inclui routers retornados por `register()` | O `app` e o `composition root` final. |
| `core` | Nao deve integrar diretamente | Regra de negocio nao entra em router HTTP. |

### Dependencias permitidas e proibidas

- Routers HTTP podem depender de `rest/controllers` e do `FastAPI` para composicao.
- Routers HTTP nao devem depender de `database`, `providers`, `pipes` de dados, `ORM` ou `UseCase` diretamente.

### Contratos de comunicacao

- O contrato entre `routers` e `rest` e o metodo de registro do `controller`, normalmente `handle(router)`.
- O contrato entre `routers` e `app` e o retorno de `register() -> APIRouter`.
- Fluxos especiais, como `WebSocket`, devem seguir o contrato proprio documentado na regra especifica da camada correspondente.

## Checklist Rapido para Novas Features na Camada

- [ ] O endpoint foi anexado ao router do contexto correto.
- [ ] `Prefix` e `tags` permanecem consistentes com o modulo.
- [ ] `Controllers` foram registrados sem mover logica de endpoint para o router.
- [ ] Sub-routers so foram introduzidos quando melhoram a composicao.
- [ ] O `app` inclui o router correto no `composition root`.
- [ ] Nenhum router HTTP conhece `session`, `repository` concreto ou provider externo.

## ✅ O que DEVE conter

- Routers por contexto com `register() -> APIRouter`.
- Composicao clara de `controllers` e sub-routers.
- `Prefix` e `tags` coerentes com o modulo.
- Exports publicos em `__init__.py` para estabilizar imports.
- Montagem global centralizada no `composition root`.

## ❌ O que NUNCA deve conter

- Regra de negocio, acesso a banco, `session handling` ou validacao de dominio em routers HTTP.
- `Controllers` inteiros embutidos no router por conveniencia.
- Dependencia direta de `UseCase`, `ORM` ou SDK externo em routers de modulo HTTP.
- Hierarquia de rota artificial sem ganho real de organizacao.

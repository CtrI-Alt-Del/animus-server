# Regras da Camada Pipes

> 💡 Use este documento ao criar ou revisar `dependency providers`, `guards` e montagem de dependencias reutilizaveis em `src/animus/pipes/`.

## Visao Geral

### Resumo da camada

| Aspecto | Diretriz |
|---|---|
| **Objetivo** | Centralizar a injecao de dependencias do `FastAPI`. |
| **Papel arquitetural** | Montar adaptadores concretos e checks reutilizaveis para `controllers` e fluxos realtime. |
| **Entrada principal** | `Request`, `WebSocket`, `Depends(...)` e recursos anexados ao estado da aplicacao. |
| **Saida principal** | `Repositories`, providers, `brokers`, `guards` e valores derivados prontos para consumo. |

### Responsabilidades principais

- Instanciar `repositories`, providers, `brokers` e recursos reutilizaveis para uso com `Depends(...)`.
- Encapsular acesso a `request.state` e `websocket.app.state`.
- Reaproveitar `guards` e validacoes de precondicao quando elas representam checks tecnicos ou de acesso recorrentes.

### Limites da camada

- `pipes` pode depender de `FastAPI`, `core`, `database`, `providers`, `pubsub` e outros adaptadores necessarios para montar dependencias.
- Nao deve virar o centro da regra de negocio nem substituir `UseCase` como orquestrador principal da feature.
- Deve continuar pequeno, previsivel e focado em fornecer dependencias, nao em montar respostas.

> ⚠️ Se um `pipe` esta executando a feature inteira, ele deixou de ser um `dependency provider`.

## Estrutura de Diretorios Globais

### Mapa de pastas relevantes

| Caminho | Responsabilidade |
|---|---|
| `src/animus/pipes/` | Modulo unico com arquivos `*_pipe.py` por assunto, como `auth`, `database`, `providers`, `pubsub`, `profiling`, `matching`, `conversation`, `storage` e `ai`. |

### Regras de organizacao e nomeacao

- Cada arquivo deve representar um assunto claro de injecao de dependencia ou precondicao reutilizavel.
- Classes devem seguir convencao `*Pipe` e expor metodos estaticos pequenos.
- Dependencias compostas devem reaproveitar outros `pipes` em vez de duplicar wiring.
- Nao especificar arquivos especificos, pois isso muda constantemente.

## Glossario arquitetural da camada

| Termo | Definicao |
|---|---|
| `Pipe` | `Dependency provider` usado para construir ou validar recursos antes da execucao principal. |
| `Guard` | `Pipe` que valida autenticacao, autorizacao ou precondicao de acesso. |
| `Adapter Factory` | `Pipe` que instancia implementacoes concretas e as devolve tipadas por contrato. |
| `Request State Accessor` | `Pipe` que recupera recursos anexados a `request.state` ou `app.state`. |
| `Fail-fast Validation` | Validacao tecnica na borda que interrompe cedo um input invalido. |

## Padroes de Projeto

### Padroes arquiteturais aceitos

- **`Dependency Injection`** via `Depends(...)`.
- **`Adapter Factory`** para `repositories`, providers, `brokers` e `workflows`.
- **`Guard Dependencies`** para autenticacao, resolucao de `owner` e checks recorrentes.
- **`Fail-fast`** para uploads invalidos ou credenciais ausentes.

### Como aplicar os padroes

- Um `pipe` deve devolver a dependencia pronta para consumo, preferencialmente tipada por `interface` do `core`.
- `Pipes` que dependem de `request` ou `websocket` devem ler recursos do estado da aplicacao sem espalhar esse detalhe para `controllers` e `routers`.
- `Guards` podem usar `repositories` ou `use_cases` pequenos para validar acesso, desde que isso continue sendo uma precondicao reutilizavel.
- Validacoes tecnicas de transporte, como upload de arquivo, podem falhar cedo no `pipe` para evitar dado invalido no dominio.

### Quando evitar

- Nao mover para `pipe` uma orquestracao que deveria estar em `UseCase`.
- Nao criar `pipe` apenas para renomear uma dependencia simples sem ganho de reuso ou isolamento.
- Nao retornar tipo concreto quando existe `interface` estavel do `core` disponivel.

## Regras de Integracao com Outras Camadas

### Mapa de integracao

| Camada | Como integra com `pipes` | Regra |
|---|---|---|
| `rest` | Consome `pipes` via `Depends(...)` | Deve simplificar wiring do endpoint. |
| `routers/websocket` | Consome `pipes` para auth e acesso a runtime compartilhado | Deve evitar acoplamento direto a infraestrutura quando houver provider reutilizavel. |
| `database` | Entra como implementacao concreta encapsulada | Nao deve vazar mais do que o necessario. |
| `providers` / `pubsub` | Entram como adaptadores concretos | Devem ser retornados preferencialmente por contrato do `core`. |

### Dependencias permitidas e proibidas

- `pipes` pode depender de `core`, `database`, `providers`, `pubsub` e mecanismos do `FastAPI`.
- `pipes` nao deve depender de `rest/controllers` para funcionar, nem carregar `APIRouter`, `response body` ou logica de serializacao.

### Contratos de comunicacao

- `Controllers` REST e fluxos `WebSocket` devem consumir `pipes` via `Depends(...)`.
- Sempre que houver `interface` do `core`, o retorno do `pipe` deve preferi-la ao adaptador concreto.
- Recursos em `request.state` ou `app.state` devem ter origem clara em `middleware` ou `lifespan`.

## Checklist Rapido para Novas Features na Camada

- [ ] O novo `pipe` resolve uma dependencia reutilizavel real ou uma precondicao recorrente.
- [ ] O retorno esta tipado por `interface` do `core` sempre que possivel.
- [ ] O `pipe` e pequeno, deterministico e nao monta resposta HTTP manualmente como responsabilidade principal.
- [ ] Se usa `request.state` ou `app.state`, o recurso existe e e gerenciado pelo ciclo correto.
- [ ] Se executa verificacao de acesso, continua sendo um `guard`, nao o fluxo principal da feature.
- [ ] O `controller` ou `router` ficou mais simples apos a introducao do `pipe`.

## ✅ O que DEVE conter

- `Dependency providers` claros para `repositories`, providers, `brokers`, `workflows` e `guards`.
- Encapsulamento de acesso a recursos de `request/app state`.
- Validacoes de precondicao pequenas e reutilizaveis na borda.
- Reaproveitamento entre endpoints e fluxos especiais.
- Retorno por `interface` do `core` sempre que aplicavel.

## ❌ O que NUNCA deve conter

- Orquestracao principal da feature, regra de negocio complexa ou `branching` de dominio.
- Controle manual de transacao, acesso direto a `APIRouter` ou construcao de payload de resposta como responsabilidade principal.
- Dependencias escondidas sem `middleware`, `lifespan` ou origem explicita.
- `Pipe` que existe apenas para mover complexidade sem melhorar reuso ou clareza.

# Regras da Camada Core

> 💡 Use este documento ao criar ou revisar regras de negocio, `entities`, `structures`, `DTOs`, `events`, `interfaces` e `use_cases` em `src/animus/core/`.

## Visao Geral

### Resumo da camada

| Aspecto | Diretriz |
|---|---|
| **Objetivo** | Concentrar a regra de negocio pura da aplicacao em `src/animus/core/`. |
| **Papel arquitetural** | Ser o centro da arquitetura, sem depender de transporte, persistencia ou SDKs externos. |
| **Entrada principal** | `use_cases` e tipos de dominio consumidos por camadas externas. |
| **Saida principal** | `DTOs`, `responses`, `events`, `errors` e `interfaces` estaveis para o restante do sistema. |

### Responsabilidades principais

- Modelar `entities`, `structures`, `DTOs`, `events`, `errors` e `responses` compartilhadas.
- Definir contratos de integracao por meio de `interfaces` de repositorio, provider, `broker` e `workflow`.
- Orquestrar fluxos de negocio em `use_cases`, mantendo a decisao funcional dentro do dominio.

### Limites da camada

- Pode depender apenas de tipos do proprio `core` e de bibliotecas genericas de modelagem e validacao.
- Nao deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest`, `request`, `response`, `Env` ou detalhes de sessao/transacao.
- Deve expor contratos claros para `rest`, `routers`, `pipes`, `database`, `providers`, `pubsub` e `websocket`.

> ⚠️ Se um arquivo do `core` conhece detalhes de HTTP, banco ou fila, a direcao de dependencia foi quebrada.

## Estrutura de Diretorios Globais

### Mapa de pastas relevantes

| Caminho | Responsabilidade |
|---|---|
| `src/animus/core/shared/` | Tipos, abstractions, decorators, `interfaces`, `errors` e `responses` reutilizaveis. |
| `src/animus/core/auth/` | Dominio e fluxos de autenticacao e conta. |
| `src/animus/core/intake/` | Dominio e fluxos de peticoes, analises, precedentes e pastas. |
| `src/animus/core/notification/` | Contratos e fluxos de notificacao por email e `push`. |

### Regras de organizacao e nomeacao

- A organizacao principal deve seguir `bounded contexts`, e nao uma divisao global por tipo tecnico.
- Cada contexto deve preservar a estrutura `domain/`, `interfaces/` e `use_cases/`.
- `__init__.py` deve expor apenas contratos publicos e imports estaveis.
- Nao especificar arquivos especificos, pois isso muda constantemente.

## Glossario arquitetural da camada

| Termo | Definicao |
|---|---|
| `Entity` | Objeto de dominio com identidade estavel e comportamento proprio. |
| `Structure` | Objeto orientado a valor, sem identidade propria, usado para conceitos pequenos e reutilizaveis. |
| `Dto` | Contrato de dados para cruzar fronteiras entre camadas e `use_cases`. |
| `UseCase` | Porta de entrada da aplicacao para um fluxo de negocio com `execute(...)`. |
| `Interface` | Contrato abstrato implementado fora do `core`. |
| `Event` | Fato de dominio usado para acionar efeitos assincronos ou realtime. |
| `Response` | Estrutura reutilizavel de saida, como lista e paginacao. |

## Padroes de Projeto

### Padroes arquiteturais aceitos

- **`Clean Architecture` + `Hexagonal Architecture`** para manter dependencias apontando para dentro.
- **`Use Case`** como orquestrador de fluxo.
- **`Ports and Adapters`** para repositorios, cache, autenticacao, `storage`, notificacao e `broker`.
- **Modelagem tatica de dominio** com `Entity`, `Structure`, `Dto`, `Event` e `Domain Error`.

### Como aplicar os padroes

- Todo fluxo novo deve nascer em um `UseCase` que recebe dependencias por contrato e retorna tipos claros.
- Regras de consistencia devem viver em `entities`, `structures` e `errors`, nao em controllers, jobs ou repositories.
- `Events` devem representar fatos reais do dominio, nao atalhos tecnicos para integrar camadas.
- Itens compartilhados devem entrar em `shared/` apenas quando houver reuso real entre contextos.

### Quando evitar

- Nao criar `UseCase` apenas para repassar dados sem decisao ou orquestracao relevante.
- Nao mover validacao de transporte ou serializacao para tipos de dominio.
- Nao transformar `shared/` em deposito de utilitarios genericos sem fronteira clara.

## Regras de Integracao com Outras Camadas

### Mapa de integracao

| Camada externa | Como integra com o `core` | Regra |
|---|---|---|
| `rest` | Importa `UseCase`, `Dto`, `Response` e `Error` | Deve apenas adaptar HTTP e delegar. |
| `websocket` | Importa `UseCase`, `Event`, `Dto` e `Error` | Deve tratar transporte realtime e delegar regra. |
| `pubsub` | Importa `UseCase`, `Event` e `interfaces` | Deve orquestrar eventos sem mover regra de negocio. |
| `database` | Implementa `interfaces` e mapeia tipos do dominio | Nunca deve ser importado pelo `core`. |
| `providers` | Implementa `interfaces` do `core` | Deve ficar totalmente fora do dominio. |

### Dependencias permitidas e proibidas

- `core` pode depender de `core/shared` e, com criterio, de contratos de outros contextos internos.
- `core` nao deve depender de `rest`, `routers`, `pipes`, `database`, `providers`, `pubsub` ou SDKs externos.

### Contratos de comunicacao

- A comunicacao com camadas externas deve acontecer por `DTOs`, `responses`, `events`, `errors` e `interfaces` do proprio `core`.
- Implementacoes concretas devem respeitar exatamente a assinatura e a semantica publicadas pelo dominio.
- O `core` nao define `status code`, formato HTTP de erro ou envelope de transporte.

## Checklist Rapido para Novas Features na Camada

- [ ] O contexto respeita a divisao `domain/`, `interfaces/` e `use_cases/`.
- [ ] O fluxo principal esta em um `UseCase` com `execute(...)`.
- [ ] Dependencias externas entram por `interfaces`, nunca por classes concretas.
- [ ] `Entities` e `structures` concentram invariantes relevantes.
- [ ] `DTOs` e `events` foram criados porque existe uma fronteira real para cruzar.
- [ ] Nenhum import do `core` aponta para framework, ORM, fila, cache ou variavel de ambiente.

## ✅ O que DEVE conter

- Tipos de dominio claros, com responsabilidade bem definida.
- `UseCase` como ponto de entrada para fluxos de negocio.
- `Interfaces` estaveis para repositorios, providers, `brokers` e `workflows`.
- `Events`, `responses` e `errors` alinhados ao comportamento real do dominio.
- Nomes consistentes como `*UseCase`, `*Dto`, `*Error`, `*Repository`, `*Provider` e `*Event`.

## ❌ O que NUNCA deve conter

- Framework web, ORM, cliente HTTP, SDK de fila, cache, `push` ou `storage` dentro do dominio.
- `SQL`, `commit`, `rollback`, leitura de `request.state` ou acesso direto a `Env`.
- Serializacao HTTP, controle de `status code` ou detalhes de transporte.
- `DTO` com comportamento de dominio complexo ou `entity` atuando como `schema` de borda.
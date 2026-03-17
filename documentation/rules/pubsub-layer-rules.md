# Regras da Camada PubSub

> 💡 Use este documento ao criar ou revisar publicacao de eventos, `jobs`, `brokers` e fluxos assincronos em `src/equiny/pubsub/`.

## Visao Geral

### Resumo da camada

| Aspecto | Diretriz |
|---|---|
| **Objetivo** | Orquestrar processamento assincrono e entrega orientada a eventos. |
| **Papel arquitetural** | Ser a borda de eventos do sistema, integrando `core`, `Inngest`, `Redis` e runtime realtime. |
| **Entrada principal** | `Events` do dominio publicados por contratos como `Broker`. |
| **Saida principal** | `Jobs`, relays e publicacoes para `Inngest`, `Redis` e fluxos de notificacao/realtime. |

### Responsabilidades principais

- Registrar funcoes do `Inngest` para jobs de `background` e integracoes assincronas.
- Implementar `brokers` concretos para publicar `events` do dominio em `Inngest` ou `Redis`.
- Executar `jobs`, relays e handlers que consomem eventos e delegam o trabalho real ao `core` ou ao runtime de socket.

### Limites da camada

- `pubsub` e uma camada de orquestracao e transporte de eventos, nao de regra de negocio.
- Pode abrir `session`, montar adaptadores concretos e acionar `UseCase`, mas nao deve concentrar decisao funcional.
- O `core` deve falar com esta camada apenas por `interfaces`, como `Broker`, e por `events` de dominio.

> ⚠️ Se um `job` esta resolvendo regra de negocio de ponta a ponta, a fronteira entre `pubsub` e `core` foi quebrada.

## Estrutura de Diretorios Globais

### Mapa de pastas relevantes

| Caminho | Responsabilidade |
|---|---|
| `src/equiny/pubsub/inngest/` | Integracao com runtime do `Inngest` e `broker` usado para eventos assincronos. |
| `src/equiny/pubsub/inngest/jobs/` | `Jobs` de `background` organizados por contexto. |
| `src/equiny/pubsub/redis/` | Runtime de `pub/sub` para entrega realtime e disparo de jobs leves. |
| `src/equiny/pubsub/redis/brokers/` | `Brokers` especializados por contexto para fan-out via `Redis`. |
| `src/equiny/pubsub/redis/jobs/` | `Jobs` acionados a partir de mensagens consumidas do `Redis`. |

### Regras de organizacao e nomeacao

- `Jobs` devem ser agrupados por contexto e seguir convencao `*Job`.
- `Brokers` concretos devem explicitar a tecnologia ou o contexto quando isso reduzir ambiguidade.
- A camada deve separar claramente runtime de transporte de `jobs` e `brokers`.
- Nao especificar arquivos especificos, pois isso muda constantemente.

## Glossario arquitetural da camada

| Termo | Definicao |
|---|---|
| `Broker` | Adaptador concreto que traduz um `event` do dominio para o mecanismo de publicacao adequado. |
| `Job` | Unidade assincrona que consome um `event`, valida `payload` e delega para `UseCase` ou runtime especializado. |
| `Inngest Function` | Handler registrado no `Inngest` para fluxos de `background`. |
| `Redis PubSub` | Runtime de distribuicao de mensagens para sockets e jobs leves. |
| `Event Relay` | Fluxo que recebe um `event` e o encaminha para notificacao, socket ou processamento posterior. |

## Padroes de Projeto

### Padroes arquiteturais aceitos

- **`Event-Driven Architecture`** para processamento desacoplado de efeitos colaterais.
- **`Ports and Adapters`** para publicar `events` sem vazar detalhes de `Inngest` ou `Redis` para o `core`.
- **`Job as Orchestrator`** para validar `payload`, abrir recursos e chamar `UseCase`.
- **`Broker` especializado por contexto** quando o fan-out depende do tipo de `event`.

### Como aplicar os padroes

- `Events` publicados pelo dominio devem chegar ao `pubsub` como classes do `core`, nao como dicionarios anonimos.
- Cada `job` deve validar `payload`, montar `repositories/providers` necessarios e chamar um fluxo do `core` ou runtime especializado.
- `Redis` deve ser usado para entrega realtime e disparo de jobs leves; `Inngest` deve ser usado para `background` e integracoes assincronas estruturadas.
- Efeitos colaterais devem ser centralizados no handler correto, mantendo responsabilidade unica por unidade.

### Quando evitar

- Nao criar `job` para trabalho que precisa ser sincrono com a `request` ou com a transacao corrente.
- Nao usar `broker` como atalho para esconder regra de negocio que deveria estar em `UseCase`.
- Nao publicar direto no SDK dentro de `core`, `database` ou `rest` quando existe `interface` de `Broker` adequada.

## Regras de Integracao com Outras Camadas

### Mapa de integracao

| Camada | Como integra com `pubsub` | Regra |
|---|---|---|
| `core` | Publica `events` e `interfaces` | Nao conhece SDK nem runtime de transporte. |
| `rest` | Pode obter `brokers` via `pipes` | Publica evento sem conhecer a implementacao concreta. |
| `websocket` | Pode publicar ou consumir efeitos via `Redis` | Deve manter o `core` isolado do transporte realtime. |
| `database` | Pode ser usado por `jobs` que montam o proprio escopo transacional | Nao deve receber regra de negocio deslocada. |

### Dependencias permitidas e proibidas

- `pubsub` pode depender de `core`, `database`, `providers`, runtime de `websocket` e SDKs de `Inngest`/`Redis`.
- `pubsub` nao deve depender de `rest/controllers` ou de composicao de routers para executar seus `jobs`.

### Contratos de comunicacao

- A publicacao de eventos deve acontecer por `interfaces` do `core`, principalmente `Broker`.
- `Payloads` consumidos por `jobs` devem refletir fielmente o contrato do `event` publicado.
- `Jobs` e `brokers` devem devolver controle para a borda sem impor detalhes de transporte ao `core`.

## Checklist Rapido para Novas Features na Camada

- [ ] O `event` novo ja existe ou foi definido no `core` antes da implementacao do `job` ou `broker`.
- [ ] O `job` esta no contexto correto e valida `payload` de forma explicita.
- [ ] O handler monta apenas as dependencias minimas necessarias.
- [ ] O fluxo escolheu corretamente entre `Inngest` e `Redis` conforme a natureza do processamento.
- [ ] O comportamento e seguro para reexecucao ou tolerante a reentrega.
- [ ] Nenhum `job` concentra regra de negocio principal.

## ✅ O que DEVE conter

- `Brokers` concretos para publicacao de `events`.
- `Jobs` e handlers organizados por contexto e por runtime.
- Validacao explicita de `payload` e montagem objetiva de dependencias.
- Escolha intencional entre `Inngest` e `Redis`.
- Unidades assincronas pequenas, previsiveis e focadas em uma responsabilidade.

## ❌ O que NUNCA deve conter

- Regra de negocio central implementada dentro de `jobs` ou `brokers`.
- Publicacao direta com SDK a partir de `core` ou `controllers` quando existe `Broker`.
- Dependencia de `request`, `request.state` ou `response object` dentro de `jobs`.
- Divergencia entre `payload` publicado e `payload` esperado pelo consumidor.

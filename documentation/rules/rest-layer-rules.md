# Regras da Camada REST

> 💡 Use este documento ao criar ou revisar `controllers`, `middlewares`, contratos HTTP e integracoes da API em `src/animus/rest/`.

## Visao Geral

### Resumo da camada

| Aspecto | Diretriz |
|---|---|
| **Objetivo** | Expor a API HTTP e adaptar `request` para fluxos do `core`. |
| **Papel arquitetural** | Ser a borda de entrada HTTP da aplicacao. |
| **Entrada principal** | `request`, `query params`, `path params`, `body`, `headers` e `dependencies`. |
| **Saida principal** | Respostas HTTP baseadas em `DTOs`, `responses` e `schemas` estaveis. |

### Responsabilidades principais

- Implementar `controllers` por contexto, com endpoints finos e focados em transporte.
- Declarar `middlewares` de `request` para `session`, clientes externos e concerns transversais.
- Traduzir validacoes, erros de dominio e dependencias injetadas em uma experiencia HTTP previsivel.

### Limites da camada

- Pode depender de `FastAPI`, `pipes`, `validation`, `core` e contratos de resposta da aplicacao.
- Nao deve conter regra de negocio, `query SQL`, modelagem ORM ou acoplamento forte a implementacoes concretas de infraestrutura.
- Deve agir como borda de entrada: validar, adaptar, delegar e responder.

> ⚠️ Se um `controller` esta decidindo regra de negocio, a borda ficou gorda demais.

## Estrutura de Diretorios Globais

### Mapa de pastas relevantes

| Caminho | Responsabilidade |
|---|---|
| `src/animus/rest/controllers/` | Agrupamento de `controllers` por contexto funcional. |
| `src/animus/rest/controllers/<context>/` | Endpoints HTTP do contexto, como `auth`, `profiling`, `matching`, `conversation`, `storage` e `docs`. |
| `src/animus/rest/middlewares/` | `Middlewares` por `request` para sessao e clientes anexados ao estado da aplicacao. |

### Regras de organizacao e nomeacao

- Cada endpoint deve viver em um `controller` dedicado e no contexto correto.
- `Controllers` devem seguir convencao `*Controller` e expor registro por `handle(router)`.
- `Middlewares` devem encapsular infraestrutura transversal, nao regra de negocio.
- Nao especificar arquivos especificos, pois isso muda constantemente.

## Glossario arquitetural da camada

| Termo | Definicao |
|---|---|
| `Controller` | Adaptador HTTP que recebe `request`, resolve dependencias e delega ao `UseCase`. |
| `Middleware` | Componente transversal executado por `request` para abrir ou anexar recursos. |
| `Depends` | Mecanismo de injecao do `FastAPI` para montar `repositories`, providers, `guards` e dependencias reutilizaveis. |
| `response_model` | Contrato de saida do endpoint; deve refletir `DTOs`, `responses` ou `schemas`, nunca `ORM`. |
| `Schema` | Estrutura de validacao e serializacao usada na borda HTTP. |

## Padroes de Projeto

### Padroes arquiteturais aceitos

- **`Thin Controller`** para separar transporte de regra de negocio.
- **Fluxo `Schema -> DTO -> UseCase -> DTO/Response`** como caminho padrao.
- **`Dependency Injection`** via `Depends(...)` e `pipes`.
- **`Middleware per Request`** para recursos compartilhados durante o ciclo HTTP.

### Como aplicar os padroes

- Todo `controller` deve registrar rota, declarar `status_code` e `response_model`, resolver dependencias e chamar `UseCase.execute(...)`.
- Conversoes de entrada devem acontecer na borda, preferencialmente via `schema` ou dependencia tipada.
- `Repositories`, `brokers` e providers devem entrar por `pipes`, evitando instanciacao manual repetida.
- `Errors` de dominio devem subir para os `handlers` globais da aplicacao e ser traduzidos fora do `core`.

### Quando evitar

- Nao criar `controller` generico demais que misture multiplas responsabilidades.
- Nao usar `middleware` para regra de negocio; ele existe para infraestrutura e concerns transversais.
- Nao transformar o endpoint em `composition root` pesado quando um `pipe` resolve a dependencia de forma mais limpa.

## Regras de Integracao com Outras Camadas

### Mapa de integracao

| Camada | Como integra com `rest` | Regra |
|---|---|---|
| `core` | `controllers` importam `UseCase`, `DTO`, `Response` e `Error` | Deve receber apenas dados adaptados da borda. |
| `validation` | Fornece `schemas` e conversao de entrada | Deve validar transporte antes do `UseCase`. |
| `pipes` | Entrega `repositories`, providers, `guards` e `brokers` | Deve simplificar o wiring do endpoint. |
| `routers` | Registra `controllers` por contexto | Nao deve absorver logica de endpoint. |

### Dependencias permitidas e proibidas

- `rest` pode depender de `core`, `validation`, `pipes` e mecanismos do `FastAPI`.
- `rest` nao deve depender diretamente de `models` ORM, `query SQL` ou SDKs que deveriam entrar por `pipes`.

### Contratos de comunicacao

- Entrada HTTP deve ser validada por `schemas`, parametros tipados ou `dependencies` equivalentes.
- Saida HTTP deve usar `DTOs`, `responses` ou `schemas` de saida.
- `Repositories`, providers e `brokers` devem chegar ao `controller` por interfaces ou dependencias encapsuladas em `pipes`.

## Checklist Rapido para Novas Features na Camada

- [ ] O endpoint novo vive no contexto correto em `controllers/<context>/`.
- [ ] A rota declara `status_code`, contrato de entrada e `response_model` quando aplicavel.
- [ ] As dependencias entram por `Depends(...)` e `pipes`.
- [ ] O `controller` converte dados para `DTO` ou tipo esperado antes de chamar o `UseCase`.
- [ ] O fluxo de erro esta coberto por `handlers` globais ou excecoes coerentes com a borda.
- [ ] Nenhum endpoint manipula `Session`, `commit`, `rollback` ou `SQL` diretamente.

## ✅ O que DEVE conter

- `Controllers` finos, rotas explicitas e contratos HTTP claros.
- Injecao de dependencias por `Depends(...)` e `pipes`.
- `Middlewares` para recursos por `request` e adaptacao transversal.
- Conversao de entrada antes do `core`.
- `Handlers` globais como ponto de traducao de erro para HTTP.

## ❌ O que NUNCA deve conter

- Regra de negocio, `query SQL`, acesso direto a `ORM` ou controle manual de transacao dentro do endpoint.
- Contrato de resposta baseado em `Model` ORM.
- Instanciacao espalhada de adaptadores concretos que poderiam ser reutilizados via `pipes`.
- `Middleware` carregando fluxo de feature em vez de concern transversal.

### ❌ Anti-padrão: Nomear Body com contexto em vez de `_Body`

**O que foi feito:**
Em `controllers` HTTP, o schema de body foi nomeado com prefixo do endpoint (ex: `SignUpBody`) em vez do padrao local `_Body`.

**Por que está errado:**
Quebra a convencao adotada para handlers de endpoint do projeto, aumenta variacao de nomenclatura sem ganho funcional e dificulta leitura rapida do arquivo quando ha um unico body por controller.

**O que deve ser feito:**
Para controllers que recebem body, usar `_Body` como nome da classe local do schema de entrada e manter o nome do caso de uso no `*Controller`.

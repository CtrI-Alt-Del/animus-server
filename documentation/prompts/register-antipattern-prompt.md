---
description: Registra um anti-padrao cometido durante a implementacao no doc de rules da camada correspondente, alinhado a arquitetura e as regras reais do Animus Server.
---

# Prompt: Registrar Anti-padrao

## Objetivo

Documentar um erro de implementacao cometido durante a execucao no arquivo de rules mais adequado do projeto, de forma clara, acionavel e aderente a arquitetura atual do Animus Server, para evitar reincidencia em sessoes futuras.

Antes de registrar o anti-padrao, leia obrigatoriamente:

- o documento de visao geral do dominio no Confluence via MCP Atlassian (se o link direto falhar, busque pela arquitetura ou pelos requisitos do projeto no espaco do Animus)
- `documentation/architecture.md`
- `documentation/rules/rules.md`
- `documentation/tooling.md`

Use o MCP Serena para navegar pela codebase e confirmar caminhos, nomes e contexto real da camada afetada.

---

## Entrada

- **Descricao do anti-padrao:** o que foi feito de errado, em qual contexto e, se houver, o trecho de codigo ou comportamento incorreto.
- **Camada afetada** (opcional): se ja souber, informe a camada (`core`, `rest`, `routers`, `pipes`, `database`, `pubsub`, `tests`, `code-conventions`). Se nao souber, identifique com base na arquitetura e no doc de rules.
- **Arquivos envolvidos** (opcional): paths reais afetados pela implementacao incorreta.

---

## Diretrizes de Execucao

### 1. Entender o contexto do erro

- Leia a descricao recebida e identifique qual limite arquitetural foi quebrado.
- Confirme a camada olhando para os paths reais do projeto e para as responsabilidades descritas em `documentation/architecture.md`.
- Se o anti-padrao envolver mais de uma camada, registre em todos os docs relevantes.
- Nao invente dominio, camada ou arquivo que nao existam no repositorio atual.

### 2. Identificar o doc de rules correto

Leia `documentation/rules/rules.md` e selecione o arquivo de rules correspondente:

| Contexto do anti-padrao | Arquivo |
| --- | --- |
| Entidades, DTOs, interfaces (ports), use cases e limites de dominio | `documentation/rules/core-layer-rules.md` |
| Controllers HTTP, adaptacao de request/response e contratos REST | `documentation/rules/rest-layer-rules.md` |
| Composicao de rotas, prefixos, tags e registro de endpoints | `documentation/rules/routers-layers-rules.md` |
| Dependency providers (`Depends`), injecao de interfaces e recursos de request | `documentation/rules/pipes-layer-rules.md` |
| Models SQLAlchemy, mappers e repositorios concretos | `documentation/rules/database-layer-rules.md` |
| Eventos, jobs assincronos e orquestracao com broker/Inngest | `documentation/rules/pubsub-layer-rules.md` |
| Nomeacao, imports e convencoes transversais | `documentation/rules/code-conventions-rules.md` |
| Estrategia e padroes de teste (geral) | `documentation/rules/testing-rules.md` |
| Testes de controllers | `documentation/rules/controllers-testing-rules.md` |
| Testes de use cases | `documentation/rules/use-cases-testing-rules.md` |
| Testes de jobs/eventos | `documentation/rules/jobs-testing-rules.md` |

Regras de mapeamento:

- Se o erro for de dependencia invertida ou acoplamento entre camadas, registre em todas as camadas impactadas e, quando fizer sentido, tambem em `documentation/rules/code-conventions-rules.md`.
- Se o erro estiver em teste, mas refletir uma violacao arquitetural do codigo produtivo, registre no doc de testes e no doc da camada produtiva afetada.
- Se o problema for estritamente de execucao de testes, prefira o documento de teste especifico (`controllers-testing-rules.md`, `use-cases-testing-rules.md` ou `jobs-testing-rules.md`).

### 3. Validar o documento antes de editar

- Abra o arquivo de rules escolhido e preserve o estilo textual existente.
- Se o arquivo tiver as secoes `## ✅ O que DEVE conter` e `## ❌ O que NUNCA deve conter`, atualize essas secoes.
- Se o arquivo nao tiver essas secoes (ex.: regras de teste especializadas ou convencoes), adicione o registro no bloco mais equivalente, preservando a estrutura atual do documento.
- O registro do anti-padrao deve atualizar secoes existentes, sem criar nova secao dedicada para anti-padroes.
- Nunca remova nem reescreva entradas existentes para encaixar o novo conteudo.

### 4. Traduzir o anti-padrao para regras acionaveis

Em vez de criar um bloco narrativo novo, converta o aprendizado em dois tipos de ajuste no documento:

- uma entrada positiva em `## ✅ O que DEVE conter`, descrevendo a pratica correta que passa a ser obrigatoria
- uma entrada negativa em `## ❌ O que NUNCA deve conter`, descrevendo explicitamente o erro que nao pode se repetir

Regras de escrita:

- As novas entradas devem ser bullets curtos, especificos e verificaveis em code review.
- O bullet em `## ✅ O que DEVE conter` deve orientar a implementacao correta.
- O bullet em `## ❌ O que NUNCA deve conter` deve registrar o anti-padrao concreto observado.
- Seja especifico sobre o erro real; nao transforme um caso concreto em uma regra excessivamente generica.
- Use caminhos, nomes de classes, arquivos e camadas reais do projeto quando isso ajudar.
- Explique implicitamente o limite quebrado ao escrever os bullets, por exemplo:
  - `rest` deve delegar regra de negocio para `UseCase` no `core`
  - `core` nunca deve depender de FastAPI, SQLAlchemy, Redis, Inngest ou SDKs concretos
  - `database` nao deve concentrar regra de negocio nem controlar transacao manualmente
  - `pipes` deve apenas prover dependencias e nao conter logica de negocio
  - `routers` deve apenas compor e registrar endpoints
  - `pubsub` deve orquestrar evento/job sem mover regra de dominio para fora do `core`
  - Testes nao devem acoplar detalhes indevidos da implementacao

### 5. Inserir no doc de rules

- Adicione os novos bullets ao final das secoes `## ✅ O que DEVE conter` e `## ❌ O que NUNCA deve conter`.
- Mantenha a linguagem normativa do documento (`deve`, `nao deve`, `pode` quando apropriado).
- Preserve a coerencia com a arquitetura em camadas do projeto:
  - `src/animus/core/` define dominio, contratos e use cases
  - `src/animus/rest/` expoe borda HTTP (controllers e middlewares)
  - `src/animus/routers/` compoe e registra rotas por contexto
  - `src/animus/pipes/` fornece dependencias para `Depends(...)`
  - `src/animus/database/` implementa persistencia e mapeamento
  - `src/animus/pubsub/` orquestra jobs/eventos assincronos
  - `src/animus/validation/` centraliza schemas e conversao de entrada/saida
  - `src/animus/providers/` encapsula integracoes externas de infraestrutura
- Nao use exemplos herdados de outros projetos, stacks ou estruturas que nao existam no Animus Server.

### 6. Confirmar o resultado

Depois de inserir:

- informe o caminho do arquivo atualizado
- exiba somente os bullets adicionados
- confirme, em uma frase curta, qual recorrencia futura esse registro ajuda a evitar

---

## Saida Esperada

- Um ou mais docs em `documentation/rules/` atualizados com o novo anti-padrao na secao mais apropriada.
- Exibicao dos bullets inseridos para confirmacao visual.
- Confirmacao objetiva do path atualizado.

---

## Restricoes

- Nao remova, resuma ou reescreva entradas existentes.
- Nao invente arquivos de rules, camadas ou paths que nao existam no projeto.
- Nao use referencias de outra arquitetura que nao a atual do Animus Server.
- Nao registre problemas hipoteticos; documente apenas o erro efetivamente observado.
- Nao crie nova secao para o anti-padrao; atualize as secoes existentes mais equivalentes no documento escolhido.
- Se faltar contexto suficiente para identificar a camada, o arquivo correto ou a correcao recomendada, use a tool `question` antes de editar.

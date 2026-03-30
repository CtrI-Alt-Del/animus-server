---
description: Prompt para concluir uma spec com validacao final, atualizacao de documentacao e geracao de resumo estruturado para PR.
---

# Prompt: Conclude Spec

**Objetivo:** Finalizar e consolidar a implementacao de uma Spec tecnica no
`animus-server`, garantindo que o codigo esteja polido, documentado e validado
no contexto da arquitetura em camadas do projeto — produzindo ao final um
checklist de validacao, os documentos atualizados e um resumo estruturado para
PR.

---

## Entradas Esperadas

- **Spec Tecnica:** O documento que guiou a implementacao
  (`documentation/features/<modulo>/specs/<nome>-spec.md`), injetado
  como caminho para o arquivo no contexto.

---

## Fase 1 — Verificacao

Esta fase e analitica e deve ser concluida antes de qualquer atualizacao de
documento.

**1.1 Testes**

Execute `poe test` na raiz do projeto. Todos os testes — novos e
existentes — devem estar passando. Caso algum falhe, interrompa e reporte.

Se a Spec impactar apenas uma parte do projeto, voce pode executar primeiro um
escopo mais especifico para feedback rapido com `uv run pytest <alvo>` (por
exemplo, um arquivo em `tests/core/...` ou `tests/rest/...`), mas a validacao
final deve considerar `poe test`.

> Falhas pre-existentes fora do escopo da Spec devem ser sinalizadas
> explicitamente, indicando que sao regressões anteriores e nao introduzidas
> pela implementacao atual.

**1.1.1 Cobertura de Testes**

> ⚠️ **Escopo obrigatorio:** Somente sao permitidos testes de **use cases**,
> **controllers** e **jobs**. Testes de outras camadas (database, providers,
> pipes, routers, validation, etc.) estao **fora do escopo** e **nao devem ser
> criados** ou modificados. Qualquer item fora desse escopo identificado no diff
> deve ser ignorado no relatorio de cobertura.

Com base no diff injetado no contexto e nas regras em
`documentation/rules/testing-rules.md`,
`documentation/rules/use-cases-testing-rules.md`,
`documentation/rules/controllers-testing-rules.md` e
`documentation/rules/jobs-testing-rules.md`, verifique se os novos
**use cases**, **controllers** e **jobs** introduzidos ou modificados pela Spec
possuem testes correspondentes.

Considere como caminhos criticos que exigem cobertura (respeitando o escopo acima):

- **Use cases** em `src/animus/core` — logica de negocio, regras de dominio, excecoes e edge cases
- **Controllers** em `src/animus/rest` — traducao de contrato HTTP, status codes, validacoes e delegacao ao core
- **Jobs** em `src/animus/pubsub/inngest/jobs` — evento consumido, payload processado, delegacao e side effect observavel

Ao final desta etapa, produza um relatorio de cobertura no seguinte formato:
```markdown
## Cobertura de Testes

- [x] <Use Case / Controller / Job A> — coberto em `tests/caminho/do/test_arquivo.py`
- [x] <Use Case / Controller / Job B> — coberto em `tests/caminho/do/test_arquivo.py`
- [ ] <Use Case / Controller / Job C> — **sem cobertura** (detalhe o que esta faltando)
```

**1.1.2 Criacao de Testes para Componentes sem Cobertura**

Caso existam itens sem cobertura no relatorio acima, acione **subagents em
paralelo** — um por componente sem cobertura — para cria-los simultaneamente,
reduzindo o tempo total de execucao desta fase.

> ⚠️ Lembre-se: apenas **use cases**, **controllers** e **jobs** devem ter
> testes criados. Nao solicite aos subagents a criacao de testes para nenhuma
> outra camada.

Cada subagent deve receber como contexto:

- O prompt `documentation/prompts/create-tests-prompt.md` como instrucao base.
- O caminho real do componente sem cobertura (`src/animus/...`) que e responsabilidade exclusiva daquele subagent.
- O caminho da Spec tecnica, para referencia de contratos e comportamentos esperados.

> Os subagents sao responsaveis por criar os arquivos de teste, seguir as regras de
> nomenclatura e estrutura do projeto, e garantir que `poe test` passe ao
> final. Execute-os **em paralelo** e aguarde a conclusao de **todos** antes de
> avancar para a Fase 2. Nao avance enquanto qualquer subagent reportar falhas.

**1.2 Lint e Formatacao**

Execute `poe codecheck` na raiz do projeto. O comando roda os checks de Ruff e
validacoes configuradas no repositorio. Nenhum warning ou erro deve restar.
Caso existam, liste-os explicitamente e corrija antes de prosseguir.

**1.3 Checagem de Tipos**

Execute `poe typecheck` na raiz do projeto. O Pyright deve retornar zero erros.
Liste qualquer violacao de tipo explicitamente e corrija antes de prosseguir.

**1.4 Cobertura de Requisitos**

Com base no diff real injetado no contexto, compare cada componente descrito na
Spec (secoes "O que deve ser criado" e "O que deve ser modificado") contra o
codigo implementado. Ao final desta etapa, produza um **checklist de validacao**
no seguinte formato:
```markdown
## Checklist de Validacao

- [x] <Requisito A> — implementado em `src/animus/...` ou `tests/...`
- [x] <Requisito B> — implementado em `src/animus/...` ou `tests/...`
- [ ] <Requisito C> — **ausente ou incompleto** (detalhe o gap)
```

**1.5 Conformidade Arquitetural e de Padroes**

Leia `documentation/rules/rules.md` para identificar quais documentos de regras
sao acionados pelas camadas impactadas pela Spec. Em seguida, leia cada um dos
docs relevantes e valide o codigo implementado contra eles.

Verifique obrigatoriamente os documentos acionados pelas camadas impactadas.
Em geral, os mais comuns no `animus-server` sao:

- `documentation/rules/core-layer-rules.md` — `src/animus/core` puro: sem
  dependencia de framework, banco, HTTP ou SDK externo
- `documentation/rules/database-layer-rules.md` — persistencia, mapeamento e
  repositorios SQLAlchemy sem regra de negocio indevida
- `documentation/rules/rest-layer-rules.md` — controllers HTTP finos,
  traduzindo contrato e delegando comportamento
- `documentation/rules/routers-layers-rules.md` — composicao de routers por
  contexto, sem endpoint direto na classe de router
- `documentation/rules/pipes-layer-rules.md` — dependency providers sem regra
  de negocio
- `documentation/rules/layer-rules.md` — jobs/eventos finos e
  idempotentes, delegando comportamento ao `core`
- `documentation/rules/testing-rules.md` — indice e estrategia geral de testes
- `documentation/rules/code-conventions-rules.md` — nomenclatura, imports,
  organizacao de modulos e tooling obrigatorio

Para cada regra violada, reporte:

- **Arquivo:** caminho relativo do arquivo com o desvio
- **Regra violada:** referencia ao doc e a regra especifica
- **Desvio encontrado:** descricao objetiva do problema
- **Correcao necessaria:** o que deve ser ajustado

Corrija todos os desvios encontrados antes de avancar para a Fase 2.

---

## Fase 2 — Consolidacao de Documentos

Esta fase e de sintese. Execute-a somente apos a Fase 1 estar completa e sem
pendencias.

**2.1 Atualizacao da Spec Tecnica**

Atualize apenas os metadados da Spec para refletir a conclusao da implementacao:

- **Status:** `closed`
- **Ultima atualizacao:** `{{ today }}`

Nao altere o conteudo tecnico da spec nesta fase — desvios de implementacao
devem ter sido capturados pelo `update-spec-prompt` durante o desenvolvimento.

**2.2 Atualizacao do PRD**

Atualize o PRD associado a Spec. Ele esta localizado no nivel acima do diretorio
da spec — ex.: se a spec esta em
`documentation/features/<modulo>/specs/<nome>-spec.md`, o PRD esta em
`documentation/features/<modulo>/prd.md`.

Marque como concluidos os itens enderecados pela implementacao. A audiencia aqui
e de produto — traduza o impacto tecnico para linguagem de negocio.

> Nao copie conteudo tecnico de baixo nivel para o PRD — sintetize o valor
> entregue.

**Divergencia spec -> PRD:** Caso a implementacao concluida introduza algum
aspecto que contradiga ou nao esteja coberto pelo PRD (ex: regra de negocio
refinada, escopo ampliado ou reduzido, comportamento diferente do especificado),
atualize o PRD para refletir a realidade entregue. Registre a divergencia no
campo **"O que mudou em relacao a Spec original"** do resumo de conclusao da spec
(secao 3.1).

**2.3 Atualizacao da Arquitetura (se aplicavel)**

Caso a implementacao tenha introduzido novo fluxo de dados, nova camada, novo
padrao de integracao ou mudanca relevante na estrutura de diretorios, atualize
`documentation/architecture.md` para refletir a realidade atual do projeto.

**2.4 Atualizacao de Rules (se aplicavel)**

Caso a implementacao tenha introduzido um padrao de projeto novo, nao mapeado
nas rules existentes, atualize o arquivo de regras correspondente com o novo
padrao e exemplos praticos.

---

## Fase 3 — Comunicacao

Esta fase produz o artefato final para facilitar a abertura do Pull Request.

**3.1 Resumo de conclusao da spec**

Gere um resumo de conclusao com a seguinte estrutura obrigatoria:
```markdown
## O que foi feito

<Descricao objetiva das mudancas implementadas, em linguagem tecnica>

## Por que foi feito assim

<Decisoes de design relevantes e tradeoffs considerados>

## O que mudou em relacao a Spec original

<Desvios ou refinamentos ocorridos durante a implementacao, incluindo
 divergencias que implicaram atualizacao do PRD. Se nenhum, declarar
 explicitamente "Nenhum desvio em relacao a Spec original.">

## Pontos de atencao para o revisor

<Riscos, areas sensiveis, dependencias externas ou decisoes que merecem revisao
cuidadosa. Inclua migracoes de banco pendentes, mudancas de contrato REST,
DTOs compartilhados, side effects em jobs/eventos, impacto em providers ou
dependencias externas (PostgreSQL, Redis, Inngest, auth, storage). Se nenhum,
declare explicitamente "Nenhum ponto de atencao identificado.">

## Checklist

- [ ] `poe codecheck` passou sem warnings
- [ ] `poe typecheck` retornou zero erros
- [ ] `poe test` passou sem falhas (ou regressões pre-existentes devidamente sinalizadas)
- [ ] Cobertura de testes verificada para use cases, controllers e jobs (lacunas criticas enderecadas)
- [ ] Limites arquiteturais validados
- [ ] Spec atualizada com status `closed` e data
- [ ] PRD atualizado com os itens concluidos (e divergencias registradas, se houver)
- [ ] `architecture.md` atualizado (se aplicavel)
- [ ] Rules atualizadas (se novos padroes foram introduzidos)
```

---

## Saidas Esperadas

Ao final da execucao, devem ter sido produzidos:

1. **Relatorio de cobertura de testes** (Fase 1.1.1) — restrito a use cases, controllers e jobs
2. **Testes criados pelos subagents em paralelo** para componentes sem cobertura (Fase 1.1.2, quando aplicavel)
3. **Checklist de validacao** de requisitos (Fase 1.4)
4. **Spec atualizada** com status `closed` e data (Fase 2.1)
5. **PRD atualizado** com itens marcados como concluidos e divergencias registradas, se houver (Fase 2.2)
6. **Resumo de conclusao da spec** com estrutura completa (Fase 3.1)
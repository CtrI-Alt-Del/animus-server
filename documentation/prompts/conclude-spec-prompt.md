---
description: Prompt para concluir uma spec com review de código integrado, validação final, atualização de documentação e geração de resumo estruturado para PR.
---

# Prompt: Conclude Spec

**Objetivo:** Finalizar e consolidar a implementação de uma Spec técnica no
`animus-server`, garantindo que o código esteja revisado, polido, documentado e
validado no contexto da arquitetura em camadas do projeto — produzindo ao final
um checklist de validação, os documentos atualizados e um resumo estruturado
para PR.

---

## Entradas Esperadas

- **Spec Técnica:** O documento que guiou a implementação
  (`documentation/features/<modulo>/specs/<nome>-spec.md`), injetado
  como caminho para o arquivo no contexto.

---

## Fase 0 — Review de Código

> ⚠️ **Esta fase deve ser executada antes de qualquer verificação estática.**

O objetivo é revisar manualmente o diff da implementação com olhos críticos de
revisor — identificando bugs, erros lógicos, inconsistências de nomenclatura e
problemas de design que ferramentas de lint e typecheck não capturam.

**0.1 Escaneamento Manual do Diff**

Com base no diff injetado no contexto, leia o código implementado e procure
ativamente por:

- Erros de digitação em nomes de variáveis, funções, classes e arquivos
- Erros lógicos: condições invertidas, retornos incorretos, operações na ordem errada
- Inconsistências de nomenclatura: snake_case vs camelCase, plural vs singular,
  prefixos/sufixos fora do padrão do projeto
- Dead code: imports não utilizados, variáveis declaradas mas nunca lidas, branches inalcançáveis
- Problemas de legibilidade: blocos muito longos sem extração de função, magic numbers sem constante nomeada
- Erros óbvios de sintaxe que podem passar pelo parser mas indicam intenção equivocada

Para cada problema encontrado, registre no formato:
```
- Arquivo: src/animus/...
- Linha(s): N-M
- Problema: descrição objetiva
- Correção aplicada: o que foi ajustado
```

**0.2 Verificação de Conformidade com a Spec**

Leia a Spec técnica e o código produzido lado a lado. Verifique se a
**intenção do código** corresponde ao **comportamento esperado pela Spec** — não
apenas se os componentes existem, mas se estão implementados corretamente
(contratos respeitados, regras de negócio codificadas fielmente, edge cases
tratados).

> Esta verificação é complementar ao checklist da Fase 1.4, que valida
> presença dos componentes. A Fase 0.2 valida a **correção lógica** da
> implementação.

**0.3 Correções**

Aplique imediatamente todas as correções identificadas nas etapas 0.1 e 0.2.
Não avance para a Fase 1 com problemas de código identificados e não corrigidos.

---

## Fase 1 — Verificação

Esta fase é analítica e deve ser concluída antes de qualquer atualização de
documento.

**1.1 Testes**

Execute `poe test` na raiz do projeto. Todos os testes — novos e
existentes — devem estar passando. Caso algum falhe, interrompa e reporte.

Se a Spec impactar apenas uma parte do projeto, você pode executar primeiro um
escopo mais específico para feedback rápido com `uv run pytest <alvo>` (por
exemplo, um arquivo em `tests/core/...` ou `tests/rest/...`), mas a validação
final deve considerar `poe test`.

> Falhas pré-existentes fora do escopo da Spec devem ser sinalizadas
> explicitamente, indicando que são regressões anteriores e não introduzidas
> pela implementação atual.

**1.1.1 Cobertura de Testes**

> ⚠️ **Escopo obrigatório:** Somente são permitidos testes de **use cases**,
> **controllers** e **jobs**. Testes de outras camadas (database, providers,
> pipes, routers, validation, etc.) estão **fora do escopo** e **não devem ser
> criados** ou modificados. Qualquer item fora desse escopo identificado no diff
> deve ser ignorado no relatório de cobertura.

Com base no diff injetado no contexto e nas regras em
`documentation/rules/testing-rules.md`,
`documentation/rules/use-cases-testing-rules.md`,
`documentation/rules/controllers-testing-rules.md` e
`documentation/rules/jobs-testing-rules.md`, verifique se os novos
**use cases**, **controllers** e **jobs** introduzidos ou modificados pela Spec
possuem testes correspondentes.

Considere como caminhos críticos que exigem cobertura (respeitando o escopo acima):

- **Use cases** em `src/animus/core` — lógica de negócio, regras de domínio, exceções e edge cases
- **Controllers** em `src/animus/rest` — tradução de contrato HTTP, status codes, validações e delegação ao core
- **Jobs** em `src/animus/pubsub/inngest/jobs` — evento consumido, payload processado, delegação e side effect observável

Ao final desta etapa, produza um relatório de cobertura no seguinte formato:
```markdown
## Cobertura de Testes

- [x] <Use Case / Controller / Job A> — coberto em `tests/caminho/do/test_arquivo.py`
- [x] <Use Case / Controller / Job B> — coberto em `tests/caminho/do/test_arquivo.py`
- [ ] <Use Case / Controller / Job C> — **sem cobertura** (detalhe o que está faltando)
```

**1.1.2 Criação de Testes para Componentes sem Cobertura**

Caso existam itens sem cobertura no relatório acima, acione **subagents em
paralelo** — um por componente sem cobertura — para criá-los simultaneamente,
reduzindo o tempo total de execução desta fase.

> ⚠️ Lembre-se: apenas **use cases**, **controllers** e **jobs** devem ter
> testes criados. Não solicite aos subagents a criação de testes para nenhuma
> outra camada.

Cada subagent deve receber como contexto:

- O prompt `documentation/prompts/create-tests-prompt.md` como instrução base.
- O caminho real do componente sem cobertura (`src/animus/...`) que é responsabilidade exclusiva daquele subagent.
- O caminho da Spec técnica, para referência de contratos e comportamentos esperados.

> Os subagents são responsáveis por criar os arquivos de teste, seguir as regras de
> nomenclatura e estrutura do projeto, e garantir que `poe test` passe ao
> final. Execute-os **em paralelo** e aguarde a conclusão de **todos** antes de
> avançar para a Fase 1.2. Não avance enquanto qualquer subagent reportar falhas.

**1.2 Lint e Formatação**

Execute `poe codecheck` na raiz do projeto. O comando roda os checks de Ruff e
validações configuradas no repositório. Nenhum warning ou erro deve restar.
Caso existam, liste-os explicitamente e corrija antes de prosseguir.

**1.3 Checagem de Tipos**

Execute `poe typecheck` na raiz do projeto. O Pyright deve retornar zero erros.
Liste qualquer violação de tipo explicitamente e corrija antes de prosseguir.

**1.4 Cobertura de Requisitos**

Com base no diff real injetado no contexto, compare cada componente descrito na
Spec (seções "O que deve ser criado" e "O que deve ser modificado") contra o
código implementado. Ao final desta etapa, produza um **checklist de validação**
no seguinte formato:
```markdown
## Checklist de Validação

- [x] <Requisito A> — implementado em `src/animus/...` ou `tests/...`
- [x] <Requisito B> — implementado em `src/animus/...` ou `tests/...`
- [ ] <Requisito C> — **ausente ou incompleto** (detalhe o gap)
```

**1.5 Conformidade Arquitetural e de Padrões**

Leia `documentation/rules/rules.md` para identificar quais documentos de regras
são acionados pelas camadas impactadas pela Spec. Em seguida, leia cada um dos
docs relevantes e valide o código implementado contra eles.

Verifique obrigatoriamente os documentos acionados pelas camadas impactadas.
Em geral, os mais comuns no `animus-server` são:

- `documentation/rules/core-layer-rules.md` — `src/animus/core` puro: sem
  dependência de framework, banco, HTTP ou SDK externo
- `documentation/rules/database-layer-rules.md` — persistência, mapeamento e
  repositórios SQLAlchemy sem regra de negócio indevida
- `documentation/rules/rest-layer-rules.md` — controllers HTTP finos,
  traduzindo contrato e delegando comportamento
- `documentation/rules/routers-layers-rules.md` — composição de routers por
  contexto, sem endpoint direto na classe de router
- `documentation/rules/pipes-layer-rules.md` — dependency providers sem regra
  de negócio
- `documentation/rules/layer-rules.md` — jobs/eventos finos e
  idempotentes, delegando comportamento ao `core`
- `documentation/rules/testing-rules.md` — índice e estratégia geral de testes
- `documentation/rules/code-conventions-rules.md` — nomenclatura, imports,
  organização de módulos e tooling obrigatório

Para cada regra violada, reporte:

- **Arquivo:** caminho relativo do arquivo com o desvio
- **Regra violada:** referência ao doc e à regra específica
- **Desvio encontrado:** descrição objetiva do problema
- **Correção necessária:** o que deve ser ajustado

Corrija todos os desvios encontrados antes de avançar para a Fase 2.

---

## Fase 2 — Consolidação de Documentos

Esta fase é de síntese. Execute-a somente após a Fase 1 estar completa e sem
pendências.

**2.1 Atualização da Spec Técnica**

Atualize apenas os metadados da Spec para refletir a conclusão da implementação:

- **Status:** `closed`
- **Última atualização:** `{{ today }}`

Não altere o conteúdo técnico da spec nesta fase — desvios de implementação
devem ter sido capturados pelo `update-spec-prompt` durante o desenvolvimento.

**2.2 Atualização do PRD**

Atualize o PRD associado à Spec. Ele está localizado no nível acima do diretório
da spec — ex.: se a spec está em
`documentation/features/<modulo>/specs/<nome>-spec.md`, o PRD está em
`documentation/features/<modulo>/prd.md`.

Marque como concluídos os itens endereçados pela implementação. A audiência aqui
é de produto — traduza o impacto técnico para linguagem de negócio.

> Não copie conteúdo técnico de baixo nível para o PRD — sintetize o valor
> entregue.

**Divergência spec → PRD:** Caso a implementação concluída introduza algum
aspecto que contradiga ou não esteja coberto pelo PRD (ex: regra de negócio
refinada, escopo ampliado ou reduzido, comportamento diferente do especificado),
atualize o PRD para refletir a realidade entregue. Registre a divergência no
campo **"O que mudou em relação à Spec original"** do resumo de conclusão da spec
(seção 3.1).

**2.3 Atualização da Arquitetura (se aplicável)**

Caso a implementação tenha introduzido novo fluxo de dados, nova camada, novo
padrão de integração ou mudança relevante na estrutura de diretórios, atualize
`documentation/architecture.md` para refletir a realidade atual do projeto.

**2.4 Atualização de Rules (se aplicável)**

Caso a implementação tenha introduzido um padrão de projeto novo, não mapeado
nas rules existentes, atualize o arquivo de regras correspondente com o novo
padrão e exemplos práticos.

---

## Fase 3 — Comunicação

Esta fase produz o artefato final para facilitar a abertura do Pull Request.

**3.1 Resumo de Conclusão da Spec**

Gere um resumo de conclusão com a seguinte estrutura obrigatória:
```markdown
## O que foi feito

<Descrição objetiva das mudanças implementadas, em linguagem técnica>

## Por que foi feito assim

<Decisões de design relevantes e tradeoffs considerados>

## O que mudou em relação à Spec original

<Desvios ou refinamentos ocorridos durante a implementação, incluindo
 divergências que implicaram atualização do PRD. Se nenhum, declarar
 explicitamente "Nenhum desvio em relação à Spec original.">

## Pontos de atenção para o revisor

<Riscos, áreas sensíveis, dependências externas ou decisões que merecem revisão
cuidadosa. Inclua migrações de banco pendentes, mudanças de contrato REST,
DTOs compartilhados, side effects em jobs/eventos, impacto em providers ou
dependências externas (PostgreSQL, Redis, Inngest, auth, storage). Se nenhum,
declare explicitamente "Nenhum ponto de atenção identificado.">

## Checklist

- [ ] Revisão de código manual aplicada (Fase 0: bugs, lógica, nomenclatura)
- [ ] `poe codecheck` passou sem warnings
- [ ] `poe typecheck` retornou zero erros
- [ ] `poe test` passou sem falhas (ou regressões pré-existentes devidamente sinalizadas)
- [ ] Cobertura de testes verificada para use cases, controllers e jobs (lacunas críticas endereçadas)
- [ ] Limites arquiteturais validados
- [ ] Spec atualizada com status `closed` e data
- [ ] PRD atualizado com os itens concluídos (e divergências registradas, se houver)
- [ ] `architecture.md` atualizado (se aplicável)
- [ ] Rules atualizadas (se novos padrões foram introduzidos)
```

---

## Saídas Esperadas

Ao final da execução, devem ter sido produzidos:

1. **Relatório de revisão de código** (Fase 0) — bugs, erros lógicos e inconsistências corrigidos
2. **Relatório de cobertura de testes** (Fase 1.1.1) — restrito a use cases, controllers e jobs
3. **Testes criados pelos subagents em paralelo** para componentes sem cobertura (Fase 1.1.2, quando aplicável)
4. **Checklist de validação** de requisitos (Fase 1.4)
5. **Spec atualizada** com status `closed` e data (Fase 2.1)
6. **PRD atualizado** com itens marcados como concluídos e divergências registradas, se houver (Fase 2.2)
7. **Resumo de conclusão da spec** com estrutura completa (Fase 3.1)
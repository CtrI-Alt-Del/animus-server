---
description: Prompt para concluir uma spec com validação final, atualização de documentação e geração de resumo estruturado para PR.
---

# Prompt: Conclude Spec

**Objetivo:** Finalizar e consolidar a implementação de uma Spec técnica no
`animus-server`, garantindo que o código esteja polido, documentado e validado —
produzindo ao final um checklist de validação, os documentos atualizados e um
rascunho estruturado para o Pull Request.

---

## Entradas Esperadas

- **Spec Técnica:** O documento que guiou a implementação
  (`documentation/features/<modulo>/specs/<nome>-spec.md`), injetado
  como caminho para o arquivo no contexto.

---

## Fase 1 — Verificação

Esta fase é analítica e deve ser concluída antes de qualquer atualização de
documento.

**1.1 Lint e Formatação**

Execute `poe codecheck` na raiz do projeto. O comando roda o Ruff para lint e
formatação. Nenhum warning ou erro deve restar. Caso existam, liste-os
explicitamente e aguarde correção antes de prosseguir.

**1.2 Checagem de Tipos**

Execute `poe typecheck` na raiz do projeto. O Pyright deve retornar zero erros.
Liste qualquer violação de tipo explicitamente e aguarde correção antes de
prosseguir.

**1.3 Testes**

Execute `poe test` na raiz do projeto. Todos os testes — novos e existentes —
devem estar passando. Caso algum falhe, interrompa e reporte.

> Falhas pré-existentes fora do escopo da Spec devem ser sinalizadas
> explicitamente, indicando que são regressões anteriores e não introduzidas
> pela implementação atual.

**1.3.1 Cobertura de Testes**

Com base no diff injetado no contexto e nas regras em
`documentation/rules/testing-rules.md`, verifique se os novos comportamentos
introduzidos pela Spec possuem testes correspondentes. Considere como caminhos
críticos que exigem cobertura:

- Lógica de negócio nova ou modificada na camada `core` (Use Cases, Entidades,
  erros de domínio)
- Casos de erro e edge cases relevantes (exceções de domínio, validações)
- Contratos HTTP novos ou alterados (status codes, payloads, validação `422`)
- Ports/interfaces do `core` implementados em `database` ou `providers`

Ao final desta etapa, produza um relatório de cobertura no seguinte formato:
```markdown
## Cobertura de Testes

- [x] <Comportamento A> — coberto em `tests/caminho/do/test_arquivo.py`
- [x] <Comportamento B> — coberto em `tests/caminho/do/test_arquivo.py`
- [ ] <Comportamento C> — **sem cobertura** (detalhe o que está faltando)
```

Caso existam lacunas em caminhos críticos, liste-as como pendências e aguarde
decisão antes de prosseguir para a Fase 2. Não avance com itens críticos
descobertos.

**1.4 Cobertura de Requisitos**

Com base no diff real injetado no contexto, compare cada componente descrito na
Spec (seções "O que deve ser criado" e "O que deve ser modificado") contra o
código implementado. Ao final desta etapa, produza um **checklist de validação**
no seguinte formato:
```markdown
## Checklist de Validação

- [x] <Requisito A> — implementado em `src/animus/camada/arquivo.py`
- [x] <Requisito B> — implementado em `src/animus/camada/arquivo.py`
- [ ] <Requisito C> — **ausente ou incompleto** (detalhe o gap)
```

**1.5 Conformidade Arquitetural**

Verifique se os arquivos alterados respeitam os limites arquiteturais do projeto
(conforme `documentation/architecture.md` e as regras das camadas envolvidas):

- `documentation/rules/core-layer-rules.md` — `core` puro: sem FastAPI,
  SQLAlchemy, sessão, SQL, env var ou HTTP
- `documentation/rules/database-rules.md` — apenas persistência/mapeamento, sem
  regra de negócio
- `documentation/rules/rest-layer-rules.md` — controllers finos: validam,
  adaptam e delegam para use case
- `documentation/rules/code-conventions-rules.md` — nomenclatura, organização
  de módulos e padrões de código

Liste explicitamente qualquer desvio identificado.

---

## Fase 2 — Consolidação de Documentos

Esta fase é de síntese. Execute-a somente após a Fase 1 estar completa e sem
pendências.

**2.1 Atualização da Spec Técnica**

Refine o documento da Spec para refletir decisões de design tomadas durante a
implementação ou desvios de caminho. A audiência é técnica — mantenha o nível
de detalhe de engenharia. Atualize também:

- **Status:** `concluído`
- **Última atualização:** `{{ today }}`

**2.2 Atualização do PRD**

Atualize o PRD associado à Spec. Ele está localizado no nível acima do diretório
da spec — ex.: se a spec está em
`documentation/features/<modulo>/specs/<nome>-spec.md`, o PRD está em
`documentation/features/<modulo>/prd.md`.

Marque como concluídos os itens endereçados pela implementação. A audiência aqui
é de produto — traduza o impacto técnico para linguagem de negócio.

> 💡 Não copie conteúdo técnico de baixo nível para o PRD — sintetize o valor
> entregue.

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

**3.1 Rascunho do Pull Request**

Gere um rascunho de descrição de PR com a seguinte estrutura obrigatória:
```markdown
## O que foi feito

<Descrição objetiva das mudanças implementadas, em linguagem técnica>

## Por que foi feito assim

<Decisões de design relevantes e tradeoffs considerados>

## O que mudou em relação à Spec original

<Desvios ou refinamentos ocorridos durante a implementação. Se nenhum, declare
explicitamente "Nenhum desvio em relação à Spec original.">

## Pontos de atenção para o revisor

<Riscos, áreas sensíveis, dependências externas ou decisões que merecem revisão
cuidadosa. Inclua migrações de banco pendentes, mudanças de contrato HTTP/DTOs,
side effects em jobs/eventos. Se nenhum, declare explicitamente "Nenhum ponto de
atenção identificado.">

## Checklist

- [ ] `poe codecheck` passou sem warnings
- [ ] `poe typecheck` retornou zero erros
- [ ] `poe test` passou sem falhas (ou regressões pré-existentes devidamente sinalizadas)
- [ ] Cobertura de testes verificada e lacunas críticas endereçadas
- [ ] Limites arquiteturais validados (`core` puro, `rest` fino, `database` isolado)
- [ ] Spec atualizada com status `concluído` e data
- [ ] PRD atualizado com os itens concluídos
- [ ] `architecture.md` atualizado (se aplicável)
- [ ] Rules atualizadas (se novos padrões foram introduzidos)
```

---

## Saídas Esperadas

Ao final da execução, devem ter sido produzidos:

1. **Relatório de cobertura de testes** (Fase 1.3.1)
2. **Checklist de validação** de requisitos (Fase 1.4)
3. **Spec atualizada** com status `concluído` e data (Fase 2.1)
4. **PRD atualizado** com itens marcados como concluídos (Fase 2.2)
5. **Rascunho de PR** com estrutura completa (Fase 3.1)
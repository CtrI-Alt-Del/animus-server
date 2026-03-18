---
description: Revisar codigo com foco em corretude, arquitetura e qualidade
---

# Prompt: Revisar codigo (animus-server)

Objetivo: revisar mudancas no `animus-server` com foco em corretude, aderencia as
regras do repo e qualidade (lint/format, typecheck e testes).

Entrada:

- Contexto: spec implementada (opcional) e/ou descricao do que mudou.
- Alvo: caminhos especificos ou o projeto inteiro.

Diretrizes de execucao:

1) Verificacao de spec e logica

- Confirme que os requisitos e criterios de aceite foram atendidos.
- Revise manualmente:
  - bugs latentes (edge cases, validacao, erros de dominio)
  - nomes e responsabilidades por camada (`core`/`database`/`rest`)
  - limites arquiteturais (dependencias apontando para dentro)

2) Qualidade estatica (comandos do repo)

- Lint/format: `poe codecheck` (ruff)
- Typecheck: `poe typecheck` (pyright)
- Priorize falhas que quebram build/execucao (type errors, import cycles, lint blocking).

3) Alinhamento com regras do projeto (leitura progressiva)

- Indice: `documentation/rules/rules.md`
- Arquitetura: `documentation/architecture.md`
- Por camada (quando aplicavel):
  - `documentation/rules/core-layer-rules.md`
  - `documentation/rules/database-layer-rules.md`
  - `documentation/rules/rest-layer-rules.md`
- Testes:
  - `documentation/rules/testing-rules.md`
  - `documentation/rules/use-cases-testing-rules.md`
  - `documentation/rules/controllers-testing-rules.md`

4) Validacao final

- Testes: `poe test`
- Se tocar em controllers/endpoints, garanta que testes REST continuam passando.

Criterio de sucesso:

- `poe codecheck`, `poe typecheck` e `poe test` passam.
- Revisao confirma aderencia a arquitetura (Clean/Hex) e consistencia de padroes.

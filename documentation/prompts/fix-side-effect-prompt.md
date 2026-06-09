---
description: Corrigir efeitos colaterais de mudancas com diagnostico e validação
---

# Prompt: Corrigir side effects (animus-server)

Objetivo: identificar e corrigir regressao, erro de import, erro de lint/type ou
falha de testes causada por alteracoes manuais, restabelecendo a integridade do
`animus-server`.

Entrada:

- Caminho(s) do arquivo/diretorio alterado(s) ou erro observado (stack trace/log).

Diretrizes de execução:

1) Diagnostico estatico

- Rode lint/format: `poe codecheck` (ruff)
- Rode typecheck: `poe typecheck` (pyright)
- Priorize:
  - erros de sintaxe/import
  - contracts quebrados (assinaturas/ports)
  - type errors que impedem execução

2) Propagação de mudanca

- Atualize todos os pontos impactados (imports, chamadas, tipos, DTOs, contratos de interface).
- Se a mudanca afetar um port do `core`, confirme que implementacoes em `database` ainda aderem ao contrato.

3) Validação com testes

- Rode testes: `poe test`.
- Se o impacto for localizado, rode um subconjunto primeiro e depois o suite completo.
- Criterio de sucesso: sem falhas em lint/type e testes verdes.

4) Sincronização de documentação

- Se o comportamento mudou em relação ao esperado, atualize a spec/PRD relevante (quando existir) e/ou regras em `documentation/rules/*.md`.
- Se a mudanca for arquitetural (nova camada/fluxo), atualize `documentation/architecture.md`.

  

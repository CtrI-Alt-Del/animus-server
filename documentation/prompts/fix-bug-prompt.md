---
description: Corrigir bug com planejamento, implementacao iterativa e validacoes
---

# Prompt: Corrigir bug (animus-server)

Objetivo: ler o bug report, planejar a correcao e implementar as mudancas
necessarias no `animus-server`, garantindo qualidade (lint/type/tests) e
respeito aos limites arquiteturais.

Entradas:

- Bug report (descricao, como reproduzir, comportamento esperado vs atual, possivel causa raiz).

Diretrizes de execucao:

1) Analise e planejamento

- Reproduza o bug (quando possivel) e identifique o ponto exato de falha.
- Classifique a mudanca por camada (`core`, `database`, `rest`, `validation`, `tests`).
- Consulte regras acionadas pelo tipo de mudanca em `documentation/rules/rules.md`.

2) Decomposicao

- Divida em micro-tarefas pequenas que mantenham o repo rodando a cada passo.
- Priorize primeiro: teste que reproduz (ou scenario minimo), depois a correcao.

3) Implementacao iterativa

- Aplique a correcao respeitando a arquitetura:
  - `core` puro: sem FastAPI/SQLAlchemy/HTTP/env
  - `database`: persistencia/mapeamento; sem regra de negocio
  - `rest`: contrato HTTP e adaptacao; controller fino

4) Ciclo de qualidade por micro-tarefa

Ao finalizar cada micro-tarefa, rode validacoes antes de seguir:

- Lint/format: `poe codecheck`
- Typecheck: `poe typecheck`
- Testes: `poe test` (ou subset primeiro, quando fizer sentido)

Criterio: nao avance com lint/type/test quebrados.

5) Revisao final

Checklist:

| # | Verificacao | Criterio de aceite |
|---|------------|--------------------|
| 1 | Completude | Requisitos do bug report atendidos |
| 2 | Funcionalidade | Bug nao ocorre mais no cenario de reproducao |
| 3 | Regressao | Suite relevante continua passando |
| 4 | Efeitos colaterais | Nenhuma mudanca inesperada de comportamento |
| 5 | Qualidade | `poe codecheck`, `poe typecheck`, `poe test` passam |

Procedimento:

1) Releia o bug report e confirme que nada ficou faltando.
2) Rode o(s) teste(s) que cobriam/reproduziam o bug e confirme que agora passam.
3) Rode a suite completa: `poe test`.

Se qualquer item falhar, volte para a etapa 3 e ajuste antes de concluir.

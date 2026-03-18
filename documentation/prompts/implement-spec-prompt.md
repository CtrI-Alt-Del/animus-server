---
description: Implementar spec tecnica com execucao iterativa e validacoes por camada
---

# Prompt: Implementar spec (animus-server)

Objetivo: executar uma spec tecnica de forma iterativa e validada no `animus-server`,
mantendo os limites arquiteturais (Clean + Hexagonal) e a qualidade do codigo.

Entrada:

- Spec tecnica aprovada/finalizada (requisitos + criterio de aceite + mudancas esperadas).

---

## Regra mestra (nao ignore)

Antes de escrever codigo:

1) Classifique a mudanca (ex.: `core`/regra de negocio, `database`/persistencia,
   `rest`/contrato HTTP, `tests`, tooling).
2) Consulte o indice: `documentation/rules/rules.md`.
3) Leia os documentos acionados pelo tipo de mudanca e aplique as regras.

Proibicoes:

- Nao assumir padrao generico (Clean/MVC) sem seguir as regras do repo.
- Nao implementar "do seu jeito" quando ja existir convencao/proximo exemplo nos testes.

---

## Diretrizes de execucao

### 1) Validacao de arquitetura (o que ler)

- Arquitetura geral: `documentation/architecture.md`
- Regras por camada:
  - `documentation/rules/core-layer-rules.md`
  - `documentation/rules/database-rules.md`
  - `documentation/rules/rest-layer-rules.md`
- Padrao de codigo/organizacao: `documentation/rules/code-conventions-rules.md`
- Testes (indice + docs especializadas):
  - `documentation/rules/testing-rules.md`
  - `documentation/rules/use-cases-testing-rules.md` (quando for `core`)
  - `documentation/rules/controllers-testing-rules.md` (quando for `rest`)

### 2) Decomposicao atomica

- Quebre o plano em micro-tarefas que gerem codigo funcional a cada passo.
- Evite PRs gigantes: prefira progresso incremental com testes acompanhando.

### 3) Ordem de execucao (bottom-up)

Implemente respeitando dependencia apontando para dentro:

1) `core`: entidades/structures/DTOs, erros de dominio, interfaces (ports), use cases.
2) `database`: models/mappers/repositorios SQLAlchemy (implementando ports).
3) `rest`: routers/controllers + validacao (Pydantic) + injecao de dependencia.
4) Ajustes de wiring (app/DI/middlewares), se necessario.

Regra: nao implemente um consumidor (ex.: controller) antes da logica (use case)
e do contrato (ports/DTOs) que ele consome.

### 4) Ciclo de qualidade por micro-tarefa

Ao finalizar cada micro-tarefa, rode validacoes antes de seguir:

- Lint/format: `poe codecheck`
- Typecheck: `poe typecheck`
- Testes: `poe test`

Criterio de aceite: corrija imediatamente falhas de lint/type/tests; nao avance
com o repo quebrado.

### 5) Ferramentas auxiliares

- Use Serena para buscar arquivos/simbolos rapidamente quando estiver explorando o repo.
- Use Context7 quando precisar de docs/exemplos atualizados de uma biblioteca especifica.

### 6) Consistencia e limites

- `core` deve ser Python puro: sem FastAPI, SQLAlchemy, sessao, SQL, env var, HTTP.
- `rest` deve ser fino: valida/adapta/delega; sem regra de negocio complexa.
- `database` implementa persistencia/mapeamento; sem regra de negocio.

---

## Saida esperada

- Implementacao completa da spec com testes relevantes.
- Mudancas organizadas por camada (estrutura do repo preservada).
- Comandos de verificacao executados e passando.

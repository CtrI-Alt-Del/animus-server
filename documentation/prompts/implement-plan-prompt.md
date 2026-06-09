---
description: Implementar um plano de implementação derivado de uma spec tecnica.
---

# Prompt: Implementar Plano

**Objetivo principal** Implementar no codebase um plano de implementação derivado de uma spec tecnica, seguindo a arquitetura e diretrizes do animus-server.

## Entrada

- Caminho do arquivo do plano (Markdown) **ou**, se nao houver plano, caminho da spec tecnica (Markdown).

## Diretrizes de execução

1. **Pre-check (obrigatorio)**
   - Leia o plano e identifique: escopo, fluxo principal, criterios de aceite, riscos e pendencias.
   - Se o documento estiver incompleto, nao invente: crie uma lista `Pendencias` e avance com defaults seguros.
   - Extraia a **tabela de dependencias de fases** para guiar a orquestração abaixo.

2. **Consultar regras/arquitetura (obrigatorio)**
   - Antes de implementar uma camada, se necessario, consulte as regras correspondentes em `documentation/rules/`.
   - Preserve padroes existentes (nomenclatura, organização de pastas, providers, presenters).

3. **Orquestração com subagents**

   Execute o plano respeitando o grafo de dependencias das fases:

   - **Fases independentes (sem dependencias entre si):** lance subagents em paralelo — um subagent por fase.
   - **Fases com dependencia:** aguarde a conclusao das fases bloqueantes antes de lancar o subagent da fase dependente.

   Cada subagent recebe como contexto:
   - O plano completo.
   - A lista de tarefas da sua fase.
   - As regras de camada relevantes (ex.: `rest-layer-rules.md`, `core-layer-rules.md`).
   - Instrução explicita: implementar apenas as tarefas da sua fase, sem ultrapassar o escopo.

   > ⚠️ **Regra** Um subagent nunca deve implementar tarefas de outra fase para "adiantar" trabalho.
   > ⚠️ **Regra** O agente orquestrador aguarda todos os subagents de um grupo paralelo antes de avancar para a proxima fase dependente.

   **Exemplo de orquestração (dado um plano hipotetico):**
   ```
   F1 (Core) — sem dependencia
     └─ subagent-F1 roda isolado

   F2 (Rest) e F3 (Drivers) — dependem de F1, mas sao independentes entre si
     └─ aguarda subagent-F1 concluir
     └─ lanca subagent-F2 e subagent-F3 em paralelo

   F4 (UI) — depende de F2 e F3
     └─ aguarda subagent-F2 e subagent-F3 concluirem
     └─ lanca subagent-F4
   ```

4. **Ciclo de implementação por tarefa (dentro de cada subagent)**
   - Localize codigo existente semelhante antes de criar algo novo.
   - Implemente a mudanca minima que entrega valor observavel.
   - Evite acoplamento entre camadas e chamadas de API na UI.

5. **Verificação (obrigatorio) ao final de cada fase**
   - Garanta que o projeto compila e que fluxos impactados funcionam.
   - Rode checks existentes e corrija falhas antes de liberar a fase para as dependentes.
   - **Obrigatorio:** rode migrations no ambiente local com `uv run alembic upgrade head` em toda execução do plano.
   - **Obrigatorio:** rode testes automatizados do projeto ao menos uma vez na execução do plano.
   - Quando a fase alterar fluxo critico, rode testes focados da area alem dos checks de lint/typecheck.

6. **Progresso e reporte**
   - Ao concluir cada fase, consolide o resultado do subagent no checklist principal.
   - Ao final de todas as fases, reporte: o que foi implementado, arquivos principais tocados, pendencias e proximos passos.

7. **Atualização de REST Client (obrigatorio quando aplicavel)**
   - Se qualquer endpoint HTTP for adicionado ou alterado, atualize os arquivos correspondentes em `rest-client/` ao final da implementação.
   - Inclua exemplos minimos para validar o endpoint (metodo, path, headers e payload quando aplicavel).
   - Se nenhum endpoint foi alterado/adicionado, declare isso explicitamente no reporte final.

## Saida esperada

- Implementação completa (ou parcial, se bloqueada) do plano/spec no codebase.
- Lista objetiva de tarefas concluidas x pendentes, com justificativa para bloqueios.
- Referencias a paths reais de arquivos alterados/criados.

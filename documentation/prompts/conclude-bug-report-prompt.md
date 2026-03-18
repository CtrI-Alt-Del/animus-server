---
description: Concluir bug report com validacao final e consolidacao da correcao
---

# Prompt: Concluir Bug Report

**Objetivo:**
Finalizar e consolidar a correção de um erro reportado, garantindo que o bug foi devidamente mitigado, que novos testes foram adicionados (se aplicável) e que a solução respeita a arquitetura do projeto.

**Entrada:**
*   **Bug Report:** O documento de report original
*   **Código Corrigido:** As alterações realizadas para sanar o problema.

**Diretrizes de Execução:**

1.  **Validação Final da Correção:**
    *   **Testes de Regressão:** Execute `poe test` para validar que o bug foi sanado e que o sistema permanece estável.
    *   **Qualidade Estática:** Execute `poe codecheck` e `poe typecheck` para garantir lint, formatação e tipagem consistentes.
    *   **Cenários de Erro:** Certifique-se de que foram adicionados testes unitários para o caso específico do bug, garantindo que ele não retorne (test-first approach para bugs).

2.  **Verificação de Padrões e Arquitetura:**
    *   **Respeito às Camadas:** Valide se a correção respeita as rules (`documentation/rules/core-layer-rules.md`, `documentation/rules/database-layer-rules.md`, `documentation/rules/rest-layer-rules.md`, etc.) e se está na camada correta identificada no diagnóstico.

3.  **Atualização do Bug Report:**
    *   Atualize o estado do Bug Report ou adicione notas sobre a resolução final.
    *   Se a causa raiz identificada durante a implementação for diferente da inicial, documente essa descoberta.

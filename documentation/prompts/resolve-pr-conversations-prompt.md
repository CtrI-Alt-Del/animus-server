---
description: Resolver comentarios de PR com implementacao e validacao das correcoes
---

# Prompt: Resolver conversas de PR

**Objetivo Principal**
Analisar, implementar e resolver todas as conversas **pendentes e não resolvidas** em um Pull Request (PR) específico do GitHub. O foco é garantir que todos os pontos de melhoria, correções de bugs e sugestões de design levantadas pelos revisores sejam devidamente endereçados no código.

> ⚠️ **Escopo obrigatório:** Somente conversas **não resolvidas** devem ser tratadas. Conversas já marcadas como resolvidas no GitHub **devem ser ignoradas por completo** — não as reabra, não as reanálise e não as mencione no relatório final.

**Entrada:**
* **Link do PR:** URL completa do Pull Request no GitHub (ex: `https://github.com/owner/repo/pull/123`).

**Diretrizes de Execução:**

1. **Extração de Contexto:**
   * Identifique o `owner`, `repo` e `pullNumber` a partir da URL fornecida.
   * Utilize o `gh` CLI para interagir com a API GraphQL do GitHub.

2. **Mapeamento de Conversas Não Resolvidas:**
   * Liste todas as threads de revisão via GraphQL com:
```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 10) {
              nodes {
                body
                path
                line
                author { login }
              }
            }
          }
        }
      }
    }
  }
' -f owner={owner} -f repo={repo} -F number={pullNumber}
```
   * **Filtre estritamente:** mantenha apenas os nós onde `isResolved: false`. Descarte qualquer thread com `isResolved: true` antes de prosseguir.
   * Se **todas** as conversas já estiverem resolvidas, informe o usuário imediatamente e encerre a execução — não há nada a fazer.

3. **Análise e Implementação:**
   * Para cada comentário **não resolvido**:
     * Localize o arquivo e as linhas de código mencionadas.
     * Analise a sugestão ou problema apontado pelo revisor.
     * Analise também os comentários da conversa.
     * Aplique as alterações necessárias no código local utilizando as ferramentas de edição de arquivo (`replace_file_content`, `multi_replace_file_content`).
     * Antes de implementar, consulte as regras da camada afetada seguindo o índice em `documentation/rules/rules.md`:
       * Regra de negócio (`core`) → `documentation/rules/core-layer-rules.md`
       * Persistência/ORM (`database`) → `documentation/rules/database-layer-rules.md`
       * Endpoint/contrato HTTP (`rest`/`routers`) → `documentation/rules/rest-layer-rules.md` e `documentation/rules/routers-layers-rules.md`
       * Jobs assíncronos/eventos (`pubsub`) → `documentation/rules/pubsub-layer-rules.md`
       * Injeção de dependência (`pipes`) → `documentation/rules/pipes-layer-rules.md`
       * Estilo/nomeação → `documentation/rules/code-conventions-rules.md`
     * Garanta que as mudanças sigam os princípios arquiteturais definidos em `documentation/architecture.md`.

4. **Resolução das Threads no GitHub:**
   * Após implementar e validar as correções de cada thread, marque-a como resolvida via GraphQL com:
```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: { threadId: $threadId }) {
      thread {
        id
        isResolved
      }
    }
  }
' -f threadId={threadId}
```
   * Substitua `{threadId}` pelo `id` retornado na query do Passo 1 para cada thread tratada.

5. **Validação das Alterações:**
   * Após implementar as correções, verifique lint e formatação com:
```bash
poe codecheck
```
   * Verifique checagem estática de tipos com:
```bash
poe typecheck
```
   * Execute os testes relevantes para as camadas modificadas:
```bash
poe test
```
   * Confirme que nenhuma regra arquitetural foi violada (ex.: `core` sem dependência de FastAPI/SQLAlchemy, controllers finos, transação controlada por middleware).

6. **Finalização:**
   * Forneça um resumo detalhado **apenas das conversas não resolvidas que foram tratadas** e quais alterações de código foram realizadas. Conversas já resolvidas não devem aparecer no relatório.

---

## FLUXO DE TRABALHO (Workflow)

### Passo 1: Coleta de Dados
Liste todas as threads de revisão do PR via GraphQL:
```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 10) {
              nodes {
                body
                path
                line
                author { login }
              }
            }
          }
        }
      }
    }
  }
' -f owner={owner} -f repo={repo} -F number={pullNumber}
```

### Passo 2: Diagnóstico — somente conversas não resolvidas
> ⚠️ **Antes de qualquer análise**, filtre os nós retornados e descarte todos com `isResolved: true`. Trabalhe exclusivamente com os que têm `isResolved: false`.

Para cada thread **não resolvida**, identifique:
* O arquivo afetado e a camada arquitetural correspondente (`core`, `database`, `rest`, `routers`, `pipes`, `pubsub`, `providers`).
* O problema descrito.
* A solução proposta.

Se houver dúvidas sobre um comentário específico ou se o comentário for ambíguo, peça esclarecimentos ao usuário antes de prosseguir.

### Passo 3: Execução
Modifique os arquivos no ambiente local para refletir as resoluções, respeitando os limites de cada camada.

### Passo 4: Resolução das Threads
Após validar cada correção, marque a thread correspondente como resolvida via GraphQL:
```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: { threadId: $threadId }) {
      thread {
        id
        isResolved
      }
    }
  }
' -f threadId={threadId}
```

### Passo 5: Conclusão
Relate o progresso listando **somente as conversas não resolvidas que foram tratadas**:
* [x] Arquivo X: Comentário sobre Y resolvido (descrição da mudança).
* [x] Arquivo Z: Ajuste de padrão realizado.

> Não inclua no relatório conversas que já estavam resolvidas antes desta execução.

### Passo 6: Atualização da documentação relacionada

Analise o documento de Spec, Report ou PRD da funcionalidade relacionada e atualize-o caso seja necessário com as novas alterações.
---
description: Prompt para analisar alteracoes e executar commits reais com Conventional Commits e task do Jira.
---

# Prompt: Fazer Commits no Codigo

## Objetivo

Criar e executar commits reais no repositorio com mensagens no padrao Conventional Commits e com inclusao obrigatoria da task do Jira.

Formato obrigatorio:

`<type>(<scope opcional>)?: <JIRA-123> <descricao em ingles>`

Exemplo:

`feat: ANI-23 add sign in screen`

## Regra Critica

Se existirem arquivos modificados, execute `git add` e `git commit` ate nao restarem mudancas pendentes. Nao apenas sugira mensagens: execute os comandos.

## Validacao automatica da mensagem

A validacao do formato de commit deve ser feita com **Commitlint + Husky** no hook `commit-msg`.

Formato validado automaticamente:

`<type>(<scope opcional>)?: <PROJ-123> <descricao em ingles>`

Exemplo valido:

`feat(auth): ANI-23 add sign in screen`

## Diretrizes de Execucao

1. Detectar alteracoes com `git status --porcelain`.
2. Se vazio, responder `No changes to commit`.
3. Se houver alteracoes, agrupar por responsabilidade e criar commits separados quando necessario.
4. Escrever mensagens em ingles no formato exigido.

## Tipos permitidos

- `build`
- `chore`
- `ci`
- `docs`
- `feat`
- `fix`
- `perf`
- `refactor`
- `revert`
- `style`
- `test`

## Checklist antes de cada commit

- Mensagem segue Conventional Commits.
- Mensagem inclui task Jira no formato `PROJ-123`.
- Descricao curta e objetiva em ingles.
- Commit representa um unico grupo de responsabilidade.

## Exemplo de comando

`git add <arquivos-do-grupo> && git commit -m "feat: ANI-23 add sign in screen"`

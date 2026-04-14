---
description: Criar um ticket do zero para o projeto baseado em um PRD ou contexto tecnico
---

## Objetivo

Ler um PRD do projeto ou um contexto tecnico do projeto e propor um ticket do zero, ou apenas o corpo dela do Jira claros, acionavel e alinhado ao contexto, arquitetura e regras da codebase. 

## Entrada

- Tipo do ticket: `task`, `logico` ou `bug`.
- Link do PRD do projeto, quando houver.
- Link do ticket, quando houver.

### Regras da entrada

- Quando o input indicar `tipo = task`, o ticket deve ser orientado pelos PRDs publicados do Confluence.
- Quando o input indicar `tipo = logico` ou `tipo = bug`, o ticket pode nao ter PRD associado.
- Para tickets `logico` ou `bug`, a secao `Requisitos de Produto` pode ser omitida completamente quando nao houver PRD relevante.

## Instrucoes

1. Identifique o tipo do ticket informado no input: `task`, `logico` ou `bug`.
2. Quando o tipo for `task`, obtenha o PRD informado.
3. Quando o tipo for `task`, antes de propor qualquer ticket, carregue os PRDs publicados do projeto no Confluence, incluindo pelo menos:
   - o PRD base `Requisitos do produto`
   - os PRDs funcionais publicados (`PRD - RF xx`) relacionados ao escopo
4. Quando o tipo for `task`, liste explicitamente os links dos PRDs carregados e use esses links como referencia principal do trabalho.
5. Quando o tipo for `task`, leia o documento principal e os PRDs relacionados e identifique funcionalidades, restricoes, regras de negocio, dependencias e riscos.
6. Quando o tipo for `logico` ou `bug`, use como base o contexto tecnico fornecido, o link do ticket original quando houver, a codebase e a documentacao do projeto.
7. Considere o contexto da codebase desse projeto, sua arquitetura e os padroes documentados no projeto.
8. Sugira os tickets necessarios para implementar o escopo descrito.
9. Quando a funcionalidade couber em uma unica entrega coerente, proponha um unico ticket.
10. Quando o escopo for grande, com dependencias ou etapas bem separadas, quebre em multiplos tickets menores.
11. Escreva cada ticket em formato pronto para cadastro no Jira.
12. Quando uma milestone/epic tiver sido fornecida, indique que cada ticket deve ser vinculado a ela.

## Criterios para quebrar tickets

- Separar backend, mobile, web ou infraestrutura quando houver dependencias independentes.
- Separar integracoes externas, migracoes, contratos de API e ajustes de UX quando fizer sentido.
- Evitar tickets grandes demais ou vagos.
- Garantir que cada ticket tenha escopo verificavel.

## Formato de saida

Para cada ticket, gere um corpo seguindo exatamente esta estrutura base:

## Objetivo

<!-- Descreva o que sera implementado, o resultado esperado e o contexto funcional. -->

Camadas impactadas: `core` · `rest` · `routers` · `validation` · `pipes` · `ui` etc ...
<!-- Ajuste a lista conforme o escopo real do ticket. -->

## Requisitos de Produto

PRD: <!-- nome ou link do RF/RNF/PRD -->

- [ ] Requisito funcional 1
- [ ] Requisito funcional 2
- [ ] Requisito funcional 3

<!-- Esta secao e obrigatoria apenas para tickets do tipo `task`. Para tickets `logico` ou `bug`, omita completamente esta secao quando nao houver PRD associado. -->

## Requisitos Tecnicos

Camadas impactadas: <!-- repetir apenas as camadas reais -->

Fluxo - <!-- nome do endpoint, caso de uso ou fluxo -->:

```text
<!-- Descrever o fluxo tecnico passo a passo -->
```

Fluxo - <!-- proximo endpoint, caso de uso ou fluxo -->:

```text
<!-- Descrever o fluxo tecnico passo a passo -->
```

Contratos esperados:

- `UseCase.execute(...) -> ReturnType` - <!-- responsabilidade -->
- `Repository.method(...) -> ReturnType` - <!-- responsabilidade -->

## Referencias na Codebase

- `path/to/file` - <!-- motivo da referencia -->
- `path/to/other_file` - <!-- motivo da referencia -->

## Observacoes / Dependencias

DoR - Verificar antes de iniciar o desenvolvimento:

- [ ] Vinculada a uma US no Jira no padrao correto
- [ ] Campo de requisito preenchido com URL do RF/RNF/PRD no Confluence
- [ ] Estimativa adequada ao escopo; se exceder o limite acordado, dividir a task
- [ ] Responsavel atribuido
- [ ] Criterio de conclusao definido

DoD - Verificar antes de mover para Concluido:

- [ ] Criterio de conclusao tecnica atingido e verificado
- [ ] Testes escritos ou atualizados quando aplicavel
- [ ] Code review realizado e PR aprovado
- [ ] Commits seguem o padrao adotado pelo projeto
- [ ] Nenhum erro critico ou warning relevante introduzido no build
- [ ] Documentacao atualizada quando aplicavel

## Regras para preenchimento

- O conteudo deve sair pronto para colar no Jira.
- Nao resuma em excesso; detalhe o suficiente para orientar implementacao.
- Nao inclua secao `Titulo` nem comentarios HTML com titulo no corpo do ticket.
- Para tickets do tipo `task`, sempre carregue e considere primeiro os PRDs publicados no Confluence antes de redigir os tickets.
- Para tickets do tipo `task`, sempre inclua os links reais dos PRDs usados como referencia, priorizando o link publicado no Confluence em vez de rascunhos ou links de edicao.
- Para tickets do tipo `logico` ou `bug`, nao invente PRD nem mantenha a secao `Requisitos de Produto` por padrao; omita essa secao quando nao houver documento funcional associado.
- Em tickets tecnicos, inclua fluxos, contratos esperados e referencias reais da codebase sempre que possivel.
- Quando houver endpoints, descreva cada fluxo separadamente.
- Quando houver lacunas arquiteturais, explicite o que ainda nao existe e precisa ser criado.
- Ajuste as camadas impactadas conforme o ticket; nao mantenha exemplos genericos.
- A secao `Observacoes / Dependencias` e sempre fixa e deve ser reproduzida exatamente como definida neste prompt.
- Vincule cada ticket a milestone/epic fornecida, quando aplicavel.

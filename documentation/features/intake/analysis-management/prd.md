# PRD — Gerenciamento de Analises no Intake

## Objetivo

Permitir que usuarios autenticados gerenciem suas analises no contexto de intake, criando novas analises, consultando a lista, visualizando detalhes, renomeando e arquivando itens ja existentes.

## Valor entregue

- [x] Usuario autenticado pode criar uma nova analise com nome gerado automaticamente.
- [x] Usuario autenticado pode listar apenas as analises da propria conta com paginacao por cursor.
- [x] Usuario autenticado pode visualizar os detalhes de uma analise especifica.
- [x] Usuario autenticado pode renomear uma analise existente.
- [x] Usuario autenticado pode arquivar uma analise de forma idempotente.
- [x] A API oculta a existencia de analises de outras contas retornando `404` nos fluxos de detalhe, rename e archive.

## Regras de negocio visiveis ao produto

- O nome da nova analise e gerado pelo servidor no formato `Nova analise #N`.
- A criacao nasce no estado `WAITING_PETITION`.
- A listagem permite filtro textual, filtro por arquivamento e paginacao por cursor.
- O arquivamento nao desfaz estado anterior e repetir a operacao nao gera erro.

## O que ficou fora desta entrega

- Validacao de existencia e ownership de `folder_id`.
- Fluxos de folders.
- Alteracoes em jobs, websocket ou migrations de banco.

## Observacoes

- Este PRD foi criado na conclusao da spec porque nao havia um PRD formal previo para este modulo.

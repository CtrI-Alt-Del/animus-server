# PRD — RF 02: Analise do texto de peticoes iniciais

Referencia original no Confluence: `https://joaogoliveiragarcia.atlassian.net/wiki/x/CID5`

## Status do recorte entregue

- [x] O usuario pode registrar uma peticao vinculada a uma analise existente e da propria conta.
- [x] O resumo da peticao e acionado manualmente em uma segunda etapa, sem processamento automatico no upload.
- [x] O backend le documentos `PDF` e `DOCX` armazenados no bucket e gera um resumo estruturado com IA.
- [x] O resumo gerado fica persistido para reprocessamentos seguros do mesmo `petition_id`.
- [x] O fluxo diferencia arquivo ausente de arquivo ilegivel e interrompe a analise antes da IA quando a leitura falha.

## Ajustes de escopo refletidos no produto

- [x] O backend deste recorte cobre cadastro da peticao e resumo manual; o upload do arquivo continua separado no fluxo de storage/signed URL.
- [x] O sistema continua aceitando apenas `PDF` e `DOCX`, mas a validacao efetiva do tipo acontece na etapa de leitura do documento para resumo.
- [ ] O limite de 20 MB por arquivo ainda nao e aplicado neste fluxo do servidor.
- [ ] A regra de um unico arquivo por analise nao foi aplicada no backend atual; multiplas peticoes por `analysis_id` continuam permitidas.
- [ ] O timeout de 60 segundos esta configurado no cliente Gemini, mas ainda nao possui traducao explicita de erro dedicada para a API.

## Valor entregue

- Reduz o tempo de triagem inicial ao permitir que a conta autenticada cadastre a peticao e obtenha um resumo objetivo do caso sem sair do fluxo do app.
- Garante isolamento por conta no acesso a analises, peticoes e documentos associados.
- Prepara a base para a etapa seguinte de busca de precedentes com um resumo estruturado e reaproveitavel.

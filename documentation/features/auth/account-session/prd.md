# PRD - RF 01: Gerenciamento de sessao do usuario

Fonte original: `https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/16908291`

## Visao Geral

Esta funcionalidade controla o acesso ao aplicativo Animus. O usuario consegue criar conta, confirmar o e-mail, entrar com credenciais validas e manter uma sessao autenticada para acessar as analises juridicas do produto com seguranca.

## Itens de Produto

- [x] Cadastro via e-mail e senha
  - Valor entregue: o backend cria a conta, persiste a senha com hash, envia um codigo OTP de 6 digitos por e-mail e permite reenviar um novo codigo quando necessario.
  - Regras de negocio refletidas na entrega:
    - a confirmacao de e-mail acontece por codigo OTP com validade de 1 hora;
    - o codigo e de uso unico e e invalidado apos a confirmacao bem-sucedida;
    - o app pode solicitar reenvio do codigo quando o anterior expirar ou nao chegar.

- [x] Login via e-mail e senha
  - Valor entregue: o backend autentica com e-mail e senha e retorna a sessao com `access_token` e `refresh_token`.
  - Regras de negocio refletidas na entrega:
    - credenciais invalidas retornam mensagem generica, sem revelar se o erro esta no e-mail, na senha ou na ausencia de senha cadastrada;
    - conta com e-mail nao confirmado retorna bloqueio explicito para o app conduzir o usuario ao fluxo correto;
    - conta desativada retorna bloqueio explicito, impedindo novo acesso.

- [x] Login com conta Google
  - Valor entregue: o backend autentica com Google, cria a conta no primeiro acesso quando necessario e reaproveita a conta existente nos acessos seguintes.

- [ ] Redefinicao de senha por e-mail
  - Pendente de implementacao.

- [ ] Edicao de perfil
  - Pendente de implementacao.

- [ ] Solicitacao de exclusao de conta pelo proprio usuario
  - Pendente de implementacao.

## Impacto para o Produto

- O app ja consegue concluir o fluxo principal de acesso do usuario por cadastro manual, verificacao de e-mail por OTP, login por e-mail e senha e login com Google.
- O mobile pode diferenciar credenciais invalidas, e-mail nao confirmado e conta desativada pelo `status_code` e pela `message`, sem quebra do envelope atual de erro.
- O fluxo de verificacao de e-mail fica mais aderente ao app mobile, sem dependencia de link HTML externo para ativacao da conta.
- A sessao continua usando o contrato atual com expiracao declarada nos tokens, preservando compatibilidade com os consumidores existentes.

## Divergencias Relevantes em Relacao ao Escopo Inicial

- O backend manteve o contrato de erro enxuto com `title` e `message`, sem adicionar um campo `code`.
- O fluxo de login por e-mail e senha foi entregue sem introduzir um DTO de entrada especifico no `core`, privilegiando uma assinatura simples no use case e alinhada ao padrao atual do contexto `auth`.
- A confirmacao de e-mail foi refinada para um fluxo por codigo OTP numerico de 6 digitos com reenvio, substituindo o link HTML legado para melhor aderencia ao uso no app.

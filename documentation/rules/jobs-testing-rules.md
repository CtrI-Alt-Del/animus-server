# Regras de testes de Jobs PubSub

## Escopo deste documento

Este documento define regras para testes de jobs assincronos em
`src/animus/pubsub/inngest/jobs/**`, com base no padrao observado em
`tests/pubsub/inngest/jobs/**`.

Objetivo: garantir testes consistentes, confiaveis e focados no contrato do
job com o runtime de eventos, sem deslocar a regra de negocio para a camada de
`pubsub`.

### Nomenclatura de arquivo, classe e metodos

- Arquivo: `test_<nome_job>.py`.
- Classe de teste: `Test<JobName>`.
- Metodo de teste: `test_should_<resultado>_when_<condicao>`.

Exemplo real:

- `tests/pubsub/inngest/jobs/auth/test_send_account_verification_email_job.py`
- `TestSendAccountVerificationEmailJob`
- `test_should_process_event_with_real_inngest_dev_server`

## Estrutura do teste

### Setup compartilhado via fixtures

Para testes de jobs do Inngest, prefira usar a fixture `inngest_runtime`
definida em `tests/fixtures/inngest_fixtures.py`.

Padrao atual:

```python
def test_should_process_event_with_real_inngest_dev_server(
    self,
    monkeypatch: MonkeyPatch,
    inngest_runtime: Any,
) -> None:
    ...
```

### Formato Arrange / Act / Assert

Organize cada teste em tres blocos logicos, separados por linha em branco:

1. Arrange: patch de side effects externos, montagem do payload e capturas.
2. Act: publicacao do evento via `inngest_runtime.post_event(...)`.
3. Assert: validacao do processamento observavel do job.

### O que sempre validar

- O evento correto e aceito pelo runtime (`response.status == 200`).
- O side effect esperado do job acontece exatamente uma vez.
- Os dados entregues ao colaborador final estao normalizados como esperado.

## Escopo do teste de job

### Foco do teste

Teste de job deve validar o contrato assincrono observavel entre:

- nome do evento publicado;
- payload consumido pelo job;
- orquestracao do handler no runtime do Inngest;
- side effect final disparado pelo job.

### O que NAO testar aqui

- detalhes internos do SDK do Inngest;
- implementacao detalhada do use case chamado pelo job;
- comportamento interno do provider externo real.

## Isolamento de dependencias e side effects

### O que mockar

Mocke fronteiras externas nao deterministicas ou lentas, como providers de
email, notificacao, storage ou integracoes terceiras.

Padrao observado:

- patch de `ResendEmailSenderProvider.send_account_verification_email` para
  capturar a chamada sem enviar email real.

### O que nao mockar por padrao

- Nao mocke o runtime de disparo do evento quando o objetivo do teste for
  validar a integracao real do job com o Inngest dev server.
- Nao mocke o proprio job.

### Regra pratica

Se o objetivo do teste e provar que o job esta registrado e processa o evento
corretamente, prefira usar o runtime real do ambiente de teste e mockar apenas
o efeito colateral externo final.

## Sincronizacao e espera assincrona

Jobs do Inngest podem concluir alguns instantes apos o `post_event` retornar.
Por isso:

- use polling com timeout explicito para aguardar o side effect;
- falhe com mensagem objetiva quando a condicao nao for satisfeita;
- mantenha timeout suficiente para evitar flakes, mas curto o bastante para nao
  mascarar travamentos.

Padrao observado:

```python
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    if len(captured_calls) == 1:
        break
    time.sleep(0.1)
else:
    raise AssertionError('condition not satisfied before timeout')
```

## Payloads e asserts

### Dados do evento

- Publique payloads minimos e explicitos via `inngest_runtime.post_event(...)`.
- Use valores literais curtos e legiveis, como emails e codigos fixos.
- Quando o job normaliza ou converte dados, valide o valor final observado, nao
  a implementacao interna da normalizacao.

### Assert recomendado

Prefira asserts objetivos sobre os dados capturados pelo mock, por exemplo:

```python
assert captured_calls == [
    {
        'account_email': 'maria@example.com',
        'otp': '123456',
    }
]
```

## Warnings e ruido do ambiente

Quando o runtime do Inngest ou dependencias do websocket emitirem warnings de
terceiros que nao fazem parte do contrato testado:

- filtre apenas os warnings conhecidos e inevitaveis;
- mantenha o filtro local ao teste, com `@pytest.mark.filterwarnings(...)`;
- nao use filtros amplos que possam esconder problema real do projeto.

## Cobertura minima por job

Para cada job novo, incluir no minimo:

- um teste validando que o evento correto e processado pelo runtime;
- um teste validando o side effect principal ou a delegacao final;
- um teste adicional quando houver ramificacao critica de payload, validacao ou
  erro recuperavel.

Se o job for apenas um orquestrador fino sem multiplos ramos, um teste de fluxo
principal pode ser suficiente no primeiro momento, desde que cubra runtime,
payload e side effect.

## Boas praticas

- Mantenha o teste orientado a comportamento observavel do job.
- Use mocks apenas nas bordas externas realmente necessarias.
- Evite depender de tempo exato; dependa de timeout + polling.
- Reaproveite `inngest_runtime` em vez de montar servidor/container manualmente
  por teste.
- Mantenha consistencia de estilo em `tests/pubsub/inngest/jobs`.

## Checklist rapido para novo teste de job

1. Arquivo no caminho correto: `tests/pubsub/inngest/jobs/<contexto>/`.
2. Nome do arquivo e da classe seguindo convencao.
3. Uso da fixture `inngest_runtime` para exercitar o runtime real.
4. Patch apenas do side effect externo final.
5. Assert de aceite do evento (`status == 200`).
6. Assert do efeito observavel com timeout/polling controlado.
7. Sem acoplamento a detalhes internos do SDK ou do use case chamado.

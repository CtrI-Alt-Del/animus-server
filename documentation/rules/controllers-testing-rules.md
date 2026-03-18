# Regras de testes da camada REST (Controllers)

## Escopo deste documento

Este documento define regras para testes de controllers da camada `rest`, com
base no padrao observado em `tests/rest/controllers/**`.

Objetivo: garantir testes consistentes, legiveis e focados no contrato HTTP
exposto ao cliente.

### Nomenclatura de arquivo, classe e metodos

- Arquivo: `test_<nome_controller>.py`.
- Classe de teste: `Test<ControllerName>`.
- Metodo de teste: `test_should_<resultado>_when_<condicao>`.

Exemplo real:

- `tests/rest/controllers/profiling/test_create_horse_controller.py`
- `TestCreateHorseController`
- `test_should_return_422_when_birth_month_is_invalid`

## Estrutura do teste

### Setup compartilhado via fixture

Para testes REST, prefira usar as fixtures `client: TestClient` e
`auth_headers: dict[str, str]` (para rotas autenticadas) definidas em
`tests/conftest.py`.

Padrao atual:

```python
def test_should_create_horse_and_return_payload(
    self, client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        '/profiling/horses',
        json={...},
        headers=auth_headers,
    )
```

### Formato Arrange / Act / Assert

Organize cada teste em tres blocos logicos, separados por linha em branco:

1. Arrange: monta payload e dados do cenario.
2. Act: executa request HTTP (`client.get/post/put/delete`).
3. Assert: valida `status_code` e corpo da resposta.

### O que sempre validar

- `status_code` esperado para o cenario.
- Contrato de resposta em sucesso (campos relevantes do JSON).
- Comportamento de validacao em erro (`422` para input invalido).

## Escopo de teste REST (o que testar)

### Foco do teste

Teste de controller deve validar contrato de borda HTTP:

- rota + verbo corretos;
- validacao de entrada;
- formato da resposta e status;
- serializacao minima esperada para o cliente.

### O que NAO testar aqui

- detalhes internos do use case;
- detalhes internos do repositorio/ORM;
- implementacao de validadores do framework alem do contrato observavel.

## Mocking e isolamento de dependencias

### Quando NAO mockar

No estado atual, os testes REST exercitam fluxo real da aplicacao com
`TestClient`, sem mock do controller/use case.

Isso e desejavel para validar integracao HTTP real entre:

- roteamento;
- schema de entrada;
- controller;
- camada de aplicacao.

### Quando mockar

Mocke apenas fronteiras externas nao deterministicas (ex.: servicos terceiros),
quando forem introduzidas e tornarem o teste instavel/lento.

## Padroes de validacao de entrada

### Erro de validacao

Para payload invalido, valide ao menos:

- `status_code == 422`.

Evite acoplar teste a mensagem textual completa de erro do framework, salvo
quando o contrato exigir esse detalhe explicitamente.

### Parametrizacao para variacoes invalidas

Use `pytest.mark.parametrize` para agrupar variacoes da mesma regra.

Exemplo observado:

```python
@pytest.mark.parametrize('birth_month', [0, 13])
def test_should_return_422_when_birth_month_is_invalid(...):
    ...
```

## Regras de dados de teste

### Valores literais vs dados dinamicos

- Prefira valores literais curtos e explicitos para leitura rapida.
- Use dados dinamicos apenas quando fazem parte da regra do cenario.

Exemplo observado:

- `datetime.now().year + 1` para validar ano futuro invalido.

### Evitar flakiness temporal

Ao usar tempo atual, mantenha a assertiva robusta para nao depender de horario
exato. Exemplo recomendado: comparar apenas regra de fronteira (ano futuro).

## Integracao com banco em testes REST

Os testes REST atuais usam fixture de banco em `tests/conftest.py` com schema
isolado por sessao de testes.

Regras praticas:

- nao compartilhar estado implicito entre testes;
- manter cada teste independente;
- confiar no setup/teardown central para criar e limpar schema.

## Cobertura minima por endpoint

Para cada endpoint novo, incluir no minimo:

- um teste de sucesso (`2xx`) validando `status_code` e payload principal;
- um teste de erro de validacao (`4xx`, normalmente `422`).

Quando houver mais de uma regra de validacao relevante, adicione casos
especificos (ou parametrizados) por regra.

## Boas praticas

- Mantenha cada teste curto e com uma unica intencao.
- Use nomes orientados a comportamento.
- Faça asserts objetivos em campos chave; evite snapshots grandes.
- Nao dependa de ordem incidental de campos no JSON.
- Reaproveite fixture `client` em vez de criar app manualmente por teste.
- Mantenha consistencia de estilo em `tests/rest/controllers`.

## Checklist rapido para novo teste de controller

1. Arquivo no caminho correto: `tests/rest/controllers/<modulo>/`.
2. Nome do arquivo e da classe seguindo convencao.
3. Uso de `client: TestClient` e `auth_headers` (se autenticado) como fixtures.
4. Cenario de sucesso com assert de `status_code` e payload.
5. Cenario de erro de validacao com `status_code` apropriado (`422`).
6. Parametrizacao para variacoes da mesma regra, quando aplicavel.
7. Independencia entre testes (sem acoplamento de estado).

# Regras de testes unitarios de Use Cases

## Escopo deste documento

Este documento define regras para testes unitarios dos use cases da camada
`core`, com base no padrao observado em `tests/core/**/use_cases`.

Objetivo: garantir testes consistentes, legiveis e focados no comportamento
de negocio, sem acoplamento com infraestrutura.

### Nomenclatura de arquivo, classe e metodos

- Arquivo: `test_<nome_use_case>.py`.
- Classe de teste: `Test<UseCaseName>`.
- Metodo de teste: `test_should_<resultado>_when_<condicao>`.

Exemplos reais:

- `test_should_create_horse_and_add_it_to_repository`
- `test_should_raise_horse_not_found_error_when_horse_does_not_exist`

## Estrutura do Teste

### Setup compartilhado por classe

Use `pytest.fixture(autouse=True)` para preparar a instancia do use case e seus
dobles de dependencia em todos os testes da classe.

Padrao recomendado:

```python
@pytest.fixture(autouse=True)
def setup(self) -> None:
    self.repository_mock = create_autospec(HorsesRepository, instance=True)
    self.use_case = CreateHorseUseCase(repository=self.repository_mock)
```

### Formato Arrange / Act / Assert

Organize cada teste em tres blocos logicos, separados por linha em branco:

1. Arrange: prepara entradas e stubs.
2. Act: executa `use_case.execute(...)`.
3. Assert: valida retorno, erro e interacoes.

### O que sempre validar

- Resultado funcional do caso de uso (DTO retornado, erro esperado, etc.).
- Interacao com dependencia externa (ex.: `assert_called_once_with`).
- Comportamento de sucesso e de falha para cada use case.

## Como e quando utilizar Mocking de Dependencias

### Quando mockar

Mocke somente fronteiras externas ao caso de uso, principalmente interfaces de
repositorio (ports), para manter o teste unitario puro e rapido.

No estado atual do projeto, o alvo principal de mock e `HorsesRepository`.

### Como mockar

- Use `create_autospec(<Interface>, instance=True)` para garantir aderencia da
  assinatura ao contrato da interface.
- Configure retorno explicito por cenario:
  - sucesso: `find_by_id.return_value = horse`
  - ausencia: `find_by_id.return_value = None`
- Verifique chamadas com argumentos exatos:
  - `assert_called_once_with(<valor_esperado>)`

### O que evitar

- Nao mockar a propria unidade sob teste (`UseCase`).
- Nao mockar entidades e estruturas de dominio sem necessidade.
- Nao validar detalhes internos irrelevantes de implementacao.

## Padroes de Teste

### Testes de caminho feliz e caminho de erro

Cada use case deve ter, no minimo:

- um teste de sucesso (resultado esperado);
- um teste de erro/regra de excecao.

Exemplo observado:

- `GetHorseUseCase` cobre retorno do `horse.dto` e `HorseNotFoundError`.

### Assert de erro com pytest

Use `pytest.raises(...)` para validar excecoes de dominio:

```python
with pytest.raises(HorseNotFoundError):
    self.use_case.execute(horse_id='missing-horse-id')
```

### Assert de estado + interacao

Sempre que fizer sentido, combine:

- assert do valor retornado (estado visivel);
- assert da chamada ao repositorio (interacao).

Isso evita falso-positivo em testes que passam sem validar colaboracoes.

## Como e quando usar Fakers

### Quando usar

Use fakers para gerar dados validos e reduzir boilerplate em cenarios onde o
valor exato nao e relevante para a regra testada.

Padrao atual:

- `HorsesFaker.fake_dto()` para entrada do use case.
- `HorsesFaker.fake()` para entidade retornada por repositorio.

### Quando NAO usar dados aleatorios

Evite aleatoriedade quando o valor for parte essencial da regra. Nesses casos,
fixe explicitamente os campos necessarios via parametros do faker.

Exemplo:

```python
horse_dto = HorsesFaker.fake_dto(name='Bidu', birth_month=5, birth_year=2018)
```

### Regras praticas para fakers

- Faker deve retornar dados validos para o dominio.
- Prefira centralizar construcao de massa de teste em `tests/fakers/...`.
- Use overrides para tornar o cenario explicito.
- Se houver flakiness por aleatoriedade, fixe seed no proprio faker de teste.

## Boas praticas

- Mantenha cada teste curto, com uma unica intencao.
- Use nomes descritivos orientados a comportamento.
- Cubra apenas contrato externo do use case (`execute`) e seus efeitos.
- Nao acople o teste a detalhes internos de implementacao.
- Reaproveite setup com fixture autouse para reduzir duplicacao.
- Mantenha consistencia de estilo entre todos os contexts de `tests/core`.

## Checklist rapido para novo teste de use case

1. Arquivo no caminho correto: `tests/core/<contexto>/use_cases/`.
2. Nome do arquivo e da classe seguindo convencao.
3. Fixture autouse com `create_autospec` da interface de dependencia.
4. Cenario de sucesso validando retorno + chamada de dependencia.
5. Cenario de erro validando excecao de dominio + chamada de dependencia.
6. Uso de faker para reduzir boilerplate, com overrides quando necessario.

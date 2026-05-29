# Troubleshooting de Migrações do Banco

Este documento descreve o problema real encontrado ao executar as migrações do
projeto com Alembic (`uv run poe db:upgrade`) e como resolver o ambiente sem
corromper a árvore de revisões.

O diagnóstico inicial apontava apenas para `DuplicateTable` em `accounts`, mas a
causa real era uma combinação de cinco problemas:

1. A aplicação carregava o `DATABASE_URL` errado por causa da ordem dos arquivos
   `.env`.
2. Uma migration autogerada tentava recriar a tabela `accounts`.
3. A árvore do Alembic tinha múltiplos heads.
4. O banco local estava em drift: algumas tabelas existiam sem a revision
   correspondente estar marcada como aplicada.
5. Algumas migrations antigas não batiam mais com os models atuais.

## Resumo da Correção

Arquivos envolvidos:

- `src/animus/constants/env.py`
- `.env`, `.env.example`
- `alembic.ini`
- `docker-compose.yaml`
- `migrations/versions/bb5751bdd2fd_.py`
- `migrations/versions/20260420_120000_create_folders_table.py`
- `migrations/versions/20260420_120000_create_analysis_precedent_feedback_tables.py`
- `migrations/versions/20260425_180000_create_analysies_precedent_legal_features_table.py`
- `migrations/versions/20260511_120000_intake_analysis_documents_case_summaries_and_drafts.py`
- `migrations/versions/20260527_120000_merge_petition_drafts_and_manual_precedents_heads.py`
- `migrations/versions/20260527_130000_reconcile_intake_schema_with_models.py`

Comportamento esperado após a correção:

```text
uv run poe db:upgrade
uv run poe db:current
# 20260527_130000 (head)

uv run alembic check
# No new upgrade operations detected.
```

## Problema 1: Conexão no Banco Errado

### Sintoma

O primeiro erro era de autenticação:

```text
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed:
FATAL: password authentication failed for user "animus"
```

Esse erro acontecia antes de qualquer migration rodar. Portanto, ele não era um
erro de schema; era um erro de conexão.

### Causa Real

Havia dois fatores:

1. O `docker-compose.yaml` publicava o Postgres do projeto em `5432:5432`.
2. O `Env` carregava os arquivos nesta ordem:

```python
env_file=('.env', '.env.example')
```

No `pydantic-settings`, quando vários arquivos dotenv são informados, os arquivos
posteriores têm prioridade sobre os anteriores. Ou seja: `.env.example` estava
sobrescrevendo `.env`.

Isso fazia o valor efetivo de `Env.DATABASE_URL` vir do `.env.example`, que
apontava para:

```text
postgresql://animus:animus@localhost:5432/animus
```

Mesmo que o `.env` local estivesse correto com `127.0.0.1:5433`, ele perdia para
o `.env.example`.

Além disso, `localhost` pode resolver primeiro para IPv6 (`::1`). No erro real,
o host usado foi `localhost (::1)`, o que indicava que o processo estava falando
com outro Postgres local, não necessariamente com o container esperado.

### Correção

Inverter a ordem dos dotenvs em `src/animus/constants/env.py`:

```python
model_config = SettingsConfigDict(
    env_file=('.env.example', '.env'),
    extra='ignore',
    env_file_encoding='utf-8',
)
```

Assim, `.env.example` fornece defaults e `.env` sobrescreve valores locais.

Também alinhar a porta do Postgres local para `5433`:

```yaml
# docker-compose.yaml
ports: [5433:5432]
```

E atualizar as URLs:

```text
# .env e .env.example
DATABASE_URL=postgresql://animus:animus@127.0.0.1:5433/animus

# alembic.ini
sqlalchemy.url = postgresql://animus:animus@127.0.0.1:5433/animus
```

Observação: `migrations/env.py` sobrescreve `sqlalchemy.url` com
`Env.DATABASE_URL`, então o `alembic.ini` não era a única fonte do erro. Mesmo
assim, manter o `alembic.ini` coerente evita diagnósticos falsos e problemas em
execuções fora do fluxo padrão.

Depois da alteração de porta, recrie o serviço:

```bash
docker compose up -d postgres
```

Valide a URL efetiva:

```bash
uv run python -c "from urllib.parse import urlparse; from animus.constants import Env; u=urlparse(Env.DATABASE_URL); print(u.hostname, u.port)"
```

O resultado esperado é:

```text
127.0.0.1 5433
```

## Problema 2: Migration Duplicada de `accounts`

### Sintoma

Depois de corrigir a conexão, o Alembic passava a falhar com:

```text
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable)
relation "accounts" already exists
```

### Causa Real

A migration inicial `20260319_000001_create_accounts_table.py` já criava a
tabela `accounts`.

Depois dela, a migration `bb5751bdd2fd_.py` também tentava executar:

```python
op.create_table('accounts', ...)
op.create_index(op.f('ix_accounts_email'), 'accounts', ['email'], unique=True)
```

Isso é uma migration autogerada incorreta. Ela não deveria recriar uma tabela já
introduzida por uma revision anterior.

O campo `password_hash` já era tratado corretamente por outra migration:

```text
8cb87a9d6608_make_password_hash_null.py
```

Logo, `bb5751bdd2fd_.py` não tinha mais nenhuma operação válida a aplicar.

### Correção

Não remova o arquivo. Outras migrations dependem do `revision` dele via
`down_revision`. Apagar a migration quebra a árvore de revisões.

Transforme a migration em no-op:

```python
"""no-op duplicate accounts revision

Revision ID: bb5751bdd2fd
Revises: 20260319_000001
Create Date: 2026-03-24 09:03:35.772981
"""

from collections.abc import Sequence


revision: str = 'bb5751bdd2fd'
down_revision: str | Sequence[str] | None = '20260319_000001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
```

## Problema 3: Múltiplos Heads no Alembic

### Sintoma

Após resolver `accounts`, `uv run poe db:upgrade` falhava com:

```text
FAILED: Multiple head revisions are present for given argument 'head';
please specify a specific target revision, '<branchname>@head' to narrow to a
specific head, or 'heads' for all heads
```

### Causa Real

O comando `alembic upgrade head` só funciona quando existe um único head. O
histórico tinha dois heads saindo da mesma revision:

```text
20260517_223000
├── 20260522_120000
└── 4d2d879df9c5
```

Eles eram branches legítimos:

- `20260522_120000` reestrutura `petition_drafts`.
- `4d2d879df9c5` adiciona `is_manually_added` em `analysis_precedents`.

Como os dois devem existir, a solução correta não é escolher um e ignorar o
outro. A solução correta é criar uma merge revision.

### Correção

Criar uma migration no-op com `down_revision` apontando para os dois heads:

```python
"""merge petition drafts and manual precedents heads

Revision ID: 20260527_120000
Revises: 20260522_120000, 4d2d879df9c5
Create Date: 2026-05-27 12:00:00
"""

from collections.abc import Sequence


revision: str = '20260527_120000'
down_revision: str | Sequence[str] | None = (
    '20260522_120000',
    '4d2d879df9c5',
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
```

Valide:

```bash
uv run alembic heads --verbose
```

O esperado é existir apenas um head depois da merge revision.

## Problema 4: Drift Local em `folders`

### Sintoma

Depois da merge revision, o upgrade falhava com:

```text
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable)
relation "folders" already exists
```

### Causa Real

O banco local estava marcado em:

```text
d40da3f4643d
```

Mas a tabela `folders` e seus índices já existiam fisicamente no banco. A revision
`20260420_120001`, que cria `folders`, ainda não estava registrada como aplicada
na tabela `alembic_version`.

Esse é um drift entre:

- o estado real do schema;
- e o estado registrado pelo Alembic.

Esse caso pode acontecer quando migrations são aplicadas parcialmente, quando se
usa `stamp` sem garantir o schema, ou quando branches antigos são reorganizados.

### Correção

Como a tabela existente batia com a migration, a correção segura foi tornar a
revision idempotente:

```python
op.create_table(
    'folders',
    ...
    if_not_exists=True,
)

op.create_index(
    op.f('ix_folders_account_id'),
    'folders',
    ['account_id'],
    if_not_exists=True,
)

op.create_index(
    op.f('ix_analyses_folder_id'),
    'analyses',
    ['folder_id'],
    if_not_exists=True,
)
```

E no downgrade:

```python
op.drop_index(
    op.f('ix_analyses_folder_id'),
    table_name='analyses',
    if_exists=True,
)
op.drop_index(
    op.f('ix_folders_account_id'),
    table_name='folders',
    if_exists=True,
)
op.drop_table('folders', if_exists=True)
```

Essa abordagem mantém o banco limpo funcionando e também permite recuperar um
banco local que já possui `folders`.

## Problema 5: Schema Diferente dos Models

### Sintoma

Mesmo após `uv run poe db:upgrade` concluir, `uv run alembic check` detectava
operações novas:

```text
FAILED: New upgrade operations detected
```

Entre elas:

- criação de `petitions`;
- criação de `petition_summaries`;
- remoção do índice `ix_analysis_documents_analysis_id`;
- mudança de tipo em colunas `created_at`.

### Causa Real

O schema final produzido pelas migrations não batia com os models importados em
`migrations/env.py`.

Os principais desalinhamentos eram:

1. `PetitionModel` e `PetitionSummaryModel` ainda existem e são usados por
   repositories, mas a migration `20260511_120000...` removia as tabelas
   `petitions` e `petition_summaries`.
2. `AnalysisDocumentModel.analysis_id` é primary key. Criar um índice separado em
   `analysis_documents.analysis_id` era redundante e aparecia como índice a
   remover no autogenerate.
3. Algumas migrations criavam `created_at` com `sa.DateTime(timezone=True)`,
   enquanto o `Model` base define `created_at` e `updated_at` como `DateTime()`
   sem timezone.

### Correção

Foram feitos dois tipos de ajuste.

Primeiro, corrigir migrations antigas para bancos limpos:

- `20260511_120000...` não deve remover `petitions` e `petition_summaries`.
- `20260511_120000...` não deve criar índice redundante em
  `analysis_documents.analysis_id`.
- Migrations que criam `created_at` em tabelas de precedentes devem usar
  `sa.DateTime()` quando o model espera `DateTime()` sem timezone.

Segundo, adicionar uma migration de reparo para bancos que já tinham passado pelo
estado quebrado:

```text
20260527_130000_reconcile_intake_schema_with_models.py
```

Essa migration:

- recria `petitions` se a tabela estiver ausente;
- recria `petition_summaries` se a tabela estiver ausente;
- recria `ix_petitions_analysis_id` se o índice estiver ausente;
- repovoa `petitions` a partir de `analysis_documents` sem duplicar linhas;
- repovoa `petition_summaries` a partir de `case_summaries` quando possível;
- remove o índice redundante `ix_analysis_documents_analysis_id`, se existir;
- ajusta `created_at` de tabelas específicas de `TIMESTAMP WITH TIME ZONE` para
  `TIMESTAMP WITHOUT TIME ZONE`, alinhando com o `Model` base.

## Procedimento de Recuperação Local

Use este fluxo quando o banco local estiver quebrado por migrations.

1. Confirme que o Postgres do projeto está publicado em `5433`:

```bash
docker ps --filter name=animus_postgres --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Resultado esperado:

```text
animus_postgres   Up ...   0.0.0.0:5433->5432/tcp
```

2. Se ainda estiver em `5432`, recrie o serviço:

```bash
docker compose up -d postgres
```

3. Confirme a URL efetiva usada pela aplicação:

```bash
uv run python -c "from urllib.parse import urlparse; from animus.constants import Env; u=urlparse(Env.DATABASE_URL); print(u.hostname, u.port)"
```

Resultado esperado:

```text
127.0.0.1 5433
```

4. Verifique o estado atual do Alembic:

```bash
uv run poe db:current
```

5. Aplique as migrations:

```bash
uv run poe db:upgrade
```

6. Confirme que ficou no head:

```bash
uv run poe db:current
```

Resultado esperado:

```text
20260527_130000 (head)
```

7. Verifique se models e schema estão alinhados:

```bash
uv run alembic check
```

Resultado esperado:

```text
No new upgrade operations detected.
```

## Validação em Banco Limpo

Além de testar no banco local, valide que a árvore completa sobe do zero em um
banco temporário.

No PowerShell:

```powershell
uv run python -c "from sqlalchemy import create_engine, text; engine=create_engine('postgresql://animus:animus@127.0.0.1:5433/postgres', isolation_level='AUTOCOMMIT'); conn=engine.connect(); conn.execute(text('DROP DATABASE IF EXISTS animus_migration_check WITH (FORCE)')); conn.execute(text('CREATE DATABASE animus_migration_check'))"

$env:DATABASE_URL='postgresql://animus:animus@127.0.0.1:5433/animus_migration_check'
uv run alembic upgrade head
uv run alembic check

uv run python -c "from sqlalchemy import create_engine, text; engine=create_engine('postgresql://animus:animus@127.0.0.1:5433/postgres', isolation_level='AUTOCOMMIT'); conn=engine.connect(); conn.execute(text('DROP DATABASE IF EXISTS animus_migration_check WITH (FORCE)'))"
```

O teste é considerado válido quando:

- `alembic upgrade head` termina sem erro;
- `alembic check` retorna `No new upgrade operations detected`;
- o banco temporário é removido no final.

## O Que Não Fazer

Não apague migrations antigas para "resolver" `DuplicateTable`.

Apagar uma migration que já está referenciada por `down_revision` quebra a árvore
do Alembic e pode impedir qualquer ambiente novo de subir do zero.

Não use `uv run poe db:sync` ou `alembic stamp head` como primeira resposta.

`stamp` só altera a tabela `alembic_version`; ele não cria, remove nem altera
tabelas. Usar `stamp` sem comparar o schema real com os models mascara o problema
e pode deixar o banco em drift permanente.

Não confie só na primeira mensagem de erro.

Neste caso, a sequência real foi:

1. erro de conexão/autenticação;
2. `DuplicateTable` em `accounts`;
3. múltiplos heads;
4. `DuplicateTable` em `folders`;
5. drift detectado por `alembic check`.

Cada erro bloqueava o próximo diagnóstico. A correção correta precisou resolver a
cadeia inteira.

## Checklist Final

Antes de considerar o problema resolvido, confirme:

- `Env.DATABASE_URL` aponta para `127.0.0.1:5433`;
- `docker ps` mostra `animus_postgres` em `5433->5432`;
- `uv run alembic heads --verbose` mostra um único head;
- `uv run poe db:upgrade` conclui sem erro;
- `uv run poe db:current` retorna `20260527_130000 (head)`;
- `uv run alembic check` retorna `No new upgrade operations detected`;
- um banco temporário limpo consegue executar `alembic upgrade head`.

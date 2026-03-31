# Plano de Implementacao

## Mapa de dependencias das fases

| Fase | Objetivo | Depende de | Pode rodar em paralelo com |
| --- | --- | --- | --- |
| F1 (Core) | Introduzir comportamento de dominio e caso de uso para atualizar `name` da conta autenticada | - | - |
| F2 (Drivers/Infra) | Confirmar e fixar o reaproveitamento da infraestrutura existente de persistencia/autenticacao, sem alterar schema/repositorio | F1 | - |
| F3 (API Layer) | Expor `PATCH /auth/account` via controller fino + registro no router `auth` | F1, F2 | - |

## Fases e tarefas

### F1 - Core

Objetivo: regra de negocio pronta e isolada no dominio/use case.

1. `T1.1` Adicionar `Account.rename(name: Name) -> None` em `src/animus/core/auth/domain/entities/account.py`.
   - Dependencia: `-`
2. `T1.2` Criar `UpdateAccountUseCase` em `src/animus/core/auth/use_cases/update_account_use_case.py` com `execute(account_id: str, name: str) -> AccountDto` e fluxo `Id.create -> Name.create -> find_by_id -> rename -> replace -> to_dto`.
   - Dependencia: `T1.1`
3. `T1.3` Exportar `UpdateAccountUseCase` em `src/animus/core/auth/use_cases/__init__.py`.
   - Dependencia: `T1.2`

### F2 - Drivers/Infra

Objetivo: integrar sem criar nova infraestrutura.

1. `T2.1` Consolidar uso dos contratos existentes `AccountsRepository.find_by_id(...)` e `replace(...)` (sem mudar interface) como dependencia do novo use case.
   - Dependencia: `T1.2`
2. `T2.2` Confirmar estrategia de injecao existente para API: `AuthPipe.get_account_id_from_request` + `DatabasePipe.get_accounts_repository_from_request`, sem alterar `SqlalchemyAccountsRepository` nem models/migrations.
   - Dependencia: `T2.1`

### F3 - API Layer

Objetivo: endpoint autenticado publicado no modulo `auth`.

1. `T3.1` Criar `UpdateAccountController` em `src/animus/rest/controllers/auth/update_account_controller.py` com `_Body{name: str}`, `PATCH /auth/account`, `status_code=200`, `response_model=AccountDto`, e chamada `UpdateAccountUseCase.execute(account_id=..., name=...)`.
   - Dependencia: `T1.3`, `T2.2`
2. `T3.2` Exportar `UpdateAccountController` em `src/animus/rest/controllers/auth/__init__.py`.
   - Dependencia: `T3.1`
3. `T3.3` Registrar `UpdateAccountController` em `src/animus/routers/auth/auth_router.py`.
   - Dependencia: `T3.2`

## Observacoes

- Escopo mantido: somente `name`; nenhum campo de senha/email nesse endpoint.
- Sem testes automatizados neste plano, conforme restricao da spec.
- Sem mudancas de banco, migrations ou fluxo de autenticacao existente.

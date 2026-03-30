from sqlalchemy.orm import Session

from animus.core.auth.domain.structures import Email
from animus.database.sqlalchemy.repositories.auth.sqlalchemy_accounts_repository import (
    SqlalchemyAccountsRepository,
)
from tests.fixtures.auth_fixtures import CreateAccountFixture


class TestSqlalchemyAccountsRepository:
    def test_should_return_password_hash_when_account_has_password_hash(
        self,
        sqlalchemy_session: Session,
        create_account: CreateAccountFixture,
    ) -> None:
        stored_password_hash = 'stored-password-hash'
        create_account(
            email='maria@example.com',
            password_hash=stored_password_hash,
        )
        repository = SqlalchemyAccountsRepository(sqlalchemy=sqlalchemy_session)

        password_hash = repository.find_password_hash_by_email(
            Email.create('maria@example.com')
        )

        assert password_hash is not None
        assert password_hash.value == stored_password_hash

    def test_should_return_none_when_account_does_not_have_password_hash(
        self,
        sqlalchemy_session: Session,
        create_account: CreateAccountFixture,
    ) -> None:
        create_account(
            email='maria@example.com',
            password_hash=None,
        )
        repository = SqlalchemyAccountsRepository(sqlalchemy=sqlalchemy_session)

        password_hash = repository.find_password_hash_by_email(
            Email.create('maria@example.com')
        )

        assert password_hash is None

    def test_should_return_none_when_account_does_not_exist(
        self,
        sqlalchemy_session: Session,
    ) -> None:
        repository = SqlalchemyAccountsRepository(sqlalchemy=sqlalchemy_session)

        password_hash = repository.find_password_hash_by_email(
            Email.create('maria@example.com')
        )

        assert password_hash is None

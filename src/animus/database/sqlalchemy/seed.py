from sqlalchemy import delete
from sqlalchemy.orm import Session

from animus.database.sqlalchemy import models
from animus.database.sqlalchemy.repositories.auth import SqlalchemyAccountsRepository
from animus.database.sqlalchemy.seeders import AuthSeeder
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.auth import Argon2idHashProvider


def _clear_database(session: Session) -> None:
    for table in reversed(models.Model.metadata.sorted_tables):
        session.execute(delete(table))


def seed() -> None:
    with Sqlalchemy.session() as session:
        _clear_database(session)

        accounts_repository = SqlalchemyAccountsRepository(session)
        hash_provider = Argon2idHashProvider()
        auth_seeder = AuthSeeder(accounts_repository, hash_provider)

        auth_seeder.seed()

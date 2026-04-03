from sqlalchemy import delete
from sqlalchemy.orm import Session

from animus.database.sqlalchemy import models
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_analisyses_repository import (
    SqlalchemyAnalisysesRepository,
)
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_petition_summaries_repository import (
    SqlalchemyPetitionSummariesRepository,
)
from animus.database.sqlalchemy.repositories.intake.sqlalchemy_petitions_repository import (
    SqlalchemyPetitionsRepository,
)
from animus.database.sqlalchemy.repositories.auth import SqlalchemyAccountsRepository
from animus.database.sqlalchemy.seeders import AuthSeeder, IntakeSeeder, StorageSeeder
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.providers.auth import Argon2idHashProvider


def _clear_database(session: Session) -> None:
    ignored_tables = {'precedents'}

    for table in reversed(models.Model.metadata.sorted_tables):
        if table.name in ignored_tables:
            continue

        session.execute(delete(table))


def seed() -> None:
    with Sqlalchemy.session() as session:
        _clear_database(session)

        accounts_repository = SqlalchemyAccountsRepository(session)
        hash_provider = Argon2idHashProvider()
        auth_seeder = AuthSeeder(accounts_repository, hash_provider)
        account_ids = auth_seeder.seed()

        intake_seeder = IntakeSeeder(
            analisyses_repository=SqlalchemyAnalisysesRepository(session),
            petitions_repository=SqlalchemyPetitionsRepository(session),
            petition_summaries_repository=SqlalchemyPetitionSummariesRepository(
                session
            ),
        )
        intake_seed = intake_seeder.seed(account_ids)
        if intake_seed is None:
            return

        storage_seeder = StorageSeeder()
        storage_seeder.seed(intake_seed['analysis_id'])

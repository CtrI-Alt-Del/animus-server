from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from animus.core.auth.interfaces import AccountsRepository
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.library.interfaces import FoldersRepository
from animus.database.sqlalchemy.repositories.auth import SqlalchemyAccountsRepository
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyAnalisysesRepository,
    SqlalchemyPetitionSummariesRepository,
    SqlalchemyPetitionsRepository,
)
from animus.database.sqlalchemy.repositories.library import SqlalchemyFoldersRepository


def get_sqlalchemy_session_from_request(request: Request) -> Session:
    return request.state.sqlalchemy_session


class DatabasePipe:
    @staticmethod
    def get_accounts_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> AccountsRepository:
        return SqlalchemyAccountsRepository(sqlalchemy)

    @staticmethod
    def get_petitions_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> PetitionsRepository:
        return SqlalchemyPetitionsRepository(sqlalchemy)

    @staticmethod
    def get_petition_summaries_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> PetitionSummariesRepository:
        return SqlalchemyPetitionSummariesRepository(sqlalchemy)

    @staticmethod
    def get_analisyses_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> AnalisysesRepository:
        return SqlalchemyAnalisysesRepository(sqlalchemy)

    @staticmethod
    def get_analysis_precedents_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> AnalysisPrecedentsRepository:
        return SqlalchemyAnalysisPrecedentsRepository(sqlalchemy)

    @staticmethod
    def get_folders_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> FoldersRepository:
        return SqlalchemyFoldersRepository(sqlalchemy)

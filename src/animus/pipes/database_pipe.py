from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from animus.core.auth.interfaces import AccountsRepository
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.analysis_documents_repository import (
    AnalysisDocumentsRepository,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.case_summaries_repository import (
    CaseSummariesRepository,
)
from animus.core.intake.interfaces.extracted_petitions_repository import (
    ExtractedPetitionsRepository,
)
from animus.core.intake.interfaces.judgment_drafts_repository import (
    JudgmentDraftsRepository,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.petition_drafts_repository import (
    PetitionDraftsRepository,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.library.interfaces import FoldersRepository
from animus.database.sqlalchemy.repositories.auth import SqlalchemyAccountsRepository
from animus.database.sqlalchemy.repositories.intake import (
    SqlalchemyAnalysisDocumentsRepository,
    SqlalchemyAnalysisPrecedentsRepository,
    SqlalchemyAnalisysesRepository,
    SqlalchemyCaseSummariesRepository,
    SqlalchemyExtractedPetitionsRepository,
    SqlalchemyJudgmentDraftsRepository,
    SqlalchemyPetitionDraftsRepository,
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
    def get_analysis_documents_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> AnalysisDocumentsRepository:
        return SqlalchemyAnalysisDocumentsRepository(sqlalchemy)

    @staticmethod
    def get_case_summaries_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> CaseSummariesRepository:
        return SqlalchemyCaseSummariesRepository(sqlalchemy)

    @staticmethod
    def get_extracted_petitions_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> ExtractedPetitionsRepository:
        return SqlalchemyExtractedPetitionsRepository(sqlalchemy)

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
    def get_petition_drafts_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> PetitionDraftsRepository:
        return SqlalchemyPetitionDraftsRepository(sqlalchemy)

    @staticmethod
    def get_judgment_drafts_repository_from_request(
        sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)],
    ) -> JudgmentDraftsRepository:
        return SqlalchemyJudgmentDraftsRepository(sqlalchemy)

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

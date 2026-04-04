from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos import AnalysisReportDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.use_cases import GetAnalysisReportUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetAnalysisReportController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/report',
            status_code=200,
            response_model=AnalysisReportDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            petitions_repository: Annotated[
                PetitionsRepository,
                Depends(DatabasePipe.get_petitions_repository_from_request),
            ],
            petition_summaries_repository: Annotated[
                PetitionSummariesRepository,
                Depends(DatabasePipe.get_petition_summaries_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
        ) -> AnalysisReportDto:
            use_case = GetAnalysisReportUseCase(
                analisyses_repository=analisyses_repository,
                petitions_repository=petitions_repository,
                petition_summaries_repository=petition_summaries_repository,
                analysis_precedents_repository=analysis_precedents_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id.value,
            )

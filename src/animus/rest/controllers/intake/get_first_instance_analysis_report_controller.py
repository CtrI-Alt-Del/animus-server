from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos import FirstInstanceAnalysisReportDto
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
    CaseSummariesRepository,
    JudgmentDraftsRepository,
)
from animus.core.intake.use_cases import GetFirstInstanceAnalysisReportUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetFirstInstanceAnalysisReportController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/first-instance-report',
            status_code=200,
            response_model=FirstInstanceAnalysisReportDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
            case_summaries_repository: Annotated[
                CaseSummariesRepository,
                Depends(DatabasePipe.get_case_summaries_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
            judgment_drafts_repository: Annotated[
                JudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
            ],
        ) -> FirstInstanceAnalysisReportDto:
            use_case = GetFirstInstanceAnalysisReportUseCase(
                analisyses_repository=analisyses_repository,
                analysis_documents_repository=analysis_documents_repository,
                case_summaries_repository=case_summaries_repository,
                analysis_precedents_repository=analysis_precedents_repository,
                judgment_drafts_repository=judgment_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id.value,
            )

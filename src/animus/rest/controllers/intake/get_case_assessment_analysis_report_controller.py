from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.structures.dtos import (
    CaseAssessmentAnalysisReportDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    CaseSummariesRepository,
    PetitionDraftsRepository,
)
from animus.core.intake.use_cases import GetCaseAssessmentAnalysisReportUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe


class GetCaseAssessmentAnalysisReportController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analyses/{analysis_id}/reports/case-assessment',
            status_code=200,
            response_model=CaseAssessmentAnalysisReportDto,
        )
        def _(
            analysis_id: str,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
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
            petition_drafts_repository: Annotated[
                PetitionDraftsRepository,
                Depends(DatabasePipe.get_petition_drafts_repository_from_request),
            ],
        ) -> CaseAssessmentAnalysisReportDto:
            use_case = GetCaseAssessmentAnalysisReportUseCase(
                analyses_repository=analyses_repository,
                analysis_documents_repository=analysis_documents_repository,
                case_summaries_repository=case_summaries_repository,
                analysis_precedents_repository=analysis_precedents_repository,
                petition_drafts_repository=petition_drafts_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                account_id=account_id.value,
            )

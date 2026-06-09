from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    SecondInstanceDecisionsRepository,
    SecondInstanceJudgmentDraftDocxProvider,
    SecondInstanceJudgmentDraftsRepository,
)
from animus.core.intake.use_cases import (
    ExportSecondInstanceJudgmentDraftDocxUseCase,
)
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.providers_pipe import ProvidersPipe


class ExportSecondInstanceJudgmentDraftDocxController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/second-instance-judgment-drafts/docx',
            status_code=201,
            response_model=AnalysisDocumentDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            judgment_drafts_repository: Annotated[
                SecondInstanceJudgmentDraftsRepository,
                Depends(DatabasePipe.get_judgment_drafts_repository_from_request),
            ],
            second_instance_decisions_repository: Annotated[
                SecondInstanceDecisionsRepository,
                Depends(
                    DatabasePipe.get_second_instance_decisions_repository_from_request,
                ),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(
                    DatabasePipe.get_analysis_precedents_repository_from_request,
                ),
            ],
            second_instance_judgment_draft_docx_provider: Annotated[
                SecondInstanceJudgmentDraftDocxProvider,
                Depends(
                    ProvidersPipe.get_second_instance_judgment_draft_docx_provider,
                ),
            ],
        ) -> AnalysisDocumentDto:
            use_case = ExportSecondInstanceJudgmentDraftDocxUseCase(
                analyses_repository=analyses_repository,
                judgment_drafts_repository=judgment_drafts_repository,
                second_instance_decisions_repository=(
                    second_instance_decisions_repository
                ),
                analysis_precedents_repository=analysis_precedents_repository,
                second_instance_judgment_draft_docx_provider=(
                    second_instance_judgment_draft_docx_provider
                ),
            )

            return use_case.execute(analysis_id=analysis.id.value)

from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import (
    AnalysesRepository,
    PetitionDraftDocxProvider,
    PetitionDraftsRepository,
)
from animus.core.intake.use_cases import ExportPetitionDraftDocxUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.providers_pipe import ProvidersPipe


class ExportPetitionDraftDocxController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/petition-drafts/docx',
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
            petition_drafts_repository: Annotated[
                PetitionDraftsRepository,
                Depends(DatabasePipe.get_petition_drafts_repository_from_request),
            ],
            petition_draft_docx_provider: Annotated[
                PetitionDraftDocxProvider,
                Depends(ProvidersPipe.get_petition_draft_docx_provider),
            ],
        ) -> AnalysisDocumentDto:
            use_case = ExportPetitionDraftDocxUseCase(
                analyses_repository=analyses_repository,
                petition_drafts_repository=petition_drafts_repository,
                petition_draft_docx_provider=petition_draft_docx_provider,
            )

            return use_case.execute(analysis_id=analysis.id.value)

from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import AnalysisDocumentsRepository
from animus.core.intake.use_cases import GetAnalysisDocumentUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class GetAnalysisDocumentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get(
            '/analysis/{analysis_id}/document',
            status_code=200,
            response_model=AnalysisDocumentDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analysis_documents_repository: Annotated[
                AnalysisDocumentsRepository,
                Depends(DatabasePipe.get_analysis_documents_repository_from_request),
            ],
        ) -> AnalysisDocumentDto:
            use_case = GetAnalysisDocumentUseCase(
                analysis_documents_repository=analysis_documents_repository,
            )

            return use_case.execute(analysis_id=analysis.id.value)

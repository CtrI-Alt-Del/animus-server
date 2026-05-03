from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos import AnalysisStatusDto
from animus.core.intake.interfaces import AnalisysesRepository
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _Body(BaseModel):
    status: str


class UpdateAnalysisStatusController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch(
            '/analyses/{analysis_id}/status',
            status_code=200,
            response_model=AnalysisStatusDto,
        )
        def _(
            body: _Body,
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
        ) -> AnalysisStatusDto:
            analysis.set_status(body.status)
            analisyses_repository.replace(analysis)

            return analysis.status.dto

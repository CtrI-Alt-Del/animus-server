from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases import AddAnalysisPrecedentUseCase
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class _Body(BaseModel):
    court: str
    kind: str
    number: int


class AddAnalysisPrecedentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/precedents',
            status_code=201,
            response_model=AnalysisPrecedentDto,
        )
        def _(
            analysis: Annotated[
                Analysis,
                Depends(IntakePipe.verify_analysis_by_account_from_request),
            ],
            body: _Body,
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            precedents_repository: Annotated[
                PrecedentsRepository,
                Depends(DatabasePipe.get_precedents_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
        ) -> AnalysisPrecedentDto:
            use_case = AddAnalysisPrecedentUseCase(
                analyses_repository=analyses_repository,
                precedents_repository=precedents_repository,
                analysis_precedents_repository=analysis_precedents_repository,
            )

            return use_case.execute(
                analysis_id=analysis.id.value,
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court=body.court,
                    kind=body.kind,
                    number=body.number,
                ),
            )

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases import CreateAnalysisPrecedentUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.validation.shared import IdSchema


class _Body(BaseModel):
    court: str
    kind: str
    number: int


class CreateAnalysisPrecedentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/precedents',
            status_code=201,
            response_model=AnalysisPrecedentDto,
        )
        def _(
            analysis_id: IdSchema,
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
            precedents_repository: Annotated[
                PrecedentsRepository,
                Depends(DatabasePipe.get_precedents_repository_from_request),
            ],
        ) -> AnalysisPrecedentDto:
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=analysis_id,
                account_id=account_id,
                analyses_repository=analyses_repository,
            )

            use_case = CreateAnalysisPrecedentUseCase(
                analysis_precedents_repository=analysis_precedents_repository,
                analyses_repository=analyses_repository,
                precedents_repository=precedents_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court=body.court,
                    kind=body.kind,
                    number=body.number,
                ),
                is_manually_added=True,
            )

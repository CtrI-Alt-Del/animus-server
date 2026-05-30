from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

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
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.validation.shared import IdSchema


class _IdentifierBody(BaseModel):
    court: str
    kind: str
    number: int

    def to_dto(self) -> PrecedentIdentifierDto:
        return PrecedentIdentifierDto(
            court=self.court,
            kind=self.kind,
            number=self.number,
        )


class _Body(BaseModel):
    analysis_id: IdSchema
    identifier: _IdentifierBody


class AddAnalysisPrecedentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/precedents',
            status_code=201,
            response_model=AnalysisPrecedentDto,
        )
        def _(
            body: _Body,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
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
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=body.analysis_id,
                account_id=account_id,
                analyses_repository=analyses_repository,
            )

            use_case = AddAnalysisPrecedentUseCase(
                analyses_repository=analyses_repository,
                precedents_repository=precedents_repository,
                analysis_precedents_repository=analysis_precedents_repository,
            )

            return use_case.execute(
                analysis_id=body.analysis_id,
                precedent_identifier_dto=body.identifier.to_dto(),
            )

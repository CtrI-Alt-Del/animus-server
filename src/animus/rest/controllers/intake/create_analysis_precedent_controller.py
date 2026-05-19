from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases import CreateAnalysisPrecedentUseCase
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


class CreateAnalysisPrecedentController:
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
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
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
                analysis_id=body.analysis_id,
                account_id=account_id,
                analisyses_repository=analisyses_repository,
            )

            use_case = CreateAnalysisPrecedentUseCase(
                analysis_precedents_repository=analysis_precedents_repository,
                analisyses_repository=analisyses_repository,
                precedents_repository=precedents_repository,
            )

            return use_case.execute(
                analysis_id=body.analysis_id,
                precedent_identifier_dto=body.identifier.to_dto(),
            )

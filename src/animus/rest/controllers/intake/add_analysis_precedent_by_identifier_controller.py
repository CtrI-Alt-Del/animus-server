from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.domain.structures.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases import AddAnalysisPrecedentByIdentifierUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class AddAnalysisPrecedentByIdentifierBody(BaseModel):
    court: str
    kind: str
    number: int

    def to_dto(self) -> PrecedentIdentifierDto:
        return PrecedentIdentifierDto(
            court=self.court,
            kind=self.kind,
            number=self.number,
        )


class AddAnalysisPrecedentByIdentifierController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/analyses/{analysis_id}/precedents',
            status_code=200,
            response_model=AnalysisStatusDto,
        )
        def _(
            analysis_id: str,
            body: AddAnalysisPrecedentByIdentifierBody,
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
        ) -> AnalysisStatusDto:
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=analysis_id,
                account_id=account_id,
                analyses_repository=analyses_repository,
            )

            use_case = AddAnalysisPrecedentByIdentifierUseCase(
                analysis_precedents_repository=analysis_precedents_repository,
                analyses_repository=analyses_repository,
                precedents_repository=precedents_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                precedent_identifier_dto=body.to_dto(),
            )

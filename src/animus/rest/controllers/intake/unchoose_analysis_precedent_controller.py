from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities.dtos import AnalysisStatusDto
from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
)
from animus.core.intake.use_cases import UnchooseAnalysisPrecedentUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class UnchooseAnalysisPrecedentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch(
            '/analyses/{analysis_id}/precedents/unchoose',
            status_code=200,
            response_model=AnalysisStatusDto,
        )
        def _(
            analysis_id: str,
            court: str,
            kind: str,
            number: int,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analyses_repository: Annotated[
                AnalysesRepository,
                Depends(DatabasePipe.get_analyses_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
        ) -> AnalysisStatusDto:
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=analysis_id,
                account_id=account_id,
                analyses_repository=analyses_repository,
            )

            use_case = UnchooseAnalysisPrecedentUseCase(
                analysis_precedents_repository=analysis_precedents_repository,
                analyses_repository=analyses_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court=court,
                    kind=kind,
                    number=number,
                ),
            )

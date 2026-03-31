from typing import Annotated

from fastapi import APIRouter, Depends

from animus.core.intake.domain.entities.dtos import AnalysisStatusDto
from animus.core.intake.domain.structures.dtos import PrecedentIdentifierDto
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
)
from animus.core.intake.use_cases import ChooseAnalysisPrecedentUseCase
from animus.core.shared.domain.structures import Id
from animus.pipes.auth_pipe import AuthPipe
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe


class ChooseAnalysisPrecedentController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.patch(
            '/analyses/{analysis_id}/precedents/choose',
            status_code=200,
            response_model=AnalysisStatusDto,
        )
        def _(
            analysis_id: str,
            court: str,
            kind: str,
            number: int,
            account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            analysis_precedents_repository: Annotated[
                AnalysisPrecedentsRepository,
                Depends(DatabasePipe.get_analysis_precedents_repository_from_request),
            ],
        ) -> AnalysisStatusDto:
            IntakePipe.verify_analysis_by_account_from_request(
                analysis_id=analysis_id,
                account_id=account_id,
                analisyses_repository=analisyses_repository,
            )

            use_case = ChooseAnalysisPrecedentUseCase(
                analysis_precedents_repository=analysis_precedents_repository,
                analisyses_repository=analisyses_repository,
            )

            return use_case.execute(
                analysis_id=analysis_id,
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court=court,
                    kind=kind,
                    number=number,
                ),
            )

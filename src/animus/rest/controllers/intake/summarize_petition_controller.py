from typing import Annotated

from fastapi import APIRouter, Depends, Response

from animus.core.intake.domain.entities import Petition
from animus.core.intake.interfaces import AnalisysesRepository, PetitionsRepository
from animus.core.intake.use_cases import RequestPetitionSummaryUseCase
from animus.core.shared.interfaces import Broker
from animus.pipes.database_pipe import DatabasePipe
from animus.pipes.intake_pipe import IntakePipe
from animus.pipes.pubsub_pipe import PubSubPipe


class SummarizePetitionController:
    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.post(
            '/petitions/{petition_id}/summary',
            status_code=202,
        )
        def _(
            petition_id: str,
            _petition: Annotated[
                Petition,
                Depends(IntakePipe.verify_petition_by_account),
            ],
            petitions_repository: Annotated[
                PetitionsRepository,
                Depends(DatabasePipe.get_petitions_repository_from_request),
            ],
            analisyses_repository: Annotated[
                AnalisysesRepository,
                Depends(DatabasePipe.get_analisyses_repository_from_request),
            ],
            broker: Annotated[Broker, Depends(PubSubPipe.get_broker_from_request)],
        ) -> Response:
            use_case = RequestPetitionSummaryUseCase(
                petitions_repository=petitions_repository,
                analisyses_repository=analisyses_repository,
                broker=broker,
            )
            use_case.execute(petition_id=petition_id)
            return Response(status_code=202)

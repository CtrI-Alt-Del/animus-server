from fastapi import APIRouter

from animus.rest.controllers.intake.create_petition_controller import (
    CreatePetitionController,
)
from animus.rest.controllers.intake.summarize_petition_controller import (
    SummarizePetitionController,
)


class IntakeRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/intake', tags=['intake'])

        CreatePetitionController.handle(router)
        SummarizePetitionController.handle(router)

        return router

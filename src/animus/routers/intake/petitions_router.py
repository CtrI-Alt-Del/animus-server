from fastapi import APIRouter

from animus.rest.controllers.intake import (
    CreatePetitionController,
    GetAnalysisPetitionController,
    GetPetitionSummaryController,
    SummarizePetitionController,
)


class PetitionsRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter()

        CreatePetitionController.handle(router)
        GetAnalysisPetitionController.handle(router)
        GetPetitionSummaryController.handle(router)
        SummarizePetitionController.handle(router)

        return router

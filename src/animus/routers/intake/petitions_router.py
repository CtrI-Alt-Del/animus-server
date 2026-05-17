from fastapi import APIRouter

from animus.rest.controllers.intake import (
    GetAnalysisPetitionController,
)


class PetitionsRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter()

        GetAnalysisPetitionController.handle(router)

        return router

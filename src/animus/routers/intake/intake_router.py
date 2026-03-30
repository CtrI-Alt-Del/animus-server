from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ChooseAnalysisPrecedentController,
    CreatePetitionController,
    GetAnalysisStatusController,
    ListAnalysisPrecedentsController,
    SearchAnalysisPrecedentsController,
    SummarizePetitionController,
)


class IntakeRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/intake', tags=['intake'])

        CreatePetitionController.handle(router)
        SummarizePetitionController.handle(router)
        SearchAnalysisPrecedentsController.handle(router)
        ListAnalysisPrecedentsController.handle(router)
        GetAnalysisStatusController.handle(router)
        ChooseAnalysisPrecedentController.handle(router)

        return router

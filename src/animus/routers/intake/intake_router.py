from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ChooseAnalysisPrecedentController,
    CreatePetitionController,
    GetAnalysisPetitionController,
    GetAnalysisStatusController,
    GetPetitionSummaryController,
    ListAnalysisPetitionsController,
    ListAnalysisPrecedentsController,
    SearchAnalysisPrecedentsController,
    SummarizePetitionController,
)


class IntakeRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/intake', tags=['intake'])

        CreatePetitionController.handle(router)
        GetAnalysisPetitionController.handle(router)
        ListAnalysisPetitionsController.handle(router)
        GetPetitionSummaryController.handle(router)
        SummarizePetitionController.handle(router)
        SearchAnalysisPrecedentsController.handle(router)
        ListAnalysisPrecedentsController.handle(router)
        GetAnalysisStatusController.handle(router)
        ChooseAnalysisPrecedentController.handle(router)

        return router

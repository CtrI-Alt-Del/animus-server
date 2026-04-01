from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ArchiveAnalysisController,
    ChooseAnalysisPrecedentController,
    CreateAnalysisController,
    CreatePetitionController,
    GetAnalysisController,
    GetAnalysisStatusController,
    ListAnalysesController,
    ListAnalysisPetitionsController,
    ListAnalysisPrecedentsController,
    RenameAnalysisController,
    SearchAnalysisPrecedentsController,
    SummarizePetitionController,
)


class IntakeRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/intake', tags=['intake'])

        CreateAnalysisController.handle(router)
        ListAnalysesController.handle(router)
        GetAnalysisController.handle(router)
        RenameAnalysisController.handle(router)
        ArchiveAnalysisController.handle(router)
        CreatePetitionController.handle(router)
        ListAnalysisPetitionsController.handle(router)
        SummarizePetitionController.handle(router)
        SearchAnalysisPrecedentsController.handle(router)
        ListAnalysisPrecedentsController.handle(router)
        GetAnalysisStatusController.handle(router)
        ChooseAnalysisPrecedentController.handle(router)

        return router

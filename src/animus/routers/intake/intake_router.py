from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ArchiveAnalysisController,
    ChooseAnalysisPrecedentController,
    CreateAnalysisController,
    CreatePetitionController,
    GetAnalysisController,
    GetAnalysisPetitionController,
    GetAnalysisReportController,
    GetAnalysisStatusController,
    ListAnalysesController,
    GetPetitionSummaryController,
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
        GetAnalysisReportController.handle(router)
        RenameAnalysisController.handle(router)
        ArchiveAnalysisController.handle(router)
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

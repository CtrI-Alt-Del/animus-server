from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ArchiveAnalysesController,
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
    ListUnfolderedAnalysesController,
    MoveAnalysesToFolderController,
    RenameAnalysisController,
    SearchAnalysisPrecedentsController,
    SummarizePetitionController,
)
from animus.rest.controllers.intake.list_processing_analyses_controller import (
    ListProcessingAnalysesController,
)


class IntakeRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/intake', tags=['intake'])

        ListProcessingAnalysesController.handle(router)
        CreateAnalysisController.handle(router)
        ListAnalysesController.handle(router)
        ListUnfolderedAnalysesController.handle(router)
        GetAnalysisController.handle(router)
        GetAnalysisReportController.handle(router)
        RenameAnalysisController.handle(router)
        ArchiveAnalysesController.handle(router)
        MoveAnalysesToFolderController.handle(router)
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

from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ArchiveAnalysisController,
    ChooseAnalysisPrecedentController,
    CreateAnalysisController,
    GetAnalysisController,
    GetAnalysisReportController,
    GetAnalysisStatusController,
    ListAnalysesController,
    ListAnalysisPetitionsController,
    ListAnalysisPrecedentsController,
    ListUnfolderedAnalysesController,
    RenameAnalysisController,
    SearchAnalysisPrecedentsController,
    UpdateAnalysisStatusController,
)
from animus.rest.controllers.intake.list_processing_analyses_controller import (
    ListProcessingAnalysesController,
)


class AnalysesRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter()

        ListProcessingAnalysesController.handle(router)
        CreateAnalysisController.handle(router)
        ListAnalysesController.handle(router)
        ListUnfolderedAnalysesController.handle(router)
        GetAnalysisController.handle(router)
        GetAnalysisReportController.handle(router)
        RenameAnalysisController.handle(router)
        ArchiveAnalysisController.handle(router)
        ListAnalysisPetitionsController.handle(router)
        SearchAnalysisPrecedentsController.handle(router)
        ListAnalysisPrecedentsController.handle(router)
        GetAnalysisStatusController.handle(router)
        UpdateAnalysisStatusController.handle(router)
        ChooseAnalysisPrecedentController.handle(router)

        return router

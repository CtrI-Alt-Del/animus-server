from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ArchiveAnalysesController,
    ChooseAnalysisPrecedentController,
    CreateAnalysisController,
    CreateAnalysisDocumentController,
    GetAnalysisController,
    GetCaseAssessmentAnalysisReportController,
    GetAnalysisDocumentController,
    GetFirstInstanceAnalysisReportController,
    GetAnalysisStatusController,
    GetCaseSummaryController,
    GetSecondInstanceAnalysisReportController,
    ListAnalysesController,
    ListAnalysisPetitionsController,
    ListAnalysisPrecedentsController,
    ListUnfolderedAnalysesController,
    MoveAnalysesToFolderController,
    RenameAnalysisController,
    RequestCaseSummaryController,
    SearchAnalysisPrecedentsController,
    UnarchiveAnalysisController,
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
        CreateAnalysisDocumentController.handle(router)
        GetAnalysisDocumentController.handle(router)
        RequestCaseSummaryController.handle(router)
        GetCaseSummaryController.handle(router)
        GetCaseAssessmentAnalysisReportController.handle(router)
        GetFirstInstanceAnalysisReportController.handle(router)
        GetSecondInstanceAnalysisReportController.handle(router)
        RenameAnalysisController.handle(router)
        ArchiveAnalysesController.handle(router)
        UnarchiveAnalysisController.handle(router)
        ListAnalysisPetitionsController.handle(router)
        SearchAnalysisPrecedentsController.handle(router)
        ListAnalysisPrecedentsController.handle(router)
        GetAnalysisStatusController.handle(router)
        UpdateAnalysisStatusController.handle(router)
        MoveAnalysesToFolderController.handle(router)
        ChooseAnalysisPrecedentController.handle(router)

        return router

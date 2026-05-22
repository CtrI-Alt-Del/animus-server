from fastapi import APIRouter

from animus.rest.controllers.intake import (
    ArchiveAnalysesController,
    ChooseAnalysisPrecedentController,
    CreateAnalysisController,
    CreateAnalysisPrecedentController,
    CreateAnalysisDocumentController,
    GetAnalysisController,
    GetCaseAssessmentAnalysisReportController,
    GetAnalysisDocumentController,
    GetPrecedentController,
    GetFirstInstanceAnalysisReportController,
    GetAnalysisStatusController,
    GetCaseSummaryController,
    GetSecondInstanceAnalysisReportController,
    GetSecondInstanceJudgmentDraftController,
    ListAnalysesController,
    ListAnalysisPetitionsController,
    ListAnalysisPrecedentsController,
    ListUnfolderedAnalysesController,
    MoveAnalysesToFolderController,
    RenameAnalysisController,
    SearchAnalysisPrecedentsController,
    TriggerCaseAssessmentCaseSummarizationController,
    TriggerFirstInstanceCaseSummarizationController,
    TriggerSecondInstanceCaseSummarizationController,
    TriggerSecondInstanceJudgmentDraftGenerationController,
    UnarchiveAnalysisController,
    UnchooseAnalysisPrecedentController,
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
        CreateAnalysisPrecedentController.handle(router)
        ListAnalysesController.handle(router)
        ListUnfolderedAnalysesController.handle(router)
        GetAnalysisController.handle(router)
        CreateAnalysisDocumentController.handle(router)
        GetAnalysisDocumentController.handle(router)
        TriggerCaseAssessmentCaseSummarizationController.handle(router)
        TriggerFirstInstanceCaseSummarizationController.handle(router)
        TriggerSecondInstanceCaseSummarizationController.handle(router)
        TriggerSecondInstanceJudgmentDraftGenerationController.handle(router)
        GetSecondInstanceJudgmentDraftController.handle(router)
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
        GetPrecedentController.handle(router)
        GetAnalysisStatusController.handle(router)
        UpdateAnalysisStatusController.handle(router)
        MoveAnalysesToFolderController.handle(router)
        ChooseAnalysisPrecedentController.handle(router)
        UnchooseAnalysisPrecedentController.handle(router)

        return router

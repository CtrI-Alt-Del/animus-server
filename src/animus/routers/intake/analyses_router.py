from fastapi import APIRouter

from animus.rest.controllers.intake import (
    AddAnalysisPrecedentController,
    RemoveAnalysisPrecedentController,
    ArchiveAnalysesController,
    ChooseAnalysisPrecedentController,
    CreateAnalysisController,
    CreateCaseAssessmentBriefingController,
    CreateSecondInstanceDecisionController,
    CreateAnalysisDocumentController,
    GetAnalysisController,
    GetCaseAssessmentAnalysisReportController,
    GetAnalysisDocumentController,
    RemoveAnalysisDocumentController,
    GetPrecedentController,
    GetFirstInstanceAnalysisReportController,
    GetPetitionDraftController,
    GetAnalysisStatusController,
    GetCaseSummaryController,
    GetSecondInstanceAnalysisReportController,
    GetSecondInstanceDecisionController,
    GetSecondInstanceJudgmentDraftController,
    ListAnalysesController,
    ListAnalysisPetitionsController,
    ListAnalysisPrecedentsController,
    ListUnfolderedAnalysesController,
    MoveAnalysesToFolderController,
    TriggerPetitionDraftRegenerationController,
    TriggerSecondInstanceJudgmentDraftRegenerationController,
    RenameAnalysisController,
    SearchAnalysisPrecedentsController,
    TriggerCaseAssessmentCaseSummarizationController,
    TriggerFirstInstanceCaseSummarizationController,
    TriggerPetitionDraftGenerationController,
    TriggerSecondInstanceCaseSummarizationController,
    TriggerSecondInstanceJudgmentDraftGenerationController,
    UnarchiveAnalysisController,
    UnchooseAnalysisPrecedentController,
    UpdateAnalysisStatusController,
    UpdatePetitionDraftController,
    UpdateSecondInstanceJudgmentDraftController,
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
        AddAnalysisPrecedentController.handle(router)
        RemoveAnalysisPrecedentController.handle(router)
        ListAnalysesController.handle(router)
        ListUnfolderedAnalysesController.handle(router)
        GetAnalysisController.handle(router)
        CreateCaseAssessmentBriefingController.handle(router)
        CreateSecondInstanceDecisionController.handle(router)
        CreateAnalysisDocumentController.handle(router)
        GetAnalysisDocumentController.handle(router)
        GetSecondInstanceDecisionController.handle(router)
        RemoveAnalysisDocumentController.handle(router)
        TriggerCaseAssessmentCaseSummarizationController.handle(router)
        TriggerFirstInstanceCaseSummarizationController.handle(router)
        TriggerPetitionDraftGenerationController.handle(router)
        TriggerSecondInstanceCaseSummarizationController.handle(router)
        TriggerSecondInstanceJudgmentDraftGenerationController.handle(router)
        TriggerPetitionDraftRegenerationController.handle(router)
        TriggerSecondInstanceJudgmentDraftRegenerationController.handle(router)
        GetPetitionDraftController.handle(router)
        UpdatePetitionDraftController.handle(router)
        GetSecondInstanceJudgmentDraftController.handle(router)
        UpdateSecondInstanceJudgmentDraftController.handle(router)
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

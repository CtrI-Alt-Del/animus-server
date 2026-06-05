from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    exports: dict[str, tuple[str, str]] = {
        'CaseAssessmentAnalysisReportDto': (
            '.case_assessment_analysis_report_dto',
            'CaseAssessmentAnalysisReportDto',
        ),
        'FirstInstanceAnalysisReportDto': (
            '.first_instance_analysis_report_dto',
            'FirstInstanceAnalysisReportDto',
        ),
        'AnalysisDocumentDto': ('.analysis_document_dto', 'AnalysisDocumentDto'),
        'CaseAssessmentBriefingDto': (
            '.case_assessment_briefing_dto',
            'CaseAssessmentBriefingDto',
        ),
        'ExtractedPetitionDto': ('.extracted_petition_dto', 'ExtractedPetitionDto'),
        'CaseSummaryEmbeddingDto': (
            '.petition_summary_embedding_dto',
            'CaseSummaryEmbeddingDto',
        ),
        'PrecedentEmbeddingDto': ('.precedent_embedding_dto', 'PrecedentEmbeddingDto'),
        'AnalysisPrecedentDto': ('.analysis_precedent_dto', 'AnalysisPrecedentDto'),
        'AnalysiesPrecedentLegalFeaturesDto': (
            '.analysies_precedent_legal_features_dto',
            'AnalysiesPrecedentLegalFeaturesDto',
        ),
        'AnalysisPrecedentDatasetRowDto': (
            '.analysis_precedent_dataset_dto',
            'AnalysisPrecedentDatasetRowDto',
        ),
        'AnalysisPrecedentApplicabilityFeedbackDto': (
            '.analysis_precedent_applicability_feedback_dto',
            'AnalysisPrecedentApplicabilityFeedbackDto',
        ),
        'AnalysisPetitionDto': ('.analysis_petition_dto', 'AnalysisPetitionDto'),
        'AnalysisPrecedentsSearchFiltersDto': (
            '.analysis_precedents_search_filters_dto',
            'AnalysisPrecedentsSearchFiltersDto',
        ),
        'CaseSummaryDto': ('.case_summary_dto', 'CaseSummaryDto'),
        'SecondInstanceDecisionDto': (
            '.second_instance_decision_dto',
            'SecondInstanceDecisionDto',
        ),
        'SecondInstanceJudgmentDraftDto': (
            '.second_instance_judgment_draft_dto',
            'SecondInstanceJudgmentDraftDto',
        ),
        'PetitionDraftDto': ('.petition_draft_dto', 'PetitionDraftDto'),
        'PetitionExtractionDto': (
            '.petition_extraction_dto',
            'PetitionExtractionDto',
        ),
        'PetitionSummaryDto': ('.case_summary_dto', 'CaseSummaryDto'),
        'PrecedentIdentifierDto': (
            '.precedent_identifier_dto',
            'PrecedentIdentifierDto',
        ),
        'SecondInstanceAnalysisReportDto': (
            '.second_instance_analysis_report_dto',
            'SecondInstanceAnalysisReportDto',
        ),
    }

    export = exports.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

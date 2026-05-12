from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .analysies_precedent_legal_features import AnalysiesPrecedentLegalFeatures
    from .analysis_report import AnalysisReport
    from .analysis_document import AnalysisDocument
    from .analysis_precedent import AnalysisPrecedent
    from .analysis_precedent_dataset_row import AnalysisPrecedentDatasetRow
    from .analysis_precedent_applicability_feedback import (
        AnalysisPrecedentApplicabilityFeedback,
    )
    from .analysis_precedent_applicability_level import (
        AnalysisPrecedentApplicabilityLevel,
        AnalysisPrecedentApplicabilityLevelValue,
    )
    from .analysis_petition import AnalysisPetition
    from .analysis_precedents_search_filters import AnalysisPrecedentsSearchFilters
    from .case_summary import CaseSummary
    from .court import Court, CourtValue
    from .judgment_draft import JudgmentDraft
    from .petition_draft import PetitionDraft
    from .petition_document import PetitionDocument
    from .petition_summary import PetitionSummary
    from .petition_summary_embedding import PetitionSummaryEmbedding
    from .precedent_embedding import PrecedentEmbedding
    from .precedent_embedding_field import (
        PrecedentEmbeddingField,
        PrecedentEmbeddingFieldValue,
    )
    from .precedent_kind import PrecedentKind, PrecedentKindValue

__all__ = [
    'AnalysisReport',
    'AnalysisDocument',
    'AnalysiesPrecedentLegalFeatures',
    'AnalysisPrecedent',
    'AnalysisPrecedentDatasetRow',
    'AnalysisPrecedentApplicabilityFeedback',
    'AnalysisPrecedentApplicabilityLevel',
    'AnalysisPrecedentApplicabilityLevelValue',
    'AnalysisPetition',
    'AnalysisPrecedentsSearchFilters',
    'CaseSummary',
    'Court',
    'CourtValue',
    'JudgmentDraft',
    'PetitionDraft',
    'PetitionDocument',
    'PetitionSummary',
    'PetitionSummaryEmbedding',
    'PrecedentKind',
    'PrecedentKindValue',
    'PrecedentEmbeddingField',
    'PrecedentEmbeddingFieldValue',
    'PrecedentEmbedding',
]


def __getattr__(name: str) -> Any:
    exports: dict[str, tuple[str, str]] = {
        'AnalysisReport': ('.analysis_report', 'AnalysisReport'),
        'AnalysisDocument': ('.analysis_document', 'AnalysisDocument'),
        'AnalysiesPrecedentLegalFeatures': (
            '.analysies_precedent_legal_features',
            'AnalysiesPrecedentLegalFeatures',
        ),
        'AnalysisPrecedent': ('.analysis_precedent', 'AnalysisPrecedent'),
        'AnalysisPrecedentDatasetRow': (
            '.analysis_precedent_dataset_row',
            'AnalysisPrecedentDatasetRow',
        ),
        'AnalysisPrecedentApplicabilityFeedback': (
            '.analysis_precedent_applicability_feedback',
            'AnalysisPrecedentApplicabilityFeedback',
        ),
        'AnalysisPrecedentApplicabilityLevel': (
            '.analysis_precedent_applicability_level',
            'AnalysisPrecedentApplicabilityLevel',
        ),
        'AnalysisPrecedentApplicabilityLevelValue': (
            '.analysis_precedent_applicability_level',
            'AnalysisPrecedentApplicabilityLevelValue',
        ),
        'AnalysisPetition': ('.analysis_petition', 'AnalysisPetition'),
        'AnalysisPrecedentsSearchFilters': (
            '.analysis_precedents_search_filters',
            'AnalysisPrecedentsSearchFilters',
        ),
        'CaseSummary': ('.case_summary', 'CaseSummary'),
        'Court': ('.court', 'Court'),
        'CourtValue': ('.court', 'CourtValue'),
        'JudgmentDraft': ('.judgment_draft', 'JudgmentDraft'),
        'PetitionDocument': ('.petition_document', 'PetitionDocument'),
        'PetitionDraft': ('.petition_draft', 'PetitionDraft'),
        'PetitionSummary': ('.petition_summary', 'PetitionSummary'),
        'PetitionSummaryEmbedding': (
            '.petition_summary_embedding',
            'PetitionSummaryEmbedding',
        ),
        'PrecedentEmbedding': ('.precedent_embedding', 'PrecedentEmbedding'),
        'PrecedentEmbeddingField': (
            '.precedent_embedding_field',
            'PrecedentEmbeddingField',
        ),
        'PrecedentEmbeddingFieldValue': (
            '.precedent_embedding_field',
            'PrecedentEmbeddingFieldValue',
        ),
        'PrecedentKind': ('.precedent_kind', 'PrecedentKind'),
        'PrecedentKindValue': ('.precedent_kind', 'PrecedentKindValue'),
    }

    export = exports.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

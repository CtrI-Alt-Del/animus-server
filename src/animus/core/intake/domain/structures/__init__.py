from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .analysis_report import AnalysisReport
    from .analysis_precedent import AnalysisPrecedent
    from .analysis_petition import AnalysisPetition
    from .analysis_precedents_search_filters import AnalysisPrecedentsSearchFilters
    from .court import Court, CourtValue
    from .petition_document import PetitionDocument
    from .petition_summary import PetitionSummary
    from .petition_summary_embedding import PetitionSummaryEmbedding
    from .precedent_embedding import PrecedentEmbedding
    from .precedent_embedding_field import (
        PrecedentEmbeddingField,
        PrecedentEmbeddingFieldValue,
    )
    from .precedent_kind import PrecedentKind, PrecedentKindValue
    from .precedent_status import PrecedentStatus, PrecedentStatusValue

__all__ = [
    'AnalysisReport',
    'AnalysisPrecedent',
    'AnalysisPetition',
    'AnalysisPrecedentsSearchFilters',
    'Court',
    'CourtValue',
    'PetitionDocument',
    'PetitionSummary',
    'PetitionSummaryEmbedding',
    'PrecedentKind',
    'PrecedentKindValue',
    'PrecedentStatus',
    'PrecedentStatusValue',
    'PrecedentEmbeddingField',
    'PrecedentEmbeddingFieldValue',
    'PrecedentEmbedding',
]


def __getattr__(name: str) -> Any:
    exports: dict[str, tuple[str, str]] = {
        'AnalysisReport': ('.analysis_report', 'AnalysisReport'),
        'AnalysisPrecedent': ('.analysis_precedent', 'AnalysisPrecedent'),
        'AnalysisPetition': ('.analysis_petition', 'AnalysisPetition'),
        'AnalysisPrecedentsSearchFilters': (
            '.analysis_precedents_search_filters',
            'AnalysisPrecedentsSearchFilters',
        ),
        'Court': ('.court', 'Court'),
        'CourtValue': ('.court', 'CourtValue'),
        'PetitionDocument': ('.petition_document', 'PetitionDocument'),
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
        'PrecedentStatus': ('.precedent_status', 'PrecedentStatus'),
        'PrecedentStatusValue': ('.precedent_status', 'PrecedentStatusValue'),
    }

    export = exports.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

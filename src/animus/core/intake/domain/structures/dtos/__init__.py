from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    exports: dict[str, tuple[str, str]] = {
        'PetitionSummaryEmbeddingDto': (
            '.petition_summary_embedding_dto',
            'PetitionSummaryEmbeddingDto',
        ),
        'PrecedentEmbeddingDto': ('.precedent_embedding_dto', 'PrecedentEmbeddingDto'),
        'AnalysisPrecedentDto': ('.analysis_precedent_dto', 'AnalysisPrecedentDto'),
        'AnalysisPrecedentsSearchFiltersDto': (
            '.analysis_precedents_search_filters_dto',
            'AnalysisPrecedentsSearchFiltersDto',
        ),
        'PetitionSummaryDto': ('.petition_summary_dto', 'PetitionSummaryDto'),
        'PrecedentIdentifierDto': (
            '.precedent_identifier_dto',
            'PrecedentIdentifierDto',
        ),
    }

    export = exports.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

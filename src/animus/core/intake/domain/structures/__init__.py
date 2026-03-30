from importlib import import_module
from typing import Any


_EXPORTS: dict[str, tuple[str, str]] = {
    'AnalysisPrecedent': ('.analysis_precedent', 'AnalysisPrecedent'),
    'Court': ('.court', 'Court'),
    'CourtValue': ('.court', 'CourtValue'),
    'PetitionDocument': ('.petition_document', 'PetitionDocument'),
    'PetitionSummary': ('.petition_summary', 'PetitionSummary'),
    'PrecedentKind': ('.precedent_kind', 'PrecedentKind'),
    'PrecedentKindValue': ('.precedent_kind', 'PrecedentKindValue'),
    'PrecedentStatus': ('.precedent_status', 'PrecedentStatus'),
    'PrecedentStatusValue': ('.precedent_status', 'PrecedentStatusValue'),
    'PetitionEmbedding': ('.petition_embedding', 'PetitionEmbedding'),
    'PrecedentEmbeddingField': (
        '.precedent_embedding_field',
        'PrecedentEmbeddingField',
    ),
    'PrecedentEmbeddingFieldValue': (
        '.precedent_embedding_field',
        'PrecedentEmbeddingFieldValue',
    ),
    'PrecedentEmbedding': ('.precedent_embedding', 'PrecedentEmbedding'),
}


def __getattr__(name: str) -> Any:
    export = _EXPORTS.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

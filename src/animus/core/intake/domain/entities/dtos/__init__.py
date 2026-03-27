from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    exports: dict[str, tuple[str, str]] = {
        'FolderDto': ('.folder_dto', 'FolderDto'),
        'AnalysisStatusDto': ('.analysis_status_dto', 'AnalysisStatusDto'),
        'PetitionDocumentDto': ('.petition_document_dto', 'PetitionDocumentDto'),
        'PetitionDto': ('.petition_dto', 'PetitionDto'),
        'PrecedentDto': ('.precedent_dto', 'PrecedentDto'),
        'AnalysisDto': ('.analysis_dto', 'AnalysisDto'),
    }

    export = exports.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

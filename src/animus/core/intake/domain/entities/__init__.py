from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    exports: dict[str, tuple[str, str]] = {
        'Folder': ('.folder', 'Folder'),
        'AnalysisStatus': ('.analysis_status', 'AnalysisStatus'),
        'AnalysisStatusValue': ('.analysis_status', 'AnalysisStatusValue'),
        'Petition': ('.petition', 'Petition'),
        'Precedent': ('.precedent', 'Precedent'),
        'Analysis': ('.analysis', 'Analysis'),
    }

    export = exports.get(name)
    if export is not None:
        module_name, symbol_name = export
        module = import_module(module_name, package=__name__)
        return getattr(module, symbol_name)

    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)

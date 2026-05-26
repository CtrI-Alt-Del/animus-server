from dataclasses import dataclass

from animus.core.shared.domain.abstracts import Event


@dataclass(frozen=True)
class _Payload:
    analysis_document_path: str


class AnalysisDocumentReplacedEvent(Event[_Payload]):
    name = 'intake/analysis.document.replaced'

    def __init__(self, analysis_document_path: str) -> None:
        payload = _Payload(analysis_document_path=analysis_document_path)
        super().__init__(AnalysisDocumentReplacedEvent.name, payload)

from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.events import AnalysisDocumentReplacedEvent
from animus.core.shared.domain.structures import FilePath
from animus.providers.storage import GcsFileStorageProvider


@dataclass(frozen=True)
class _Payload:
    analysis_document_path: str


class RemoveAnalysisDocumentFileJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='remove-analysis-document-file',
            trigger=TriggerEvent(event=AnalysisDocumentReplacedEvent.name),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                RemoveAnalysisDocumentFileJob._normalize_payload,
                data,
            )
            payload = _Payload(
                analysis_document_path=str(normalized_data['analysis_document_path'])
            )

            await context.step.run(
                'remove_analysis_document_file',
                RemoveAnalysisDocumentFileJob._remove_analysis_document_file,
                payload,
            )

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {'analysis_document_path': str(data['analysis_document_path'])}

    @staticmethod
    async def _remove_analysis_document_file(payload: _Payload) -> None:
        file_storage_provider = GcsFileStorageProvider()
        file_storage_provider.remove_files(
            [FilePath.create(value=payload.analysis_document_path)]
        )

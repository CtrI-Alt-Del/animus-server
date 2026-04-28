from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.events import PetitionReplacedEvent
from animus.core.shared.domain.structures import FilePath
from animus.providers.storage import SupabaseFileStorageProvider


@dataclass(frozen=True)
class _Payload:
    petition_document_path: str


class RemovePetitionDocumentFileJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='remove-petition-document-file',
            trigger=TriggerEvent(event=PetitionReplacedEvent.name),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                RemovePetitionDocumentFileJob._normalize_payload,
                data,
            )
            payload = _Payload(
                petition_document_path=str(normalized_data['petition_document_path'])
            )

            await context.step.run(
                'remove_petition_document_file',
                RemovePetitionDocumentFileJob._remove_petition_document_file,
                payload,
            )

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {'petition_document_path': str(data['petition_document_path'])}

    @staticmethod
    async def _remove_petition_document_file(payload: _Payload) -> None:
        file_storage_provider = SupabaseFileStorageProvider()
        file_storage_provider.remove_files(
            [FilePath.create(value=payload.petition_document_path)]
        )

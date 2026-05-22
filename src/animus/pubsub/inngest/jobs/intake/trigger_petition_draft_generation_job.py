import asyncio
from dataclasses import dataclass
from typing import Any

from inngest import Context, Inngest, TriggerEvent

from animus.core.intake.domain.events import (
    CaseSummaryFinishedEvent,
    PetitionDraftGenerationTriggeredEvent,
)
from animus.core.shared.domain.structures import Id
from animus.database.sqlalchemy.repositories.intake import SqlalchemyAnalysesRepository
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pubsub.inngest.inngest_broker import InngestBroker


@dataclass(frozen=True)
class _Payload:
    analysis_id: str
    account_id: str


class TriggerPetitionDraftGenerationJob:
    @staticmethod
    def handle(inngest: Inngest) -> Any:
        @inngest.create_function(
            fn_id='trigger-petition-draft-generation',
            trigger=TriggerEvent(event=CaseSummaryFinishedEvent.name),
        )
        async def _(context: Context) -> None:
            data = dict(context.event.data)

            normalized_data = await context.step.run(
                'normalize_payload',
                TriggerPetitionDraftGenerationJob._normalize_payload,
                data,
            )
            payload = _Payload(
                analysis_id=str(normalized_data['analysis_id']),
                account_id=str(normalized_data['account_id']),
            )

            triggered_event_data = await context.step.run(
                'resolve_triggered_event',
                lambda payload=payload: (
                    TriggerPetitionDraftGenerationJob._resolve_triggered_event(payload)
                ),
            )
            if triggered_event_data is None:
                return

            await context.step.run(
                'publish_triggered_event',
                lambda: InngestBroker(inngest).publish(  # type: ignore
                    PetitionDraftGenerationTriggeredEvent(
                        analysis_id=str(triggered_event_data['analysis_id'])
                    )
                ),
            )

        return _

    @staticmethod
    async def _normalize_payload(data: dict[str, Any]) -> dict[str, str]:
        return {
            'analysis_id': str(data['analysis_id']),
            'account_id': str(data['account_id']),
        }

    @staticmethod
    async def _resolve_triggered_event(
        payload: _Payload,
    ) -> dict[str, str] | None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: TriggerPetitionDraftGenerationJob._resolve_triggered_event_sync(
                payload
            ),
        )

    @staticmethod
    def _resolve_triggered_event_sync(payload: _Payload) -> dict[str, str] | None:
        with Sqlalchemy.session() as session:
            analysis = SqlalchemyAnalysesRepository(session).find_by_id(
                Id.create(payload.analysis_id)
            )
            if analysis is None:
                return None

            if analysis.type.is_case_analysis.is_false:
                return None

            return {'analysis_id': analysis.id.value}

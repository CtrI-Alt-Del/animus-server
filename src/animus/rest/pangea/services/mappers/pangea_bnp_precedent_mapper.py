from datetime import datetime, timezone
from typing import Any

from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)


class PangeaBnpPrecedentMapper:
    @staticmethod
    def to_dto(payload: dict[str, Any]) -> PrecedentDto:
        raw_date = payload.get('ultimaAtualizacao')
        last_updated = (
            datetime.strptime(raw_date, '%d/%m/%Y').isoformat()
            if raw_date
            else datetime.now(timezone.utc).isoformat()
        )
        enunciation_text = payload.get('questao', '').strip()
        thesis_text = payload.get('teseFirmada', '').strip()
        court = payload.get('orgao', '')
        kind = payload.get('tipo')
        process_number = payload.get('nr')
        process_status = payload.get('situacao', '').strip()
        if not court:
            raise ValueError
        if not kind:
            raise ValueError
        if not process_number:
            raise ValueError
        if not process_number:
            raise ValueError

        precedent_identifer = PrecedentIdentifierDto(
            court=court,
            kind=kind,
            number=process_number,
        )

        return PrecedentDto(
            id=payload.get('id'),
            identifier=precedent_identifer,
            status=process_status,
            enunciation=enunciation_text,
            thesis=thesis_text,
            last_updated_in_pangea_at=last_updated,
        )

    @classmethod
    def to_entity(cls, payload: dict[str, Any]) ->Precedent:
        return Precedent.create(cls.to_dto(payload))

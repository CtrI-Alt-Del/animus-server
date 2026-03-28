import re
from datetime import UTC, datetime

from animus.core.intake.domain.entities.dtos.precedent_dto import PrecedentDto
from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.rest.pangea.services.models.pangea_bnp_process import (
    PangeaBnpPrecedentProcess,
)


class PangeaBnpPrecedentMapper:
    @staticmethod
    def _clean_text(text: str | None) -> str:
        if not text:
            return ''
        text = re.sub(r'<[^>]*>', ' ', text)
        text = (
            text.replace('\\r', ' ')
            .replace('\\n', ' ')
            .replace('\r', ' ')
            .replace('\n', ' ')
        )
        return ' '.join(text.split()).strip()

    @staticmethod
    def to_dto(process: PangeaBnpPrecedentProcess) -> PrecedentDto:
        try:
            last_updated = (
                datetime.strptime(process.ultima_atualizacao, '%d/%m/%Y').isoformat()
                if process.ultima_atualizacao
                else datetime.now(UTC).isoformat()
            )
        except (ValueError, TypeError):
            last_updated = datetime.now(UTC).isoformat()
        thesis_source = process.tese
        if not thesis_source and process.highlight:
            thesis_source = process.highlight.tese
        thesis_text = PangeaBnpPrecedentMapper._clean_text(thesis_source)
        enunciation_text = PangeaBnpPrecedentMapper._clean_text(process.questao)
        if not process.orgao or not process.tipo or not process.nr:
            raise ValueError(f'Dados obrigatórios ausentes no precedente {process.id}')
        identifier = PrecedentIdentifierDto(
            court=process.orgao,
            kind=process.tipo,
            number=int(process.nr),
        )

        return PrecedentDto(
            identifier=identifier,
            status=process.situacao.strip(),
            enunciation=enunciation_text,
            thesis=thesis_text if thesis_text else enunciation_text,
            last_updated_in_pangea_at=last_updated,
        )

    @classmethod
    def to_entity(cls, process: PangeaBnpPrecedentProcess) -> Precedent:
        return Precedent.create(cls.to_dto(process))

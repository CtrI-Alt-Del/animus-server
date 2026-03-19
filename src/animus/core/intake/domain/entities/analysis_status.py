from enum import StrEnum

from animus.core.intake.domain.entities.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.shared.domain.abstracts import Entity
from animus.core.shared.domain.decorators import entity
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id


class AnalysisStatusValue(StrEnum):
    SEARCHING = 'SEARCHING'
    ANALYZING = 'ANALYZING'
    GENERATING = 'GENERATING'
    DONE = 'DONE'
    FAILED = 'FAILED'


@entity
class AnalysisStatus(Entity):
    value: AnalysisStatusValue

    @classmethod
    def create(cls, dto: AnalysisStatusDto) -> 'AnalysisStatus':
        try:
            normalized_value = AnalysisStatusValue(dto.value.upper())
        except ValueError as error:
            raise ValidationError(f'Status de analise invalido: {dto.value}') from error

        return cls(id=Id.create(dto.id), value=normalized_value)

    @property
    def dto(self) -> AnalysisStatusDto:
        return AnalysisStatusDto(id=self.id.value, value=self.value.value)

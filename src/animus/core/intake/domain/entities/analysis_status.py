from enum import StrEnum

from animus.core.intake.domain.entities.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class AnalysisStatusValue(StrEnum):
    SEARCHING = 'SEARCHING'
    ANALYZING = 'ANALYZING'
    GENERATING = 'GENERATING'
    DONE = 'DONE'
    FAILED = 'FAILED'


@structure
class AnalysisStatus(Structure):
    value: AnalysisStatusValue

    @classmethod
    def create(cls, dto: AnalysisStatusDto) -> 'AnalysisStatus':
        try:
            normalized_value = AnalysisStatusValue(dto.value.upper())
        except ValueError as error:
            raise ValidationError(f'Status de analise invalido: {dto.value}') from error

        return cls(value=normalized_value)

    @property
    def dto(self) -> AnalysisStatusDto:
        return AnalysisStatusDto(value=self.value.value)

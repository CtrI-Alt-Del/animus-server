from enum import StrEnum

from animus.core.intake.domain.entities.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class AnalysisStatusValue(StrEnum):
    WAITING_PETITION = 'WAITING_PETITION'
    ANALYZING_PETITION = 'ANALYZING_PETITION'
    PETITION_ANALYZED = 'PETITION_ANALYZED'
    SEARCHING_PRECEDENTS = 'SEARCHING_PRECEDENTS'
    ANALYZING_PRECEDENTS_APPLICABILITY = 'ANALYZING_PRECEDENTS_APPLICABILITY'
    GENERATING_SYNTHESIS = 'GENERATING_SYNTHESIS'
    WAITING_PRECEDENT_CHOISE = 'WAITING_PRECEDENT_CHOISE'
    PRECEDENT_CHOSED = 'PRECEDENT_CHOSED'
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

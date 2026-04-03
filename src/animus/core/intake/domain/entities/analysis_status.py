from enum import StrEnum

from animus.core.intake.domain.entities.dtos.analysis_status_dto import (
    AnalysisStatusDto,
)
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class AnalysisStatusValue(StrEnum):
    WAITING_PETITION = 'WAITING_PETITION'
    PETITION_UPLOADED = 'PETITION_UPLOADED'
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

    @classmethod
    def create_as_failed(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.FAILED)

    @classmethod
    def create_as_waiting_petition(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.WAITING_PETITION)

    @classmethod
    def create_as_petition_uploaded(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.PETITION_UPLOADED)

    @classmethod
    def create_as_analyzing_petition(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.ANALYZING_PETITION)

    @classmethod
    def create_as_petition_analyzed(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.PETITION_ANALYZED)

    @classmethod
    def create_as_searching_precedents(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.SEARCHING_PRECEDENTS)

    @classmethod
    def create_as_analyzing_precedents_applicability(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.ANALYZING_PRECEDENTS_APPLICABILITY)

    @classmethod
    def create_as_generating_synthesis(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.GENERATING_SYNTHESIS)

    @classmethod
    def create_as_waiting_precedent_choise(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.WAITING_PRECEDENT_CHOISE)

    @classmethod
    def create_as_precedent_chosed(cls) -> 'AnalysisStatus':
        return cls(value=AnalysisStatusValue.PRECEDENT_CHOSED)

    @property
    def dto(self) -> AnalysisStatusDto:
        return AnalysisStatusDto(value=self.value.value)

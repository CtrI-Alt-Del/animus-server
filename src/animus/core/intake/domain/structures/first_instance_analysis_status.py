from __future__ import annotations

from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class FirstInstanceAnalysisStatusValue(StrEnum):
    WAITING_DOCUMENT_UPLOAD = 'WAITING_DOCUMENT_UPLOAD'
    DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED'
    ANALYZING_CASE = 'ANALYZING_CASE'
    CASE_ANALYZED = 'CASE_ANALYZED'
    SEARCHING_PRECEDENTS = 'SEARCHING_PRECEDENTS'
    ANALYZING_PRECEDENTS_SIMILARITY = 'ANALYZING_PRECEDENTS_SIMILARITY'
    ANALYZING_PRECEDENTS_APPLICABILITY = 'ANALYZING_PRECEDENTS_APPLICABILITY'
    GENERATING_SYNTHESIS = 'GENERATING_SYNTHESIS'
    DONE = 'DONE'
    FAILED = 'FAILED'


@structure
class FirstInstanceAnalysisStatus(Structure):
    value: FirstInstanceAnalysisStatusValue

    @classmethod
    def create(cls, value: str) -> FirstInstanceAnalysisStatus:
        try:
            return cls(FirstInstanceAnalysisStatusValue(value.upper()))
        except ValueError as error:
            msg = f'Status de analise first instance invalido: {value}'
            raise ValidationError(msg) from error

    @classmethod
    def create_as_analyzing_case(cls) -> FirstInstanceAnalysisStatus:
        return cls(FirstInstanceAnalysisStatusValue.ANALYZING_CASE)

    @classmethod
    def create_as_waiting_document_upload(cls) -> FirstInstanceAnalysisStatus:
        return cls(FirstInstanceAnalysisStatusValue.WAITING_DOCUMENT_UPLOAD)

    @classmethod
    def create_as_document_uploaded(cls) -> FirstInstanceAnalysisStatus:
        return cls(FirstInstanceAnalysisStatusValue.DOCUMENT_UPLOADED)

    @classmethod
    def create_as_case_analyzed(cls) -> FirstInstanceAnalysisStatus:
        return cls(FirstInstanceAnalysisStatusValue.CASE_ANALYZED)

    @classmethod
    def create_as_done(cls) -> FirstInstanceAnalysisStatus:
        return cls(FirstInstanceAnalysisStatusValue.DONE)

    @classmethod
    def create_as_failed(cls) -> FirstInstanceAnalysisStatus:
        return cls(FirstInstanceAnalysisStatusValue.FAILED)

    @classmethod
    def get_processing_statuses(cls) -> tuple[FirstInstanceAnalysisStatusValue, ...]:
        return (
            FirstInstanceAnalysisStatusValue.ANALYZING_CASE,
            FirstInstanceAnalysisStatusValue.SEARCHING_PRECEDENTS,
            FirstInstanceAnalysisStatusValue.ANALYZING_PRECEDENTS_SIMILARITY,
            FirstInstanceAnalysisStatusValue.ANALYZING_PRECEDENTS_APPLICABILITY,
            FirstInstanceAnalysisStatusValue.GENERATING_SYNTHESIS,
        )

    @property
    def dto(self) -> str:
        return self.value.value

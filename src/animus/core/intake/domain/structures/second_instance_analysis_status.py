from __future__ import annotations

from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class SecondInstanceAnalysisStatusValue(StrEnum):
    WAITING_DOCUMENT_UPLOAD = 'WAITING_DOCUMENT_UPLOAD'
    DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED'
    EXTRACTING_PETITION = 'EXTRACTING_PETITION'
    ANALYZING_CASE = 'ANALYZING_CASE'
    CASE_ANALYZED = 'CASE_ANALYZED'
    SEARCHING_PRECEDENTS = 'SEARCHING_PRECEDENTS'
    ANALYZING_PRECEDENTS_SIMILARITY = 'ANALYZING_PRECEDENTS_SIMILARITY'
    ANALYZING_PRECEDENTS_APPLICABILITY = 'ANALYZING_PRECEDENTS_APPLICABILITY'
    GENERATING_JUDGMENT_DRAFT = 'GENERATING_JUDGMENT_DRAFT'
    GENERATING_SYNTHESIS = 'GENERATING_SYNTHESIS'
    PRECEDENTS_SEARCHED = 'PRECEDENTS_SEARCHED'
    DONE = 'DONE'
    PETITION_NOT_FOUND = 'PETITION_NOT_FOUND'
    FAILED = 'FAILED'


@structure
class SecondInstanceAnalysisStatus(Structure):
    value: SecondInstanceAnalysisStatusValue

    @classmethod
    def create(cls, value: str) -> SecondInstanceAnalysisStatus:
        try:
            return cls(SecondInstanceAnalysisStatusValue(value.upper()))
        except ValueError as error:
            msg = f'Status de analise second instance invalido: {value}'
            raise ValidationError(msg) from error

    @classmethod
    def create_as_analyzing_case(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.ANALYZING_CASE)

    @classmethod
    def create_as_waiting_document_upload(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.WAITING_DOCUMENT_UPLOAD)

    @classmethod
    def create_as_document_uploaded(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.DOCUMENT_UPLOADED)

    @classmethod
    def create_as_case_analyzed(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.CASE_ANALYZED)

    @classmethod
    def create_as_extracting_petition(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.EXTRACTING_PETITION)

    @classmethod
    def create_as_analyzing_precedents_similarity(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.ANALYZING_PRECEDENTS_SIMILARITY)

    @classmethod
    def create_as_generating_judgment_draft(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.GENERATING_JUDGMENT_DRAFT)

    @classmethod
    def create_as_petition_not_found(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.PETITION_NOT_FOUND)

    @classmethod
    def create_as_precedents_searched(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.PRECEDENTS_SEARCHED)

    @classmethod
    def create_as_failed(cls) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.FAILED)

    @classmethod
    def create_as_done(
        cls,
    ) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.DONE)

    @classmethod
    def create_as_analyzing_precedents_applicability(
        cls,
    ) -> SecondInstanceAnalysisStatus:
        return cls(SecondInstanceAnalysisStatusValue.ANALYZING_PRECEDENTS_APPLICABILITY)

    @property
    def dto(self) -> str:
        return self.value.value

    @classmethod
    def get_processing_statuses(cls) -> tuple[SecondInstanceAnalysisStatusValue, ...]:
        return (
            SecondInstanceAnalysisStatusValue.EXTRACTING_PETITION,
            SecondInstanceAnalysisStatusValue.ANALYZING_CASE,
            SecondInstanceAnalysisStatusValue.SEARCHING_PRECEDENTS,
            SecondInstanceAnalysisStatusValue.ANALYZING_PRECEDENTS_SIMILARITY,
            SecondInstanceAnalysisStatusValue.ANALYZING_PRECEDENTS_APPLICABILITY,
            SecondInstanceAnalysisStatusValue.GENERATING_SYNTHESIS,
            SecondInstanceAnalysisStatusValue.GENERATING_JUDGMENT_DRAFT,
        )

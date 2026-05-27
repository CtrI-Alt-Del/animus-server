from __future__ import annotations

from enum import StrEnum

from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError


class CaseAssessmentAnalysisStatusValue(StrEnum):
    WAITING_DOCUMENT_UPLOAD = 'WAITING_DOCUMENT_UPLOAD'
    DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED'
    ANALYZING_CASE = 'ANALYZING_CASE'
    CASE_ANALYZED = 'CASE_ANALYZED'
    SEARCHING_PRECEDENTS = 'SEARCHING_PRECEDENTS'
    ANALYZING_PRECEDENTS_SIMILARITY = 'ANALYZING_PRECEDENTS_SIMILARITY'
    ANALYZING_PRECEDENTS_APPLICABILITY = 'ANALYZING_PRECEDENTS_APPLICABILITY'
    GENERATING_SYNTHESIS = 'GENERATING_SYNTHESIS'
    GENERATING_PETITION_DRAFT = 'GENERATING_PETITION_DRAFT'
    PRECEDENTS_SEARCHED = 'PRECEDENTS_SEARCHED'
    DONE = 'DONE'
    FAILED = 'FAILED'


@structure
class CaseAssessmentAnalysisStatus(Structure):
    value: CaseAssessmentAnalysisStatusValue

    @classmethod
    def create(cls, value: str) -> CaseAssessmentAnalysisStatus:
        try:
            return cls(CaseAssessmentAnalysisStatusValue(value.upper()))
        except ValueError as error:
            msg = f'Status de analise case assessment invalido: {value}'
            raise ValidationError(msg) from error

    @classmethod
    def create_as_analyzing_case(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.ANALYZING_CASE)

    @classmethod
    def create_as_waiting_document_upload(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.WAITING_DOCUMENT_UPLOAD)

    @classmethod
    def create_as_document_uploaded(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.DOCUMENT_UPLOADED)

    @classmethod
    def create_as_case_analyzed(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.CASE_ANALYZED)

    @classmethod
    def create_as_precedents_searched(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.PRECEDENTS_SEARCHED)

    @classmethod
    def create_as_done(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.DONE)

    @classmethod
    def create_as_failed(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.FAILED)

    @classmethod
    def create_as_generating_synthesis(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.GENERATING_SYNTHESIS)

    @classmethod
    def create_as_generating_petition_draft(cls) -> CaseAssessmentAnalysisStatus:
        return cls(CaseAssessmentAnalysisStatusValue.GENERATING_PETITION_DRAFT)

    @property
    def dto(self) -> str:
        return self.value.value

    @classmethod
    def get_processing_statuses(
        cls,
    ) -> tuple[CaseAssessmentAnalysisStatusValue, ...]:
        return (
            CaseAssessmentAnalysisStatusValue.ANALYZING_CASE,
            CaseAssessmentAnalysisStatusValue.SEARCHING_PRECEDENTS,
            CaseAssessmentAnalysisStatusValue.ANALYZING_PRECEDENTS_SIMILARITY,
            CaseAssessmentAnalysisStatusValue.ANALYZING_PRECEDENTS_APPLICABILITY,
            CaseAssessmentAnalysisStatusValue.GENERATING_SYNTHESIS,
            CaseAssessmentAnalysisStatusValue.GENERATING_PETITION_DRAFT,
        )

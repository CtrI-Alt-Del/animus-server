from enum import StrEnum


class LawyerAnalysisStatus(StrEnum):
    WAITING_DOCUMENT_UPLOAD = 'WAITING_DOCUMENT_UPLOAD'
    DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED'
    ANALYZING_CASE = 'ANALYZING_CASE'
    CASE_ANALYZED = 'CASE_ANALYZED'
    SEARCHING_PRECEDENTS = 'SEARCHING_PRECEDENTS'
    GENERATING_PETITION_DRAFT = 'GENERATING_PETITION_DRAFT'
    DONE = 'DONE'
    FAILED = 'FAILED'

    @classmethod
    def get_processing_statuses(cls) -> tuple['LawyerAnalysisStatus', ...]:
        return (
            cls.ANALYZING_CASE,
            cls.SEARCHING_PRECEDENTS,
            cls.GENERATING_PETITION_DRAFT,
        )

from enum import StrEnum


class JudgeAnalysisStatus(StrEnum):
    WAITING_DOCUMENT_UPLOAD = 'WAITING_DOCUMENT_UPLOAD'
    DOCUMENT_UPLOADED = 'DOCUMENT_UPLOADED'
    EXTRACTING_PETITION = 'EXTRACTING_PETITION'
    ANALYZING_CASE = 'ANALYZING_CASE'
    CASE_ANALYZED = 'CASE_ANALYZED'
    SEARCHING_PRECEDENTS = 'SEARCHING_PRECEDENTS'
    GENERATING_JUDGMENT_DRAFT = 'GENERATING_JUDGMENT_DRAFT'
    DONE = 'DONE'
    FAILED = 'FAILED'

    @classmethod
    def get_processing_statuses(cls) -> tuple['JudgeAnalysisStatus', ...]:
        return (
            cls.EXTRACTING_PETITION,
            cls.ANALYZING_CASE,
            cls.SEARCHING_PRECEDENTS,
            cls.GENERATING_JUDGMENT_DRAFT,
        )

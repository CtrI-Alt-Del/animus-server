from animus.core.intake.domain.entities.analysis_type import AnalysisType
from animus.core.intake.domain.entities.judge_analysis_status import JudgeAnalysisStatus
from animus.core.intake.domain.entities.lawyer_analysis_status import LawyerAnalysisStatus
from animus.core.intake.domain.errors import AnalysisDocumentNotFoundError, AnalysisNotFoundError
from animus.core.intake.domain.structures.case_summary import CaseSummary
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalisysesRepository,
    CaseSummariesRepository,
)
from animus.core.shared.domain.structures import Id


class CreateCaseSummaryUseCase:
    def __init__(
        self,
        case_summaries_repository: CaseSummariesRepository,
        analysis_documents_repository: AnalysisDocumentsRepository,
        analisyses_repository: AnalisysesRepository,
    ) -> None:
        self._case_summaries_repository = case_summaries_repository
        self._analysis_documents_repository = analysis_documents_repository
        self._analisyses_repository = analisyses_repository

    def execute(self, analysis_id: str, dto: CaseSummaryDto) -> CaseSummaryDto:
        analysis_id_entity = Id.create(analysis_id)

        analysis_document = self._analysis_documents_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if analysis_document is None:
            raise AnalysisDocumentNotFoundError

        case_summary = CaseSummary.create(dto)
        existing_case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if existing_case_summary is None:
            self._case_summaries_repository.add(
                analysis_id=analysis_id_entity,
                case_summary=case_summary,
            )
        else:
            self._case_summaries_repository.replace(
                analysis_id=analysis_id_entity,
                case_summary=case_summary,
            )

        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        if analysis.type == AnalysisType.LAWYER:
            analysis.set_status(LawyerAnalysisStatus.CASE_ANALYZED)
        else:
            analysis.set_status(JudgeAnalysisStatus.CASE_ANALYZED)

        self._analisyses_repository.replace(analysis)
        return case_summary.dto

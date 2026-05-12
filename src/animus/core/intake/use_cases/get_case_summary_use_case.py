from animus.core.intake.domain.errors import CaseSummaryUnavailableError
from animus.core.intake.domain.structures.dtos.case_summary_dto import CaseSummaryDto
from animus.core.intake.interfaces import CaseSummariesRepository
from animus.core.shared.domain.structures import Id


class GetCaseSummaryUseCase:
    def __init__(self, case_summaries_repository: CaseSummariesRepository) -> None:
        self._case_summaries_repository = case_summaries_repository

    def execute(self, analysis_id: str) -> CaseSummaryDto:
        analysis_id_entity = Id.create(analysis_id)
        case_summary = self._case_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        if case_summary is None:
            raise CaseSummaryUnavailableError

        return case_summary.dto

from animus.core.intake.domain.entities.analysis import Analysis  # noqa: TC001
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.shared.domain.structures import Id


class ArchiveAnalysesUseCase:
    def __init__(self, analyses_repository: AnalysesRepository) -> None:
        self._analyses_repository = analyses_repository

    def execute(self, account_id: str, analysis_ids: list[str]) -> list[AnalysisDto]:
        normalized_account_id = Id.create(account_id)

        analyses: list[Analysis] = []
        for analysis_id in analysis_ids:
            normalized_analysis_id = Id.create(analysis_id)
            analysis = self._analyses_repository.find_by_id(normalized_analysis_id)

            if analysis is None or analysis.account_id != normalized_account_id:
                raise AnalysisNotFoundError

            analyses.append(analysis)

        for analysis in analyses:
            analysis.archive()
            self._analyses_repository.replace(analysis)

        return [analysis.dto for analysis in analyses]

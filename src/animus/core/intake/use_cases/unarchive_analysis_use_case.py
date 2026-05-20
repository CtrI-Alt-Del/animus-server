from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.shared.domain.structures import Id


class UnarchiveAnalysisUseCase:
    def __init__(self, analyses_repository: AnalysesRepository) -> None:
        self._analyses_repository = analyses_repository

    def execute(self, account_id: str, analysis_id: str) -> AnalysisDto:
        normalized_account_id = Id.create(account_id)
        normalized_analysis_id = Id.create(analysis_id)
        analysis = self._analyses_repository.find_by_id(normalized_analysis_id)

        if analysis is None or analysis.account_id != normalized_account_id:
            raise AnalysisNotFoundError

        analysis.unarchive()
        self._analyses_repository.replace(analysis)

        return analysis.dto

from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analyses_repository import AnalysesRepository
from animus.core.shared.domain.structures import Id


class ListProcessingAnalysesUseCase:
    def __init__(self, analyses_repository: AnalysesRepository) -> None:
        self._analyses_repository = analyses_repository

    def execute(self, account_id: str) -> list[AnalysisDto]:
        account_id_vo = Id.create(account_id)

        analyses = self._analyses_repository.find_many_in_processing(
            account_id=account_id_vo
        )

        return [analysis.dto for analysis in analyses]

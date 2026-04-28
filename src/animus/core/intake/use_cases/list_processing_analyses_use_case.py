from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.shared.domain.structures import Id


class ListProcessingAnalysesUseCase:
    def __init__(self, analisyses_repository: AnalisysesRepository) -> None:
        self._analisyses_repository = analisyses_repository

    def execute(self, account_id: str) -> list[AnalysisDto]:
        account_id_vo = Id.create(account_id)

        analyses = self._analisyses_repository.find_many_in_processing(
            account_id=account_id_vo
        )

        return [analysis.dto for analysis in analyses]

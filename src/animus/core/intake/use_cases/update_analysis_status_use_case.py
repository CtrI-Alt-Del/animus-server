from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.interfaces import AnalisysesRepository
from animus.core.shared.domain.structures import Id


class UpdateAnalysisStatusUseCase:
    def __init__(self, analisyses_repository: AnalisysesRepository) -> None:
        self._analisyses_repository = analisyses_repository

    def execute(self, analysis_id: str, status: str) -> None:
        analysis_id_entity = Id.create(analysis_id)
        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)

        if analysis is None:
            raise AnalysisNotFoundError

        analysis.set_status(status)
        self._analisyses_repository.replace(analysis)

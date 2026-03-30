from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.shared.domain.structures import Id


class ListAnalysisPrecedentsUseCase:
    def __init__(
        self,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
    ) -> None:
        self._analysis_precedents_repository = analysis_precedents_repository

    def execute(self, analysis_id: str) -> list[AnalysisPrecedentDto]:
        analysis_precedents = (
            self._analysis_precedents_repository.find_many_by_analysis_id(
                Id.create(analysis_id)
            )
        )

        return [
            analysis_precedent.dto for analysis_precedent in analysis_precedents.items
        ]

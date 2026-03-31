from animus.core.intake.domain.structures.dtos.analysis_petition_dto import (
    AnalysisPetitionDto,
)
from animus.core.intake.interfaces import (
    PetitionSummariesRepository,
    PetitionsRepository,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class ListAnalysisPetitionsUseCase:
    def __init__(
        self,
        petitions_repository: PetitionsRepository,
        petition_summaries_repository: PetitionSummariesRepository,
    ) -> None:
        self._petitions_repository = petitions_repository
        self._petition_summaries_repository = petition_summaries_repository

    def execute(self, analysis_id: str) -> ListResponse[AnalysisPetitionDto]:
        petitions = (
            self._petitions_repository.find_all_by_analysis_id_ordered_by_uploaded_at(
                analysis_id=Id.create(analysis_id),
            )
        )

        analysis_petitions: list[AnalysisPetitionDto] = []
        for petition in petitions.items:
            summary = self._petition_summaries_repository.find_by_petition_id(
                petition.id
            )
            analysis_petitions.append(
                AnalysisPetitionDto(
                    petition=petition.dto,
                    summary=summary.dto if summary is not None else None,
                )
            )

        return ListResponse(items=analysis_petitions)

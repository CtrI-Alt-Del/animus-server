from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionNotFoundError,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.shared.domain.structures import Id


class CreatePetitionSummaryUseCase:
    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
        petitions_repository: PetitionsRepository,
        analisyses_repository: AnalisysesRepository,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository
        self._petitions_repository = petitions_repository
        self._analisyses_repository = analisyses_repository

    def execute(self, petition_id: str, dto: PetitionSummaryDto) -> PetitionSummaryDto:
        petition_id_entity = Id.create(petition_id)
        print('dto', dto)
        petition_summary = PetitionSummary.create(dto)

        existing_summary = self._petition_summaries_repository.find_by_petition_id(
            petition_id=petition_id_entity,
        )

        if existing_summary is None:
            self._petition_summaries_repository.add(
                petition_id=petition_id_entity,
                petition_summary=petition_summary,
            )
        else:
            self._petition_summaries_repository.replace(
                petition_id=petition_id_entity,
                petition_summary=petition_summary,
            )

        petition = self._petitions_repository.find_by_id(petition_id_entity)
        if petition is None:
            raise PetitionNotFoundError

        analysis = self._analisyses_repository.find_by_id(petition.analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError

        updated_analysis = self._create_analysis_with_petition_analyzed_status(analysis)
        self._analisyses_repository.replace(updated_analysis)

        return petition_summary.dto

    @staticmethod
    def _create_analysis_with_petition_analyzed_status(analysis: Analysis) -> Analysis:
        analysis.set_status(AnalysisStatusValue.PETITION_ANALYZED.value)
        return analysis

from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.domain.events import PetitionReplacedEvent
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class CreatePetitionUseCase:
    def __init__(
        self,
        petitions_repository: PetitionsRepository,
        analisyses_repository: AnalisysesRepository,
        broker: Broker,
    ) -> None:
        self._petitions_repository = petitions_repository
        self._analisyses_repository = analisyses_repository
        self._broker = broker

    def execute(
        self,
        analysis_id: str,
        uploaded_at: str,
        document: PetitionDocumentDto,
    ) -> PetitionDto:
        analysis_id_entity = Id.create(analysis_id)
        existing_petition = self._petitions_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )

        if existing_petition is not None:
            self._broker.publish(
                PetitionReplacedEvent(
                    petition_document_path=existing_petition.document.file_path.value,
                )
            )
            self._petitions_repository.remove(existing_petition.id)

        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        updated_analysis = self._create_analysis_with_petition_uploaded_status(analysis)
        self._analisyses_repository.replace(updated_analysis)

        petition = Petition.create(
            PetitionDto(
                analysis_id=analysis_id,
                uploaded_at=uploaded_at,
                document=document,
            )
        )

        self._petitions_repository.add(petition)

        return petition.dto

    @staticmethod
    def _create_analysis_with_petition_uploaded_status(analysis: Analysis) -> Analysis:
        analysis.set_status(AnalysisStatusValue.PETITION_UPLOADED.value)
        return analysis

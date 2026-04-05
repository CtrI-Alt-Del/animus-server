from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatus
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.errors import AnalysisNotFoundError, PetitionNotFoundError
from animus.core.intake.domain.events import PetitionSummaryRequestedEvent
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class RequestPetitionSummaryUseCase:
    def __init__(
        self,
        petitions_repository: PetitionsRepository,
        analisyses_repository: AnalisysesRepository,
        broker: Broker,
    ) -> None:
        self._petitions_repository = petitions_repository
        self._analisyses_repository = analisyses_repository
        self._broker = broker

    def execute(self, petition_id: str) -> None:
        petition_id_entity = Id.create(petition_id)
        petition = self._petitions_repository.find_by_id(petition_id_entity)
        if petition is None:
            raise PetitionNotFoundError

        analysis = self._analisyses_repository.find_by_id(petition.analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError

        updated_analysis = self._create_analysis_with_analyzing_petition_status(
            analysis
        )
        self._analisyses_repository.replace(updated_analysis)

        self._broker.publish(
            PetitionSummaryRequestedEvent(petition_id=petition_id_entity.value)
        )

    @staticmethod
    def _create_analysis_with_analyzing_petition_status(analysis: Analysis) -> Analysis:
        status = AnalysisStatus.create_as_analyzing_petition()

        return Analysis.create(
            AnalysisDto(
                id=analysis.id.value,
                name=analysis.name.value,
                folder_id=analysis.folder_id.value
                if analysis.folder_id is not None
                else None,
                account_id=analysis.account_id.value,
                status=status.value.value,
                is_archived=analysis.is_archived.value,
                created_at=analysis.created_at.value.isoformat(),
            )
        )

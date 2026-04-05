from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.events import PetitionSummaryRequestedEvent
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionNotFoundError,
)
from animus.core.intake.interfaces import AnalisysesRepository, PetitionsRepository
from animus.core.intake.use_cases import RequestPetitionSummaryUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker


class TestRequestPetitionSummaryUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petitions_repository_mock = create_autospec(
            PetitionsRepository,
            instance=True,
        )
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = RequestPetitionSummaryUseCase(
            petitions_repository=self.petitions_repository_mock,
            analisyses_repository=self.analisyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_and_update_analysis_status(self) -> None:
        petition_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        petition_id_entity = Id.create(petition_id)
        petition = PetitionsFaker.fake(
            petition_id=petition_id,
            analysis_id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
            document=PetitionDocumentDto(
                file_path='intake/analyses/01TEST/petitions/petition.pdf',
                name='petition.pdf',
            ),
        )
        analysis = AnalysesFaker.fake(
            analysis_id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
            status=AnalysisStatusValue.PETITION_UPLOADED.value,
        )
        self.petitions_repository_mock.find_by_id.return_value = petition
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        self.use_case.execute(petition_id=petition_id)

        self.petitions_repository_mock.find_by_id.assert_called_once_with(
            petition_id_entity,
        )
        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            petition.analysis_id,
        )
        self.analisyses_repository_mock.replace.assert_called_once()
        self.broker_mock.publish.assert_called_once()

        updated_analysis = self.analisyses_repository_mock.replace.call_args.args[0]
        published_event = self.broker_mock.publish.call_args.args[0]

        assert updated_analysis.status.value == AnalysisStatusValue.ANALYZING_PETITION
        assert isinstance(published_event, PetitionSummaryRequestedEvent)
        assert published_event.payload.petition_id == petition_id

    def test_should_raise_validation_error_when_petition_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            self.use_case.execute(petition_id='invalid-petition-id')

        self.petitions_repository_mock.find_by_id.assert_not_called()
        self.analisyses_repository_mock.find_by_id.assert_not_called()
        self.analisyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_petition_not_found_error_when_petition_does_not_exist(
        self,
    ) -> None:
        petition_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.petitions_repository_mock.find_by_id.return_value = None

        with pytest.raises(PetitionNotFoundError):
            self.use_case.execute(petition_id=petition_id)

        self.analisyses_repository_mock.find_by_id.assert_not_called()
        self.analisyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        petition_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        petition = PetitionsFaker.fake(
            petition_id=petition_id,
            analysis_id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
            document=PetitionDocumentDto(
                file_path='intake/analyses/01TEST/petitions/petition.pdf',
                name='petition.pdf',
            ),
        )
        self.petitions_repository_mock.find_by_id.return_value = petition
        self.analisyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(petition_id=petition_id)

        self.analisyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

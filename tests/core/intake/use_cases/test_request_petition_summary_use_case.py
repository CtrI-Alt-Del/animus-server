from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.events import FistInstanceCaseSummarizationTriggeredEvent
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
    PetitionNotFoundError,
)
from animus.core.intake.interfaces import AnalysesRepository, PetitionsRepository
from animus.core.intake.use_cases import TriggerFistInstanceCaseSummarizationUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker


class TestTriggerFistInstanceCaseSummarizationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petitions_repository_mock = create_autospec(
            PetitionsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = TriggerFistInstanceCaseSummarizationUseCase(
            petitions_repository=self.petitions_repository_mock,
            analyses_repository=self.analyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_and_update_analysis_status(self) -> None:
        analysis_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        analysis_id_entity = Id.create(analysis_id)
        petition = PetitionsFaker.fake(
            petition_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            analysis_id=analysis_id,
            document=AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/01TEST/petitions/petition.pdf',
                name='petition.pdf',
            ),
        )
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            status=FirstInstanceAnalysisStatus.create_as_document_uploaded().dto,
        )
        self.petitions_repository_mock.find_by_id.return_value = petition
        self.analyses_repository_mock.find_by_id.return_value = analysis

        self.use_case.execute(analysis_id=analysis_id)

        self.petitions_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity,
        )
        self.analyses_repository_mock.find_by_id.assert_called_once_with(
            petition.analysis_id,
        )
        self.analyses_repository_mock.replace.assert_called_once()
        self.broker_mock.publish.assert_called_once()

        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]
        published_event = self.broker_mock.publish.call_args.args[0]

        assert (
            updated_analysis.status
            == FirstInstanceAnalysisStatus.create_as_analyzing_case()
        )
        assert isinstance(published_event, FistInstanceCaseSummarizationTriggeredEvent)
        assert published_event.payload.analysis_id == analysis_id

    def test_should_raise_validation_error_when_petition_id_is_invalid(self) -> None:
        with pytest.raises(ValidationError):
            self.use_case.execute(analysis_id='invalid-petition-id')

        self.petitions_repository_mock.find_by_id.assert_not_called()
        self.analyses_repository_mock.find_by_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_petition_not_found_error_when_petition_does_not_exist(
        self,
    ) -> None:
        analysis_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        self.petitions_repository_mock.find_by_id.return_value = None

        with pytest.raises(PetitionNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.find_by_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        petition = PetitionsFaker.fake(
            petition_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
            analysis_id=analysis_id,
            document=AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/01TEST/petitions/petition.pdf',
                name='petition.pdf',
            ),
        )
        self.petitions_repository_mock.find_by_id.return_value = petition
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

from unittest.mock import ANY, call, create_autospec

import pytest

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.events import PetitionReplacedEvent
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.use_cases.create_petition_use_case import CreatePetitionUseCase
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker


class TestCreatePetitionUseCase:
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
        self.use_case = CreatePetitionUseCase(
            petitions_repository=self.petitions_repository_mock,
            analisyses_repository=self.analisyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_create_petition_and_add_it_to_repository(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        analysis_id_entity = Id.create(analysis_id)
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            status=AnalysisStatusValue.WAITING_PETITION.value,
        )
        self.petitions_repository_mock.find_by_analysis_id.return_value = None
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        document = PetitionDocumentDto(
            file_path='petitions/initial-petition.pdf',
            name='Initial Petition.pdf',
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            uploaded_at='2026-03-31T10:30:00+00:00',
            document=document,
        )

        self.petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=analysis_id_entity,
        )
        self.petitions_repository_mock.remove.assert_not_called()
        self.petitions_repository_mock.add.assert_called_once()
        self.broker_mock.publish.assert_not_called()
        added_petition = self.petitions_repository_mock.add.call_args.args[0]

        self.analisyses_repository_mock.replace.assert_called_once()
        replaced_analysis = self.analisyses_repository_mock.replace.call_args.args[0]

        assert added_petition.dto == result
        assert replaced_analysis.status.value == AnalysisStatusValue.PETITION_UPLOADED
        assert result.id is not None
        assert result.analysis_id == analysis_id
        assert result.uploaded_at == '2026-03-31T10:30:00+00:00'
        assert result.document == document

    def test_should_replace_existing_petition_publish_event_and_update_analysis_status(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        analysis_id_entity = Id.create(analysis_id)
        existing_document = PetitionDocumentDto(
            file_path='petitions/old-petition.pdf',
            name='Old Petition.pdf',
        )
        existing_petition = PetitionsFaker.fake(
            petition_id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
            analysis_id=analysis_id,
            document=existing_document,
        )
        analysis = AnalysesFaker.fake(
            analysis_id=analysis_id,
            status=AnalysisStatusValue.WAITING_PETITION.value,
        )
        document = PetitionDocumentDto(
            file_path='petitions/new-petition.pdf',
            name='New Petition.pdf',
        )

        self.petitions_repository_mock.find_by_analysis_id.return_value = (
            existing_petition
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            analysis_id=analysis_id,
            uploaded_at='2026-03-31T10:30:00+00:00',
            document=document,
        )

        self.petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            analysis_id=analysis_id_entity,
        )
        self.broker_mock.publish.assert_called_once()
        published_event = self.broker_mock.publish.call_args.args[0]
        self.petitions_repository_mock.remove.assert_called_once_with(
            existing_petition.id
        )
        self.petitions_repository_mock.add.assert_called_once()
        self.analisyses_repository_mock.replace.assert_called_once()

        added_petition = self.petitions_repository_mock.add.call_args.args[0]
        updated_analysis = self.analisyses_repository_mock.replace.call_args.args[0]

        assert self.petitions_repository_mock.mock_calls == [
            call.find_by_analysis_id(analysis_id=analysis_id_entity),
            call.remove(existing_petition.id),
            call.add(ANY),
        ]
        assert isinstance(published_event, PetitionReplacedEvent)
        assert (
            published_event.payload.petition_document_path
            == existing_document.file_path
        )
        assert updated_analysis.status.value == AnalysisStatusValue.PETITION_UPLOADED
        assert added_petition.dto == result
        assert result.analysis_id == analysis_id
        assert result.document == document

    def test_should_raise_validation_error_when_analysis_id_is_invalid(self) -> None:
        document = PetitionDocumentDto(
            file_path='petitions/initial-petition.pdf',
            name='Initial Petition.pdf',
        )

        with pytest.raises(ValidationError, match=r'ULID invalido|ULID inválido'):
            self.use_case.execute(
                analysis_id='invalid-analysis-id',
                uploaded_at='2026-03-31T10:30:00+00:00',
                document=document,
            )

        self.petitions_repository_mock.add.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_by_id.return_value = None
        document = PetitionDocumentDto(
            file_path='petitions/initial-petition.pdf',
            name='Initial Petition.pdf',
        )

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                uploaded_at='2026-03-31T10:30:00+00:00',
                document=document,
            )

        self.petitions_repository_mock.add.assert_not_called()
        self.analisyses_repository_mock.replace.assert_not_called()

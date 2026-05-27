from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.events import (
    SecondInstanceCaseSummarizationTriggeredEvent,
)
from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
)
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
)
from animus.core.intake.use_cases import TriggerSecondInstanceCaseSummarizationUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TestTriggerSecondInstanceCaseSummarizationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analysis_documents_repository_mock = create_autospec(
            AnalysisDocumentsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.broker_mock = create_autospec(Broker, instance=True)
        self.use_case = TriggerSecondInstanceCaseSummarizationUseCase(
            analysis_documents_repository=self.analysis_documents_repository_mock,
            analyses_repository=self.analyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_publish_event_and_update_analysis_status_for_second_instance(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=SecondInstanceAnalysisStatus.create_as_document_uploaded().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_second_instance().dto,
            )
        )

        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            analysis_document
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.replace.assert_called_once()
        self.broker_mock.publish.assert_called_once()

        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]
        published_event = self.broker_mock.publish.call_args.args[0]

        assert (
            updated_analysis.status
            == SecondInstanceAnalysisStatus.create_as_extracting_court_document_pieces()
        )
        assert isinstance(
            published_event, SecondInstanceCaseSummarizationTriggeredEvent
        )
        assert published_event.payload.analysis_id == analysis_id

    def test_should_raise_analysis_document_not_found_error_when_document_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = None

        with pytest.raises(AnalysisDocumentNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.find_by_id.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )
        self.analysis_documents_repository_mock.find_by_analysis_id.return_value = (
            analysis_document
        )
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id)

        self.analyses_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()

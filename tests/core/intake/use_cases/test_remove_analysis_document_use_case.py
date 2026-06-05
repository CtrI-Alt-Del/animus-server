from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.events import AnalysisDocumentRemovedEvent
from animus.core.intake.domain.errors import (
    AnalysisDocumentNotFoundError,
    AnalysisNotFoundError,
)
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
)
from animus.core.intake.use_cases.remove_analysis_document_use_case import (
    RemoveAnalysisDocumentUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TestRemoveAnalysisDocumentUseCase:
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
        self.use_case = RemoveAnalysisDocumentUseCase(
            analysis_documents_repository=self.analysis_documents_repository_mock,
            analyses_repository=self.analyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_remove_analysis_document_publish_event_and_reset_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=FirstInstanceAnalysisStatus.create_as_document_uploaded().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_first_instance().dto,
            )
        )
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_file_path.return_value = (
            analysis_document
        )

        self.use_case.execute(
            analysis_id=analysis_id,
            file_path='intake/analyses/document.pdf',
        )

        self.analysis_documents_repository_mock.remove_by_file_path.assert_called_once()
        self.broker_mock.publish.assert_called_once()
        self.analyses_repository_mock.replace.assert_called_once()

        published_event = self.broker_mock.publish.call_args.args[0]
        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]

        assert isinstance(published_event, AnalysisDocumentRemovedEvent)
        assert (
            published_event.payload.analysis_document_path
            == 'intake/analyses/document.pdf'
        )
        assert (
            updated_analysis.status
            == FirstInstanceAnalysisStatus.create_as_waiting_document_upload()
        )

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=Id.create().value,
                file_path='intake/analyses/document.pdf',
            )

        self.analysis_documents_repository_mock.remove_by_file_path.assert_not_called()
        self.broker_mock.publish.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_remove_case_assessment_document_without_resetting_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=CaseAssessmentAnalysisStatus.create_as_briefing_submitted().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_case_assessment().dto,
            )
        )
        analysis_document = AnalysisDocument.create(
            AnalysisDocumentDto(
                analysis_id=analysis_id,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_file_path.return_value = (
            analysis_document
        )

        self.use_case.execute(
            analysis_id=analysis_id,
            file_path='intake/analyses/document.pdf',
        )

        self.analysis_documents_repository_mock.remove_by_file_path.assert_called_once()
        self.broker_mock.publish.assert_called_once()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_analysis_document_not_found_error_when_document_does_not_exist(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=CaseAssessmentAnalysisStatus.create_as_document_uploaded().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_case_assessment().dto,
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_file_path.return_value = None

        with pytest.raises(AnalysisDocumentNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                file_path='intake/analyses/document.pdf',
            )

        self.analysis_documents_repository_mock.remove_by_file_path.assert_not_called()
        self.broker_mock.publish.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

    def test_should_raise_analysis_document_not_found_error_when_file_path_differs(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=CaseAssessmentAnalysisStatus.create_as_document_uploaded().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_case_assessment().dto,
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.analysis_documents_repository_mock.find_by_file_path.return_value = None

        with pytest.raises(AnalysisDocumentNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                file_path='intake/analyses/other-document.pdf',
            )

        self.analysis_documents_repository_mock.remove_by_file_path.assert_not_called()
        self.broker_mock.publish.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

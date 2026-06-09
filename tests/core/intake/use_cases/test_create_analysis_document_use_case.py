from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.structures.second_instance_analysis_status import (
    SecondInstanceAnalysisStatus,
)
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.structures.analysis_document import AnalysisDocument
from animus.core.intake.domain.structures.dtos.analysis_document_dto import (
    AnalysisDocumentDto,
)
from animus.core.intake.interfaces import (
    AnalysisDocumentsRepository,
    AnalysesRepository,
)
from animus.core.intake.use_cases.create_analysis_document_use_case import (
    CreateAnalysisDocumentUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.interfaces import Broker


class TestCreateAnalysisDocumentUseCase:
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
        self.use_case = CreateAnalysisDocumentUseCase(
            analysis_documents_repository=self.analysis_documents_repository_mock,
            analyses_repository=self.analyses_repository_mock,
            broker=self.broker_mock,
        )

    def test_should_add_analysis_document_without_updating_case_assessment_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=CaseAssessmentAnalysisStatus.create_as_waiting_document_upload().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_case_assessment().dto,
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        result = self.use_case.execute(
            analysis_id=analysis_id,
            uploaded_at='2026-03-31T10:30:00+00:00',
            file_path='intake/analyses/document.pdf',
            name='document.pdf',
        )

        self.analysis_documents_repository_mock.add.assert_called_once()
        self.analysis_documents_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_documents_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

        assert (
            result
            == AnalysisDocument.create(
                AnalysisDocumentDto(
                    analysis_id=analysis_id,
                    uploaded_at='2026-03-31T10:30:00+00:00',
                    file_path='intake/analyses/document.pdf',
                    name='document.pdf',
                )
            ).dto
        )

    def test_should_add_analysis_document_without_replacing_existing_one_and_update_second_instance_status(
        self,
    ) -> None:
        analysis_id = Id.create().value
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise',
                account_id=Id.create().value,
                status=SecondInstanceAnalysisStatus.create_as_waiting_document_upload().dto,
                created_at='2026-03-31T10:30:00+00:00',
                type=AnalysisType.create_as_second_instance().dto,
            )
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            analysis_id=analysis_id,
            uploaded_at='2026-03-31T10:30:00+00:00',
            file_path='intake/analyses/new-document.pdf',
            name='new-document.pdf',
        )

        self.analysis_documents_repository_mock.add.assert_called_once()
        self.analysis_documents_repository_mock.find_by_analysis_id.assert_not_called()
        self.analysis_documents_repository_mock.replace.assert_not_called()
        self.broker_mock.publish.assert_not_called()
        self.analyses_repository_mock.replace.assert_called_once()

        updated_analysis = self.analyses_repository_mock.replace.call_args.args[0]

        assert result.file_path == 'intake/analyses/new-document.pdf'
        assert (
            updated_analysis.status
            == SecondInstanceAnalysisStatus.create_as_document_uploaded()
        )

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=Id.create().value,
                uploaded_at='2026-03-31T10:30:00+00:00',
                file_path='intake/analyses/document.pdf',
                name='document.pdf',
            )

        self.analysis_documents_repository_mock.add.assert_not_called()
        self.analysis_documents_repository_mock.replace.assert_not_called()
        self.analyses_repository_mock.replace.assert_not_called()

from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities.dtos import (
    PetitionDocumentDto,
    PrecedentDto,
)
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.analysis_precedents_repository import (
    AnalysisPrecedentsRepository,
)
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.intake.use_cases.get_analysis_report_use_case import (
    GetAnalysisReportUseCase,
)
from animus.core.shared.domain.errors.forbidden_error import ForbiddenError
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse
from animus.fakers.intake.entities.analyses_faker import AnalysesFaker
from animus.fakers.intake.entities.petitions_faker import PetitionsFaker
from animus.fakers.intake.structures.petition_summaries_faker import (
    PetitionSummariesFaker,
)


class TestGetAnalysisReportUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository, instance=True
        )
        self.petitions_repository_mock = create_autospec(
            PetitionsRepository, instance=True
        )
        self.petition_summaries_repository_mock = create_autospec(
            PetitionSummariesRepository, instance=True
        )
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository, instance=True
        )
        self.use_case = GetAnalysisReportUseCase(
            analisyses_repository=self.analisyses_repository_mock,
            petitions_repository=self.petitions_repository_mock,
            petition_summaries_repository=self.petition_summaries_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
        )

    def test_should_return_analysis_report_dto_with_aggregated_data_and_classified_precedents(
        self,
    ) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)
        petition = PetitionsFaker.fake(
            analysis_id=analysis_id,
            document=PetitionDocumentDto(file_path='path/to/file.pdf', name='file.pdf'),
        )
        summary = PetitionSummariesFaker.fake()

        precedent_1 = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=Id.create().value,
                    identifier=PrecedentIdentifierDto(court='STF', kind='RG', number=1),
                    status='vigente',
                    enunciation='E1',
                    thesis='T1',
                    last_updated_in_pangea_at='2026-04-04T10:00:00Z',
                ),
                similarity_percentage=90.0,
                is_chosen=True,
                synthesis='S1',
            )
        )
        precedent_2 = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=Id.create().value,
                    identifier=PrecedentIdentifierDto(court='STF', kind='RG', number=2),
                    status='vigente',
                    enunciation='E2',
                    thesis='T2',
                    last_updated_in_pangea_at='2026-04-04T10:00:00Z',
                ),
                similarity_percentage=75.0,
                is_chosen=False,
                synthesis='S2',
            )
        )

        self.analisyses_repository_mock.find_by_id.return_value = analysis
        self.petitions_repository_mock.find_by_analysis_id.return_value = petition
        self.petition_summaries_repository_mock.find_by_analysis_id.return_value = (
            summary
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[precedent_1, precedent_2]
        )

        # Act
        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        # Assert
        assert result.analysis == analysis.dto
        assert result.petition == petition.dto
        assert result.summary == summary.dto
        assert len(result.precedents) == 2
        assert result.precedents[0].applicability_level == 2
        assert result.precedents[1].applicability_level == 1

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.petitions_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.petition_summaries_repository_mock.find_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )

    def test_should_raise_forbidden_error_when_account_id_does_not_match(self) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        wrong_account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)

        self.analisyses_repository_mock.find_by_id.return_value = analysis

        # Act & Assert
        with pytest.raises(ForbiddenError):
            self.use_case.execute(analysis_id=analysis_id, account_id=wrong_account_id)

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value

        self.analisyses_repository_mock.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

    def test_should_classify_precedents_correctly(self) -> None:
        # Arrange
        analysis_id = Id.create().value
        account_id = Id.create().value
        analysis = AnalysesFaker.fake(analysis_id=analysis_id, account_id=account_id)
        petition = PetitionsFaker.fake(
            analysis_id=analysis_id,
            document=PetitionDocumentDto(file_path='path/to/file.pdf', name='file.pdf'),
        )
        summary = PetitionSummariesFaker.fake()

        def create_precedent(percentage: float | None) -> AnalysisPrecedent:
            return AnalysisPrecedent.create(
                AnalysisPrecedentDto(
                    analysis_id=analysis_id,
                    precedent=PrecedentDto(
                        id=Id.create().value,
                        identifier=PrecedentIdentifierDto(
                            court='STF', kind='RG', number=int(percentage or 0)
                        ),
                        status='vigente',
                        enunciation='E',
                        thesis='T',
                        last_updated_in_pangea_at='2026-04-04T10:00:00Z',
                    ),
                    similarity_percentage=percentage,
                    is_chosen=False,
                    synthesis='S',
                )
            )

        precedents = [
            create_precedent(85.0),
            create_precedent(84.9),
            create_precedent(70.0),
            create_precedent(69.9),
            create_precedent(None),
        ]

        self.analisyses_repository_mock.find_by_id.return_value = analysis
        self.petitions_repository_mock.find_by_analysis_id.return_value = petition
        self.petition_summaries_repository_mock.find_by_analysis_id.return_value = (
            summary
        )
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=precedents
        )

        # Act
        result = self.use_case.execute(analysis_id=analysis_id, account_id=account_id)

        # Assert
        assert result.precedents[0].applicability_level == 2  # 85.0
        assert result.precedents[1].applicability_level == 1  # 84.9
        assert result.precedents[2].applicability_level == 1  # 70.0
        assert result.precedents[3].applicability_level == 0  # 69.9
        assert result.precedents[4].applicability_level == 0  # None

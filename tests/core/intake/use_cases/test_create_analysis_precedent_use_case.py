from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis, Precedent
from animus.core.intake.domain.entities.dtos import AnalysisDto, PrecedentDto
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.errors.precedent_not_found_error import (
    PrecedentNotFoundError,
)
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.analysis_type import AnalysisType
from animus.core.intake.domain.structures.case_assessment_analysis_status import (
    CaseAssessmentAnalysisStatus,
)
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases import CreateAnalysisPrecedentUseCase
from animus.core.shared.domain.structures import Id


class TestCreateAnalysisPrecedentUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository,
            instance=True,
        )
        self.analisyses_repository_mock = create_autospec(
            AnalisysesRepository,
            instance=True,
        )
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository,
            instance=True,
        )
        self.use_case = CreateAnalysisPrecedentUseCase(
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            analisyses_repository=self.analisyses_repository_mock,
            precedents_repository=self.precedents_repository_mock,
        )

    def test_should_create_analysis_precedent_when_analysis_and_precedent_exist(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Analise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                type=AnalysisType.create_as_first_instance().dto,
                status=CaseAssessmentAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )
        precedent = Precedent.create(
            PrecedentDto(
                id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
                identifier=precedent_identifier_dto,
                status='vigente',
                enunciation='Enunciado do precedente',
                thesis='Tese do precedente',
                last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
            )
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = precedent
        self.analysis_precedents_repository_mock.find_by_analysis_id_and_precedent_id.return_value = None

        result = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.precedents_repository_mock.find_by_identifier.assert_called_once()
        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_called_once()
        assert result.analysis_id == analysis_id
        assert result.precedent.identifier == precedent_identifier_dto

    def test_should_return_existing_analysis_precedent_when_it_already_exists(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Analise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                type=AnalysisType.create_as_first_instance().dto,
                status=CaseAssessmentAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )
        precedent = Precedent.create(
            PrecedentDto(
                id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
                identifier=precedent_identifier_dto,
                status='vigente',
                enunciation='Enunciado do precedente',
                thesis='Tese do precedente',
                last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
            )
        )
        existing_analysis_precedent = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=precedent.dto,
                is_chosen=False,
                similarity_score=None,
                synthesis=None,
                thesis_similarity_score=0.0,
                enunciation_similarity_score=0.0,
                total_search_hits=0,
                similarity_rank=0,
                final_rank=0,
                applicability_level=0,
                legal_features=None,
            )
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = precedent
        self.analysis_precedents_repository_mock.find_by_analysis_id_and_precedent_id.return_value = (
            existing_analysis_precedent
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_not_called()
        assert result == existing_analysis_precedent.dto

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analisyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
            )

    def test_should_raise_precedent_not_found_error_when_precedent_does_not_exist(
        self,
    ) -> None:
        analysis = Analysis.create(
            AnalysisDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Analise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                type=AnalysisType.create_as_first_instance().dto,
                status=CaseAssessmentAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )
        self.analisyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = None

        with pytest.raises(PrecedentNotFoundError):
            self.use_case.execute(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
            )

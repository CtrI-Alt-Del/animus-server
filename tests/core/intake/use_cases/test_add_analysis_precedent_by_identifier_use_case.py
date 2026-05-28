from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis, Precedent
from animus.core.intake.domain.entities.dtos import AnalysisDto, PrecedentDto
from animus.core.intake.domain.errors import (
    AnalysisNotFoundError,
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
    AnalysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases import AddAnalysisPrecedentByIdentifierUseCase
from animus.core.shared.domain.structures import Id


class TestAddAnalysisPrecedentByIdentifierUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository,
            instance=True,
        )
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository,
            instance=True,
        )
        self.use_case = AddAnalysisPrecedentByIdentifierUseCase(
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            analyses_repository=self.analyses_repository_mock,
            precedents_repository=self.precedents_repository_mock,
        )

    def test_should_add_new_precedent_to_analysis_when_it_does_not_exist_yet(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        precedent = Precedent.create(
            PrecedentDto(
                id=precedent_id,
                identifier=precedent_identifier_dto,
                status='vigente',
                enunciation='Enunciado do precedente',
                thesis='Tese do precedente',
                last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
            )
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                type=AnalysisType.create_as_first_instance().dto,
                status=CaseAssessmentAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = precedent
        self.analysis_precedents_repository_mock.find_by_analysis_id_and_precedent_id.return_value = (
            None
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_called_once()
        args, _ = self.analysis_precedents_repository_mock.add_many_by_analysis_id.call_args
        assert args[0] == Id.create(analysis_id)
        assert len(args[1]) == 1
        added_precedent = args[1][0]
        assert added_precedent.precedent.id == Id.create(precedent_id)
        assert added_precedent.is_chosen.value is True
        assert added_precedent.applicability_level.dto == 2
        assert added_precedent.is_manually_added.value is True
        
        assert result.value == analysis.status.dto

    def test_should_choose_existing_precedent_when_it_already_exists_in_analysis(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        precedent = Precedent.create(
            PrecedentDto(
                id=precedent_id,
                identifier=precedent_identifier_dto,
                status='vigente',
                enunciation='Enunciado do precedente',
                thesis='Tese do precedente',
                last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
            )
        )
        analysis = Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Análise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                type=AnalysisType.create_as_first_instance().dto,
                status=CaseAssessmentAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )
        existing_relation = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=precedent.dto,
                is_chosen=False,
                similarity_score=84.5,
                synthesis='Sintese do precedente',
            )
        )

        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = precedent
        self.analysis_precedents_repository_mock.find_by_analysis_id_and_precedent_id.return_value = (
            existing_relation
        )

        result = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analysis_precedents_repository_mock.choose_by_analysis_id_and_precedent_id.assert_called_once_with(
            Id.create(analysis_id),
            Id.create(precedent_id),
        )
        assert result.value == analysis.status.dto

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
            )

    def test_should_raise_precedent_not_found_error_when_precedent_does_not_exist_in_pangea(
        self,
    ) -> None:
        analysis = Analysis.create(
            AnalysisDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                name='Análise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                type=AnalysisType.create_as_first_instance().dto,
                status=CaseAssessmentAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
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

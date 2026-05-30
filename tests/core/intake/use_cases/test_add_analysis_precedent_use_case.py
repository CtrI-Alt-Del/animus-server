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
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.first_instance_analysis_status import (
    FirstInstanceAnalysisStatus,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalysesRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases.add_analysis_precedent_use_case import (
    AddAnalysisPrecedentUseCase,
)


class TestAddAnalysisPrecedentUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.analyses_repository_mock = create_autospec(
            AnalysesRepository,
            instance=True,
        )
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository,
            instance=True,
        )
        self.analysis_precedents_repository_mock = create_autospec(
            AnalysisPrecedentsRepository,
            instance=True,
        )
        self.use_case = AddAnalysisPrecedentUseCase(
            analyses_repository=self.analyses_repository_mock,
            precedents_repository=self.precedents_repository_mock,
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
        )

    def test_should_add_manual_precedent_when_it_does_not_exist(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        analysis = self._create_analysis_entity(analysis_id)
        precedent = self._create_precedent_entity()
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = precedent
        self.analysis_precedents_repository_mock.find_by_analysis_id_and_precedent_id.return_value = None

        response = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_called_once()
        add_call = self.analysis_precedents_repository_mock.add_many_by_analysis_id.call_args.kwargs
        saved_precedent = add_call['analysis_precedents'][0]
        assert isinstance(saved_precedent, AnalysisPrecedent)
        assert saved_precedent.is_chosen.is_true
        assert saved_precedent.is_manually_added.is_true
        assert response.precedent.id == precedent.id.value
        assert response.is_chosen is True
        assert response.is_manually_added is True

    def test_should_return_existing_precedent_when_already_added(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        analysis = self._create_analysis_entity(analysis_id)
        precedent = self._create_precedent_entity()
        existing_analysis_precedent = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=precedent.dto,
                is_chosen=True,
                is_manually_added=True,
            )
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis
        self.precedents_repository_mock.find_by_identifier.return_value = precedent
        self.analysis_precedents_repository_mock.find_by_analysis_id_and_precedent_id.return_value = existing_analysis_precedent

        response = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_not_called()
        assert response.precedent.id == precedent.id.value
        assert response.is_manually_added is True

    def test_should_raise_when_analysis_does_not_exist(self) -> None:
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

        self.precedents_repository_mock.find_by_identifier.assert_not_called()

    def test_should_raise_when_precedent_does_not_exist(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        self.analyses_repository_mock.find_by_id.return_value = (
            self._create_analysis_entity(analysis_id)
        )
        self.precedents_repository_mock.find_by_identifier.return_value = None

        with pytest.raises(PrecedentNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
            )

        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_not_called()

    @staticmethod
    def _create_analysis_entity(analysis_id: str) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                name='Análise teste',
                type=AnalysisType.create_as_first_instance().dto,
                status=FirstInstanceAnalysisStatus.create_as_done().dto,
                is_archived=False,
                created_at='2026-01-01T00:00:00+00:00',
            )
        )

    @staticmethod
    def _create_precedent_entity() -> Precedent:
        return Precedent.create(
            PrecedentDto(
                id='01ARZ3NDEKTSV4RRFFQ69G5FAB',
                identifier=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
                status='vigente',
                enunciation='Enunciado',
                thesis='Tese',
                last_updated_in_pangea_at='2026-01-01T00:00:00+00:00',
            )
        )

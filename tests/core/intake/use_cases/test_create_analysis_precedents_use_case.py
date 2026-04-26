from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.entities.dtos import AnalysisDto, PrecedentDto
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentDto,
    AnalysisPrecedentsSearchFiltersDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
)
from animus.core.intake.use_cases.create_analysis_precedents_use_case import (
    CreateAnalysisPrecedentsUseCase,
)
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Id


class TestCreateAnalysisPrecedentsUseCase:
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
        self.use_case = CreateAnalysisPrecedentsUseCase(
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            analisyses_repository=self.analisyses_repository_mock,
        )

    def test_should_create_and_save_precedents_without_synthesis_output(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        filters_dto = AnalysisPrecedentsSearchFiltersDto(
            courts=['STF'],
            precedent_kinds=['RG'],
            limit=10,
        )
        analysis_precedents = [
            self._create_analysis_precedent_dto(
                analysis_id=analysis_id,
                number=101,
                similarity_score=84.5,
                similarity_rank=1,
                synthesis=None,
            )
        ]
        analysis = self._create_analysis_entity(analysis_id)
        self.analisyses_repository_mock.find_by_id.return_value = analysis

        self.use_case.execute(
            analysis_id=analysis_id,
            filters_dto=filters_dto,
            analysis_precedents=analysis_precedents,
        )

        analysis_id_entity = Id.create(analysis_id)
        self.analysis_precedents_repository_mock.remove_many_by_analysis_id.assert_called_once_with(
            analysis_id_entity
        )
        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_called_once()
        add_call = self.analysis_precedents_repository_mock.add_many_by_analysis_id.call_args.kwargs
        saved_precedents = add_call['analysis_precedents']
        assert add_call['analysis_id'] == analysis_id_entity
        assert len(saved_precedents) == 1
        assert isinstance(saved_precedents[0], AnalysisPrecedent)
        assert saved_precedents[0].similarity_score is not None
        assert saved_precedents[0].similarity_score.value == 84.5
        assert saved_precedents[0].synthesis is None
        assert saved_precedents[0].legal_features is None

        self.analisyses_repository_mock.find_by_id.assert_called_once_with(
            analysis_id_entity
        )
        self.analisyses_repository_mock.replace.assert_called_once()
        updated_analysis = self.analisyses_repository_mock.replace.call_args.args[0]
        assert (
            updated_analysis.status.value.value
            == AnalysisStatusValue.WAITING_PRECEDENT_CHOISE.value
        )
        assert updated_analysis.precedents_search_filters is not None
        assert updated_analysis.precedents_search_filters.dto == filters_dto

    def test_should_merge_synthesis_output_when_synthesis_is_provided(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        filters_dto = AnalysisPrecedentsSearchFiltersDto(
            courts=['STF'],
            precedent_kinds=['RG'],
            limit=10,
        )
        analysis_precedents = [
            self._create_analysis_precedent_dto(
                analysis_id=analysis_id,
                number=101,
                similarity_score=84.5,
                similarity_rank=1,
                synthesis=None,
            )
        ]
        synthesis_output = SimpleNamespace(
            items=[
                SimpleNamespace(
                    court='STF',
                    kind='RG',
                    number=101,
                    synthesis='  Sintese final  ',
                    legal_features=SimpleNamespace(
                        central_issue_match=2,
                        structural_issue_match=1,
                        context_compatibility=2,
                        is_lateral_topic=0,
                        is_accessory_topic=0,
                    ),
                )
            ]
        )
        self.analisyses_repository_mock.find_by_id.return_value = (
            self._create_analysis_entity(analysis_id)
        )

        self.use_case.execute(
            analysis_id=analysis_id,
            filters_dto=filters_dto,
            analysis_precedents=analysis_precedents,
            synthesis_output=synthesis_output,
        )

        saved_precedents = self.analysis_precedents_repository_mock.add_many_by_analysis_id.call_args.kwargs[
            'analysis_precedents'
        ]
        assert len(saved_precedents) == 1
        assert saved_precedents[0].synthesis is not None
        assert saved_precedents[0].synthesis.value == 'Sintese final'
        assert saved_precedents[0].legal_features is not None
        assert saved_precedents[0].legal_features.central_issue_match.value == 2

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        filters_dto = AnalysisPrecedentsSearchFiltersDto(limit=10)
        analysis_precedents = [
            self._create_analysis_precedent_dto(
                analysis_id=analysis_id,
                number=101,
                similarity_score=84.5,
                similarity_rank=1,
                synthesis=None,
            )
        ]
        self.analisyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                filters_dto=filters_dto,
                analysis_precedents=analysis_precedents,
            )

        self.analysis_precedents_repository_mock.remove_many_by_analysis_id.assert_called_once_with(
            Id.create(analysis_id)
        )
        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_called_once()
        self.analisyses_repository_mock.replace.assert_not_called()

    def test_should_raise_app_error_when_synthesis_for_precedent_is_missing(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        filters_dto = AnalysisPrecedentsSearchFiltersDto(limit=10)
        analysis_precedents = [
            self._create_analysis_precedent_dto(
                analysis_id=analysis_id,
                number=101,
                similarity_score=84.5,
                similarity_rank=1,
                synthesis=None,
            )
        ]
        synthesis_output = SimpleNamespace(
            items=[
                SimpleNamespace(
                    court='STF',
                    kind='RG',
                    number=999,
                    synthesis='Sintese de outro precedente',
                    legal_features=SimpleNamespace(
                        central_issue_match=2,
                        structural_issue_match=1,
                        context_compatibility=2,
                        is_lateral_topic=0,
                        is_accessory_topic=0,
                    ),
                )
            ]
        )

        with pytest.raises(AppError) as error:
            self.use_case.execute(
                analysis_id=analysis_id,
                filters_dto=filters_dto,
                analysis_precedents=analysis_precedents,
                synthesis_output=synthesis_output,
            )

        assert (
            error.value.message
            == 'Missing synthesis for at least one precedent identifier'
        )
        self.analysis_precedents_repository_mock.remove_many_by_analysis_id.assert_not_called()
        self.analysis_precedents_repository_mock.add_many_by_analysis_id.assert_not_called()
        self.analisyses_repository_mock.find_by_id.assert_not_called()
        self.analisyses_repository_mock.replace.assert_not_called()

    @staticmethod
    def _create_analysis_precedent_dto(
        analysis_id: str,
        number: int,
        similarity_score: float,
        similarity_rank: int,
        synthesis: str | None,
    ) -> AnalysisPrecedentDto:
        return AnalysisPrecedentDto(
            analysis_id=analysis_id,
            precedent=PrecedentDto(
                id='01B3EAF4Q2V7D9N8M6K5J4H3G2',
                identifier=PrecedentIdentifierDto(
                    court='STF', kind='RG', number=number
                ),
                status='vigente',
                enunciation='Enunciado do precedente',
                thesis='Tese do precedente',
                last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
            ),
            is_chosen=False,
            similarity_score=similarity_score,
            thesis_similarity_score=0.8,
            enunciation_similarity_score=0.75,
            total_search_hits=3,
            similarity_rank=similarity_rank,
            synthesis=synthesis,
        )

    @staticmethod
    def _create_analysis_entity(analysis_id: str) -> Analysis:
        return Analysis.create(
            AnalysisDto(
                id=analysis_id,
                name='Analise de precedentes',
                folder_id=None,
                account_id='01ARZ3NDEKTSV4RRFFQ69G5FAA',
                status=AnalysisStatusValue.SEARCHING_PRECEDENTS.value,
                is_archived=False,
                created_at='2026-03-31T10:30:00+00:00',
            )
        )

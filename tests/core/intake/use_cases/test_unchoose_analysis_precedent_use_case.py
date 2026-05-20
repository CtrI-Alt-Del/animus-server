from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Analysis
from animus.core.intake.domain.entities.dtos import AnalysisDto, PrecedentDto
from animus.core.intake.domain.errors.analysis_not_found_error import (
    AnalysisNotFoundError,
)
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
    AnalysesRepository,
)
from animus.core.intake.use_cases import UnchooseAnalysisPrecedentUseCase
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class TestUnchooseAnalysisPrecedentUseCase:
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
        self.use_case = UnchooseAnalysisPrecedentUseCase(
            analysis_precedents_repository=self.analysis_precedents_repository_mock,
            analyses_repository=self.analyses_repository_mock,
        )

    def test_should_unchoose_precedent_when_identifier_exists(self) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        analysis_precedent = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=precedent_id,
                    identifier=precedent_identifier_dto,
                    status='vigente',
                    enunciation='Enunciado do precedente',
                    thesis='Tese do precedente',
                    last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
                ),
                similarity_score=84.5,
                synthesis='Sintese do precedente',
                is_chosen=True,
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

        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[analysis_precedent]
        )
        self.analyses_repository_mock.find_by_id.return_value = analysis

        result = self.use_case.execute(
            analysis_id=analysis_id,
            precedent_identifier_dto=precedent_identifier_dto,
        )

        self.analysis_precedents_repository_mock.unchoose_by_analysis_id_and_precedent_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
            precedent_id=analysis_precedent.precedent.id,
        )
        self.analyses_repository_mock.replace.assert_called_once_with(analysis)
        assert result.value == analysis.status.dto

    def test_should_raise_precedent_not_found_error_when_identifier_does_not_exist(
        self,
    ) -> None:
        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[]
        )

        with pytest.raises(PrecedentNotFoundError):
            self.use_case.execute(
                analysis_id='01ARZ3NDEKTSV4RRFFQ69G5FAV',
                precedent_identifier_dto=PrecedentIdentifierDto(
                    court='STF',
                    kind='RG',
                    number=101,
                ),
            )

    def test_should_raise_analysis_not_found_error_when_analysis_does_not_exist(
        self,
    ) -> None:
        analysis_id = '01ARZ3NDEKTSV4RRFFQ69G5FAV'
        precedent_id = '01B3EAF4Q2V7D9N8M6K5J4H3G2'
        precedent_identifier_dto = PrecedentIdentifierDto(
            court='STF',
            kind='RG',
            number=101,
        )
        analysis_precedent = AnalysisPrecedent.create(
            AnalysisPrecedentDto(
                analysis_id=analysis_id,
                precedent=PrecedentDto(
                    id=precedent_id,
                    identifier=precedent_identifier_dto,
                    status='vigente',
                    enunciation='Enunciado do precedente',
                    thesis='Tese do precedente',
                    last_updated_in_pangea_at='2026-03-31T10:30:00+00:00',
                ),
                similarity_score=84.5,
                synthesis='Sintese do precedente',
                is_chosen=True,
            )
        )

        self.analysis_precedents_repository_mock.find_many_by_analysis_id.return_value = ListResponse(
            items=[analysis_precedent]
        )
        self.analyses_repository_mock.find_by_id.return_value = None

        with pytest.raises(AnalysisNotFoundError):
            self.use_case.execute(
                analysis_id=analysis_id,
                precedent_identifier_dto=precedent_identifier_dto,
            )

        self.analysis_precedents_repository_mock.unchoose_by_analysis_id_and_precedent_id.assert_called_once_with(
            analysis_id=Id.create(analysis_id),
            precedent_id=analysis_precedent.precedent.id,
        )

from unittest.mock import create_autospec

import pytest

from animus.core.intake.domain.entities import Precedent
from animus.core.intake.domain.entities.dtos import PrecedentDto
from animus.core.intake.domain.structures.dtos import (
    AnalysisPrecedentsSearchFiltersDto,
    PetitionSummaryDto,
    PrecedentEmbeddingDto,
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.interfaces import (
    PetitionSummariesRepository,
    PetitionSummaryEmbeddingsProvider,
    PrecedentsEmbeddingsRepository,
    PrecedentsRepository,
)
from animus.core.intake.use_cases.search_analysis_precedents_use_case import (
    SearchAnalysisPrecedentsUseCase,
)
from animus.core.shared.domain.structures import Id
from animus.core.shared.responses import ListResponse


class TestSearchAnalysisPrecedentsUseCase:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.petition_summaries_repository_mock = create_autospec(
            PetitionSummariesRepository,
            instance=True,
        )
        self.petition_summary_embeddings_provider_mock = create_autospec(
            PetitionSummaryEmbeddingsProvider,
            instance=True,
        )
        self.precedents_embeddings_repository_mock = create_autospec(
            PrecedentsEmbeddingsRepository,
            instance=True,
        )
        self.precedents_repository_mock = create_autospec(
            PrecedentsRepository,
            instance=True,
        )
        self.use_case = SearchAnalysisPrecedentsUseCase(
            petition_summaries_repository=self.petition_summaries_repository_mock,
            petition_summary_embeddings_provider=self.petition_summary_embeddings_provider_mock,
            precedents_embeddings_repository=self.precedents_embeddings_repository_mock,
            precedents_repository=self.precedents_repository_mock,
        )

    def test_should_prioritize_matching_competence_and_legitimacy_axes(self) -> None:
        # Arrange
        analysis_id = Id.create().value
        rg_242 = self._create_precedent(
            number=242,
            enunciation='Competencia para processar e julgar acoes indenizatorias decorrentes de acidente do trabalho propostas por sucessores do trabalhador falecido.',
            thesis='Compete a Justica do Trabalho processar e julgar as acoes propostas pelos sucessores do trabalhador falecido.',
        )
        rg_932 = self._create_precedent(
            number=932,
            enunciation='Possibilidade de responsabilizacao objetiva do empregador por danos decorrentes de acidentes de trabalho.',
            thesis='O art. 927, paragrafo unico, permite a responsabilizacao objetiva do empregador em atividade de risco.',
        )
        rr_556 = self._create_precedent(
            court='STJ',
            kind='RR',
            number=556,
            enunciation='Discute-se a possibilidade de cumular auxilio-acidente com aposentadoria.',
            thesis='Para casos de doenca profissional ou do trabalho, aplica-se a disciplina do art. 23 da Lei 8.213/1991.',
        )

        self.petition_summaries_repository_mock.find_by_analysis_id.return_value = PetitionSummary.create(
            PetitionSummaryDto(
                case_summary='Acao de indenizacao por danos morais e materiais decorrentes de acidente de trabalho com obito, proposta por sucessores e dependentes.',
                legal_issue='Competencia da Justica do Trabalho e legitimidade dos sucessores para buscar responsabilizacao civil subjetiva do empregador por culpa e falha em normas de seguranca.',
                central_question='A Justica do Trabalho e competente para julgar a demanda proposta por sucessores de trabalhador falecido e, no merito, a culpa patronal por inobservancia de normas de seguranca gera dever de indenizar?',
                relevant_laws=['CF, artigo 114', 'CF, artigo 7o, XXVIII'],
                key_facts=[
                    'Os autores sao sucessores e dependentes do trabalhador falecido.',
                    'Ha alegacao de culpa patronal por descumprimento de normas de seguranca.',
                ],
                search_terms=[
                    'competencia justica do trabalho sucessores',
                    'culpa empregador acidente fatal',
                ],
            )
        )
        self.petition_summary_embeddings_provider_mock.generate.return_value = []
        self.precedents_embeddings_repository_mock.find_many.return_value = (
            ListResponse(
                items=[
                    self._create_embedding(rg_242.dto.identifier, 'THESIS', 0.78),
                    self._create_embedding(rg_242.dto.identifier, 'ENUNCIATION', 0.56),
                    self._create_embedding(rg_932.dto.identifier, 'THESIS', 1.0),
                    self._create_embedding(rg_932.dto.identifier, 'ENUNCIATION', 0.82),
                    self._create_embedding(rr_556.dto.identifier, 'THESIS', 0.88),
                    self._create_embedding(rr_556.dto.identifier, 'ENUNCIATION', 0.74),
                ]
            )
        )
        self.precedents_repository_mock.find_many_by_identifiers.return_value = (
            ListResponse(items=[rg_242, rg_932, rr_556])
        )

        # Act
        result = self.use_case.execute(
            analysis_id=analysis_id,
            dto=AnalysisPrecedentsSearchFiltersDto(limit=5),
        )

        # Assert
        assert result[0].precedent.identifier.number == 932
        assert result[1].precedent.identifier.number == 556
        assert result[2].precedent.identifier.number == 242
        assert result[0].similarity_rank == 1
        assert result[1].similarity_rank == 2
        assert result[2].similarity_rank == 3

    def test_should_prioritize_objective_liability_when_risk_axis_is_explicit(
        self,
    ) -> None:
        # Arrange
        analysis_id = Id.create().value
        competence_precedent = self._create_precedent(
            number=242,
            enunciation='Competencia para processar e julgar acoes indenizatorias propostas por sucessores do trabalhador falecido.',
            thesis='Compete a Justica do Trabalho processar e julgar as acoes propostas por sucessores.',
        )
        objective_precedent = self._create_precedent(
            number=932,
            enunciation='Possibilidade de responsabilizacao objetiva do empregador por danos decorrentes de acidentes de trabalho.',
            thesis='E constitucional a responsabilizacao objetiva do empregador quando a atividade normalmente desenvolvida apresentar exposicao habitual a risco especial.',
        )

        self.petition_summaries_repository_mock.find_by_analysis_id.return_value = PetitionSummary.create(
            PetitionSummaryDto(
                case_summary='Acao de indenizacao por acidente de trabalho em atividade de risco, com pedido de reparacao civil.',
                legal_issue='Responsabilidade objetiva do empregador por atividade de risco e exposicao habitual a risco especial.',
                central_question='A atividade de risco normalmente desenvolvida pelo trabalhador autoriza a responsabilizacao objetiva do empregador nos termos do art. 927, paragrafo unico, do Codigo Civil?',
                relevant_laws=['CC, artigo 927, paragrafo unico'],
                key_facts=[
                    'A atividade expunha o trabalhador a risco especial de forma habitual.',
                ],
                search_terms=['responsabilidade objetiva atividade de risco'],
            )
        )
        self.petition_summary_embeddings_provider_mock.generate.return_value = []
        self.precedents_embeddings_repository_mock.find_many.return_value = (
            ListResponse(
                items=[
                    self._create_embedding(
                        competence_precedent.dto.identifier, 'THESIS', 0.86
                    ),
                    self._create_embedding(
                        competence_precedent.dto.identifier, 'ENUNCIATION', 0.72
                    ),
                    self._create_embedding(
                        objective_precedent.dto.identifier, 'THESIS', 0.9
                    ),
                    self._create_embedding(
                        objective_precedent.dto.identifier, 'ENUNCIATION', 0.76
                    ),
                ]
            )
        )
        self.precedents_repository_mock.find_many_by_identifiers.return_value = (
            ListResponse(items=[competence_precedent, objective_precedent])
        )

        # Act
        result = self.use_case.execute(
            analysis_id=analysis_id,
            dto=AnalysisPrecedentsSearchFiltersDto(limit=5),
        )

        # Assert
        assert result[0].precedent.identifier.number == 932
        assert result[1].precedent.identifier.number == 242

    @staticmethod
    def _create_precedent(
        number: int,
        enunciation: str,
        thesis: str,
        court: str = 'STF',
        kind: str = 'RG',
    ) -> Precedent:
        return Precedent.create(
            PrecedentDto(
                id=Id.create().value,
                identifier=PrecedentIdentifierDto(
                    court=court,
                    kind=kind,
                    number=number,
                ),
                status='Transitado em julgado',
                enunciation=enunciation,
                thesis=thesis,
                last_updated_in_pangea_at='2026-04-19T00:00:00+00:00',
            )
        )

    @staticmethod
    def _create_embedding(
        identifier: PrecedentIdentifierDto,
        field: str,
        score: float,
    ) -> PrecedentEmbedding:
        return PrecedentEmbedding.create(
            PrecedentEmbeddingDto(
                score=score,
                vector=[],
                field=field,
                identifier=identifier,
                chunk='chunk',
            )
        )

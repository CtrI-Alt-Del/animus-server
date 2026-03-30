import re
import unicodedata
from collections.abc import Iterable
from typing import TypedDict

from animus.core.intake.domain.errors import PetitionSummaryUnavailableError
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.analysis_precedents_search_filters import (
    AnalysisPrecedentsSearchFilters,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.domain.structures.precedent_embedding_field import (
    PrecedentEmbeddingFieldValue,
)
from animus.core.intake.domain.structures.precedent_identifier import (
    PrecedentIdentifier,
)
from animus.core.intake.interfaces import (
    PetitionSummariesRepository,
    PetitionSummaryEmbeddingsProvider,
    PrecedentsEmbeddingsRepository,
    PrecedentsRepository,
)
from animus.core.shared.domain.structures import Id, Integer, Text


class PetitionSummaryTest:
    """
    Fixture estática baseada em petição real.
    Ação declaratória de direito c/c repetição de indébito tributário.
    Direito de sociedade uniprofissional (limitada) à tributação fixa do ISS
    por profissional habilitado, nos termos do art. 9º, §§ 1º e 3º, do
    Decreto-Lei nº 406/1968 — TR 1323 do STJ.
    """

    case_summary: Text = Text.create(
        "Ação declaratória de direito cumulada com repetição de indébito tributário "
        "ajuizada por sociedade uniprofissional de natureza limitada em face do Município, "
        "pleiteando o reconhecimento do direito à tributação fixa do ISS por profissional "
        "habilitado, nos termos do art. 9º, §§ 1º e 3º, do Decreto-Lei nº 406/1968, e a "
        "restituição dos valores recolhidos indevidamente nos últimos cinco anos sob "
        "alíquota variável sobre receita bruta. O Município recusa a aplicação do regime "
        "diferenciado sob o fundamento de que a forma societária limitada afastaria o "
        "conceito de sociedade de profissionais, o que contraria a jurisprudência dos "
        "tribunais superiores consolidada no Tema Repetitivo 1323 do STJ."
    )

    legal_issue: Text = Text.create(
        "Direito de sociedade uniprofissional constituída sob a forma limitada à "
        "tributação fixa do ISS por profissional habilitado, nos termos do art. 9º, "
        "§§ 1º e 3º, do Decreto-Lei nº 406/1968, independentemente da adoção da forma "
        "societária limitada, e cabimento da repetição de indébito dos valores "
        "recolhidos a maior sob alíquota variável sobre receita bruta."
    )

    central_question: Text = Text.create(
        "A adoção da forma societária limitada afasta o direito de sociedade "
        "uniprofissional à tributação fixa do ISS prevista no art. 9º, §§ 1º e 3º, "
        "do Decreto-Lei nº 406/1968, quando a sociedade é composta exclusivamente por "
        "sócios habilitados que prestam os serviços diretamente?"
    )

    relevant_laws: list[Text] = [
        Text.create("Art. 9º, §§ 1º e 3º, do Decreto-Lei nº 406/1968"),
        Text.create("Art. 165, inciso I, do Código Tributário Nacional (CTN)"),
        Text.create("Art. 319 do Código de Processo Civil"),
        Text.create("Art. 85 do Código de Processo Civil (honorários advocatícios)"),
        Text.create("Tema Repetitivo 1323 do Superior Tribunal de Justiça (STJ)"),
    ]

    key_facts: list[Text] = [
        Text.create(
            "A autora é sociedade uniprofissional constituída sob a forma limitada, "
            "cujo objeto social é a prestação de serviços técnicos profissionais "
            "exclusivamente por seus sócios, todos habilitados nos respectivos "
            "conselhos de fiscalização profissional."
        ),
        Text.create(
            "O Município recusa a aplicação do regime de tributação fixa do ISS "
            "previsto no Decreto-Lei nº 406/1968, exigindo ISS com base na alíquota "
            "variável sobre receita bruta, sob o fundamento de que a forma societária "
            "limitada afastaria o conceito de sociedade de profissionais."
        ),
        Text.create(
            "A forma societária limitada não afasta, por si só, o direito à tributação "
            "fixa do ISS, desde que a sociedade tenha por objeto apenas a prestação de "
            "serviços técnicos especializados, seja composta exclusivamente por sócios "
            "habilitados e não conte com sócios capitalistas."
        ),
        Text.create(
            "Nos últimos cinco anos a autora recolheu ISS sob alíquota variável sobre "
            "receita bruta quando deveria tê-lo feito por valor fixo mensal, gerando "
            "indébito tributário passível de restituição com correção pela SELIC."
        ),
        Text.create(
            "A restrição municipal baseada exclusivamente na natureza jurídica da "
            "sociedade não encontra respaldo no Decreto-Lei nº 406/1968 e contraria "
            "o entendimento firmado pelo STJ no Tema Repetitivo 1323."
        ),
    ]

    search_terms: list[Text] = [
        Text.create("sociedade uniprofissional ISS tributação fixa"),
        Text.create("Decreto-Lei 406/1968 art. 9º ISS fixo"),
        Text.create("ISS sociedade simples limitada profissionais"),
        Text.create("Tema Repetitivo 1323 STJ ISS sociedade uniprofissional"),
        Text.create("tributação fixa ISS por profissional habilitado"),
        Text.create("forma societária limitada ISS fixo sócios habilitados"),
        Text.create("repetição de indébito tributário ISS alíquota variável"),
        Text.create("ISS receita bruta versus tributação fixa mensal"),
        Text.create("sociedade de profissionais ISS município restrição"),
        Text.create("indébito tributário ISS restituição cinco anos SELIC"),
    ]


class _IdentifierScore(TypedDict):
    thesis_max: float
    enunciation_max: float
    thesis_hits: int
    enunciation_hits: int
    total_hits: int


class _PetitionLexicalProfile(TypedDict):
    issue_anchors: set[str]
    law_anchors: set[str]
    context_anchors: set[str]
    accessory_terms: set[str]
    core_terms: set[str]
    domain_anchors: set[str]


class SearchAnalysisPrecedentsUseCase:
    _GENERIC_NEGATIVE_TERMS = {
        "fgts",
        "urv",
        "imposto de renda",
        "contribuicao previdenciaria",
        "prestacao previdenciaria",
        "insalubridade",
        "periculosidade",
        "ajuda de custo",
        "rescisao indireta",
    }

    _ACCESSORY_MARKERS = {
        "juros",
        "correcao monetaria",
        "correção monetária",
        "honorarios",
        "honorários",
        "custas",
        "prescricao",
        "prescrição",
        "ipca-e",
        "parcelas vencidas",
        "parcelas vincendas",
        "quinquenio",
        "quinquênio",
        "sumula 85",
        "súmula 85",
        "11.960/09",
    }

    _SPECIALIZATION_TERMS = {
        "ferias",
        "férias",
        "aposentadoria",
        "aposentado",
        "aposentado antes",
        "licenca-premio",
        "licença-prêmio",
        "licença premio",
        "conversao em pecunia",
        "conversão em pecúnia",
        "renuncia",
        "renúncia",
        "piso salarial",
        "rsc",
        "retribuicao por titulacao",
        "retribuição por titulação",
        "ferrovia",
    }

    def __init__(
        self,
        petition_summaries_repository: PetitionSummariesRepository,
        petition_summary_embeddings_provider: PetitionSummaryEmbeddingsProvider,
        precedents_embeddings_repository: PrecedentsEmbeddingsRepository,
        precedents_repository: PrecedentsRepository,
    ) -> None:
        self._petition_summaries_repository = petition_summaries_repository
        self._petition_summary_embeddings_provider = (
            petition_summary_embeddings_provider
        )
        self._precedents_embeddings_repository = precedents_embeddings_repository
        self._precedents_repository = precedents_repository

    def execute(
        self,
        analysis_id: str,
        dto: AnalysisPrecedentsSearchFiltersDto,
    ) -> list[AnalysisPrecedentDto]:
        analysis_id_entity = Id.create(analysis_id)
        filters = AnalysisPrecedentsSearchFilters.create(dto)

        petition_summary = self._petition_summaries_repository.find_by_analysis_id(
            analysis_id=analysis_id_entity,
        )
        if petition_summary is None:
            raise PetitionSummaryUnavailableError

        petition_summary_embeddings = (
            self._petition_summary_embeddings_provider.generate(
                petition_summary,
            )
        )

        lexical_profile = self._extract_lexical_profile(petition_summary)

        candidate_limit = Integer.create(filters.limit.value * 10)
        precedent_embeddings = self._precedents_embeddings_repository.find_many(
            petition_summary_embeddings=petition_summary_embeddings,
            filters=filters,
            limit=candidate_limit,
        )

        if not precedent_embeddings.items:
            return []

        scored_identifiers = self._score_identifiers(precedent_embeddings.items)
        precedents = self._precedents_repository.find_many_by_identifiers(
            identifiers=list(scored_identifiers.keys()),
        )
        precedents_by_identifier = {
            self._get_identifier_key(precedent.identifier): precedent
            for precedent in precedents.items
        }

        analysis_precedents: list[AnalysisPrecedent] = []
        for identifier, scores in scored_identifiers.items():
            precedent = precedents_by_identifier.get(
                self._get_identifier_key(identifier)
            )
            if precedent is None:
                continue

            lexical_adjustment = self._calculate_lexical_adjustment(
                enunciation=precedent.enunciation.value,
                thesis=precedent.thesis.value,
                lexical_profile=lexical_profile,
            )

            applicability_percentage = self._calculate_applicability_percentage(
                thesis_score=scores["thesis_max"],
                enunciation_score=scores["enunciation_max"],
                total_hits=scores["total_hits"],
                lexical_adjustment=lexical_adjustment,
            )

            analysis_precedents.append(
                AnalysisPrecedent.create(
                    AnalysisPrecedentDto(
                        analysis_id=analysis_id_entity.value,
                        precedent=precedent.dto,
                        applicability_percentage=applicability_percentage,
                        synthesis=None,
                        is_chosen=False,
                    )
                )
            )

        sorted_analysis_precedents = sorted(
            analysis_precedents,
            key=lambda item: (
                item.applicability_percentage.value
                if item.applicability_percentage is not None
                else 0.0
            ),
            reverse=True,
        )

        return [item.dto for item in sorted_analysis_precedents[: filters.limit.value]]

    def _score_identifiers(
        self,
        precedent_embeddings: Iterable[PrecedentEmbedding],
    ) -> dict[PrecedentIdentifier, _IdentifierScore]:
        scores_by_identifier: dict[PrecedentIdentifier, _IdentifierScore] = {}

        for precedent_embedding in precedent_embeddings:
            if precedent_embedding.identifier not in scores_by_identifier:
                scores_by_identifier[precedent_embedding.identifier] = {
                    "thesis_max": 0.0,
                    "enunciation_max": 0.0,
                    "thesis_hits": 0,
                    "enunciation_hits": 0,
                    "total_hits": 0,
                }

            score_data = scores_by_identifier[precedent_embedding.identifier]
            score_data["total_hits"] += 1

            field_name = precedent_embedding.field.value
            if field_name is PrecedentEmbeddingFieldValue.THESIS:
                score_data["thesis_max"] = max(
                    score_data["thesis_max"],
                    precedent_embedding.score.value,
                )
                score_data["thesis_hits"] += 1
                continue

            if field_name is PrecedentEmbeddingFieldValue.ENUNCIATION:
                score_data["enunciation_max"] = max(
                    score_data["enunciation_max"],
                    precedent_embedding.score.value,
                )
                score_data["enunciation_hits"] += 1

        return scores_by_identifier

    def _calculate_applicability_percentage(
        self,
        thesis_score: float,
        enunciation_score: float,
        total_hits: int,
        lexical_adjustment: float,
    ) -> float:
        base_score = (thesis_score * 0.58) + (enunciation_score * 0.42)
        coverage_bonus = min(total_hits * 0.02, 0.08)

        final_score = base_score + coverage_bonus + lexical_adjustment
        normalized_percentage = round(final_score * 100, 2)

        return min(max(normalized_percentage, 0.0), 95.0)

    def _calculate_lexical_adjustment(
        self,
        enunciation: str,
        thesis: str,
        lexical_profile: _PetitionLexicalProfile,
    ) -> float:
        combined_text = self._normalize_text(f"{enunciation} {thesis}")

        issue_hits = sum(
            1 for term in lexical_profile["issue_anchors"] if term in combined_text
        )
        law_hits = sum(
            1 for term in lexical_profile["law_anchors"] if term in combined_text
        )
        context_hits = sum(
            1 for term in lexical_profile["context_anchors"] if term in combined_text
        )
        accessory_hits = sum(
            1 for term in lexical_profile["accessory_terms"] if term in combined_text
        )
        generic_negative_hits = sum(
            1 for term in self._GENERIC_NEGATIVE_TERMS if term in combined_text
        )

        # Penalidade forte: sem nenhum sinal da controvérsia central
        if issue_hits == 0 and law_hits == 0:
            return -0.25

        issue_bonus = min(issue_hits * 0.08, 0.24)
        law_bonus = min(law_hits * 0.04, 0.12)
        context_bonus = min(context_hits * 0.01, 0.03)

        specialization_penalty = 0.0
        if issue_hits == 0 and law_hits > 0:
            specialization_penalty += 0.07

        accessory_penalty = 0.0
        if issue_hits == 0 and accessory_hits > 0:
            accessory_penalty += min(accessory_hits * 0.025, 0.08)

        specialization_terms_penalty = self._calculate_specialization_terms_penalty(
            combined_text=combined_text,
            core_terms=lexical_profile["core_terms"],
        )

        negative_penalty = min(generic_negative_hits * 0.04, 0.16)

        # Penalidade de domínio: precedente sem nenhum termo específico do
        # caso (lei, decreto, instituto jurídico central) recebe penalidade
        # adicional, mesmo que compartilhe termos processuais genéricos.
        domain_hits = sum(
            1 for term in lexical_profile["domain_anchors"] if term in combined_text
        )
        domain_penalty = 0.0 if domain_hits > 0 else 0.15

        return (
            issue_bonus
            + law_bonus
            + context_bonus
            - specialization_penalty
            - accessory_penalty
            - specialization_terms_penalty
            - negative_penalty
            - domain_penalty
        )

    def _calculate_specialization_terms_penalty(
        self,
        combined_text: str,
        core_terms: set[str],
    ) -> float:
        penalty = 0.0

        for term in self._SPECIALIZATION_TERMS:
            normalized_term = self._normalize_text(term)
            if normalized_term in combined_text and normalized_term not in core_terms:
                penalty += 0.03

        return min(penalty, 0.12)

    def _extract_lexical_profile(
        self,
        petition_summary: PetitionSummary,
    ) -> _PetitionLexicalProfile:
        issue_anchors: set[str] = set()
        law_anchors: set[str] = set()
        context_anchors: set[str] = set()
        accessory_terms: set[str] = set()

        # 1) issue_anchors: controvérsia central
        issue_anchors.update(
            self._extract_phrases(
                self._normalize_text(petition_summary.legal_issue.value),
                max_phrases=5,
            )
        )
        issue_anchors.update(
            self._extract_phrases(
                self._normalize_text(petition_summary.central_question.value),
                max_phrases=5,
            )
        )

        # 2) law_anchors: base legal e termos nucleares
        for item in petition_summary.relevant_laws:
            normalized = self._normalize_text(item.value)
            if self._is_accessory_text(normalized):
                accessory_terms.add(normalized)
                continue

            law_anchors.add(normalized)
            law_anchors.update(re.findall(r"\d{1,5}\.?\d{0,3}/\d{2,4}", normalized))

        for item in petition_summary.search_terms:
            normalized = self._normalize_text(item.value)
            if self._is_accessory_text(normalized):
                accessory_terms.add(normalized)
            else:
                law_anchors.add(normalized)

        # 3) context_anchors: fatos e resumo geral
        for item in petition_summary.key_facts:
            normalized = self._normalize_text(item.value)
            if self._is_accessory_text(normalized):
                accessory_terms.add(normalized)
            else:
                context_anchors.add(normalized)

        context_anchors.update(
            self._extract_phrases(
                self._normalize_text(petition_summary.case_summary.value),
                max_phrases=4,
            )
        )

        issue_anchors = {t for t in issue_anchors if len(t) >= 4}
        law_anchors = {t for t in law_anchors if len(t) >= 4 and t not in issue_anchors}
        context_anchors = {
            t
            for t in context_anchors
            if len(t) >= 4 and t not in issue_anchors and t not in law_anchors
        }
        accessory_terms = {t for t in accessory_terms if len(t) >= 4}

        core_terms = issue_anchors | law_anchors

        # 4) domain_anchors: termos específicos do domínio do caso —
        # números de lei/decreto e termos não-genéricos dos search_terms.
        # Precedentes sem nenhum desses termos recebem penalidade adicional.
        domain_anchors: set[str] = set()

        # Números de lei e decreto são os identificadores mais específicos
        for item in petition_summary.relevant_laws:
            normalized = self._normalize_text(item.value)
            if self._is_accessory_text(normalized):
                continue
            domain_anchors.update(re.findall(r"\d{1,5}\.?\d{0,3}/\d{2,4}", normalized))

        # Search terms que contêm números (referências legais específicas)
        # ou frases distintivas do domínio (>= 3 palavras)
        for item in petition_summary.search_terms:
            normalized = self._normalize_text(item.value)
            if self._is_accessory_text(normalized):
                continue
            has_number = bool(re.search(r"\d", normalized))
            has_multiple_words = len(normalized.split()) >= 3
            if has_number or has_multiple_words:
                domain_anchors.add(normalized)
                domain_anchors.update(
                    re.findall(r"\d{1,5}\.?\d{0,3}/\d{2,4}", normalized)
                )

        domain_anchors = {t for t in domain_anchors if len(t) >= 4}

        return {
            "issue_anchors": issue_anchors,
            "law_anchors": law_anchors,
            "context_anchors": context_anchors,
            "accessory_terms": accessory_terms,
            "core_terms": core_terms,
            "domain_anchors": domain_anchors,
        }

    def _extract_phrases(self, text: str, max_phrases: int) -> set[str]:
        parts = re.split(r"[.;:,\n\-–\(\)]+", text)
        phrases = [part.strip() for part in parts if len(part.strip()) >= 8]
        phrases = sorted(set(phrases), key=len, reverse=True)
        return set(phrases[:max_phrases])

    def _is_accessory_text(self, text: str) -> bool:
        normalized = self._normalize_text(text)
        return any(marker in normalized for marker in self._ACCESSORY_MARKERS)

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text.lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _get_identifier_key(
        self,
        identifier: PrecedentIdentifier,
    ) -> tuple[str, str, int]:
        return (
            identifier.court.dto,
            identifier.kind.dto,
            identifier.number.value,
        )

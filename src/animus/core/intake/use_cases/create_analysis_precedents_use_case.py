from typing import cast

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.structures import AnalysisPrecedent
from animus.core.intake.domain.structures.dtos.analysies_precedent_legal_features_dto import (
    AnalysiesPrecedentLegalFeaturesDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedent_dto import (
    AnalysisPrecedentDto,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.interfaces import (
    AnalysisPrecedentsRepository,
    AnalisysesRepository,
)
from animus.core.shared.domain.errors import AppError
from animus.core.shared.domain.structures import Id


class CreateAnalysisPrecedentsUseCase:
    def __init__(
        self,
        analysis_precedents_repository: AnalysisPrecedentsRepository,
        analisyses_repository: AnalisysesRepository,
    ) -> None:
        self._analysis_precedents_repository = analysis_precedents_repository
        self._analisyses_repository = analisyses_repository

    def execute(
        self,
        analysis_id: str,
        filters_dto: AnalysisPrecedentsSearchFiltersDto,
        analysis_precedents: list[AnalysisPrecedentDto],
        synthesis_output: object | None = None,
    ) -> list[AnalysisPrecedentDto]:
        analysis_id_entity = Id.create(analysis_id)

        if synthesis_output is not None:
            merged_analysis_precedents = self._merge_syntheses(
                filters_dto,
                analysis_precedents,
                synthesis_output,
            )
        else:
            merged_analysis_precedents = [
                AnalysisPrecedent.create(analysis_precedent)
                for analysis_precedent in analysis_precedents
            ]

        self._analysis_precedents_repository.remove_many_by_analysis_id(
            analysis_id_entity
        )
        self._analysis_precedents_repository.add_many_by_analysis_id(
            analysis_id=analysis_id_entity,
            analysis_precedents=merged_analysis_precedents,
        )

        analysis = self._analisyses_repository.find_by_id(analysis_id_entity)
        if analysis is None:
            raise AnalysisNotFoundError

        analysis.set_precedents_search_filters(filters_dto)
        analysis.set_status(AnalysisStatusValue.WAITING_PRECEDENT_CHOISE.value)
        self._analisyses_repository.replace(analysis)

        return [
            analysis_precedent.dto for analysis_precedent in merged_analysis_precedents
        ]

    @staticmethod
    def _apply_label_consistency(dto: AnalysisPrecedentDto) -> AnalysisPrecedentDto:
        f = dto.legal_features
        if f is None or dto.applicability_level is None:
            return dto

        corrected_level = dto.applicability_level

        no_central_match = f.central_issue_match == 0
        no_structural_match = f.structural_issue_match == 0
        no_match = no_central_match and no_structural_match

        # R1: nenhum match + contexto incompatível → 0
        if no_match and f.context_compatibility == 0:
            corrected_level = 0

        # R2: contexto incompatível sem match forte → no máximo 1
        elif (
            (
                f.context_compatibility == 0
                and f.central_issue_match < 2
                and f.structural_issue_match < 2
            )
            or no_match
            or (f.is_accessory_topic == 1 and f.central_issue_match < 2)
        ):
            corrected_level = min(corrected_level, 1)

        if corrected_level == dto.applicability_level:
            return dto

        return AnalysisPrecedentDto(
            analysis_id=dto.analysis_id,
            precedent=dto.precedent,
            is_chosen=dto.is_chosen,
            similarity_score=dto.similarity_score,
            thesis_similarity_score=dto.thesis_similarity_score,
            enunciation_similarity_score=dto.enunciation_similarity_score,
            total_search_hits=dto.total_search_hits,
            similarity_rank=dto.similarity_rank,
            final_rank=dto.final_rank,
            applicability_level=corrected_level,
            legal_features=dto.legal_features,
            synthesis=dto.synthesis,
        )

    @staticmethod
    def _legal_rank_score(dto: AnalysisPrecedentDto) -> float:
        applicability_level = dto.applicability_level or 0
        similarity_score = dto.similarity_score or 0.0
        f = dto.legal_features

        if f is None:
            return (200 * applicability_level) + (0.05 * similarity_score)

        # Gap entre níveis = 200, máximo das features = ~100
        # Garante que label=2 sempre supera label=1, independente das features
        features_score = (
            +20 * f.central_issue_match  # 0, 20, 40
            + 15 * f.context_compatibility  # 0, 15, 30
            + 10 * f.structural_issue_match  # 0, 10, 20
            - 10 * f.is_lateral_topic  # 0, -10
            - 8 * f.is_accessory_topic  # 0, -8
        )
        # Máximo: 40+30+20 = 90 | Mínimo: -10-8 = -18 | Range: 108

        return 200 * applicability_level + features_score + 0.05 * similarity_score

    @classmethod
    def _rerank_key(cls, dto: AnalysisPrecedentDto) -> tuple[float, float]:
        return (
            -cls._legal_rank_score(dto),
            -(dto.similarity_score or 0.0),
        )

    def _merge_syntheses(
        self,
        filters_dto: AnalysisPrecedentsSearchFiltersDto,
        analysis_precedents: list[AnalysisPrecedentDto],
        synthesis_output: object,
    ) -> list[AnalysisPrecedent]:
        synthesis_items = self._coerce_synthesis_items(synthesis_output)

        synthesis_by_identifier: dict[
            tuple[str, str, int],
            tuple[str, int, AnalysiesPrecedentLegalFeaturesDto],
        ] = {}

        for item in synthesis_items:
            court = getattr(item, 'court', None)
            kind = getattr(item, 'kind', None)
            number = getattr(item, 'number', None)
            synthesis = getattr(item, 'synthesis', None)
            raw_applicability_level = getattr(item, 'applicability_level', None)
            legal_features = getattr(item, 'legal_features', None)

            if raw_applicability_level is None:
                applicability_level = 0
            else:
                applicability_level = raw_applicability_level

            if (
                not isinstance(court, str)
                or not isinstance(kind, str)
                or not isinstance(number, int)
                or not isinstance(synthesis, str)
                or not isinstance(applicability_level, int)
                or applicability_level not in (0, 1, 2)
                or legal_features is None
            ):
                msg = 'Invalid synthesis output type from analysis precedents workflow'
                raise AppError('Erro de execução do workflow', msg)

            central_issue_match = getattr(legal_features, 'central_issue_match', None)
            structural_issue_match = getattr(
                legal_features, 'structural_issue_match', None
            )
            context_compatibility = getattr(
                legal_features, 'context_compatibility', None
            )
            is_lateral_topic = getattr(legal_features, 'is_lateral_topic', None)
            is_accessory_topic = getattr(legal_features, 'is_accessory_topic', None)

            if (
                not isinstance(central_issue_match, int)
                or not isinstance(structural_issue_match, int)
                or not isinstance(context_compatibility, int)
                or not isinstance(is_lateral_topic, int)
                or not isinstance(is_accessory_topic, int)
            ):
                msg = 'Invalid synthesis output type from analysis precedents workflow'
                raise AppError('Erro de execução do workflow', msg)

            identifier_key = (court, kind, number)
            if identifier_key in synthesis_by_identifier:
                msg = 'Duplicate precedent identifier returned by synthesis workflow'
                raise AppError('Erro de execução do workflow', msg)

            synthesis_by_identifier[identifier_key] = (
                synthesis.strip(),
                applicability_level,
                AnalysiesPrecedentLegalFeaturesDto(
                    central_issue_match=central_issue_match,
                    structural_issue_match=structural_issue_match,
                    context_compatibility=context_compatibility,
                    is_lateral_topic=is_lateral_topic,
                    is_accessory_topic=is_accessory_topic,
                ),
            )

        raw_dtos: list[AnalysisPrecedentDto] = []

        for analysis_precedent in analysis_precedents:
            identifier = analysis_precedent.precedent.identifier
            identifier_key = (
                identifier.court,
                identifier.kind,
                identifier.number,
            )

            synthesis_result = synthesis_by_identifier.get(identifier_key)
            if synthesis_result is None:
                msg = 'Missing synthesis for at least one precedent identifier'
                raise AppError('Erro de execução do workflow', msg)

            synthesis, applicability_level, legal_features_dto = synthesis_result

            raw_dtos.append(
                AnalysisPrecedentDto(
                    analysis_id=analysis_precedent.analysis_id,
                    precedent=analysis_precedent.precedent,
                    is_chosen=analysis_precedent.is_chosen,
                    similarity_score=analysis_precedent.similarity_score,
                    thesis_similarity_score=analysis_precedent.thesis_similarity_score,
                    enunciation_similarity_score=(
                        analysis_precedent.enunciation_similarity_score
                    ),
                    total_search_hits=analysis_precedent.total_search_hits,
                    similarity_rank=analysis_precedent.similarity_rank,
                    final_rank=analysis_precedent.final_rank,
                    applicability_level=applicability_level,
                    legal_features=legal_features_dto,
                    synthesis=synthesis,
                )
            )

        consistent_dtos = [self._apply_label_consistency(dto) for dto in raw_dtos]

        reranked_dtos = sorted(
            consistent_dtos,
            key=self._rerank_key,
        )

        reranked_dtos = reranked_dtos[: filters_dto.limit]

        analysis_precedent_entities: list[AnalysisPrecedent] = []

        for rank, dto in enumerate(reranked_dtos, start=1):
            final_dto = AnalysisPrecedentDto(
                analysis_id=dto.analysis_id,
                precedent=dto.precedent,
                is_chosen=dto.is_chosen,
                similarity_score=dto.similarity_score,
                thesis_similarity_score=dto.thesis_similarity_score,
                enunciation_similarity_score=dto.enunciation_similarity_score,
                total_search_hits=dto.total_search_hits,
                similarity_rank=dto.similarity_rank,
                final_rank=rank,
                applicability_level=dto.applicability_level,
                legal_features=dto.legal_features,
                synthesis=dto.synthesis,
            )

            analysis_precedent_entities.append(AnalysisPrecedent.create(final_dto))

        return analysis_precedent_entities

    def _coerce_synthesis_items(self, synthesis_output: object) -> list[object]:
        output_items = getattr(synthesis_output, 'items', None)
        if not isinstance(output_items, list):
            msg = 'Invalid synthesis output type from analysis precedents workflow'
            raise AppError('Erro de execução do workflow', msg)

        return cast('list[object]', output_items)

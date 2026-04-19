from typing import cast

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.intake.domain.errors import AnalysisNotFoundError
from animus.core.intake.domain.structures import AnalysisPrecedent
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
        synthesis_output: object,
    ) -> None:
        merged_analysis_precedents = self._merge_syntheses(
            analysis_precedents,
            synthesis_output,
        )

        analysis_id_entity = Id.create(analysis_id)

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

    def _merge_syntheses(
        self,
        analysis_precedents: list[AnalysisPrecedentDto],
        synthesis_output: object,
    ) -> list[AnalysisPrecedent]:
        synthesis_items = self._coerce_synthesis_items(synthesis_output)

        syntheses_by_identifier: dict[tuple[str, str, int], str] = {}
        for item in synthesis_items:
            court = getattr(item, 'court', None)
            kind = getattr(item, 'kind', None)
            number = getattr(item, 'number', None)
            synthesis = getattr(item, 'synthesis', None)

            if (
                not isinstance(court, str)
                or not isinstance(kind, str)
                or not isinstance(number, int)
                or not isinstance(synthesis, str)
            ):
                msg = 'Invalid synthesis output type from analysis precedents workflow'
                raise AppError('Erro de execução do workflow', msg)

            identifier_key = (court, kind, number)
            if identifier_key in syntheses_by_identifier:
                msg = 'Duplicate precedent identifier returned by synthesis workflow'
                raise AppError('Erro de execução do workflow', msg)

            syntheses_by_identifier[identifier_key] = synthesis.strip()

        analysis_precedent_entities: list[AnalysisPrecedent] = []
        for analysis_precedent in analysis_precedents:
            identifier = analysis_precedent.precedent.identifier
            identifier_key = (
                identifier.court,
                identifier.kind,
                identifier.number,
            )
            synthesis = syntheses_by_identifier.get(identifier_key)
            if not synthesis:
                msg = 'Missing synthesis for at least one precedent identifier'
                raise AppError('Erro de execução do workflow', msg)

            analysis_precedent_entities.append(
                AnalysisPrecedent.create(
                    AnalysisPrecedentDto(
                        analysis_id=analysis_precedent.analysis_id,
                        precedent=analysis_precedent.precedent,
                        is_chosen=analysis_precedent.is_chosen,
                        similarity_percentage=analysis_precedent.similarity_percentage,
                        thesis_similarity_score=(
                            analysis_precedent.thesis_similarity_score
                        ),
                        enunciation_similarity_score=(
                            analysis_precedent.enunciation_similarity_score
                        ),
                        total_search_hits=analysis_precedent.total_search_hits,
                        similarity_rank=analysis_precedent.similarity_rank,
                        applicability_level=analysis_precedent.applicability_level,
                        synthesis=synthesis,
                    )
                )
            )

        return analysis_precedent_entities

    def _coerce_synthesis_items(self, synthesis_output: object) -> list[object]:
        output_items = getattr(synthesis_output, 'items', None)
        if not isinstance(output_items, list):
            msg = 'Invalid synthesis output type from analysis precedents workflow'
            raise AppError('Erro de execução do workflow', msg)

        return cast('list[object]', output_items)

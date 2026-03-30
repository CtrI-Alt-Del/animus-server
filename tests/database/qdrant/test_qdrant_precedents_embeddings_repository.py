import pytest
from qdrant_client import QdrantClient

from animus.core.intake.domain.structures import (
    AnalysisPrecedentsSearchFilters,
    PetitionSummaryEmbedding,
    PrecedentEmbedding,
)
from animus.core.intake.domain.structures.dtos.analysis_precedents_search_filters_dto import (
    AnalysisPrecedentsSearchFiltersDto,
)
from animus.core.intake.domain.structures.dtos.precedent_embedding_dto import (
    PrecedentEmbeddingDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.shared.domain.structures import Decimal, Integer, Text
from animus.database.qdrant.qdrant_precedents_embeddings_repository import (
    QdrantPrecedentsEmbeddingsRepository,
)


def _vector(size: int, value: float) -> list[float]:
    return [value] * size


class TestQdrantPrecedentsEmbeddingsRepository:
    @pytest.mark.usefixtures('reset_qdrant')
    def test_should_add_and_find_precedent_embeddings_using_qdrant_container(
        self,
        qdrant_client: QdrantClient,
    ) -> None:
        repository = QdrantPrecedentsEmbeddingsRepository()
        collection_name = 'dev_precedents'

        repository.add_many(
            precedents_embeddings=[
                PrecedentEmbedding.create(
                    PrecedentEmbeddingDto(
                        score=1.0,
                        vector=_vector(3072, 0.1),
                        field='ENUNCIATION',
                        identifier=PrecedentIdentifierDto(
                            court='STF',
                            kind='RG',
                            number=101,
                        ),
                        chunk='Trecho do enunciado',
                    )
                ),
                PrecedentEmbedding.create(
                    PrecedentEmbeddingDto(
                        score=1.0,
                        vector=_vector(3072, 0.1),
                        field='THESIS',
                        identifier=PrecedentIdentifierDto(
                            court='STF',
                            kind='RG',
                            number=101,
                        ),
                        chunk='Trecho da tese',
                    )
                ),
            ]
        )

        assert qdrant_client.collection_exists(collection_name=collection_name)

        result = repository.find_many(
            petition_summary_embeddings=[
                PetitionSummaryEmbedding.create(
                    vector=[Decimal.create(value) for value in _vector(3072, 0.1)],
                    chunk=Text.create('Resumo da peticao'),
                )
            ],
            filters=AnalysisPrecedentsSearchFilters.create(
                AnalysisPrecedentsSearchFiltersDto(
                    courts=['STF'],
                    precedent_kinds=['RG'],
                    limit=5,
                )
            ),
            limit=Integer.create(5),
        )

        identifiers = [item.identifier.dto for item in result.items]
        fields = [item.field.dto for item in result.items]
        chunks = [item.chunk.value for item in result.items]

        assert len(result.items) == 2
        assert identifiers == [
            PrecedentIdentifierDto(court='STF', kind='RG', number=101),
            PrecedentIdentifierDto(court='STF', kind='RG', number=101),
        ]
        assert fields == ['ENUNCIATION', 'THESIS']
        assert chunks == ['Trecho do enunciado', 'Trecho da tese']

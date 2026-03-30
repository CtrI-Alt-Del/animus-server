from typing import Any, TypedDict, cast

from sentence_transformers import SentenceTransformer

from animus.core.intake.domain.entities.precedent import Precedent
from animus.core.intake.domain.structures.dtos.precedent_embedding_dto import (
    PrecedentEmbeddingDto,
)
from animus.core.intake.domain.structures.dtos.precedent_identifier_dto import (
    PrecedentIdentifierDto,
)
from animus.core.intake.domain.structures.precedent_embedding import PrecedentEmbedding
from animus.core.intake.interfaces.precedent_embeddings_provider import (
    PrecedentEmbeddingsProvider,
)


class _EmbeddingMetadata(TypedDict):
    precedent: Precedent
    field: str
    chunk: str


class BertimbauPrecedentEmbeddingsProvider(PrecedentEmbeddingsProvider):
    _BATCH_SIZE = 64

    def __init__(self) -> None:
        self._model: Any = SentenceTransformer("rufimelo/Legal-BERTimbau-sts-large")

    def generate(self, precedents: list[Precedent]) -> list[PrecedentEmbedding]:
        if not precedents:
            return []

        texts_to_embed: list[str] = []
        metadata_tracking: list[_EmbeddingMetadata] = []

        for precedent in precedents:
            if precedent.enunciation.value:
                texts_to_embed.append(precedent.enunciation.value)
                metadata_tracking.append(
                    {
                        "precedent": precedent,
                        "field": "ENUNCIATION",
                        "chunk": precedent.enunciation.value,
                    }
                )
            if precedent.thesis.value:
                texts_to_embed.append(precedent.thesis.value)
                metadata_tracking.append(
                    {
                        "precedent": precedent,
                        "field": "THESIS",
                        "chunk": precedent.thesis.value,
                    }
                )

        if not texts_to_embed:
            return []

        raw_vectors = self._model.encode(
            texts_to_embed,
            batch_size=BertimbauPrecedentEmbeddingsProvider._BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        vectors = cast("list[list[float]]", raw_vectors.tolist())

        results: list[PrecedentEmbedding] = []
        for metadata, vector in zip(metadata_tracking, vectors):  # noqa: B905
            precedent = metadata["precedent"]
            identifier = precedent.identifier
            results.append(
                PrecedentEmbedding.create(
                    PrecedentEmbeddingDto(
                        score=1.0,
                        vector=vector,
                        field=metadata["field"],
                        identifier=PrecedentIdentifierDto(
                            court=identifier.court.dto,
                            kind=identifier.kind.dto,
                            number=identifier.number.value,
                        ),
                        chunk=metadata["chunk"],
                    )
                )
            )

        return results

import time
from typing import Any

from openai import OpenAI

from animus.constants.env import Env
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


class OpenAIPrecedentEmbeddingsProvider(PrecedentEmbeddingsProvider):
    _BATCH_SIZE = 10
    _BATCH_DELAY = 6.0

    def __init__(self) -> None:
        self._client = OpenAI(api_key=Env.OPENAI_API_KEY)
        self._model = "text-embedding-3-large"

    def generate(self, precedents: list[Precedent]) -> list[PrecedentEmbedding]:
        if not precedents:
            return []

        texts_to_embed: list[str] = []
        metadata_tracking: list[dict[str, Any]] = []

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

        vectors: list[list[float]] = []
        for i in range(
            0, len(texts_to_embed), OpenAIPrecedentEmbeddingsProvider._BATCH_SIZE
        ):
            batch = texts_to_embed[
                i : i + OpenAIPrecedentEmbeddingsProvider._BATCH_SIZE
            ]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            vectors.extend([item.embedding for item in response.data])
            if i + OpenAIPrecedentEmbeddingsProvider._BATCH_SIZE < len(texts_to_embed):
                time.sleep(OpenAIPrecedentEmbeddingsProvider._BATCH_DELAY)

        results: list[PrecedentEmbedding] = []
        for metadata, vector in zip(metadata_tracking, vectors):  # noqa: B905
            prec: Precedent = metadata["precedent"]
            results.append(
                PrecedentEmbedding.create(
                    PrecedentEmbeddingDto(
                        score=1.0,
                        vector=vector,
                        field=metadata["field"],
                        identifier=PrecedentIdentifierDto(
                            court=prec.identifier.court.dto,
                            kind=prec.identifier.kind.dto,
                            number=prec.identifier.number.value,
                        ),
                        chunk=metadata["chunk"],
                    )
                )
            )

        return results

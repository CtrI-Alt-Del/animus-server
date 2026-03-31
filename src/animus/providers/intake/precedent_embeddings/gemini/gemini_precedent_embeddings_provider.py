import time
from typing import Any, cast

import google.genai as genai
from google.genai.types import ContentEmbedding  # noqa: TC002

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


class GeminiPrecedentEmbeddingsProvider(PrecedentEmbeddingsProvider):
    _BATCH_SIZE = 10
    _BATCH_DELAY = 6.0

    def __init__(self) -> None:
        self._client = genai.Client(api_key=Env.GEMINI_API_KEY)
        self._model = 'gemini-embedding-1.0'

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
                        'precedent': precedent,
                        'field': 'ENUNCIATION',
                        'chunk': precedent.enunciation.value,
                    }
                )
            if precedent.thesis.value:
                texts_to_embed.append(precedent.thesis.value)
                metadata_tracking.append(
                    {
                        'precedent': precedent,
                        'field': 'THESIS',
                        'chunk': precedent.thesis.value,
                    }
                )

        if not texts_to_embed:
            return []

        embeddings: list[ContentEmbedding] = []
        for i in range(
            0, len(texts_to_embed), GeminiPrecedentEmbeddingsProvider._BATCH_SIZE
        ):
            batch = texts_to_embed[
                i : i + GeminiPrecedentEmbeddingsProvider._BATCH_SIZE
            ]
            response = self._client.models.embed_content(  # type:ignore
                model=self._model,
                contents=cast('Any', batch),
            )
            embeddings.extend(response.embeddings)  # type:ignore
            if i + GeminiPrecedentEmbeddingsProvider._BATCH_SIZE < len(texts_to_embed):
                time.sleep(GeminiPrecedentEmbeddingsProvider._BATCH_DELAY)

        results: list[PrecedentEmbedding] = []
        for metadata, vector in zip(metadata_tracking, embeddings):  # noqa: B905
            prec: Precedent = metadata['precedent']
            results.append(
                PrecedentEmbedding.create(
                    PrecedentEmbeddingDto(
                        score=1.0,
                        vector=[float(v) for v in vector.values],  # type:ignore
                        field=metadata['field'],
                        identifier=PrecedentIdentifierDto(
                            court=prec.identifier.court.dto,
                            kind=prec.identifier.kind.dto,
                            number=prec.identifier.number.value,
                        ),
                        chunk=metadata['chunk'],
                    )
                )
            )

        return results

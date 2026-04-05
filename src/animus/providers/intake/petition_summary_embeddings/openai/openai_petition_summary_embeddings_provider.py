import time

from openai import OpenAI

from animus.constants.env import Env
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.domain.structures.petition_summary_embedding import (
    PetitionSummaryEmbedding,
)
from animus.core.intake.interfaces.petition_embeddings_provider import (
    PetitionSummaryEmbeddingsProvider,
)
from animus.core.shared.domain.structures import Decimal, Text


class OpenAIPetitionSummaryEmbeddingsProvider(PetitionSummaryEmbeddingsProvider):
    _BATCH_SIZE = 10
    _BATCH_DELAY = 6.0

    _ACCESSORY_MARKERS = (
        'súmula 85',
        'sumula 85',
        '11.960',
        'ipca-e',
        'juros',
        'correção monetária',
        'correcao monetaria',
        'prescrição',
        'prescricao',
        'quinquênio',
        'quinquenio',
        'parcelas vencidas',
        'parcelas vincendas',
        'honorários',
        'honorarios',
        'custas',
    )

    def __init__(self) -> None:
        self._client = OpenAI(api_key=Env.OPENAI_API_KEY)
        self._model = 'text-embedding-3-large'

    def generate(
        self,
        petition_summary: PetitionSummary,
    ) -> list[PetitionSummaryEmbedding]:
        texts_to_embed: list[str] = []

        texts_to_embed.append(petition_summary.case_summary.value)
        texts_to_embed.append(petition_summary.legal_issue.value)
        texts_to_embed.append(petition_summary.central_question.value)

        core_laws = [
            item.value
            for item in petition_summary.relevant_laws
            if not self._is_accessory_text(item.value)
        ]
        if core_laws:
            texts_to_embed.append('Fundamentos normativos: ' + ' | '.join(core_laws))

        for item in petition_summary.key_facts:
            if not self._is_accessory_text(item.value):
                texts_to_embed.append(item.value)

        for item in petition_summary.search_terms:
            if not self._is_accessory_text(item.value):
                texts_to_embed.append(item.value)

        vectors: list[list[float]] = []
        for i in range(0, len(texts_to_embed), self._BATCH_SIZE):
            batch = texts_to_embed[i : i + self._BATCH_SIZE]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            vectors.extend([item.embedding for item in response.data])
            if i + self._BATCH_SIZE < len(texts_to_embed):
                time.sleep(self._BATCH_DELAY)

        return [
            PetitionSummaryEmbedding.create(
                vector=[Decimal.create(float(value)) for value in vector],
                chunk=Text.create(chunk),
            )
            for chunk, vector in zip(texts_to_embed, vectors, strict=True)
        ]

    def _is_accessory_text(self, text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in self._ACCESSORY_MARKERS)

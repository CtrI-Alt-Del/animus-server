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
    _BATCH_DELAY: float = 0.5

    def __init__(self) -> None:
        self._client = OpenAI(api_key=Env.OPENAI_API_KEY)
        self._model = 'text-embedding-3-large'

    def generate(
        self,
        petition_summary: PetitionSummary,
    ) -> list[PetitionSummaryEmbedding]:
        texts = _ChunkBuilder(petition_summary).build()
        vectors = self._embed(texts)

        return [
            PetitionSummaryEmbedding.create(
                vector=[Decimal.create(float(v)) for v in vector],
                chunk=Text.create(chunk),
            )
            for chunk, vector in zip(texts, vectors, strict=True)
        ]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []

        for i in range(0, len(texts), self._BATCH_SIZE):
            batch = texts[i : i + self._BATCH_SIZE]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            vectors.extend([item.embedding for item in response.data])

            if i + self._BATCH_SIZE < len(texts):
                time.sleep(self._BATCH_DELAY)

        return vectors


class _ChunkBuilder:
    """Constrói a lista de chunks de texto a serem embeddados para uma petição.

    Estratégia de dois níveis:
    - Chunks atômicos: um por campo do summary, com prefixo semântico. Cobrem
      buscas direcionadas a uma dimensão específica (competência, legitimidade etc.).
    - Chunks compostos: combinam múltiplos campos relacionados num único vetor.
      Cobrem buscas por contexto combinado, onde a relevância emerge da co-ocorrência
      de conceitos.

    excluded_or_accessory_topics é intencionalmente omitido: embeddar o que NÃO
    é relevante aumentaria ruído na busca vetorial e poderia atrair falsos positivos.
    """

    def __init__(self, petition_summary: PetitionSummary) -> None:
        self._summary = petition_summary
        self._texts: list[str] = []
        self._seen: set[str] = set()

    def build(self) -> list[str]:
        self._add_atomic_chunks()
        self._add_composite_chunks()
        return self._texts

    def _add_atomic_chunks(self) -> None:
        s = self._summary

        self._add(s.case_summary.value)
        self._add(f'Questão jurídica principal: {s.legal_issue.value}')
        self._add(f'Pergunta jurídica central: {s.central_question.value}')

        self._add_optional_single_chunks()
        self._add_prefixed_list_chunks()
        self._add_relevant_laws_chunk()

    def _add_optional_single_chunks(self) -> None:
        s = self._summary

        if s.type_of_action is not None:
            self._add(f'Tipo de ação: {s.type_of_action.value}')

        if s.jurisdiction_issue is not None:
            self._add(f'Questão de competência: {s.jurisdiction_issue.value}')

        if s.standing_issue is not None:
            self._add(f'Questão de legitimidade: {s.standing_issue.value}')

    def _add_prefixed_list_chunks(self) -> None:
        s = self._summary
        list_fields = [
            ('Questão jurídica secundária: ', s.secondary_legal_issues),
            ('Pergunta jurídica adicional: ', s.alternative_questions),
            ('Fato relevante: ', s.key_facts),
            ('Pedido principal: ', s.requested_relief),
            ('Tema processual relevante: ', s.procedural_issues),
            ('', s.search_terms),
        ]

        for prefix, items in list_fields:
            for item in items:
                self._add(f'{prefix}{item.value}')

    def _add_relevant_laws_chunk(self) -> None:
        relevant_laws = self._summary.relevant_laws
        if not relevant_laws:
            return

        laws = ' | '.join(item.value for item in relevant_laws)
        self._add(f'Fundamentos normativos: {laws}')

    def _add_composite_chunks(self) -> None:
        self._add(self._build_structural_chunk())

        procedural = self._build_procedural_chunk()
        if procedural is not None:
            self._add(procedural)

        relief = self._build_relief_chunk()
        if relief is not None:
            self._add(relief)

        normative = self._build_normative_chunk()
        if normative is not None:
            self._add(normative)

    def _build_structural_chunk(self) -> str:
        """Combina os campos de maior peso semântico num único vetor.

        Sempre retorna um valor não-vazio: legal_issue e central_question
        são campos obrigatórios em PetitionSummary.
        """
        s = self._summary
        parts: list[str] = []

        if s.type_of_action is not None:
            parts.append(f'Tipo de ação: {s.type_of_action.value}')

        parts.append(f'Questão jurídica principal: {s.legal_issue.value}')
        parts.append(f'Pergunta jurídica central: {s.central_question.value}')

        if s.jurisdiction_issue is not None:
            parts.append(f'Questão de competência: {s.jurisdiction_issue.value}')

        if s.standing_issue is not None:
            parts.append(f'Questão de legitimidade: {s.standing_issue.value}')

        secondary = [item.value for item in s.secondary_legal_issues]
        if secondary:
            parts.append('Questões jurídicas secundárias: ' + ' | '.join(secondary))

        return ' || '.join(parts)

    def _build_procedural_chunk(self) -> str | None:
        issues = [item.value for item in self._summary.procedural_issues]
        if not issues:
            return None
        return 'Temas processuais e estruturais: ' + ' | '.join(issues)

    def _build_relief_chunk(self) -> str | None:
        relief = [item.value for item in self._summary.requested_relief]
        if not relief:
            return None
        return 'Pedidos principais: ' + ' | '.join(relief)

    def _build_normative_chunk(self) -> str | None:
        laws = [item.value for item in self._summary.relevant_laws]
        if not laws:
            return None
        return 'Base normativa principal do caso: ' + ' | '.join(laws)

    def _add(self, text: str | None) -> None:
        if text is None:
            return

        normalized = ' '.join(text.split()).strip()
        if not normalized:
            return

        lowered = normalized.lower()
        if lowered in self._seen:
            return

        self._seen.add(lowered)
        self._texts.append(normalized)

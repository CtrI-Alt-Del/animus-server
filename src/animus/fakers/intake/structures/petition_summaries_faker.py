from faker import Faker

from animus.core.intake.domain.structures import PetitionSummary
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)


class PetitionSummariesFaker:
    _faker = Faker()

    @staticmethod
    def fake(
        case_summary: str | None = None,
        legal_issue: str | None = None,
        central_question: str | None = None,
        relevant_laws: list[str] | None = None,
        key_facts: list[str] | None = None,
        search_terms: list[str] | None = None,
    ) -> PetitionSummary:
        return PetitionSummary.create(
            PetitionSummariesFaker.fake_dto(
                case_summary=case_summary,
                legal_issue=legal_issue,
                central_question=central_question,
                relevant_laws=relevant_laws,
                key_facts=key_facts,
                search_terms=search_terms,
            )
        )

    @staticmethod
    def fake_dto(
        case_summary: str | None = None,
        legal_issue: str | None = None,
        central_question: str | None = None,
        relevant_laws: list[str] | None = None,
        key_facts: list[str] | None = None,
        search_terms: list[str] | None = None,
    ) -> PetitionSummaryDto:
        generated_relevant_laws = relevant_laws or [
            f"Lei {PetitionSummariesFaker._faker.random_int(min=1000, max=99999)}"
            for _ in range(2)
        ]
        generated_key_facts = key_facts or [
            PetitionSummariesFaker._faker.sentence(nb_words=8) for _ in range(3)
        ]
        generated_search_terms = search_terms or [
            PetitionSummariesFaker._faker.word() for _ in range(6)
        ]

        return PetitionSummaryDto(
            case_summary=(
                case_summary or PetitionSummariesFaker._faker.paragraph(nb_sentences=4)
            ),
            legal_issue=(
                legal_issue
                or 'Controvérsia sobre cumprimento de obrigação contratual'
            ),
            central_question=(
                central_question
                or 'A parte ré descumpriu dever legal ou contratual aplicável ao caso?'
            ),
            relevant_laws=generated_relevant_laws,
            key_facts=generated_key_facts,
            search_terms=generated_search_terms,
        )

    @staticmethod
    def fake_many(count: int) -> list[PetitionSummary]:
        return [PetitionSummariesFaker.fake() for _ in range(count)]

    @staticmethod
    def fake_many_dto(count: int) -> list[PetitionSummaryDto]:
        return [PetitionSummariesFaker.fake_dto() for _ in range(count)]

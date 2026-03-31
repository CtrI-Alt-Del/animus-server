from datetime import UTC, datetime

from animus.core.intake.domain.entities.analysis import Analysis
from animus.core.intake.domain.entities.dtos.analysis_dto import AnalysisDto
from animus.core.intake.domain.entities.dtos.petition_document_dto import (
    PetitionDocumentDto,
)
from animus.core.intake.domain.entities.dtos.petition_dto import PetitionDto
from animus.core.intake.domain.entities.petition import Petition
from animus.core.intake.domain.structures.dtos.petition_summary_dto import (
    PetitionSummaryDto,
)
from animus.core.intake.domain.structures.petition_summary import PetitionSummary
from animus.core.intake.interfaces.analisyses_repository import AnalisysesRepository
from animus.core.intake.interfaces.petition_summaries_repository import (
    PetitionSummariesRepository,
)
from animus.core.intake.interfaces.petitions_repository import PetitionsRepository
from animus.core.shared.domain.structures.id import Id


class IntakeSeeder:
    def __init__(
        self,
        analisyses_repository: AnalisysesRepository,
        petitions_repository: PetitionsRepository,
        petition_summaries_repository: PetitionSummariesRepository,
    ) -> None:
        self._analisyses_repository = analisyses_repository
        self._petitions_repository = petitions_repository
        self._petition_summaries_repository = petition_summaries_repository

    def seed(self, account_ids: list[Id]) -> dict[str, Id] | None:
        if not account_ids:
            return None

        analysis = Analysis.create(
            AnalysisDto(
                id='01KMQTN9YCHWG20ZZEPNBRYW87',
                name='Analise de exemplo',
                account_id=account_ids[0].value,
                status='WAITING_PETITION',
                created_at=datetime.now(UTC).isoformat(),
            )
        )
        self._analisyses_repository.add(analysis)

        petition = Petition.create(
            PetitionDto(
                id='01KMQV3F09J22AWX0P7X21D9PK',
                analysis_id=analysis.id.value,
                uploaded_at=datetime.now(UTC).isoformat(),
                document=PetitionDocumentDto(
                    file_path=f'intake/analises/{analysis.id.value}/petitions/Ação Cobrança Lei 12855 Tema Repetitivo 974 SIRDR 3 STJ.pdf',
                    name='peticao-inicial.pdf',
                ),
            )
        )
        self._petitions_repository.add(petition)

        petition_summary = PetitionSummary.create(
            PetitionSummaryDto(
                case_summary='Resumo de seed da peticao inicial',
                legal_issue='Controvérsia sobre cobrança em contrato de prestação de serviço',
                central_question='Há inadimplemento contratual apto a justificar a cobrança requerida?',
                relevant_laws=[
                    'Código Civil, Art. 389',
                    'Código Civil, Art. 395',
                ],
                key_facts=[
                    'Dados de exemplo para fluxo de resumo',
                    'Petição vinculada a uma análise existente',
                ],
                search_terms=[
                    'inadimplemento contratual',
                    'cobrança de obrigação',
                    'responsabilidade civil contratual',
                ],
            )
        )
        self._petition_summaries_repository.add(
            petition_id=petition.id,
            petition_summary=petition_summary,
        )

        return {
            'analysis_id': analysis.id,
            'petition_id': petition.id,
        }

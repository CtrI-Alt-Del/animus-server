from animus.core.intake.domain.structures.court import Court
from animus.core.intake.domain.structures.dtos.case_assessment_briefing_dto import (
    CaseAssessmentBriefingDto,
)
from animus.core.intake.domain.structures.legal_area import LegalArea
from animus.core.shared.domain.abstracts import Structure
from animus.core.shared.domain.decorators import structure
from animus.core.shared.domain.errors import ValidationError
from animus.core.shared.domain.structures import Id, Text


@structure
class CaseAssessmentBriefing(Structure):
    analysis_id: Id
    legal_area: LegalArea
    court_jurisdiction: Court
    main_claims: Text
    intended_thesis: Text

    @classmethod
    def create(cls, dto: CaseAssessmentBriefingDto) -> 'CaseAssessmentBriefing':
        main_claims = dto.main_claims.strip()
        if not main_claims:
            raise ValidationError('Pedido principal obrigatorio')

        intended_thesis = dto.intended_thesis.strip()
        if not intended_thesis:
            raise ValidationError('Tese pretendida obrigatoria')

        return cls(
            analysis_id=Id.create(dto.analysis_id),
            legal_area=LegalArea.create(dto.legal_area),
            court_jurisdiction=Court.create(dto.court_jurisdiction),
            main_claims=Text.create(main_claims),
            intended_thesis=Text.create(intended_thesis),
        )

    @property
    def dto(self) -> CaseAssessmentBriefingDto:
        return CaseAssessmentBriefingDto(
            analysis_id=self.analysis_id.value,
            legal_area=self.legal_area.dto,
            court_jurisdiction=self.court_jurisdiction.dto,
            main_claims=self.main_claims.value,
            intended_thesis=self.intended_thesis.value,
        )

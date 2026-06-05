from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class CaseAssessmentBriefingModel(Model):
    __tablename__ = 'case_assessment_briefings'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    legal_area: Mapped[str] = mapped_column(String, nullable=False)
    court_jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    main_claims: Mapped[str] = mapped_column(Text, nullable=False)
    intended_thesis: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[Any] = relationship(
        'AnalysisModel',
        back_populates='case_assessment_briefing',
    )

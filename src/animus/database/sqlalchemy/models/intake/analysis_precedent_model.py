from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class AnalysisPrecedentModel(Model):
    __tablename__ = 'analysis_precedents'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    precedent_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('precedents.id', ondelete='CASCADE'),
        primary_key=True,
    )
    is_chosen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    applicability_percentage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    synthesis: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Any] = relationship('AnalysisModel')
    precedent: Mapped[Any] = relationship('PrecedentModel')

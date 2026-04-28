from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
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
    similarity_percentage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    thesis_similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    enunciation_similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    total_search_hits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    similarity_rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    applicability_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    synthesis: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Any] = relationship('AnalysisModel')
    precedent: Mapped[Any] = relationship('PrecedentModel')

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class SecondInstanceJudgmentDraftModel(Model):
    __tablename__ = 'second_instance_judgment_drafts'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    report: Mapped[str] = mapped_column(Text, nullable=False)
    merit_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    precedent_adherence_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    ruling: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    preliminary_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    no_applicable_precedent_notice: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    analysis: Mapped[Any] = relationship(
        'AnalysisModel', back_populates='judgment_draft'
    )

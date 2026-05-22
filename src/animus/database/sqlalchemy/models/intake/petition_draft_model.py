from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class PetitionDraftModel(Model):
    __tablename__ = 'petition_drafts'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    structured_facts: Mapped[str] = mapped_column(Text, nullable=False)
    legal_grounds: Mapped[str] = mapped_column(Text, nullable=False)
    central_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    requests: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    precedent_citations: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    analysis: Mapped[Any] = relationship(
        'AnalysisModel', back_populates='petition_draft'
    )

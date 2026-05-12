from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class PetitionDraftModel(Model):
    __tablename__ = 'petition_drafts'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[Any] = relationship('AnalysisModel', back_populates='petition_draft')

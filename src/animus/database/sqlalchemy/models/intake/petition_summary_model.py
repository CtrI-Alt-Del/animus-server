from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class PetitionSummaryModel(Model):
    __tablename__ = 'petition_summaries'

    petition_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('petitions.id', ondelete='CASCADE'),
        primary_key=True,
    )
    case_summary: Mapped[str] = mapped_column(Text, nullable=False)
    legal_issue: Mapped[str] = mapped_column(Text, nullable=False)
    central_question: Mapped[str] = mapped_column(Text, nullable=False)
    relevant_laws: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    key_facts: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    search_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    petition: Mapped[Any] = relationship('PetitionModel', back_populates='summary')

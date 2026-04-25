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
    type_of_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    secondary_legal_issues: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    alternative_questions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    jurisdiction_issue: Mapped[str | None] = mapped_column(Text, nullable=True)
    standing_issue: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_relief: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    procedural_issues: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    excluded_or_accessory_topics: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    petition: Mapped[Any] = relationship('PetitionModel', back_populates='summary')

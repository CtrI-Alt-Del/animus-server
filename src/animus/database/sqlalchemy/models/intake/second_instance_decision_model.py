from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class SecondInstanceDecisionModel(Model):
    __tablename__ = 'second_instance_decisions'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[Any] = relationship(
        'AnalysisModel',
        back_populates='second_instance_decision',
    )

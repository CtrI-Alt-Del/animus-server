from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class AnalysisPrecedentApplicabilityFeedbackModel(Model):
    __tablename__ = 'analysis_precedent_applicability_feedbacks'

    analysis_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    precedent_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    applicability_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_from_human: Mapped[bool] = mapped_column(Boolean, nullable=False)

    analysis_precedent: Mapped[Any] = relationship('AnalysisPrecedentModel')

    __table_args__ = (
        ForeignKeyConstraint(
            ['analysis_id', 'precedent_id'],
            ['analysis_precedents.analysis_id', 'analysis_precedents.precedent_id'],
            ondelete='CASCADE',
        ),
    )

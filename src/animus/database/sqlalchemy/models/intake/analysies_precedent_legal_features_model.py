from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class AnalysiesPrecedentLegalFeaturesModel(Model):
    __tablename__ = 'analysies_precedent_legal_features'

    analysis_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    precedent_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    central_issue_match: Mapped[int] = mapped_column(Integer, nullable=False)
    structural_issue_match: Mapped[int] = mapped_column(Integer, nullable=False)
    context_compatibility: Mapped[int] = mapped_column(Integer, nullable=False)
    is_lateral_topic: Mapped[int] = mapped_column(Integer, nullable=False)
    is_accessory_topic: Mapped[int] = mapped_column(Integer, nullable=False)

    analysis_precedent: Mapped[Any] = relationship(
        'AnalysisPrecedentModel',
        back_populates='legal_features',
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ['analysis_id', 'precedent_id'],
            ['analysis_precedents.analysis_id', 'analysis_precedents.precedent_id'],
            ondelete='CASCADE',
        ),
    )

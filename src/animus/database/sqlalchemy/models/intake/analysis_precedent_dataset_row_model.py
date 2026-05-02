from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class AnalysisPrecedentDatasetRowModel(Model):
    __tablename__ = 'analysis_precedent_dataset_rows'

    analysis_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    precedent_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    applicability_level: Mapped[int] = mapped_column(Integer, nullable=False)
    is_from_human: Mapped[bool] = mapped_column(Boolean, nullable=False)
    thesis_similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    enunciation_similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    total_search_hits: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    identifier_court: Mapped[str] = mapped_column(String(10), nullable=False)
    identifier_kind: Mapped[str] = mapped_column(String(10), nullable=False)
    identifier_number: Mapped[int] = mapped_column(Integer, nullable=False)
    precedent_status: Mapped[str] = mapped_column(String(120), nullable=False)
    last_updated_in_pangea_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    central_issue_match: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    structural_issue_match: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    context_compatibility: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    is_lateral_topic: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_accessory_topic: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    analysis_precedent: Mapped[Any] = relationship('AnalysisPrecedentModel')

    __table_args__ = (
        ForeignKeyConstraint(
            ['analysis_id', 'precedent_id'],
            ['analysis_precedents.analysis_id', 'analysis_precedents.precedent_id'],
            ondelete='CASCADE',
        ),
    )

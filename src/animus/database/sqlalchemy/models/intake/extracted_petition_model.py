from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class ExtractedPetitionModel(Model):
    __tablename__ = 'extracted_petitions'

    analysis_id: Mapped[str] = mapped_column(
        String(26),
        ForeignKey('analyses.id', ondelete='CASCADE'),
        primary_key=True,
    )
    first_page: Mapped[int] = mapped_column(Integer, nullable=False)
    last_page: Mapped[int] = mapped_column(Integer, nullable=False)

    analysis: Mapped[Any] = relationship(
        'AnalysisModel', back_populates='extracted_petition'
    )

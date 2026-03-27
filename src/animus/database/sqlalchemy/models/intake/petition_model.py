from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animus.database.sqlalchemy.models.model import Model


class PetitionModel(Model):
    __tablename__ = 'petitions'

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    document_file_path: Mapped[str] = mapped_column(String, nullable=False)
    document_name: Mapped[str] = mapped_column(String, nullable=False)

    summary: Mapped[Any] = relationship(
        'PetitionSummaryModel',
        back_populates='petition',
        uselist=False,
        cascade='all, delete-orphan',
    )

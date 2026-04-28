from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from animus.database.sqlalchemy.models.model import Model


class PrecedentModel(Model):
    __tablename__ = 'precedents'

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    court: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(120), nullable=False)

    enunciation: Mapped[str] = mapped_column(Text, nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)

    last_updated_in_pangea_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    __table_args__ = (
        UniqueConstraint('court', 'kind', 'number', name='uq_precedent_identifier'),
    )

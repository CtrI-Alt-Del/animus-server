from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from animus.database.sqlalchemy.models.model import Model


class AccountModel(Model):
    __tablename__ = 'accounts'

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

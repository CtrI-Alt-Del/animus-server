from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session, sessionmaker
from ulid import ULID

from animus.core.intake.domain.entities.analysis_status import AnalysisStatusValue
from animus.core.shared.domain.structures import Text
from animus.database.sqlalchemy.models.intake import AnalysisModel
from animus.providers.auth.jwt.jose.jose_jwt_provider import JoseJwtProvider

BuildAuthHeadersFixture = Callable[[str], dict[str, str]]
CreateAnalysisFixture = Callable[..., AnalysisModel]


@pytest.fixture
def build_auth_headers() -> BuildAuthHeadersFixture:
    def _build_auth_headers(account_id: str) -> dict[str, str]:
        access_token = (
            JoseJwtProvider().encode(Text.create(account_id)).access_token.value
        )
        return {'Authorization': f'Bearer {access_token}'}

    return _build_auth_headers


@pytest.fixture
def create_analysis(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> CreateAnalysisFixture:
    def _create_analysis(
        *,
        account_id: str,
        analysis_id: str | None = None,
        name: str = 'Analise inicial',
        status: str = AnalysisStatusValue.WAITING_PETITION.value,
        folder_id: str | None = None,
        is_archived: bool = False,
    ) -> AnalysisModel:
        session = sqlalchemy_session_factory()
        model = AnalysisModel(
            id=analysis_id or str(ULID()),
            name=name,
            folder_id=folder_id,
            account_id=account_id,
            status=status,
            is_archived=is_archived,
            created_at=datetime.now(UTC),
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        session.expunge(model)
        session.close()
        return model

    return _create_analysis

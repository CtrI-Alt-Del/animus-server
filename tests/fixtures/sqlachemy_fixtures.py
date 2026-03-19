from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from animus.database.sqlalchemy.models.model import Model


@pytest.fixture(scope='session')
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer('postgres:16-alpine') as postgres:
        yield postgres


@pytest.fixture(scope='session')
def engine(postgres_container: PostgresContainer) -> Generator[Engine]:
    url = postgres_container.get_connection_url()
    url = url.replace('postgresql://', 'postgresql+psycopg2://')

    engine = create_engine(url, future=True)

    Model.metadata.create_all(bind=engine)

    yield engine

    Model.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def sqlalchemy_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def reset_database(engine: Engine) -> Generator[None]:
    with engine.begin() as connection:
        for table in reversed(Model.metadata.sorted_tables):
            connection.execute(table.delete())

    yield

    with engine.begin() as connection:
        for table in reversed(Model.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def sqlalchemy_session(
    sqlalchemy_session_factory: sessionmaker[Session],
) -> Generator[Session]:
    db = sqlalchemy_session_factory()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

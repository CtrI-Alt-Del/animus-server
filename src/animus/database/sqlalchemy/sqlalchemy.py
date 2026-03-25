from sqlalchemy import create_engine
from contextlib import contextmanager
from collections.abc import Iterator
from sqlalchemy.orm import sessionmaker, Session

from animus.constants import Env

DATABASE_URL = (
    Env.DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
    if Env.DATABASE_URL.startswith('postgresql://')
    else Env.DATABASE_URL
)

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}
    if DATABASE_URL.startswith('sqlite')
    else {},
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session
)


class Sqlalchemy:
    @staticmethod
    def get_session() -> Session:
        return SessionLocal()

    @staticmethod
    @contextmanager
    def session() -> Iterator[Session]:
        session = Sqlalchemy.get_session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        else:
            session.commit()
        finally:
            session.close()

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from starlette.responses import Response

from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy


class HandleSqlalchemySessionMiddleware:
    @staticmethod
    def handle(app: FastAPI) -> None:
        @app.middleware('http')
        async def _(
            request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            sqlalchemy_session = Sqlalchemy.get_session()
            request.state.sqlalchemy_session = sqlalchemy_session
            try:
                response = await call_next(request)
            except Exception:
                sqlalchemy_session.rollback()
                raise
            else:
                sqlalchemy_session.commit()
                return response
            finally:
                sqlalchemy_session.close()

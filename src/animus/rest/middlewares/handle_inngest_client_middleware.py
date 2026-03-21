from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from inngest import Inngest
from starlette.responses import Response


class HandleInngestClientMiddleware:
    @staticmethod
    def handle(app: FastAPI, inngest: Inngest) -> None:
        @app.middleware('http')
        async def _(
            request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            request.state.inngest_client = inngest
            return await call_next(request)

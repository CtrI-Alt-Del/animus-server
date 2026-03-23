from fastapi import FastAPI

from animus.pubsub.inngest.inngest_pubsub import InngestPubSub
from animus.rest.handlers import AppErrorHandler
from animus.rest.middlewares import (
    HandleInngestClientMiddleware,
    HandleSqlalchemySessionMiddleware,
)
from animus.routers import AuthRouter
from animus.routers.docs.docs_router import DocsRouter


class FastAPIApp:
    @staticmethod
    def register() -> FastAPI:
        app = FastAPI(
            docs_url=None,
            redoc_url=None,
        )

        app.include_router(AuthRouter.register())
        app.include_router(DocsRouter.register())

        HandleSqlalchemySessionMiddleware.handle(app)

        inngest = InngestPubSub.register(app)
        HandleInngestClientMiddleware.handle(app, inngest)

        AppErrorHandler.register(app)

        return app

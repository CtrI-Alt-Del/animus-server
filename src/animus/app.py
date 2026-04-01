import os

from fastapi import FastAPI

from animus.constants import Env
from animus.pubsub.inngest.inngest_pubsub import InngestPubSub
from animus.rest.handlers import AppErrorHandler
from animus.rest.middlewares import (
    HandleInngestClientMiddleware,
    HandleSqlalchemySessionMiddleware,
)
from animus.routers.auth.auth_router import AuthRouter
from animus.routers.docs.docs_router import DocsRouter
from animus.routers.intake.intake_router import IntakeRouter
from animus.routers.storage.storage_router import StorageRouter


class FastAPIApp:
    @staticmethod
    def _configure_storage_emulator() -> None:
        storage_emulator_host = Env.STORAGE_EMULATOR_HOST
        if Env.MODE == 'dev' and not storage_emulator_host:
            storage_emulator_host = 'http://localhost:4443'

        if storage_emulator_host:
            os.environ['STORAGE_EMULATOR_HOST'] = storage_emulator_host
        else:
            os.environ.pop('STORAGE_EMULATOR_HOST', None)

    @staticmethod
    def register() -> FastAPI:
        FastAPIApp._configure_storage_emulator()

        app = FastAPI(
            docs_url=None,
            redoc_url=None,
        )

        app.include_router(AuthRouter.register())
        app.include_router(IntakeRouter.register())
        app.include_router(StorageRouter.register())
        app.include_router(DocsRouter.register())

        HandleSqlalchemySessionMiddleware.handle(app)

        inngest = InngestPubSub.register(app)
        HandleInngestClientMiddleware.handle(app, inngest)

        AppErrorHandler.register(app)

        return app

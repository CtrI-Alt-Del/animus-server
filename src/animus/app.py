from fastapi import FastAPI


class FastAPIApp:
    @staticmethod
    def register() -> FastAPI:
        app = FastAPI(
            docs_url=None,
            redoc_url=None,
        )

        return app

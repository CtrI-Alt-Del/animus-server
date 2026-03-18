from fastapi import FastAPI


class FastAPIApp:
    @staticmethod
    def register() -> FastAPI:
        return FastAPI(
            docs_url=None,
            redoc_url=None,
        )

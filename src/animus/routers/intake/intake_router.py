from fastapi import APIRouter

from animus.routers.intake.analyses_router import AnalysesRouter
from animus.routers.intake.petitions_router import PetitionsRouter


class IntakeRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/intake', tags=['intake'])

        router.include_router(AnalysesRouter.register())
        router.include_router(PetitionsRouter.register())

        return router

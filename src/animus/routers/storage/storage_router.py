from fastapi import APIRouter

from animus.rest.controllers.storage import GeneratePetitionUploadUrlController


class StorageRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/storage', tags=['storage'])

        GeneratePetitionUploadUrlController.handle(router)

        return router

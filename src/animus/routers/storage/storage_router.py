from fastapi import APIRouter

from animus.rest.controllers.storage import GenerateAnalysisDocumentUploadUrlController


class StorageRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/storage', tags=['storage'])

        GenerateAnalysisDocumentUploadUrlController.handle(router)

        return router

from fastapi import APIRouter

from animus.rest.controllers.library import (
    ArchiveFolderController,
    CreateFolderController,
    GetFolderController,
    ListFoldersController,
    RenameFolderController,
)


class LibraryRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/library', tags=['library'])

        CreateFolderController.handle(router)
        GetFolderController.handle(router)
        RenameFolderController.handle(router)
        ArchiveFolderController.handle(router)
        ListFoldersController.handle(router)

        return router

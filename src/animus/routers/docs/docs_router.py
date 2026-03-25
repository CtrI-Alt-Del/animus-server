from fastapi import APIRouter

from animus.rest.controllers.docs.render_docs_page_controller import (
    RenderDocsPageController,
)


class DocsRouter:
    @staticmethod
    def register() -> APIRouter:
        router = APIRouter(prefix='/docs', include_in_schema=False)

        RenderDocsPageController.handle(router)

        return router

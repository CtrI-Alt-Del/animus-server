from fastapi import APIRouter
from fastapi.responses import HTMLResponse


class RenderDocsPageController:
    _SCALAR_HTML = """
    <!doctype html>
    <html lang="pt-BR">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Animus API | Machine Learning Jurídico</title>
        <meta name="description" content="Documentação oficial da API Animus: Soluções de Inteligência Artificial e Machine Learning para o ambiente jurídico." />

        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
        <link rel="manifest" href="/site.webmanifest">
      </head>
      <body>
        <script
            id="api-reference"
            data-url="/openapi.json"
            data-theme="default"
        ></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
      </body>
    </html>
    """

    @staticmethod
    def handle(router: APIRouter) -> None:
        @router.get('/', include_in_schema=False)
        def _() -> HTMLResponse:
            return HTMLResponse(RenderDocsPageController._SCALAR_HTML)

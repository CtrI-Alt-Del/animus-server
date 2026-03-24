from typing import Any, Protocol

from animus.core.shared.responses.rest_response import RestResponse

type Json = dict[str, Any]


class RestClient(Protocol):
    def get(self, path: str, query_params: Json | None = None) -> RestResponse[Any]: ...

    def post(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]: ...

    def put(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]: ...

    def patch(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]: ...

    def delete(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]: ...

    def get_base_url(self) -> str: ...

    def set_base_url(self, base_url: str) -> None: ...

    def set_header(self, key: str, value: str) -> None: ...

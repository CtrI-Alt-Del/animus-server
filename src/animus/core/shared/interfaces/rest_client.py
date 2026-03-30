from typing import Any, Protocol

from animus.core.shared.responses.rest_response import RestResponse

type Json = dict[str, Any]


class RestClient(Protocol):
    def get[T](
        self, path: str, response_model: type[T], query_params: Json | None = None
    ) -> RestResponse[T]: ...

    def post[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]: ...

    def put[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]: ...

    def patch[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]: ...

    def delete[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]: ...

    def get_base_url(self) -> str: ...
    def set_base_url(self, base_url: str) -> None: ...
    def set_header(self, key: str, value: str) -> None: ...

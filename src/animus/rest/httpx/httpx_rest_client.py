from typing import Any

import httpx
from animus.core.shared.interfaces.rest_client import RestClient
from animus.core.shared.responses.rest_response import RestResponse

type Json = dict[str, Any]


class HttpxRestClient(RestClient):
    def __init__(self):
        self._client = httpx.Client()

    def _build_response[T](
        self, response: httpx.Response, response_model: type[T]
    ) -> RestResponse[T]:
        body: Any = None
        error_message = None

        try:
            if response.content:
                raw_json = response.json()

                if isinstance(raw_json, dict) and hasattr(response_model, 'create'):
                    body = response_model.create(**raw_json)  # type: ignore
                elif isinstance(raw_json, dict):
                    body = response_model(**raw_json)  # type: ignore
                else:
                    body = response_model(raw_json)  # type: ignore

        except Exception as e:
            #@TODO: criar classe de LOG!
            print(f"DEBUG: Falha ao instanciar o modelo {response_model.__name__}: {e}")
            body = response.text if response.text else None
            if response.is_error:
                error_message = f'Parse Error: {e!s}'

        if response.is_error and not error_message:
            error_message = str(body) if body else f'HTTP Error {response.status_code}'

        return RestResponse(
            body=body,
            status_code=response.status_code,
            error_message=error_message,
        )

    def get[T](
        self, path: str, response_model: type[T], query_params: Json | None = None
    ) -> RestResponse[T]:
        response = self._client.get(url=path, params=query_params)
        return self._build_response(response, response_model)

    def post[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]:
        response = self._client.post(url=path, json=body, params=query_params)
        return self._build_response(response, response_model)

    def put[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]:
        response = self._client.put(url=path, json=body, params=query_params)
        return self._build_response(response, response_model)

    def patch[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]:
        response = self._client.patch(url=path, json=body, params=query_params)
        return self._build_response(response, response_model)

    def delete[T](
        self,
        path: str,
        response_model: type[T],
        body: Any | None = None,
        query_params: Json | None = None,
    ) -> RestResponse[T]:
        response = self._client.request(
            'DELETE', url=path, json=body, params=query_params
        )
        return self._build_response(response, response_model)

    def get_base_url(self) -> str:
        return str(self._client.base_url)

    def set_base_url(self, base_url: str) -> None:
        self._client.base_url = httpx.URL(base_url)

    def set_header(self, key: str, value: str) -> None:
        self._client.headers[key] = value

    def close(self) -> None:
        self._client.close()

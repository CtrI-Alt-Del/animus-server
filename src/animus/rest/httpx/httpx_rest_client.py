from typing import Any

import httpx
from animus.core.shared.interfaces.rest_client import RestClient
from animus.core.shared.responses.rest_response import RestResponse

type Json = dict[str, Any]


class HttpxRestClient(RestClient):
    def __init__(self):
        self._client = httpx.Client()

    def _build_response(self, response: httpx.Response) -> RestResponse[Any]:
        body = None
        error_message = None
        try:
            if response.content:
                body = response.json()
        except Exception:
            body = response.text if response.text else None

        if response.is_error:
            error_message = str(body) if body else f'HTTP Error {response.status_code}'

        return RestResponse(
            body=body,
            status_code=response.status_code,
            error_message=error_message,
        )

    def get(self, path: str, query_params: Json | None = None) -> RestResponse[Any]:
        response = self._client.get(url=path, params=query_params)
        return self._build_response(response)

    def post(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]:
        response = self._client.post(url=path, json=body, params=query_params)
        return self._build_response(response)

    def put(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]:
        response = self._client.put(url=path, json=body, params=query_params)
        return self._build_response(response)

    def patch(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]:
        response = self._client.patch(url=path, json=body, params=query_params)
        return self._build_response(response)

    def delete(
        self, path: str, body: Any | None = None, query_params: Json | None = None
    ) -> RestResponse[Any]:
        response = self._client.request(
            'DELETE', url=path, json=body, params=query_params
        )
        return self._build_response(response)

    def get_base_url(self) -> str:
        return str(self._client.base_url)

    def set_base_url(self, base_url: str) -> None:
        self._client.base_url = httpx.URL(base_url)

    def set_header(self, key: str, value: str) -> None:
        self._client.headers[key] = value

    def close(self) -> None:
        self._client.close()

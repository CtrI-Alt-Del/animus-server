from http import HTTPStatus
from collections.abc import Callable
from typing import Never

from animus.core.shared.domain.errors import AppError


class RestResponse[Body]:
    def __init__(
        self,
        body: Body | None = None,
        status_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        self._body = body
        self._status_code = int(status_code or HTTPStatus.OK)
        self._error_message = error_message

    @property
    def body(self) -> Body:
        if self.is_failure or self._error_message is not None:
            raise AppError(
                'Rest Response Error',
                f'Rest Response status: {self.status_code}\n Rest Response error message: {self._error_message}',
            )
        if self._body is None:
            raise AppError(
                'Rest Response Error', f'Rest Response failed: {self.status_code}'
            )
        return self._body

    def throw_error(self) -> Never:
        raise AppError(
            'Rest Response Error', f'Rest Response failed: {self.status_code}'
        )

    def map_body[NewBody](
        self, mapper: Callable[[Body], NewBody | None]
    ) -> 'RestResponse[NewBody]':
        if self._error_message is not None:
            raise AppError(
                'Rest Response Error',
                f'Rest Response failed. Error message: {self._error_message}',
            )
        if self._body is None:
            raise AppError('Rest Response Error', 'Rest Response failed. Body is null')
        return RestResponse(body=mapper(self._body), status_code=self._status_code)

    @property
    def is_successful(self) -> bool:
        return self._status_code <= HTTPStatus.BAD_REQUEST

    @property
    def is_failure(self) -> bool:
        return (
            self._status_code >= HTTPStatus.BAD_REQUEST
            or self._error_message is not None
        )

    @property
    def error_message(self) -> str:
        if self._error_message is not None:
            return self._error_message
        raise AppError(
            'Rest Response Error', f'Rest Response failed: {self.status_code}'
        )

    @property
    def status_code(self) -> int:
        return self._status_code

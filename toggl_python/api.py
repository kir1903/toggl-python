from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Type, TypeVar

from httpx import Client, HTTPStatusError, Response
from pydantic import BaseModel

from toggl_python.exceptions import BadRequest


if TYPE_CHECKING:
    from toggl_python.auth import BasicAuth, TokenAuth

COMMON_HEADERS: dict[str, str] = {"content-type": "application/json"}
ROOT_URL: str = "https://api.track.toggl.com/api/v9"

ResponseSchema = TypeVar("ResponseSchema", bound=BaseModel)


class ApiWrapper:
    def __init__(self, auth: BasicAuth | TokenAuth, base_url: str = ROOT_URL) -> None:
        self.client = Client(
            base_url=base_url,
            auth=auth,
            headers=COMMON_HEADERS,
            http2=True,
        )

    def raise_for_status(self, response: Response) -> None:
        """Disable exception chaining to avoid huge not informative traceback."""
        try:
            _ = response.raise_for_status()
        except HTTPStatusError as base_exception:
            raise BadRequest(base_exception.response.text) from None

    def _request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Perform HTTP request and raise an exception on non-2xx status."""
        response = self.client.request(method, url, **kwargs)
        self.raise_for_status(response)

        return response

    def _request_and_validate(
        self, method: str, url: str, schema: Type[ResponseSchema], **kwargs: Any
    ) -> ResponseSchema:
        """Perform request and validate response body against a single `schema`."""
        response = self._request(method, url, **kwargs)

        return schema.model_validate(response.json())

    def _request_and_validate_list(
        self, method: str, url: str, schema: Type[ResponseSchema], **kwargs: Any
    ) -> List[ResponseSchema]:
        """Perform request and validate every item of response body against `schema`."""
        response = self._request(method, url, **kwargs)

        return [schema.model_validate(item) for item in response.json()]

    def _request_and_check_success(self, method: str, url: str, **kwargs: Any) -> bool:
        """Perform request and return whether it was successful.

        Used for endpoints whose response body carries no useful data.
        """
        response = self._request(method, url, **kwargs)

        return response.is_success

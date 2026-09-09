from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import Response as HttpxResponse
from pydantic import BaseModel
from toggl_python.api import ApiWrapper
from toggl_python.auth import TokenAuth
from toggl_python.exceptions import BadRequest

from tests.responses.me_get import FAKE_TOKEN


if TYPE_CHECKING:
    from respx import MockRouter


class SampleSchema(BaseModel):
    id: int
    name: str


@pytest.fixture()
def api_wrapper() -> ApiWrapper:
    auth = TokenAuth(token=FAKE_TOKEN)

    return ApiWrapper(auth=auth)


def test_request_and_validate(response_mock: MockRouter, api_wrapper: ApiWrapper) -> None:
    payload = {"id": 1, "name": "sample"}
    mocked_route = response_mock.get("/sample").mock(
        return_value=HttpxResponse(status_code=200, json=payload),
    )

    result = api_wrapper._request_and_validate("GET", "/sample", SampleSchema)

    assert mocked_route.called is True
    assert result == SampleSchema.model_validate(payload)


def test_request_and_validate_list(response_mock: MockRouter, api_wrapper: ApiWrapper) -> None:
    payload = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    mocked_route = response_mock.get("/sample").mock(
        return_value=HttpxResponse(status_code=200, json=payload),
    )

    result = api_wrapper._request_and_validate_list("GET", "/sample", SampleSchema)

    assert mocked_route.called is True
    assert result == [SampleSchema.model_validate(item) for item in payload]


def test_request_and_check_success(response_mock: MockRouter, api_wrapper: ApiWrapper) -> None:
    mocked_route = response_mock.delete("/sample/1").mock(
        return_value=HttpxResponse(status_code=200, json={}),
    )

    result = api_wrapper._request_and_check_success("DELETE", "/sample/1")

    assert mocked_route.called is True
    assert result is True


def test_request_raises_bad_request_on_error_status(
    response_mock: MockRouter, api_wrapper: ApiWrapper
) -> None:
    error_message = "Bad request text"
    mocked_route = response_mock.get("/sample").mock(
        return_value=HttpxResponse(status_code=400, text=error_message),
    )

    with pytest.raises(BadRequest, match=error_message):
        _ = api_wrapper._request("GET", "/sample")

    assert mocked_route.called is True

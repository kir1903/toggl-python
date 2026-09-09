from __future__ import annotations

from typing import Optional

from toggl_python.schemas.base import BaseSchema, dump_payload


class SamplePayloadSchema(BaseSchema):
    a: Optional[int] = None
    b: str = "default"


def test_dump_payload__excludes_none_fields() -> None:
    schema = SamplePayloadSchema(a=None, b="value")

    assert dump_payload(schema) == {"b": "value"}


def test_dump_payload__keeps_unset_fields_with_non_none_default_by_default() -> None:
    schema = SamplePayloadSchema(a=1)

    assert dump_payload(schema) == {"a": 1, "b": "default"}


def test_dump_payload__exclude_unset_drops_fields_not_explicitly_passed() -> None:
    schema = SamplePayloadSchema(a=1)

    assert dump_payload(schema, exclude_unset=True) == {"a": 1}


def test_dump_payload__exclude_unset_keeps_explicitly_passed_default_value() -> None:
    schema = SamplePayloadSchema(a=1, b="default")

    assert dump_payload(schema, exclude_unset=True) == {"a": 1, "b": "default"}

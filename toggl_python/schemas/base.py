from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_serializer,
)


class BaseSchema(BaseModel):
    pass


def dump_payload(schema: BaseSchema, *, exclude_unset: bool = False) -> Dict[str, object]:
    """Serialize a query params / request body schema the way entity methods need it.

    `None` fields are always dropped since the API treats an omitted field
    differently from an explicit `null`. `exclude_unset` additionally drops
    fields that were not passed at all, which matters for partial PUT/PATCH bodies.
    """
    return schema.model_dump(mode="json", exclude_none=True, exclude_unset=exclude_unset)


class SinceParamSchemaMixin(BaseSchema):
    since: Optional[AwareDatetime]

    @field_validator("since")
    @classmethod
    def check_if_since_is_too_old(cls, value: Optional[datetime]) -> Optional[datetime]:
        if not value:
            return value

        now = datetime.now(tz=timezone.utc)
        three_months = timedelta(days=90)
        utc_value = value.astimezone(tz=timezone.utc)

        if now - three_months > utc_value:
            error_message = "Since cannot be older than 3 months"
            raise ValueError(error_message)

        return value

    @field_serializer("since", when_used="json")
    def serialize_since(self, value: Optional[datetime]) -> Optional[int]:
        if not value:
            return value

        return int(value.timestamp())


class BulkEditOperations(str, Enum):
    add = "add"
    remove = "remove"
    # Renamed to avoid using system keyword
    change = "replace"


class BulkEditOperation(BaseSchema):
    operation: BulkEditOperations
    field_name: str
    field_value: Union[bool, str, int, AwareDatetime, List[int], List[str]]

    @model_serializer(when_used="json")
    def serialize_schema(
        self,
    ) -> Dict[str, Union[bool, str, int, AwareDatetime, List[int], List[str]]]:
        return {
            "op": self.operation,
            "path": f"/{self.field_name}",
            "value": self.field_value,
        }


class BulkEditMethodParams(BaseSchema):
    ids: List[int] = Field(max_length=100, min_length=1)
    operations: List[BulkEditOperation] = Field(min_length=1)

    @field_serializer("ids", when_used="json")
    def serialize_ids(self, value: List[int]) -> str:
        return ",".join(str(item) for item in value)


class BulkEditResponseFailure(BaseSchema):
    id: int
    message: str


class BulkEditResponse(BaseSchema):
    success: List[int]
    failure: List[BulkEditResponseFailure]

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from toggl_python.api import ApiWrapper
from toggl_python.schemas.base import dump_payload
from toggl_python.schemas.current_user import (
    DateFormat,
    DurationFormat,
    MeFeaturesResponse,
    MePreferencesResponse,
    MeResponse,
    MeResponseWithRelatedData,
    TimeFormat,
    UpdateMePasswordRequest,
    UpdateMePreferencesRequest,
    UpdateMeRequest,
    UpdateMeResponse,
)
from toggl_python.schemas.project import (
    MePaginatedProjectsQueryParams,
    MeProjectsQueryParams,
    ProjectResponse,
)
from toggl_python.schemas.time_entry import (
    MeTimeEntryQueryParams,
    MeTimeEntryResponse,
    MeTimeEntryWithMetaResponse,
    MeWebTimerResponse,
)


if TYPE_CHECKING:
    from datetime import datetime

    from pydantic import EmailStr


class CurrentUser(ApiWrapper):
    prefix: str = "/me"

    def logged(self) -> bool:
        # Returns 200 OK and empty response body
        return self._request_and_check_success("GET", f"{self.prefix}/logged")

    def me(self, with_related_data: bool = False) -> MeResponse:
        response_schema = MeResponseWithRelatedData if with_related_data else MeResponse

        return self._request_and_validate(
            "GET",
            self.prefix,
            response_schema,
            params={"with_related_data": with_related_data},
        )

    def update_me(
        self,
        beginning_of_week: Optional[int] = None,
        country_id: Optional[int] = None,
        default_workspace_id: Optional[int] = None,
        email: Optional[EmailStr] = None,
        fullname: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> UpdateMeResponse:
        """Update instance without validating if new value is equal to current one.

        So API request will be sent anyway.
        """
        payload_schema = UpdateMeRequest(
            beginning_of_week=beginning_of_week,
            country_id=country_id,
            default_workspace_id=default_workspace_id,
            email=email,
            fullname=fullname,
            timezone=timezone,
        )
        payload = dump_payload(payload_schema, exclude_unset=True)

        return self._request_and_validate("PUT", self.prefix, UpdateMeResponse, json=payload)

    def change_password(self, current_password: str, new_password: str) -> bool:
        """Validate and change user password.

        API response does not indicate about successful password change,
        that is why return if response is successful.
        """
        payload_schema = UpdateMePasswordRequest(
            current_password=current_password, new_password=new_password
        )
        payload = payload_schema.model_dump_json()

        return self._request_and_check_success("PUT", self.prefix, content=payload)

    def features(self) -> List[MeFeaturesResponse]:
        return self._request_and_validate_list(
            "GET", f"{self.prefix}/features", MeFeaturesResponse
        )

    def preferences(self) -> MePreferencesResponse:
        return self._request_and_validate(
            "GET", f"{self.prefix}/preferences", MePreferencesResponse
        )

    def update_preferences(
        self,
        date_format: Optional[DateFormat] = None,
        duration_format: Optional[DurationFormat] = None,
        time_format: Optional[TimeFormat] = None,
    ) -> bool:
        """Update different formats using pre-defined Enums.

        API documentation is not up to date, available fields to update are found manually.
        """
        payload_schema = UpdateMePreferencesRequest(
            date_format=date_format,
            duration_format=duration_format,
            timeofday_format=time_format,
        )
        payload = payload_schema.model_dump_json(exclude_none=True, exclude_unset=True)

        return self._request_and_check_success(
            "POST", f"{self.prefix}/preferences", content=payload
        )

    def get_time_entry(
        self, time_entry_id: int, meta: bool = False
    ) -> Union[MeTimeEntryResponse, MeTimeEntryWithMetaResponse]:
        """Intentionally use the same schema for requests with `include_sharing=true`.

        Tested responses do not differ from requests with `include_sharing=false`
        that is why there is no `include_sharing` method argument.
        """
        response_schema = MeTimeEntryWithMetaResponse if meta else MeTimeEntryResponse

        return self._request_and_validate(
            "GET",
            f"{self.prefix}/time_entries/{time_entry_id}",
            response_schema,
            params={"meta": meta},
        )

    def get_current_time_entry(self) -> Optional[MeTimeEntryResponse]:
        """Return empty response if there is no running TimeEntry."""
        response = self._request("GET", f"{self.prefix}/time_entries/current")
        response_body = response.json()

        return MeTimeEntryResponse.model_validate(response_body) if response_body else None

    def get_time_entries(
        self,
        meta: bool = False,
        since: Union[int, datetime, None] = None,
        before: Union[str, datetime, None] = None,
        start_date: Union[str, datetime, None] = None,
        end_date: Union[str, datetime, None] = None,
    ) -> List[Union[MeTimeEntryResponse, MeTimeEntryWithMetaResponse]]:
        """Intentionally use the same schema for requests with `include_sharing=true`.

        Tested responses do not differ from requests with `include_sharing=false`
        that is why there is no `include_sharing` method argument.
        """
        payload_schema = MeTimeEntryQueryParams(
            meta=meta,
            since=since,
            before=before,
            start_date=start_date,
            end_date=end_date,
        )
        payload = dump_payload(payload_schema)

        response_schema = MeTimeEntryWithMetaResponse if meta else MeTimeEntryResponse

        return self._request_and_validate_list(
            "GET", f"{self.prefix}/time_entries", response_schema, params=payload
        )

    def get_web_timer(self) -> MeWebTimerResponse:
        return self._request_and_validate("GET", f"{self.prefix}/web-timer", MeWebTimerResponse)

    def get_projects(
        self,
        include_archived: Optional[bool] = None,
        since: Union[int, datetime, None] = None,
    ) -> List[ProjectResponse]:
        payload_schema = MeProjectsQueryParams(include_archived=include_archived, since=since)
        payload = dump_payload(payload_schema)

        return self._request_and_validate_list(
            "GET", f"{self.prefix}/projects", ProjectResponse, params=payload
        )

    def get_paginated_projects(
        self,
        since: Union[int, datetime, None] = None,
        start_project_id: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> List[ProjectResponse]:
        query_params_schema = MePaginatedProjectsQueryParams(
            since=since, start_project_id=start_project_id, per_page=per_page
        )
        query_params = dump_payload(query_params_schema)

        return self._request_and_validate_list(
            "GET", f"{self.prefix}/projects/paginated", ProjectResponse, params=query_params
        )

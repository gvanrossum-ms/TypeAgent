# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from pydantic import BaseModel, Field


class DateVal(BaseModel):
    day: int
    month: int
    year: int


class TimeVal(BaseModel):
    hour: int = Field(description="In 24 hour form")
    minute: int
    seconds: int


class DateTime(BaseModel):
    date: DateVal
    time: TimeVal | None = None


class DateTimeRange(BaseModel):
    start_date: DateTime
    stop_date: DateTime | None = None

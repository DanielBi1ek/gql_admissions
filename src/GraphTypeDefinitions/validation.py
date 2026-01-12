from __future__ import annotations

import datetime
import typing

import strawberry

from . import error_codes as codes


def to_naive_datetime(value: typing.Optional[datetime.datetime]) -> typing.Optional[datetime.datetime]:
    if value is None:
        return None
    if value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return value


def normalize_datetime_field(entity: typing.Any, field_name: str) -> None:
    if not hasattr(entity, field_name):
        return
    value = getattr(entity, field_name)
    if value is None or value is strawberry.UNSET:
        return
    setattr(entity, field_name, to_naive_datetime(value))


def resolve_unset(value: typing.Any, default: typing.Any) -> typing.Any:
    return default if value is strawberry.UNSET else value


def is_digits(value: typing.Optional[str]) -> bool:
    return isinstance(value, str) and value.isdigit()


def build_error(
    error_cls: typing.Any,
    *,
    msg: str,
    code: str,
    location: str,
    input_obj: typing.Any,
) -> typing.Any:
    return error_cls(msg=msg, code=code, location=location, _input=input_obj)


def validate_required(
    value: typing.Any,
    *,
    error_cls: typing.Any,
    location: str,
    input_obj: typing.Any,
    msg: str = "Missing required value",
    code: str = codes.ERR_MISSING_REQUIRED,
) -> typing.Optional[typing.Any]:
    if value is None:
        return build_error(error_cls, msg=msg, code=code, location=location, input_obj=input_obj)
    return None


def validate_numeric(
    value: typing.Any,
    *,
    error_cls: typing.Any,
    location: str,
    input_obj: typing.Any,
    msg: str = "Required amount must be numeric",
    code: str = codes.ERR_REQUIRED_NUMERIC,
) -> typing.Optional[typing.Any]:
    if not isinstance(value, (int, float)):
        return build_error(error_cls, msg=msg, code=code, location=location, input_obj=input_obj)
    return None


def validate_positive(
    value: typing.Any,
    *,
    error_cls: typing.Any,
    location: str,
    input_obj: typing.Any,
    msg: str = "Required amount must be greater than 0",
    code: str = codes.ERR_REQUIRED_POSITIVE,
) -> typing.Optional[typing.Any]:
    if value <= 0:
        return build_error(error_cls, msg=msg, code=code, location=location, input_obj=input_obj)
    return None


def validate_digits(
    value: typing.Any,
    *,
    error_cls: typing.Any,
    location: str,
    input_obj: typing.Any,
    msg: str,
    code: str,
) -> typing.Optional[typing.Any]:
    if not is_digits(value):
        return build_error(error_cls, msg=msg, code=code, location=location, input_obj=input_obj)
    return None


async def validate_fk_exists(
    loader: typing.Any,
    entity_id: typing.Any,
    *,
    error_cls: typing.Any,
    location: str,
    input_obj: typing.Any,
    msg: str,
    code: str,
) -> typing.Optional[typing.Any]:
    entity = await loader.load(entity_id)
    if entity is None:
        return build_error(error_cls, msg=msg, code=code, location=location, input_obj=input_obj)
    return None

from __future__ import annotations
import ipaddress
from typing import Any

from .endpoints import HuduEndpoint
from .constants import (TRUTHY_VALUES,
                        FALSY_VALUES,
                        VLAN_ID_RANGES_PATTERN,
                        FROMABLE_TOABLE_TYPES,
                        ALLOWED_UPLOADABLE_TYPES
                        )

class HuduValidationError(ValueError):
    """Raised when a request payload fails local SDK validation."""

def validate_relatables(fromable_endpoint: str, toable_endpoint: str) -> None:
    if fromable_endpoint not in FROMABLE_TOABLE_TYPES:
        raise HuduValidationError(f"Objects of type {fromable_endpoint} cannot be related to any other objects")

    if toable_endpoint not in FROMABLE_TOABLE_TYPES:
        raise HuduValidationError(f"Objects of type {toable_endpoint} cannot be related to any other objects")

def validate_payload(
    endpoint: HuduEndpoint,
    payload: dict[str, Any],
    operation: str,
    *,
    allow_unknown_fields: bool = False,
) -> None:
    if not isinstance(payload, dict):
        raise HuduValidationError("payload must be a dict")

    meta = endpoint.meta

    if operation == "create" and not meta.supports_create:
        raise HuduValidationError(f"{endpoint.name} does not support create")

    if operation == "update" and not meta.supports_update:
        raise HuduValidationError(f"{endpoint.name} does not support update")

    if operation == "create":
        required_fields = set(meta.create_required_fields or ())
        allowed_fields = set(meta.create_fields.keys() or ())
    elif operation == "update":
        required_fields = set(meta.update_required_fields or ())
        allowed_fields = set(meta.update_fields.keys() or ())
    else:
        raise HuduValidationError(f"Unsupported operation: {operation}")

    if allowed_fields and not allow_unknown_fields:
        unknown_fields = sorted(set(payload.keys()) - allowed_fields)
        if unknown_fields:
            raise HuduValidationError(
                f"Unknown field(s) for {endpoint.name} {operation}: {', '.join(unknown_fields)}"
            )

    missing_required = sorted(
        field_name
        for field_name in required_fields
        if payload.get(field_name) in (None, "")
    )
    if missing_required:
        raise HuduValidationError(
            f"Missing required field(s) for {endpoint.name} {operation}: {', '.join(missing_required)}"
        )

def validate_required_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required and must be a non-empty string")
    return value


def validate_required_int(value: int, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} is required and must be an integer")
    return value


def validate_int_range(value: int, field_name: str, minimum: int, maximum: int) -> int:
    validate_required_int(value, field_name)
    if not (minimum <= value <= maximum):
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return value


def validate_choice(value: str, field_name: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of: {', '.join(sorted(allowed))}")
    return value


def validate_vlan_id(value: int) -> int:
    return validate_int_range(value, "vlan_id", 4, 4094)


def validate_vlan_id_ranges(value: str) -> str:
    validate_required_string(value, "vlan_id_ranges")
    if not VLAN_ID_RANGES_PATTERN.fullmatch(value):
        raise ValueError(
            "vlan_id_ranges must look like '1-4' or '200-300,400-450'"
        )
    return value


def validate_network_address(value: str) -> str:
    validate_required_string(value, "address")
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise ValueError(f"address must be a valid CIDR network: {value}") from exc
    return value


def validate_ip_address(value: str) -> str:
    validate_required_string(value, "address")
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError(f"address must be a valid IP address: {value}") from exc
    return value


def to_bool(value: object, default: bool = False) -> bool:
    try:
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in TRUTHY_VALUES:
            return True
        if s in FALSY_VALUES:
            return False
    except Exception:
        pass

    return default


def validate_uploadable_type(value: str) -> bool:
    uploadable = value in ALLOWED_UPLOADABLE_TYPES
    return uploadable
from __future__ import annotations

from typing import Any

from .endpoints import HuduEndpoint


class HuduValidationError(ValueError):
    """Raised when a request payload fails local SDK validation."""


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
from __future__ import annotations

import json
import keyword
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def safe_ident(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "unnamed"
    if value[0].isdigit():
        value = f"_{value}"
    if keyword.iskeyword(value):
        value = f"{value}_"
    return value


def enum_name_from_path(path: str) -> str:
    name = path.strip("/") or "root"
    name = name.replace("/", "_")
    name = name.replace("{", "").replace("}", "")
    return safe_ident(name).upper()


def resource_name_from_path(path: str) -> str:
    name = re.sub(r"/\{[^}]+\}", "", path.strip("/"))
    name = name.replace("/", "_")
    return safe_ident(name or "root")


def resolve_local_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref or not ref.startswith("#/"):
        return {}

    node: Any = spec
    for part in ref[2:].split("/"):
        if not isinstance(node, dict):
            return {}
        node = node.get(part)
        if node is None:
            return {}

    return deepcopy(node) if isinstance(node, dict) else {}


def merge_object_schemas(parts: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for part in parts:
        if not isinstance(part, dict):
            continue

        if part.get("description") and not merged.get("description"):
            merged["description"] = part["description"]

        if part.get("enum") and not merged.get("enum"):
            merged["enum"] = list(part["enum"])

        if part.get("type") and merged.get("type") in {None, "object"}:
            merged["type"] = part["type"]

        for k, v in (part.get("properties", {}) or {}).items():
            merged["properties"][k] = v

        merged["required"].extend(part.get("required", []) or [])

        # preserve array bits if relevant
        if "items" in part and "items" not in merged:
            merged["items"] = part["items"]

    merged["required"] = list(dict.fromkeys(merged["required"]))
    return merged


def normalize_schema(spec: dict[str, Any], schema: dict[str, Any] | None, seen: set[str] | None = None) -> dict[str, Any]:
    if not schema:
        return {}

    seen = seen or set()
    schema = deepcopy(schema)

    # fully resolve top-level $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen:
            return {"$ref": ref}
        seen.add(ref)

        resolved = resolve_local_ref(spec, ref)
        if not resolved:
            return schema

        resolved = normalize_schema(spec, resolved, seen)

        # keep original ref around for metadata visibility
        if "$ref" not in resolved:
            resolved["$ref"] = ref
        return resolved

    # merge allOf
    if "allOf" in schema:
        normalized_parts = [normalize_schema(spec, part, seen.copy()) for part in schema.get("allOf", []) or []]
        merged = merge_object_schemas(normalized_parts)

        # preserve some top-level metadata too
        if schema.get("description") and not merged.get("description"):
            merged["description"] = schema["description"]
        if schema.get("type") and not merged.get("type"):
            merged["type"] = schema["type"]
        if schema.get("enum") and not merged.get("enum"):
            merged["enum"] = schema["enum"]

        return merged

    # normalize array items
    if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        schema["items"] = normalize_schema(spec, schema["items"], seen.copy())

    # normalize object properties
    if schema.get("type") == "object":
        props = schema.get("properties", {}) or {}
        schema["properties"] = {
            key: normalize_schema(spec, child, seen.copy())
            for key, child in props.items()
        }

    # normalize any inline refs inside properties even without explicit type=object
    elif "properties" in schema:
        props = schema.get("properties", {}) or {}
        schema["properties"] = {
            key: normalize_schema(spec, child, seen.copy())
            for key, child in props.items()
        }

    return schema


def schema_to_fieldmeta_dict(
    spec: dict[str, Any],
    name: str,
    schema: dict[str, Any],
    *,
    required: bool = False,
    location: str | None = None,
) -> dict[str, Any]:
    if not schema:
        return {
            "name": name,
            "type": None,
            "required": required,
            "location": location,
            "description": None,
            "enum": (),
            "item_type": None,
            "ref": None,
            "properties": {},
        }

    original_ref = schema.get("$ref")
    schema = normalize_schema(spec, schema)

    ref = original_ref or schema.get("$ref")
    field_type = schema.get("type")
    enum = tuple(schema.get("enum", []) or [])
    description = schema.get("description")
    item_type = None
    properties: dict[str, Any] = {}

    if field_type == "array":
        items = normalize_schema(spec, schema.get("items", {}) or {})
        item_type = items.get("type") or items.get("$ref")

        if items.get("type") == "object" or items.get("properties"):
            nested_required = set(items.get("required", []) or [])
            for child_name, child_schema in (items.get("properties", {}) or {}).items():
                properties[child_name] = schema_to_fieldmeta_dict(
                    spec,
                    child_name,
                    child_schema,
                    required=child_name in nested_required,
                )

    elif field_type == "object" or schema.get("properties"):
        nested_required = set(schema.get("required", []) or [])
        for child_name, child_schema in (schema.get("properties", {}) or {}).items():
            properties[child_name] = schema_to_fieldmeta_dict(
                spec,
                child_name,
                child_schema,
                required=child_name in nested_required,
            )

    return {
        "name": name,
        "type": field_type,
        "required": required,
        "location": location,
        "description": description,
        "enum": enum,
        "item_type": item_type,
        "ref": ref,
        "properties": properties,
    }


def unwrap_wrapped_body_schema(
    spec: dict[str, Any],
    schema: dict[str, Any],
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """
    Handles:
    1. direct object bodies
    2. wrapped bodies like {"photo": {...}}
    3. $ref/allOf-based bodies after normalization
    """
    if not schema:
        return {}, ()

    schema = normalize_schema(spec, schema)
    props = schema.get("properties", {}) or {}
    required = tuple(schema.get("required", []) or [])

    # If direct object fields exist, use them
    if props:
        # unwrap single wrapper object like {"photo": {...}}
        if len(props) == 1:
            _, only_val = next(iter(props.items()))
            only_val = normalize_schema(spec, only_val)
            inner_props = only_val.get("properties", {}) or {}
            inner_required = tuple(only_val.get("required", []) or [])
            if inner_props:
                return inner_props, inner_required

        return props, required

    # array / primitive / unresolved schema: no field map available
    return {}, ()


def extract_response_ref(spec: dict[str, Any], schema: dict[str, Any]) -> str | None:
    if not schema:
        return None

    if "$ref" in schema:
        return schema["$ref"]

    normalized = normalize_schema(spec, schema)

    if "$ref" in normalized:
        return normalized["$ref"]

    props = normalized.get("properties", {}) or {}
    for _, prop in props.items():
        if isinstance(prop, dict):
            if "$ref" in prop:
                return prop["$ref"]
            if prop.get("type") == "array":
                items = prop.get("items", {}) or {}
                if "$ref" in items:
                    return items["$ref"]

    return None


def get_request_body_schema_and_content_types(
    spec: dict[str, Any],
    operation: dict[str, Any],
) -> tuple[dict[str, Any], tuple[str, ...]]:
    # OpenAPI 3.x
    request_body = operation.get("requestBody", {}) or {}
    if request_body:
        if "$ref" in request_body:
            request_body = normalize_schema(spec, request_body)

        content = request_body.get("content", {}) or {}
        if content:
            preferred_type = (
                "application/json"
                if "application/json" in content
                else "multipart/form-data"
                if "multipart/form-data" in content
                else "application/x-www-form-urlencoded"
                if "application/x-www-form-urlencoded" in content
                else next(iter(content.keys()))
            )
            media = content.get(preferred_type, {}) or {}
            return media.get("schema", {}) or {}, tuple(content.keys())

    # Swagger 2 fallback handled elsewhere
    return {}, ()


def parse_operation(spec: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    path_params: dict[str, Any] = {}
    query_params: dict[str, Any] = {}
    form_params: dict[str, Any] = {}
    body_fields: dict[str, Any] = {}
    body_required: tuple[str, ...] = ()
    content_types: set[str] = set()

    for param in operation.get("parameters", []) or []:
        if "$ref" in param:
            param = normalize_schema(spec, param)

        pin = param.get("in")
        name = param.get("name", "body")
        required = bool(param.get("required"))

        if pin in {"path", "query", "formData"}:
            field_schema = param.get("schema", param)
            field = schema_to_fieldmeta_dict(
                spec,
                name,
                field_schema,
                required=required,
                location=pin,
            )
            if pin == "path":
                path_params[name] = field
            elif pin == "query":
                query_params[name] = field
            elif pin == "formData":
                form_params[name] = field

        elif pin == "body":
            schema = param.get("schema", {}) or {}
            props, req = unwrap_wrapped_body_schema(spec, schema)
            body_required = req
            for field_name, field_schema in props.items():
                body_fields[field_name] = schema_to_fieldmeta_dict(
                    spec,
                    field_name,
                    field_schema,
                    required=field_name in set(req),
                    location="body",
                )

    # OpenAPI 3 requestBody support
    if not body_fields:
        request_schema, request_content_types = get_request_body_schema_and_content_types(spec, operation)
        if request_schema:
            props, req = unwrap_wrapped_body_schema(spec, request_schema)
            body_required = req
            for field_name, field_schema in props.items():
                body_fields[field_name] = schema_to_fieldmeta_dict(
                    spec,
                    field_name,
                    field_schema,
                    required=field_name in set(req),
                    location="body",
                )
            content_types.update(request_content_types)

    response_ref = None
    for _, response in (operation.get("responses", {}) or {}).items():
        response = response or {}

        # Swagger 2
        schema = response.get("schema", {}) or {}
        response_ref = extract_response_ref(spec, schema)
        if response_ref:
            break

        # OpenAPI 3
        content = response.get("content", {}) or {}
        for _, media in content.items():
            if not isinstance(media, dict):
                continue
            schema = media.get("schema", {}) or {}
            response_ref = extract_response_ref(spec, schema)
            if response_ref:
                break
        if response_ref:
            break

    # Swagger 2 consumes
    content_types.update(operation.get("consumes", []) or [])

    return {
        "path_params": path_params,
        "query_params": query_params,
        "form_params": form_params,
        "body_fields": body_fields,
        "body_required": body_required,
        "response_ref": response_ref,
        "content_types": tuple(sorted(content_types)),
        "operation_id": operation.get("operationId"),
    }


def build_endpoint_meta(spec: dict[str, Any], path: str, path_item: dict[str, Any]) -> dict[str, Any]:
    methods_present = tuple(m.upper() for m in path_item if m in HTTP_METHODS)

    tag = None
    for m in HTTP_METHODS:
        if m in path_item:
            tags = path_item[m].get("tags") or []
            tag = tags[0] if tags else None
            break

    path_params: dict[str, Any] = {}
    query_params: dict[str, Any] = {}
    form_params: dict[str, Any] = {}
    create_fields: dict[str, Any] = {}
    update_fields: dict[str, Any] = {}
    create_required_fields: tuple[str, ...] = ()
    update_required_fields: tuple[str, ...] = ()
    operation_ids: dict[str, str] = {}
    response_refs: dict[str, str] = {}
    content_types: set[str] = set()

    for method in HTTP_METHODS:
        operation = path_item.get(method)
        if not operation:
            continue

        parsed = parse_operation(spec, operation)

        path_params.update(parsed["path_params"])
        query_params.update(parsed["query_params"])
        form_params.update(parsed["form_params"])
        content_types.update(parsed["content_types"])

        if parsed["operation_id"]:
            operation_ids[method.upper()] = parsed["operation_id"]
        if parsed["response_ref"]:
            response_refs[method.upper()] = parsed["response_ref"]

        if method == "post":
            if parsed["body_fields"]:
                create_fields = parsed["body_fields"]
                create_required_fields = parsed["body_required"]
            elif parsed["form_params"]:
                create_fields = parsed["form_params"]
                create_required_fields = tuple(
                    name for name, meta in parsed["form_params"].items() if meta["required"]
                )

        elif method in {"put", "patch"}:
            if parsed["body_fields"]:
                update_fields = parsed["body_fields"]
                update_required_fields = parsed["body_required"]
            elif parsed["form_params"]:
                update_fields = parsed["form_params"]
                update_required_fields = tuple(
                    name for name, meta in parsed["form_params"].items() if meta["required"]
                )

    is_collection_get = "get" in path_item and "{" not in path
    supports_archive = path.endswith("/archive") and "put" in path_item
    supports_unarchive = path.endswith("/unarchive") and "put" in path_item

    special_non_paginated = {
        "api_info",
        "cards_lookup",
        "cards_jump",
        "companies_jump",
        "exports",
        "s3_exports",
    }

    resource_name = resource_name_from_path(path)
    is_paginated = is_collection_get and resource_name not in special_non_paginated

    return {
        "path": path.strip("/"),
        "resource_name": resource_name,
        "tag": tag,
        "is_paginated": is_paginated,
        "company_scoped": "{company_id}" in path,
        "content_types": tuple(sorted(content_types)),
        "methods": methods_present,
        "supports_list": is_collection_get,
        "supports_get": "get" in path_item,
        "supports_create": "post" in path_item and not supports_archive and not supports_unarchive,
        "supports_update": ("put" in path_item or "patch" in path_item) and not supports_archive and not supports_unarchive,
        "supports_delete": "delete" in path_item,
        "supports_archive": supports_archive,
        "supports_unarchive": supports_unarchive,
        "path_params": path_params,
        "query_params": query_params,
        "form_params": form_params,
        "create_fields": create_fields,
        "update_fields": update_fields,
        "create_required_fields": create_required_fields,
        "update_required_fields": update_required_fields,
        "operation_ids": operation_ids,
        "response_refs": response_refs,
    }
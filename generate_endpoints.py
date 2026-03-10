from __future__ import annotations

import json
import keyword
import re
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


def schema_to_fieldmeta_dict(
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

    ref = schema.get("$ref")
    field_type = schema.get("type")
    enum = tuple(schema.get("enum", []) or [])
    description = schema.get("description")
    item_type = None
    properties: dict[str, Any] = {}

    if field_type == "array":
        items = schema.get("items", {}) or {}
        item_type = items.get("type") or items.get("$ref")
        if items.get("type") == "object":
            nested_required = set(items.get("required", []) or [])
            for child_name, child_schema in (items.get("properties", {}) or {}).items():
                properties[child_name] = schema_to_fieldmeta_dict(
                    child_name,
                    child_schema,
                    required=child_name in nested_required,
                )

    elif field_type == "object":
        nested_required = set(schema.get("required", []) or [])
        for child_name, child_schema in (schema.get("properties", {}) or {}).items():
            properties[child_name] = schema_to_fieldmeta_dict(
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


def unwrap_wrapped_body_schema(schema: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    """
    Handles patterns like:
    {
      "type": "object",
      "properties": {
        "photo": {
          "type": "object",
          "properties": {...}
        }
      }
    }
    """
    if not schema:
        return {}, ()

    props = schema.get("properties", {}) or {}
    required = tuple(schema.get("required", []) or [])

    if len(props) == 1:
        _, only_val = next(iter(props.items()))
        if isinstance(only_val, dict) and only_val.get("type") == "object":
            inner_props = only_val.get("properties", {}) or {}
            inner_required = tuple(only_val.get("required", []) or [])
            if inner_props:
                return inner_props, inner_required

    return props, required


def extract_response_ref(schema: dict[str, Any]) -> str | None:
    if not schema:
        return None

    if "$ref" in schema:
        return schema["$ref"]

    props = schema.get("properties", {}) or {}
    for _, prop in props.items():
        if isinstance(prop, dict):
            if "$ref" in prop:
                return prop["$ref"]
            if prop.get("type") == "array":
                items = prop.get("items", {}) or {}
                if "$ref" in items:
                    return items["$ref"]

    return None


def parse_operation(operation: dict[str, Any]) -> dict[str, Any]:
    path_params: dict[str, Any] = {}
    query_params: dict[str, Any] = {}
    form_params: dict[str, Any] = {}
    body_fields: dict[str, Any] = {}
    body_required: tuple[str, ...] = ()

    for param in operation.get("parameters", []) or []:
        pin = param.get("in")
        name = param.get("name", "body")
        required = bool(param.get("required"))

        if pin in {"path", "query", "formData"}:
            field = schema_to_fieldmeta_dict(
                name,
                param,
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
            props, req = unwrap_wrapped_body_schema(schema)
            body_required = req
            for field_name, field_schema in props.items():
                body_fields[field_name] = schema_to_fieldmeta_dict(
                    field_name,
                    field_schema,
                    required=field_name in set(req),
                    location="body",
                )

    response_ref = None
    for _, response in (operation.get("responses", {}) or {}).items():
        schema = (response or {}).get("schema", {}) or {}
        response_ref = extract_response_ref(schema)
        if response_ref:
            break

    return {
        "path_params": path_params,
        "query_params": query_params,
        "form_params": form_params,
        "body_fields": body_fields,
        "body_required": body_required,
        "response_ref": response_ref,
        "content_types": tuple(operation.get("consumes", []) or []),
        "operation_id": operation.get("operationId"),
    }


def build_endpoint_meta(path: str, path_item: dict[str, Any]) -> dict[str, Any]:
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

        parsed = parse_operation(operation)

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

    # Small heuristic for Hudu
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


def render_fieldmeta_expr(meta: dict[str, Any], indent: int = 0) -> str:
    sp = " " * indent
    return (
        "FieldMeta(\n"
        f"{sp}    name={meta['name']!r},\n"
        f"{sp}    type={meta['type']!r},\n"
        f"{sp}    required={meta['required']!r},\n"
        f"{sp}    location={meta['location']!r},\n"
        f"{sp}    description={meta['description']!r},\n"
        f"{sp}    enum={meta['enum']!r},\n"
        f"{sp}    item_type={meta['item_type']!r},\n"
        f"{sp}    ref={meta['ref']!r},\n"
        f"{sp}    properties={render_fieldmeta_dict(meta['properties'], indent + 4)},\n"
        f"{sp})"
    )


def render_fieldmeta_dict(items: dict[str, Any], indent: int = 0) -> str:
    sp = " " * indent
    if not items:
        return "{}"
    parts = []
    for key, meta in items.items():
        parts.append(f"{sp}    {key!r}: {render_fieldmeta_expr(meta, indent + 4)}")
    return "{\n" + ",\n".join(parts) + f"\n{sp}}}"


def render_endpoint_meta_expr(meta: dict[str, Any], indent: int = 0) -> str:
    sp = " " * indent
    return (
        "EndpointMeta(\n"
        f"{sp}    path={meta['path']!r},\n"
        f"{sp}    resource_name={meta['resource_name']!r},\n"
        f"{sp}    tag={meta['tag']!r},\n"
        f"{sp}    is_paginated={meta['is_paginated']!r},\n"
        f"{sp}    company_scoped={meta['company_scoped']!r},\n"
        f"{sp}    content_types={meta['content_types']!r},\n"
        f"{sp}    methods={meta['methods']!r},\n"
        f"{sp}    supports_list={meta['supports_list']!r},\n"
        f"{sp}    supports_get={meta['supports_get']!r},\n"
        f"{sp}    supports_create={meta['supports_create']!r},\n"
        f"{sp}    supports_update={meta['supports_update']!r},\n"
        f"{sp}    supports_delete={meta['supports_delete']!r},\n"
        f"{sp}    supports_archive={meta['supports_archive']!r},\n"
        f"{sp}    supports_unarchive={meta['supports_unarchive']!r},\n"
        f"{sp}    path_params={render_fieldmeta_dict(meta['path_params'], indent + 4)},\n"
        f"{sp}    query_params={render_fieldmeta_dict(meta['query_params'], indent + 4)},\n"
        f"{sp}    form_params={render_fieldmeta_dict(meta['form_params'], indent + 4)},\n"
        f"{sp}    create_fields={render_fieldmeta_dict(meta['create_fields'], indent + 4)},\n"
        f"{sp}    update_fields={render_fieldmeta_dict(meta['update_fields'], indent + 4)},\n"
        f"{sp}    create_required_fields={meta['create_required_fields']!r},\n"
        f"{sp}    update_required_fields={meta['update_required_fields']!r},\n"
        f"{sp}    operation_ids={meta['operation_ids']!r},\n"
        f"{sp}    response_refs={meta['response_refs']!r},\n"
        f"{sp})"
    )


def generate_enum_module(spec_path: str, out_path: str) -> None:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    paths = spec.get("paths", {}) or {}

    entries: list[tuple[str, dict[str, Any]]] = []
    for path, path_item in sorted(paths.items()):
        entries.append((enum_name_from_path(path), build_endpoint_meta(path, path_item)))

    lines = [
        "from __future__ import annotations",
        "",
        "# -----------------------------------------------------------",
        "# THIS FILE IS AUTO-GENERATED FROM THE OPENAPI JSON SPEC.",
        "# DO NOT EDIT MANUALLY.",
        "# -----------------------------------------------------------",
        "",
        "from dataclasses import dataclass, field",
        "from enum import Enum",
        "",
        "",
        "@dataclass(frozen=True)",
        "class FieldMeta:",
        "    name: str",
        "    type: str | None = None",
        "    required: bool = False",
        "    location: str | None = None",
        "    description: str | None = None",
        "    enum: tuple[str, ...] = ()",
        "    item_type: str | None = None",
        "    ref: str | None = None",
        "    properties: dict[str, 'FieldMeta'] = field(default_factory=dict)",
        "",
        "",
        "@dataclass(frozen=True)",
        "class EndpointMeta:",
        "    path: str",
        "    resource_name: str",
        "    tag: str | None = None",
        "    is_paginated: bool = False",
        "    company_scoped: bool = False",
        "    content_types: tuple[str, ...] = ()",
        "    methods: tuple[str, ...] = ()",
        "    supports_list: bool = False",
        "    supports_get: bool = False",
        "    supports_create: bool = False",
        "    supports_update: bool = False",
        "    supports_delete: bool = False",
        "    supports_archive: bool = False",
        "    supports_unarchive: bool = False",
        "    path_params: dict[str, FieldMeta] = field(default_factory=dict)",
        "    query_params: dict[str, FieldMeta] = field(default_factory=dict)",
        "    form_params: dict[str, FieldMeta] = field(default_factory=dict)",
        "    create_fields: dict[str, FieldMeta] = field(default_factory=dict)",
        "    update_fields: dict[str, FieldMeta] = field(default_factory=dict)",
        "    create_required_fields: tuple[str, ...] = ()",
        "    update_required_fields: tuple[str, ...] = ()",
        "    operation_ids: dict[str, str] = field(default_factory=dict)",
        "    response_refs: dict[str, str] = field(default_factory=dict)",
        "",
        "",
        "class HuduEndpoint(Enum):",
    ]

    for name, meta in entries:
        lines.append(f"    {name} = {render_endpoint_meta_expr(meta, 4)}")

    lines.extend(
        [
            "",
            "    def __init__(self, meta: EndpointMeta):",
            "        self.meta = meta",
            "        self.endpoint = meta.path",
            "        self.path = '/' + meta.path if meta.path else '/'",
            "        self.resource_name = meta.resource_name",
            "        self.is_paginated = meta.is_paginated",
            "",
            "    def item_path(self, item_id: int | str) -> str:",
            "        return f'/{self.endpoint}/{item_id}'",
            "",
            "    def __str__(self) -> str:",
            "        return self.endpoint",
            "",
        ]
    )

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_enum_module(
        spec_path="hudu-openapiv1.json",
        out_path="src/hudu_magic/endpoints.py",
    )
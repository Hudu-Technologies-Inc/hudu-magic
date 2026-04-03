import json
import re
from pathlib import Path
from pprint import pformat


def normalize_resource_name(path: str) -> str:
    path = path.strip("/")
    path = re.sub(r"\{[^}]+\}", "", path)
    path = path.replace("//", "/").strip("/")
    return path.replace("/", "_") or "root"


def enum_name_for_path(path: str) -> str:
    name = normalize_resource_name(path)
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name.upper()


def unwrap_body_schema(schema: dict) -> tuple[dict, tuple[str, ...]]:
    """
    Handles common Hudu patterns like:
      {"type":"object","properties":{"article":{...}}}
      {"type":"object","properties":{...}}
    Returns (properties_dict, required_tuple)
    """
    if not schema:
        return {}, ()

    props = schema.get("properties", {}) or {}
    required = tuple(schema.get("required", []) or [])

    # unwrap single wrapper object like {"article": {"type":"object", ...}}
    if len(props) == 1:
        only_key, only_val = next(iter(props.items()))
        if isinstance(only_val, dict) and only_val.get("type") == "object":
            inner_props = only_val.get("properties", {}) or {}
            inner_required = tuple(only_val.get("required", []) or [])
            if inner_props:
                return inner_props, inner_required

    return props, required


def schema_to_fieldmeta(name: str, schema: dict, *, required: bool = False, location: str | None = None):
    field_type = schema.get("type")
    enum_vals = tuple(schema.get("enum", []) or [])
    description = schema.get("description")

    item_type = None
    nested_properties = {}

    if field_type == "array":
        items = schema.get("items", {}) or {}
        item_type = items.get("type") or items.get("$ref")
        if items.get("type") == "object":
            nested_required = set(items.get("required", []) or [])
            for child_name, child_schema in (items.get("properties", {}) or {}).items():
                nested_properties[child_name] = schema_to_fieldmeta(
                    child_name,
                    child_schema,
                    required=child_name in nested_required,
                )

    elif field_type == "object":
        nested_required = set(schema.get("required", []) or [])
        for child_name, child_schema in (schema.get("properties", {}) or {}).items():
            nested_properties[child_name] = schema_to_fieldmeta(
                child_name,
                child_schema,
                required=child_name in nested_required,
            )

    return {
        "name": name,
        "type": field_type or schema.get("$ref"),
        "required": required,
        "location": location,
        "enum": enum_vals,
        "description": description,
        "item_type": item_type,
        "properties": nested_properties,
    }


def collect_params(operation: dict):
    path_params = {}
    query_params = {}
    body_props = {}
    body_required = ()

    for param in operation.get("parameters", []) or []:
        pin = param.get("in")
        name = param.get("name", "body")

        if pin in {"query", "path", "formData"}:
            fm = schema_to_fieldmeta(
                name,
                param,
                required=bool(param.get("required")),
                location=pin,
            )
            if pin == "path":
                path_params[name] = fm
            else:
                query_params[name] = fm

        elif pin == "body":
            schema = param.get("schema", {}) or {}
            body_props, body_required = unwrap_body_schema(schema)

    return path_params, query_params, body_props, body_required


def build_meta_for_path(path: str, path_item: dict) -> dict:
    methods_present = tuple(m.upper() for m in path_item.keys() if m.lower() in {"get", "post", "put", "delete", "patch"})
    tag = None
    if "get" in path_item:
        tag = (path_item["get"].get("tags") or [None])[0]
    elif "post" in path_item:
        tag = (path_item["post"].get("tags") or [None])[0]

    path_params = {}
    query_params = {}
    create_fields = {}
    update_fields = {}
    create_required = ()
    update_required = ()
    operation_ids = {}
    content_types = set()
    response_ref = None

    for method_name in ("get", "post", "put", "delete"):
        op = path_item.get(method_name)
        if not op:
            continue

        operation_ids[method_name.upper()] = op.get("operationId", "")
        content_types.update(op.get("consumes", []) or [])

        pp, qp, body_props, body_required = collect_params(op)

        path_params.update(pp)
        query_params.update(qp)

        if method_name == "post":
            create_fields = body_props
            create_required = body_required
        elif method_name == "put":
            update_fields = body_props
            update_required = body_required

        # best-effort response ref extraction
        for code, resp in (op.get("responses", {}) or {}).items():
            schema = (resp or {}).get("schema", {}) or {}
            if "$ref" in schema:
                response_ref = schema["$ref"]
                break
            props = schema.get("properties", {}) or {}
            for _, prop in props.items():
                if isinstance(prop, dict) and "$ref" in prop:
                    response_ref = prop["$ref"]
                    break
            if response_ref:
                break

    is_collection = "get" in path_item and "{" not in path
    is_item = "get" in path_item and "{" in path and not path.endswith("/archive") and not path.endswith("/unarchive")
    supports_archive = "/archive" in path and "put" in path_item
    supports_unarchive = "/unarchive" in path and "put" in path_item

    # Hudu-specific heuristic:
    # list endpoints with GET + no path vars are the usual paginated ones
    # action/special endpoints should not be auto-paginated
    is_paginated = (
        is_collection
        and path not in {"/api_info", "/cards/jump", "/cards/lookup", "/exports/{id}"}
    )

    return {
        "path": path.strip("/"),
        "resource_name": normalize_resource_name(path),
        "tag": tag,
        "is_paginated": is_paginated,
        "company_scoped": "{company_id}" in path,
        "content_types": tuple(sorted(content_types)),
        "methods": methods_present,
        "supports_list": is_collection,
        "supports_get": "get" in path_item,
        "supports_create": "post" in path_item and not supports_archive and not supports_unarchive,
        "supports_update": "put" in path_item and not supports_archive and not supports_unarchive,
        "supports_delete": "delete" in path_item,
        "supports_archive": supports_archive,
        "supports_unarchive": supports_unarchive,
        "path_params": path_params,
        "query_params": query_params,
        "create_fields": create_fields,
        "update_fields": update_fields,
        "create_required_fields": create_required,
        "update_required_fields": update_required,
        "response_ref": response_ref,
        "operation_ids": operation_ids,
    }


def generate_endpoint_meta(spec_path: str) -> dict[str, dict]:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    paths = spec.get("paths", {}) or {}

    result = {}
    for path, path_item in sorted(paths.items()):
        enum_name = enum_name_for_path(path)
        result[enum_name] = build_meta_for_path(path, path_item)
    return result


if __name__ == "__main__":
    metas = generate_endpoint_meta("hudu-openapiv1.json")
    print(pformat(metas, width=120, sort_dicts=False))
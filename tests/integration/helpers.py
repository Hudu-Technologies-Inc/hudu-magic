from __future__ import annotations


def extract_id(result):
    if isinstance(result, dict):
        if "id" in result:
            return result["id"]

        for value in result.values():
            if isinstance(value, dict) and "id" in value:
                return value["id"]

    raise AssertionError(f"Could not find id in result: {result!r}")


def get_nested_value(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            if isinstance(value, dict):
                nested = get_nested_value(value, key)
                if nested is not None:
                    return nested
    return None
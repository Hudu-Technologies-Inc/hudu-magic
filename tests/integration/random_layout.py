from __future__ import annotations
import random
import uuid


SAFE_FIELD_TYPES = [
    "Text",
    "Number",
    "CheckBox",
    "Website",
    "Email",
    "Phone",
    "Date",
    "RichText",
    "Heading",
    "Password",
]


def random_field(i: int) -> dict:
    field = {
        "label": f"SDK Field {i + 1}",
        "field_type": random.choice(SAFE_FIELD_TYPES),
        "position": i + 1,
    }

    if random.choice([True, False]):
        field["required"] = random.choice([True, False])

    if random.choice([True, False]):
        field["show_in_list"] = random.choice([True, False])

    return field


def random_asset_layout_payload() -> dict:
    field_count = random.randint(8, 12)
    fields = [random_field(i) for i in range(field_count)]

    return {
        "asset_layout": {
            "name": f"SDK TEST Layout {uuid.uuid4()}",
            "icon": "fas fa-server",
            "color": "#00AEEF",
            "icon_color": "#FFFFFF",
            "fields": fields,
            "include_passwords": random.choice([True, False]),
            "include_photos": random.choice([True, False]),
            "include_comments": random.choice([True, False]),
            "include_files": random.choice([True, False]),
        }
    }

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
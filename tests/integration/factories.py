# tests/integration/factories.py
from __future__ import annotations
import random
import uuid
from hudu_magic.helpers.general import ensure_https

from hudu_magic.constants import FIELD_TYPES

ASSET_LAYOUT_FIELD_TYPES = [
    t for t in FIELD_TYPES
    if t != "Heading"
]

def website_payload(company_id: int) -> dict:
    return {
        "company_id": company_id,
        "name": ensure_https(unique_name("SDK TEST Website")),
        "notes": "Created by integration test",
        "paused": False,
        "disable_dns": True,
        "disable_ssl": True,
        "disable_whois": True,
    }



def unique_name(prefix: str) -> str:
    return f"{prefix} {uuid.uuid4()}"


def company_payload() -> dict:
    return {
        "name": unique_name("SDK TEST Company"),
        "website": "https://example.com",
        "notes": "Created by integration test",
    }


def company_update_payload() -> dict:
    return {
        "notes": "Updated by integration test",
    }


def article_payload(company_id: int | None = None, folder_id: int | None = None) -> dict:
    payload = {
        "name": unique_name("SDK TEST Article"),
        "content": "<p>Hello from integration test</p>",
    }
    if company_id is not None:
        payload["company_id"] = company_id
    if folder_id is not None:
        payload["folder_id"] = folder_id
    return payload


def article_update_payload() -> dict:
    return {
        "content": "<p>Updated from integration test</p>",
    }


def asset_layout_payload() -> dict:
    field_count = random.randint(8, 12)

    fields = []
    for i in range(field_count):
        field = {
            "label": f"SDK Field {i + 1}",
            "field_type": random.choice([F for F in FIELD_TYPES if F != "Heading"]),
            "position": i + 1,
        }
        if random.choice([True, False]):
            field["required"] = random.choice([True, False])
        if random.choice([True, False]):
            field["show_in_list"] = random.choice([True, False])
        fields.append(field)

    return {
        "name": unique_name("SDK TEST Layout"),
        "icon": "fas fa-server",
        "color": "#00AEEF",
        "icon_color": "#FFFFFF",
        "fields": fields,
    }


def asset_layout_update_payload() -> dict:
    return {
        "icon": "fas fa-network-wired",
        "color": "#228B22",
    }


def folder_payload(company_id: int | None = None) -> dict:
    payload = {
        "name": unique_name("SDK TEST Folder"),
        "icon": "fas fa-folder",
        "description": "Created by integration test",
    }
    if company_id is not None:
        payload["company_id"] = company_id
    return payload


def folder_update_payload() -> dict:
    return {
        "description": "Updated by integration test",
    }



def website_update_payload() -> dict:
    return {
        "notes": "Updated by integration test",
        "paused": True,
    }

def asset_layout_update_payload_from_created(created: dict) -> dict:
    layout = created.get("asset_layout", created)

    return {
        "name": layout.get("name"),
        "icon": "fas fa-network-wired",
        "color": "#228B22",
        "icon_color": layout.get("icon_color", "#FFFFFF"),
        "fields": layout.get("fields", []),
        "include_passwords": layout.get("include_passwords", False),
        "include_photos": layout.get("include_photos", False),
        "include_comments": layout.get("include_comments", False),
        "include_files": layout.get("include_files", False),
    }
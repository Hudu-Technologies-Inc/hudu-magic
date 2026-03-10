# tests/integration/factories.py
from __future__ import annotations

import random
import uuid


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
    field_types = ["Text", "Number", "CheckBox", "Website", "Email", "Phone", "Date", "RichText", "Heading", "Password"]
    field_count = random.randint(8, 12)

    fields = []
    for i in range(field_count):
        field = {
            "label": f"SDK Field {i + 1}",
            "field_type": random.choice(field_types),
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


def website_payload(company_id: int) -> dict:
    return {
        "company_id": company_id,
        "name": unique_name("SDK TEST Website"),
        "notes": "Created by integration test",
        "paused": False,
        "disable_dns": True,
        "disable_ssl": True,
        "disable_whois": True,
    }


def website_update_payload() -> dict:
    return {
        "notes": "Updated by integration test",
        "paused": True,
    }
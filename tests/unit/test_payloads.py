"""Request body shaping for the Hudu API."""

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.payloads import (
    maybe_wrap_payload,
    normalize_asset_number_field_value,
    normalize_asset_payload_for_save,
    normalize_asset_website_field_value,
    transform_asset_fields_for_save,
)


def test_maybe_wrap_procedures_create_is_flat():
    """Hudu 2.39.6+ expects flat JSON for procedures create/update, not a ``procedure`` root."""
    payload = {"name": "Test", "company_id": 1}
    assert maybe_wrap_payload(HuduEndpoint.PROCEDURES, payload) == payload


def test_maybe_wrap_procedures_id_update_is_flat():
    payload = {"name": "Renamed"}
    assert maybe_wrap_payload(HuduEndpoint.PROCEDURES_ID, payload) == payload


def test_maybe_wrap_procedure_tasks_still_nested():
    payload = {"name": "Step", "procedure_id": 1}
    assert maybe_wrap_payload(HuduEndpoint.PROCEDURE_TASKS, payload) == {
        "procedure_task": payload,
    }


def test_maybe_wrap_exports_create_nested():
    payload = {
        "format": "pdf",
        "company_id": 1,
        "include_passwords": True,
        "include_websites": True,
    }
    assert maybe_wrap_payload(HuduEndpoint.EXPORTS, payload) == {"export": payload}


def test_maybe_wrap_exports_idempotent_when_already_wrapped():
    payload = {"export": {"format": "csv", "company_id": 2}}
    assert maybe_wrap_payload(HuduEndpoint.EXPORTS, payload) == payload


def test_normalize_asset_website_field_value():
    assert normalize_asset_website_field_value(None) is None
    assert normalize_asset_website_field_value(1) == 1
    assert normalize_asset_website_field_value("") == ""
    assert normalize_asset_website_field_value("  ") == ""
    assert normalize_asset_website_field_value("example.com") == "https://example.com"
    assert normalize_asset_website_field_value("HTTP://X.com/y") == "https://X.com/y"
    assert normalize_asset_website_field_value("https://ok") == "https://ok"


def test_normalize_asset_number_field_value():
    assert normalize_asset_number_field_value(None) is None
    assert normalize_asset_number_field_value(True) is True
    assert normalize_asset_number_field_value(7) == 7
    assert normalize_asset_number_field_value(1.0) == 1
    assert normalize_asset_number_field_value(2.6) == 3
    assert normalize_asset_number_field_value(" 42 ") == 42
    assert normalize_asset_number_field_value("99.0") == 99
    assert normalize_asset_number_field_value("not-a-number") == "not-a-number"
    nan = float("nan")
    assert normalize_asset_number_field_value(nan) is nan
    inf = float("inf")
    assert normalize_asset_number_field_value(inf) is inf


def test_transform_asset_fields_for_save_normalizes_website_when_field_type_set():
    out = transform_asset_fields_for_save(
        [
            {
                "label": "Portal",
                "field_type": "Website",
                "value": "wiki.internal",
            },
            {
                "label": "Plain",
                "field_type": "Text",
                "value": "wiki.internal",
            },
        ]
    )
    assert out == [
        {"portal": "https://wiki.internal"},
        {"plain": "wiki.internal"},
    ]


def test_normalize_asset_payload_for_save_applies_website_via_fields():
    payload = normalize_asset_payload_for_save(
        {
            "name": "Host",
            "company_id": 1,
            "asset_layout_id": 2,
            "fields": [
                {"label": "Docs", "field_type": "Website", "value": "http://docs.example"},
            ],
        }
    )
    assert payload["custom_fields"] == [{"docs": "https://docs.example"}]


def test_transform_asset_fields_for_save_normalizes_number_when_field_type_set():
    out = transform_asset_fields_for_save(
        [
            {"label": "Qty", "field_type": "Number", "value": 3.0},
            {"label": "Port", "field_type": "Number", "value": "8080"},
            {"label": "Note", "field_type": "Text", "value": "1.0"},
        ]
    )
    assert out == [
        {"qty": 3},
        {"port": 8080},
        {"note": "1.0"},
    ]


def test_normalize_asset_payload_for_save_applies_number_via_fields():
    payload = normalize_asset_payload_for_save(
        {
            "name": "Srv",
            "company_id": 1,
            "asset_layout_id": 2,
            "fields": [
                {"label": "Rack Unit", "field_type": "Number", "value": 12.0},
            ],
        }
    )
    assert payload["custom_fields"] == [{"rack_unit": 12}]

"""Unit tests for :mod:`hudu_magic.helpers.asset_layouts`."""

from unittest.mock import MagicMock

import pytest

from hudu_magic.constants import LIST_SELECT_FIELD_TYPE
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.helpers.asset_layouts import (
    collect_list_ids_from_layouts,
    normalize_layout_for_create,
    layout_fields_for_create,
    layout_field_linkable_is_asset_layout_scope,
)
from hudu_magic.models import AssetLayout


def test_layout_fields_for_create_strips_list_id_on_non_list_select():
    raw = [
        {
            "label": "a",
            "field_type": "Text",
            "position": 2,
            "list_id": 99,
            "id": 1,
            "value": "x",
        },
        {
            "label": "b",
            "field_type": LIST_SELECT_FIELD_TYPE,
            "position": 1,
            "list_id": 5,
            "id": 2,
        },
    ]
    out = layout_fields_for_create(raw)
    assert len(out) == 2
    assert out[0]["position"] == 1
    assert out[0]["field_type"] == LIST_SELECT_FIELD_TYPE
    assert out[0]["list_id"] == 5
    assert out[1]["field_type"] == "Text"
    assert "list_id" not in out[1]


def test_layout_fields_for_create_omits_integration_linkable():
    raw = [
        {
            "label": "x",
            "field_type": "Text",
            "position": 1,
            "linkable_id": 42,
            "linkable_type": "Integration::Something",
        },
    ]
    out = layout_fields_for_create(raw)
    assert "linkable_id" not in out[0]


def test_layout_field_linkable_is_asset_layout_scope_blank_type_with_id():
    assert layout_field_linkable_is_asset_layout_scope(
        {"linkable_id": 5, "linkable_type": None}
    )


def test_collect_list_ids_from_layouts():
    layouts = [
        {
            "fields": [
                {"field_type": LIST_SELECT_FIELD_TYPE, "list_id": 3, "position": 1},
                {"field_type": "Text", "list_id": 3, "position": 2},
            ]
        }
    ]
    assert collect_list_ids_from_layouts(layouts) == {3}


def test_normalize_layout_for_create_list_id_map():
    layout = {
        "name": "L1",
        "icon": "fas fa-server",
        "fields": [
            {
                "label": "s",
                "field_type": LIST_SELECT_FIELD_TYPE,
                "position": 1,
                "list_id": 10,
            },
        ],
    }
    payload = normalize_layout_for_create(layout, list_id_map={10: 200})
    assert payload["name"] == "L1"
    assert payload["fields"][0]["list_id"] == 200
    assert payload["icon"] == "fas fa-server"


def test_normalize_layout_for_create_applies_create_defaults():
    layout = {"name": "Bare", "fields": []}
    payload = normalize_layout_for_create(layout)
    assert payload["icon"] == "fas fa-play-circle"
    assert payload["color"] == "#6136ff"
    assert payload["icon_color"] == "#ffffff"
    assert payload["include_passwords"] is True
    assert payload["include_photos"] is True
    assert payload["include_comments"] is True
    assert payload["include_files"] is True


def test_normalize_layout_for_create_preserves_explicit_false_include():
    layout = {
        "name": "X",
        "include_photos": False,
        "fields": [],
    }
    payload = normalize_layout_for_create(layout)
    assert payload["include_photos"] is False


def test_normalize_layout_for_create_missing_list_id_raises():
    layout = {
        "name": "L1",
        "fields": [
            {
                "label": "s",
                "field_type": LIST_SELECT_FIELD_TYPE,
                "position": 1,
                "list_id": 10,
            },
        ],
    }
    with pytest.raises(KeyError):
        normalize_layout_for_create(layout, list_id_map={11: 99})


def test_asset_layout_to_create_payload_matches_helper():
    client = MagicMock()
    data = {"name": "FromModel", "fields": []}
    layout = AssetLayout(client, HuduEndpoint.ASSET_LAYOUTS, data)
    assert layout.to_create_payload() == normalize_layout_for_create(data)

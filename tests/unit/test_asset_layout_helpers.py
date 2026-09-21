"""Unit tests for :mod:`hudu_magic.helpers.asset_layouts`."""

from unittest.mock import MagicMock

import pytest

from hudu_magic.constants import LIST_SELECT_FIELD_TYPE
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.helpers.asset_layouts import (
    build_deferred_linkable_update_payload,
    collect_list_ids_from_layouts,
    layout_field_linkable_is_asset_layout_scope,
    layout_fields_for_create,
    layout_has_self_referential_linkables,
    layout_needs_linkable_patch,
    normalize_layout_for_create,
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
        {"field_type": "AssetTag", "linkable_id": 5, "linkable_type": None}
    )
    # Stale linkable_id on non-AssetTag fields must not participate.
    assert not layout_field_linkable_is_asset_layout_scope(
        {"field_type": "Text", "linkable_id": 5, "linkable_type": None}
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


def test_layout_has_self_referential_linkables():
    layout = {
        "id": 72,
        "name": "Serveurs",
        "fields": [
            {
                "label": "Hyperviseur",
                "field_type": "AssetLink",
                "position": 1,
                "linkable_id": 72,
                "linkable_type": "AssetLayout",
            },
            {
                "label": "Site",
                "field_type": "AssetLink",
                "position": 2,
                "linkable_id": 10,
                "linkable_type": "AssetLayout",
            },
        ],
    }
    assert layout_has_self_referential_linkables(layout) is True
    layout["fields"][0]["linkable_id"] = 99
    assert layout_has_self_referential_linkables(layout) is False


def test_normalize_defers_self_referential_linkable_until_mapped():
    layout = {
        "id": 72,
        "name": "Serveurs",
        "icon": "fas fa-server",
        "fields": [
            {
                "label": "Hyperviseur",
                "field_type": "AssetLink",
                "position": 1,
                "linkable_id": 72,
                "linkable_type": "AssetLayout",
            },
            {
                "label": "Location",
                "field_type": "AssetLink",
                "position": 2,
                "linkable_id": 10,
                "linkable_type": "AssetLayout",
            },
        ],
    }
    batch = {10, 72}
    # Before the layout exists on target: self-ref omitted, other refs mapped.
    create_payload = normalize_layout_for_create(
        layout,
        layout_id_map={10: 500},
        batch_source_layout_ids=batch,
    )
    by_label = {f["label"]: f for f in create_payload["fields"]}
    assert "linkable_id" not in by_label["Hyperviseur"]
    assert by_label["Location"]["linkable_id"] == 500

    # After create: source 72 -> target 900 is known, self-ref remaps.
    patch_payload = normalize_layout_for_create(
        layout,
        layout_id_map={10: 500, 72: 900},
        batch_source_layout_ids=batch,
    )
    by_label = {f["label"]: f for f in patch_payload["fields"]}
    assert by_label["Hyperviseur"]["linkable_id"] == 900
    assert by_label["Location"]["linkable_id"] == 500


def test_normalize_self_ref_raises_when_defer_disabled_and_unmapped():
    layout = {
        "id": 72,
        "name": "Serveurs",
        "fields": [
            {
                "label": "Hyperviseur",
                "field_type": "AssetLink",
                "position": 1,
                "linkable_id": 72,
            },
        ],
    }
    with pytest.raises(RuntimeError, match="ordering bug"):
        normalize_layout_for_create(
            layout,
            layout_id_map={},
            batch_source_layout_ids={72},
            defer_self_linkables=False,
        )


def test_normalize_defers_unmapped_batch_linkables_for_cycles():
    layout_a = {
        "id": 1,
        "name": "A",
        "fields": [
            {
                "label": "ToB",
                "field_type": "AssetLink",
                "position": 1,
                "linkable_id": 2,
                "linkable_type": "AssetLayout",
            },
        ],
    }
    batch = {1, 2}
    # Simulate creating A before B exists on target.
    create_a = normalize_layout_for_create(
        layout_a,
        layout_id_map={},
        batch_source_layout_ids=batch,
        defer_unmapped_batch_linkables=True,
    )
    assert "linkable_id" not in create_a["fields"][0]

    patch_a = normalize_layout_for_create(
        layout_a,
        layout_id_map={1: 100, 2: 200},
        batch_source_layout_ids=batch,
    )
    assert patch_a["fields"][0]["linkable_id"] == 200


def test_layout_needs_linkable_patch_for_batch_and_self():
    self_layout = {
        "id": 5,
        "fields": [{"label": "self", "linkable_id": 5, "field_type": "AssetLink"}],
    }
    other = {
        "id": 5,
        "fields": [{"label": "to6", "linkable_id": 6, "field_type": "AssetLink"}],
    }
    none = {
        "id": 5,
        "fields": [{"label": "text", "field_type": "Text"}],
    }
    assert layout_needs_linkable_patch(self_layout, {5, 6}) is True
    assert layout_needs_linkable_patch(other, {5, 6}) is True
    assert layout_needs_linkable_patch(none, {5, 6}) is False
    assert layout_needs_linkable_patch(other, {5}) is False


def test_build_deferred_linkable_update_payload_includes_target_field_ids():
    source = {
        "id": 10,
        "name": "Servers",
        "fields": [
            {
                "label": "Hypervisor",
                "field_type": "AssetTag",
                "position": 1,
                "linkable_id": 10,
            },
            {
                "label": "Notes",
                "field_type": "Text",
                "position": 2,
                "linkable_id": 10,  # stale; ignored
            },
        ],
    }
    target = {
        "id": 100,
        "name": "Servers",
        "fields": [
            {
                "id": 501,
                "label": "Hypervisor",
                "field_type": "AssetTag",
                "position": 1,
            },
            {
                "id": 502,
                "label": "Notes",
                "field_type": "Text",
                "position": 2,
            },
        ],
    }
    patch = build_deferred_linkable_update_payload(
        source, target, layout_id_map={10: 100}
    )
    assert patch == {
        "fields": [
            {
                "id": 501,
                "label": "Hypervisor",
                "field_type": "AssetTag",
                "linkable_id": 100,
                "position": 1,
            }
        ]
    }


def test_layout_fields_for_create_ignores_linkable_on_text():
    out = layout_fields_for_create(
        [
            {
                "label": "t",
                "field_type": "Text",
                "position": 1,
                "linkable_id": 99,
            },
            {
                "label": "a",
                "field_type": "AssetTag",
                "position": 2,
                "linkable_id": 7,
            },
        ]
    )
    assert "linkable_id" not in out[0]
    assert out[1]["linkable_id"] == 7

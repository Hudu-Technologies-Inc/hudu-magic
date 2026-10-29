import pytest

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.validation import HuduValidationError, validate_payload


def test_articles_endpoint_exists():
    assert HuduEndpoint.ARTICLES.endpoint == "articles"


def test_articles_is_paginated():
    assert HuduEndpoint.ARTICLES.is_paginated is True


def test_api_info_not_paginated():
    assert HuduEndpoint.API_INFO.is_paginated is False


def test_photos_has_form_params():
    assert HuduEndpoint.PHOTOS.meta.form_params

def test_endpoint_has_methods():
    assert "GET" in HuduEndpoint.ASSETS.meta.methods


def test_rack_storage_items_create_fields_are_flat():
    """OpenAPI 2.49.0 inlines create props; clients pass flat fields, not a wrapper key."""
    meta = HuduEndpoint.RACK_STORAGE_ITEMS.meta
    assert "rack_storage_item" not in meta.create_fields
    assert meta.create_required_fields == ("rack_storage_id", "start_unit", "end_unit")
    validate_payload(
        HuduEndpoint.RACK_STORAGE_ITEMS,
        {"rack_storage_id": 1, "start_unit": 1, "end_unit": 4},
        "create",
    )


def test_rack_storage_items_create_requires_units():
    with pytest.raises(HuduValidationError, match="start_unit"):
        validate_payload(
            HuduEndpoint.RACK_STORAGE_ITEMS,
            {"rack_storage_id": 1, "end_unit": 4},
            "create",
        )


def test_rack_storage_items_update_fields_are_flat():
    meta = HuduEndpoint.RACK_STORAGE_ITEMS_ID.meta
    assert "rack_storage_item" not in meta.update_fields
    assert "start_unit" in meta.update_fields
    validate_payload(
        HuduEndpoint.RACK_STORAGE_ITEMS_ID,
        {"start_unit": 2, "end_unit": 5},
        "update",
    )
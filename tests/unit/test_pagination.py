from hudu_magic.constants import HUDU_DEFAULT_PAGE_SIZE, HUDU_DENSE_PAGE_SIZE
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.helpers.pagination import (
    collect_paginated_items,
    default_page_size_for,
    extract_page_items,
)


def test_default_page_size_for_dense_resources():
    assert default_page_size_for(HuduEndpoint.ARTICLES) == HUDU_DENSE_PAGE_SIZE
    assert default_page_size_for(HuduEndpoint.ASSETS) == HUDU_DENSE_PAGE_SIZE
    assert default_page_size_for("companies/3/assets") == HUDU_DENSE_PAGE_SIZE
    assert default_page_size_for(HuduEndpoint.COMPANIES) == HUDU_DEFAULT_PAGE_SIZE
    assert default_page_size_for("asset_passwords/1/shares") == HUDU_DEFAULT_PAGE_SIZE


def test_extract_page_items_prefers_named_keys():
    assert extract_page_items(
        {"assets": [{"id": 1}], "items": [{"id": 9}]},
        ("assets", "items"),
    ) == [{"id": 1}]
    assert extract_page_items([{"id": 2}]) == [{"id": 2}]
    assert extract_page_items({"items": [{"id": 3}]}) == [{"id": 3}]


def test_collect_paginated_items_stops_on_duplicate_signature():
    pages = [
        {"rows": [{"id": 1}, {"id": 2}]},
        {"rows": [{"id": 1}, {"id": 2}]},
    ]

    def fetch(params):
        return pages[params["page"] - 1]

    items = collect_paginated_items(
        fetch,
        {"page_size": 2},
        property_names=("rows",),
        default_page_size=None,
    )
    assert items == [{"id": 1}, {"id": 2}]


def test_collect_paginated_items_injects_default_page_size():
    seen = []

    def fetch(params):
        seen.append(dict(params))
        return {"rows": []}

    collect_paginated_items(fetch, property_names=("rows",), default_page_size=500)
    assert seen[0]["page_size"] == 500
    assert seen[0]["page"] == 1

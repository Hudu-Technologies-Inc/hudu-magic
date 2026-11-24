"""Shared list pagination (empty page / duplicate-page stop conditions)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from ..constants import HUDU_DEFAULT_PAGE_SIZE, HUDU_DENSE_PAGE_SIZE
from ..endpoints import HuduEndpoint

# Resources whose list rows are often large (HTML bodies, custom fields, etc.).
_DENSE_LIST_RESOURCE_NAMES = frozenset({"articles", "assets"})


def default_page_size_for(endpoint_or_path: HuduEndpoint | str) -> int:
    """
    Choose an omitted-``page_size`` default.

    Articles and assets use :data:`HUDU_DENSE_PAGE_SIZE` (250); everything else
    uses :data:`HUDU_DEFAULT_PAGE_SIZE` (1000).
    """
    if isinstance(endpoint_or_path, HuduEndpoint):
        name = endpoint_or_path.resource_name
    else:
        name = str(endpoint_or_path).strip("/").rstrip("/").split("/")[-1]
    if name in _DENSE_LIST_RESOURCE_NAMES:
        return HUDU_DENSE_PAGE_SIZE
    return HUDU_DEFAULT_PAGE_SIZE


def extract_page_items(
    result: Any,
    property_names: Sequence[str] | None = None,
) -> list:
    """Pull the item list out of a page payload (dict wrapper or bare list)."""
    if isinstance(result, list):
        return result
    if not isinstance(result, dict):
        return []

    for key in property_names or ():
        value = result.get(key)
        if isinstance(value, list):
            return value

    for key in ("items", "data"):
        value = result.get(key)
        if isinstance(value, list):
            return value

    return []


def collect_paginated_items(
    fetch_page: Callable[[dict], Any],
    params: dict | None = None,
    *,
    property_names: Sequence[str] | None = None,
    default_page_size: int | None = HUDU_DEFAULT_PAGE_SIZE,
    max_pages: int | None = None,
) -> list[dict]:
    """
    Walk ``page=1..N`` until an empty page or a repeated id signature.

    When ``page_size`` is absent from ``params`` and ``default_page_size`` is set,
    that size is sent so list endpoints use fewer round-trips.
    ``max_pages`` is an optional safety cap (``None`` = unlimited).
    """
    query = dict(params or {})
    if default_page_size is not None and "page_size" not in query:
        query["page_size"] = default_page_size

    page = 1
    all_items: list[dict] = []
    seen_signatures: set[tuple] = set()

    while True:
        if max_pages is not None and page > max_pages:
            raise RuntimeError(
                f"Pagination exceeded max_pages={max_pages} "
                f"(last page had {len(all_items)} accumulated items)"
            )

        page_params = dict(query)
        page_params["page"] = page
        result = fetch_page(page_params)
        items = extract_page_items(result, property_names)

        if not items:
            break

        signature = tuple(
            item.get("id") for item in items if isinstance(item, dict)
        )
        if signature in seen_signatures:
            break

        seen_signatures.add(signature)
        all_items.extend(item for item in items if isinstance(item, dict))
        page += 1

    return all_items

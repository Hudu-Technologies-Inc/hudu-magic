from unittest.mock import MagicMock

import pytest

from hudu_magic.client import HuduClient
from hudu_magic.constants import HUDU_DEFAULT_PAGE_SIZE, HUDU_DENSE_PAGE_SIZE
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import Article, HuduCollection, Matcher, Procedure, Share
from hudu_magic.validation import HuduNotImplementedError


def test_get_dispatches_paginated_single_item_wraps_to_model():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    client._get_all_pages = MagicMock(return_value=[{"id": 1}])
    client._get_nonpaginated = MagicMock()

    result = client.get(HuduEndpoint.ARTICLES)

    client._get_all_pages.assert_called_once()
    client._get_nonpaginated.assert_not_called()

    assert isinstance(result, HuduCollection)
    assert len(result) == 1
    assert isinstance(result[0], Article)
    assert result[0].id == 1


def test_get_dispatches_paginated_multiple_items_returns_collection():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    client._get_all_pages = MagicMock(
        return_value=[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    )
    client._get_nonpaginated = MagicMock()

    result = client.get(HuduEndpoint.ARTICLES)

    assert isinstance(result, HuduCollection)
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2

def test_wrap_result_procedures_accepts_processes_collection_key():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    result = client._wrap_result(
        HuduEndpoint.PROCEDURES,
        {"processes": [{"id": 1, "name": "One"}]},
    )

    assert isinstance(result, HuduCollection)
    assert len(result) == 1
    assert isinstance(result[0], Procedure)
    assert result[0].id == 1


def test_wrap_result_shares_accepts_shares_collection_key():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    listed = client._wrap_result(
        HuduEndpoint.ASSET_PASSWORDS_ASSET_PASSWORD_ID_SHARES,
        {"shares": [{"id": 4, "shareable_id": 9, "url": "https://example/s/a"}]},
    )
    assert isinstance(listed, HuduCollection)
    assert len(listed) == 1
    assert isinstance(listed[0], Share)
    assert listed[0].id == 4

    one = client._wrap_result(
        HuduEndpoint.ASSET_PASSWORDS_ASSET_PASSWORD_ID_SHARES_ID,
        {"share": {"id": 4, "shareable_id": 9, "url": "https://example/s/a"}},
    )
    assert isinstance(one, Share)
    assert one.url == "https://example/s/a"


def test_client_share_aliases():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")
    assert client.share is client.shares
    assert client.sharing_link is client.shares
    assert client.sharing_links is client.shares


def test_get_dispatches_nonpaginated():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    client._get_all_pages = MagicMock()
    client._get_nonpaginated = MagicMock(return_value={"version": "1"})

    result = client.get(HuduEndpoint.API_INFO)

    client._get_nonpaginated.assert_called_once()
    client._get_all_pages.assert_not_called()

    assert result == {"version": "1"}


def test_get_all_pages_defaults_page_size_and_stops_on_empty():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")
    client._get_nonpaginated = MagicMock(
        side_effect=[
            {"articles": [{"id": 1}, {"id": 2}]},
            {"articles": []},
        ]
    )

    items = client._get_all_pages(HuduEndpoint.ARTICLES)

    assert items == [{"id": 1}, {"id": 2}]
    assert client._get_nonpaginated.call_count == 2
    first_params = client._get_nonpaginated.call_args_list[0].args[1]
    assert first_params["page"] == 1
    assert first_params["page_size"] == HUDU_DENSE_PAGE_SIZE


def test_get_all_pages_uses_dense_size_for_assets_and_default_elsewhere():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")
    client._get_nonpaginated = MagicMock(return_value={"assets": []})
    client._get_all_pages(HuduEndpoint.ASSETS)
    assert (
        client._get_nonpaginated.call_args.args[1]["page_size"] == HUDU_DENSE_PAGE_SIZE
    )

    client._get_nonpaginated = MagicMock(return_value={"companies": []})
    client._get_all_pages(HuduEndpoint.COMPANIES)
    assert (
        client._get_nonpaginated.call_args.args[1]["page_size"] == HUDU_DEFAULT_PAGE_SIZE
    )

    client._get_nonpaginated = MagicMock(return_value={"assets": []})
    client._paginate("companies/9/assets", property_names=("assets",))
    assert (
        client._get_nonpaginated.call_args.args[1]["page_size"] == HUDU_DENSE_PAGE_SIZE
    )


def test_get_all_pages_respects_explicit_page_size_and_max_pages():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")
    client._get_nonpaginated = MagicMock(
        side_effect=[
            {"articles": [{"id": 1}]},
            {"articles": [{"id": 2}]},
            {"articles": [{"id": 3}]},
        ]
    )

    with pytest.raises(RuntimeError, match="max_pages"):
        client._get_all_pages(HuduEndpoint.ARTICLES, {"page_size": 1}, max_pages=2)

    assert client._get_nonpaginated.call_count == 2
    assert client._get_nonpaginated.call_args_list[0].args[1]["page_size"] == 1


def test_client_matchers_resource_and_aliases():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")
    assert client.matcher is client.matchers
    assert client.matchers.endpoint == HuduEndpoint.MATCHERS

    listed = client._wrap_result(
        HuduEndpoint.MATCHERS,
        {"matchers": [{"id": 3, "company_id": 9}]},
    )
    assert isinstance(listed, HuduCollection)
    assert isinstance(listed[0], Matcher)
    assert listed[0].id == 3

    with pytest.raises(HuduNotImplementedError, match="get by id"):
        client.matchers.get(3)
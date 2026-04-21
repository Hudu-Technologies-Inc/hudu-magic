from unittest.mock import MagicMock

from hudu_magic.client import HuduClient
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import Article, HuduCollection, Procedure


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


def test_get_dispatches_nonpaginated():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    client._get_all_pages = MagicMock()
    client._get_nonpaginated = MagicMock(return_value={"version": "1"})

    result = client.get(HuduEndpoint.API_INFO)

    client._get_nonpaginated.assert_called_once()
    client._get_all_pages.assert_not_called()

    assert result == {"version": "1"}
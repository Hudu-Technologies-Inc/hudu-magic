from unittest.mock import MagicMock

from hudu_magic.client import HuduClient
from hudu_magic.endpoints import HuduEndpoint


def test_get_dispatches_paginated():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    client._get_all_pages = MagicMock(return_value=[{"id": 1}])
    client._get_nonpaginated = MagicMock()

    result = client.get(HuduEndpoint.ARTICLES)

    client._get_all_pages.assert_called_once()
    client._get_nonpaginated.assert_not_called()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == 1

def test_get_dispatches_nonpaginated():
    client = HuduClient(api_key="x", instance_url="example.hudu.app")

    client._get_all_pages = MagicMock()
    client._get_nonpaginated = MagicMock(return_value={"version": "1"})

    result = client.get(HuduEndpoint.API_INFO)

    client._get_nonpaginated.assert_called_once()
    client._get_all_pages.assert_not_called()

    assert result == {"version": "1"}
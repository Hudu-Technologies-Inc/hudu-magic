from unittest.mock import MagicMock

import pytest
import requests

from hudu_magic.client import HuduClient
from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.validation import HuduAPIError


def _response(
    status_code=200,
    text='{"ok": true}',
    content_type="application/json",
    method="GET",
    url="https://example.hudu.app/api/v1/x",
    body=None,
):
    r = requests.Response()
    r.status_code = status_code
    r._content = text.encode("utf-8")
    r.headers["Content-Type"] = content_type
    r.url = url
    r.request = MagicMock()
    r.request.method = method
    r.request.url = url
    r.request.body = body
    return r


def test_build_url_with_enum():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    url = client.build_url(HuduEndpoint.API_INFO)
    assert url == "https://ex.hudu.app/api/v1/api_info"


def test_build_url_with_string_strips_leading_slash():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    assert client.build_url("/custom/path") == "https://ex.hudu.app/api/v1/custom/path"


def test_resolve_path_enum_with_id():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    path = client.resolve_path(HuduEndpoint.COMPANIES_ID, 42)
    assert path == "/companies/42"


def test_resolve_path_string_with_id():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    assert client.resolve_path("widgets", 7) == "/widgets/7"


def test_resolve_path_string_with_brace_id():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    assert client.resolve_path("items/{id}/sub", 99) == "/items/99/sub"


def test_handle_response_json_ok():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    out = client._handle_response(_response(text='{"a": 1}'))
    assert out == {"a": 1}


def test_handle_response_empty_body():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    r = _response(text="   ")
    assert client._handle_response(r) is None


def test_handle_response_non_json_content_type():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    r = _response(text="plain", content_type="text/plain")
    assert client._handle_response(r) == "plain"


def test_handle_response_error_uses_json_message():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    r = _response(
        status_code=422,
        text='{"message": "bad input"}',
        content_type="application/json",
        method="POST",
    )
    with pytest.raises(HuduAPIError) as excinfo:
        client._handle_response(r)
    assert "422" in str(excinfo.value)
    assert "bad input" in str(excinfo.value)


def test_check_version_caches(monkeypatch):
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    client.get = MagicMock(return_value={"version": "1.2.3"})
    assert client.check_version() == "1.2.3"
    assert client.check_version() == "1.2.3"
    client.get.assert_called_once()


def test_get_forces_nonpaginated_when_paginate_false():
    client = HuduClient(api_key="k", instance_url="https://ex.hudu.app")
    client._get_all_pages = MagicMock()
    client._get_nonpaginated = MagicMock(return_value={"articles": []})
    client.get(HuduEndpoint.ARTICLES, paginate=False)
    client._get_nonpaginated.assert_called_once()
    client._get_all_pages.assert_not_called()

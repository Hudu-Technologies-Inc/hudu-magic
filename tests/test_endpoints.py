from hudu_magic.endpoints import HuduEndpoint


def test_endpoint_path():
    assert HuduEndpoint.COMPANIES.path == "/companies"


def test_endpoint_item_path():
    assert HuduEndpoint.ARTICLES.item_path(123) == "/articles/123"


def test_endpoint_pagination_flag():
    assert HuduEndpoint.ARTICLES.is_paginated is True
    assert HuduEndpoint.NETWORKS.is_paginated is False
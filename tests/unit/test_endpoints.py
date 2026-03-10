from hudu_magic.endpoints import HuduEndpoint

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
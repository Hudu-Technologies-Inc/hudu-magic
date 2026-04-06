from unittest.mock import MagicMock

import pytest

from hudu_magic.endpoints import HuduEndpoint
from hudu_magic.models import Article


def test_huduobject_getattr_and_dict_access():
    client = MagicMock()
    data = {"id": 5, "name": "Hello"}
    obj = Article(client, HuduEndpoint.ARTICLES, data)
    assert obj.id == 5
    assert obj.name == "Hello"
    assert obj.get("missing", "d") == "d"


def test_huduobject_repr_contains_class_and_id():
    client = MagicMock()
    obj = Article(client, HuduEndpoint.ARTICLES, {"id": 3, "name": "N"})
    assert "Article" in repr(obj)
    assert "3" in repr(obj)
    assert "N" in repr(obj)


def test_huduobject_unknown_attribute():
    client = MagicMock()
    obj = Article(client, HuduEndpoint.ARTICLES, {"id": 1})
    with pytest.raises(AttributeError):
        _ = obj.no_such_field
